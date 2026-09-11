import inspect
import json
import threading
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from canvasapi.course import Course

from .actions import (AbsencePolicy, Create, Delete, DeploymentContext, DeploymentResult,
                      Outcome, Update)
from .checksums import MD5Sums
from .executor import execute_dag, retry_rate_limit
from .handlers import build_builtin_handlers
from .migration import migrate_ledger
from .planner import PlanningError, plan_deployment
from ..deployment_report import DeploymentReport
from ..our_logging import get_logger
from ..resources import CanvasResource, iter_keys


def make_iso(date, time_zone):
    # Kept here as a public helper used by existing callers.
    import pytz
    if isinstance(date, datetime):
        return date.isoformat()
    if not isinstance(date, str):
        raise TypeError("Date must be a datetime object or a string")
    for form in ("%b %d, %Y, %I:%M %p", "%b %d %Y %I:%M %p", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(date, form)
            return parsed.isoformat() if parsed.tzinfo else pytz.timezone(time_zone).localize(parsed).isoformat()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date}")


def post_process_resource(resource_data, timezone) -> dict:
    import re
    from zoneinfo import ZoneInfo
    text = json.dumps(resource_data)
    pattern = r'''<\s*timestamp\s*(?:format\s*=\s*(\\"|')([^"']*)\1)?\s*(/>|>\s*</timestamp>)'''
    while match := re.search(pattern, text):
        text = text.replace(match.group(0), datetime.now(ZoneInfo(timezone)).strftime(match.group(2) or "%B %d, %Y at %I:%M %p"))
    return json.loads(text)


def _raw_key(key: tuple[str, str]) -> str:
    return f"{key[0]}|{key[1]}"


def _reference_requests(resource: CanvasResource) -> list[tuple[str, str, str, str]]:
    return list(iter_keys(json.dumps(resource["data"])))


def _snapshot_execution_inputs(
        action: Create | Update,
        raw_key: str,
        writable: dict,
        requests: list[tuple[str, str, str, str]],
        lock,
) -> tuple[dict[str, object], dict | None]:
    references: dict[str, object] = {}
    with lock:
        entries = writable["resources"]
        for token, resource_type, resource_id, field in requests:
            info = entries[_raw_key((resource_type, resource_id))]["canvas_info"]
            if field not in info:
                raise ValueError(f"Missing field '{field}' in {resource_type} {resource_id}")
            references[token] = deepcopy(info[field])

        update_info = None
        if isinstance(action, Update):
            entry = entries.get(raw_key)
            update_info = deepcopy(entry.get("canvas_info")) if entry else None
    return references, update_info


def _bind(resource: CanvasResource, references: dict[str, object], timezone: str) -> CanvasResource:
    copied = deepcopy(resource)
    text = json.dumps(copied["data"])
    for token, value in references.items():
        text = text.replace(token, str(value))
    copied["data"] = post_process_resource(json.loads(text), timezone)
    return copied


def _action_kind(action: Create | Update | Delete) -> str:
    if isinstance(action, Create):
        return "create"
    if isinstance(action, Update):
        return "update"
    return "untrack" if action.absence_policy is AbsencePolicy.UNTRACK else "delete"


def _log_plan(nodes) -> None:
    logger = get_logger()
    logger.info("Planned %d actions", len(nodes))
    counts: dict[str, dict[str, int]] = {}
    for node in nodes:
        resource_type = node.planned_change.resource_type
        counts.setdefault(resource_type, {kind: 0 for kind in ("create", "update", "delete", "untrack")})[_action_kind(node.action)] += 1
    for resource_type in sorted(counts):
        row = counts[resource_type]
        logger.info(
            "Plan %s: create=%d update=%d delete=%d untrack=%d",
            resource_type, row["create"], row["update"], row["delete"], row["untrack"],
        )


def _planning_error_context(error):
    resource = getattr(error, "resource", None)
    if resource:
        return {
            "resource_type": resource["type"],
            "resource_id": str(resource["id"]),
        }, resource.get("content_path")
    return None, None


def _course_url(course: Course) -> str | None:
    canvas = getattr(course, "canvas", None)
    requester = getattr(canvas, "_Canvas__requester", None)
    base_url = getattr(requester, "original_url", None)
    course_id = getattr(course, "id", None)
    if not base_url or course_id is None:
        return None
    return f"{str(base_url).rstrip('/')}/courses/{course_id}"


def deploy_to_canvas(course: Course, timezone: str,
                     resources: dict[tuple[str, str], CanvasResource],
                     report: DeploymentReport, deploy_root: Path,
                     dryrun: bool = False, no_cleanup: bool = False):
    report.configure(dryrun=dryrun, no_cleanup=no_cleanup)
    store = MD5Sums(course, deploy_root)
    try:
        canonical, migration_changed = migrate_ledger(store.load())
        handlers = build_builtin_handlers()
        plan = plan_deployment(deepcopy(resources), deepcopy(canonical), handlers, deploy_root,
                               no_cleanup=no_cleanup)
        report.set_expected_changes(plan.expected_changes)
        _log_plan(plan.nodes)
    except Exception as error:
        change, source = _planning_error_context(error)
        report.add_deployment_error("planning", error, change, source)
        return report

    if dryrun:
        return report

    report.set_course_url(_course_url(course))
    writable = deepcopy(canonical)
    context = DeploymentContext(course, deploy_root, timezone)
    lock = threading.Lock()
    completed: dict[str, tuple[Outcome, DeploymentResult | None]] = {}

    def run(node):
        action = node.action
        resource_key = node.planned_change.key
        raw_key = _raw_key(resource_key)
        if isinstance(action, Delete):
            if action.absence_policy is AbsencePolicy.UNTRACK:
                outcome = Outcome.UNTRACKED
            else:
                deleted = retry_rate_limit(
                    lambda: handlers[action.resource_type].delete(context, action.resource_id, deepcopy(action.canvas_info)),
                    key=node.key,
                )
                outcome = Outcome.DELETED if deleted else Outcome.ALREADY_ABSENT
            with lock:
                writable["resources"].pop(raw_key, None)
                completed[node.key] = outcome, None
            return outcome, None

        requests = _reference_requests(action.resource)
        references, update_info = _snapshot_execution_inputs(
            action, raw_key, writable, requests, lock,
        )
        resource = _bind(action.resource, references, timezone)
        spec = handlers[resource_key[0]]
        if isinstance(action, Create):
            result = retry_rate_limit(lambda: spec.create(context, resource), key=node.key)
            outcome = Outcome.CREATED
        else:
            if not update_info:
                raise ValueError(f"No Canvas identity for update of {resource_key[0]} {resource_key[1]}")
            result = retry_rate_limit(
                lambda: spec.update(context, resource, deepcopy(update_info)), key=node.key,
            )
            outcome = Outcome.UPDATED
        if not isinstance(result, DeploymentResult) or not result.canvas_info or not result.canvas_info.get("id"):
            raise ValueError(f"Handler returned incomplete Canvas identity for {resource_key}")

        canvas_info = deepcopy(result.canvas_info)
        recorded_result = DeploymentResult(canvas_info, result.url, result.review)
        entry = {"checksum": action.checksum, "canvas_info": canvas_info}
        with lock:
            writable["resources"][raw_key] = entry
            completed[node.key] = outcome, recorded_result
        return outcome, recorded_result

    logger = get_logger()
    execution_started = False
    coordinator_failed = False
    interrupted: KeyboardInterrupt | None = None
    resolved = {"successful": 0, "failed": 0, "blocked": 0}
    observed_errors: dict[str, tuple[str, Exception]] = {}
    execution_started_at = time.perf_counter()

    def observe_resolution(node, status, value):
        resolved[status if status != "success" else "successful"] += 1
        if status in {"failed", "blocked"}:
            observed_errors[node.key] = status, value
        kind = _action_kind(node.action)
        identity = f"{kind} {node.planned_change.resource_type} {node.planned_change.resource_id}"
        if status == "success":
            logger.info("%d/%d: %s", sum(resolved.values()), len(plan.nodes), identity)
        elif status == "failed":
            logger.error("%d/%d: %s FAILED", sum(resolved.values()), len(plan.nodes), identity)
        else:
            logger.info("%d/%d: %s BLOCKED", sum(resolved.values()), len(plan.nodes), identity)

    try:
        execution_started = True
        if "on_resolved" in inspect.signature(execute_dag).parameters:
            execution = execute_dag(plan.nodes, run, on_resolved=observe_resolution)
        else:
            # Preserve compatibility with callers that replace the coordinator.
            execution = execute_dag(plan.nodes, run)
    except KeyboardInterrupt as error:
        interrupted = error
        report.report["deployment"]["errors"].append({
            "stage": "deployment",
            "error": "Deployment interrupted by user",
        })
        execution = None
    except Exception as error:
        coordinator_failed = True
        report.add_deployment_error("deployment", error)
        execution = None

    by_key = {node.key: node for node in plan.nodes}
    for key in sorted(completed, key=lambda item: by_key[item].plan_order):
        node = by_key[key]
        outcome, result = completed[key]
        report.add_change_made(
            node.planned_change, outcome,
            url=result.url if result else None,
            review=result.review if result else None,
        )

    if execution is not None:
        errors = {
            **{key: ("failed", error) for key, error in execution.failures.items()},
            **{key: ("blocked", error) for key, error in execution.blocked.items()},
        }
    elif interrupted is not None:
        errors = observed_errors
    else:
        errors = {}
    for key in sorted(errors, key=lambda item: by_key[item].plan_order):
        status, error = errors[key]
        node = by_key[key]
        report.add_deployment_error(
            "deployment", error, node.planned_change,
            status=status, action=_action_kind(node.action),
        )

    if migration_changed or completed or interrupted is not None or (execution_started and coordinator_failed):
        try:
            store.save(writable)
        except KeyboardInterrupt as error:
            report.report["deployment"]["errors"].append({
                "stage": "ledger_persistence",
                "error": "Ledger persistence interrupted by user",
            })
            if interrupted is None:
                interrupted = error
        except Exception as error:
            report.add_deployment_error("ledger_persistence", error)
    if interrupted is not None:
        raise interrupted
    logger.info(
        "Deployment completed in %.2fs: successful=%d failed=%d blocked=%d",
        time.perf_counter() - execution_started_at,
        resolved["successful"], resolved["failed"], resolved["blocked"],
    )
    return report
