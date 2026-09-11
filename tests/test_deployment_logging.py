import logging
import re
import threading
from copy import deepcopy

from mdxcanvas.deploy.actions import DeploymentResult, HandlerSpec
from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.handlers import build_builtin_handlers
from mdxcanvas.deployment_report import DeploymentReport


class Store:
    def __init__(self, envelope):
        self.envelope = deepcopy(envelope)
        self.saves = []

    def load(self):
        return deepcopy(self.envelope)

    def save(self, envelope):
        self.saves.append(deepcopy(envelope))


def resource(resource_type, resource_id, data):
    return {
        "type": resource_type,
        "id": resource_id,
        "data": data,
        "content_path": "course.md",
    }


def install(monkeypatch, store, handlers):
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr(
        "mdxcanvas.deploy.canvas_deploy.build_builtin_handlers", lambda: handlers,
    )


def messages(caplog, prefix):
    return [record.getMessage() for record in caplog.records if record.getMessage().startswith(prefix)]


def progress_records(caplog):
    return [
        record for record in caplog.records
        if re.match(r"\d+/\d+: ", record.getMessage())
    ]


def test_dry_run_logs_deterministic_grouped_plan_without_execution_records(
        monkeypatch, tmp_path, caplog):
    calls = []
    handlers = build_builtin_handlers()

    def unexpected(*_args):
        calls.append("handler")
        raise AssertionError("dry-run invoked a handler")

    for resource_type in ("page", "quiz"):
        original = handlers[resource_type]
        handlers[resource_type] = HandlerSpec(
            unexpected,
            unexpected,
            original.delete,
            modified_action=original.modified_action,
            absence_policy=original.absence_policy,
            prepare_cycle_breaker=original.prepare_cycle_breaker,
        )
    store = Store({
        "mdxcanvas_version": "0.8.0",
        "resources": {
            "quiz|changed": {"checksum": "old", "canvas_info": {"id": "2"}},
            "assignment|stale": {"checksum": "old", "canvas_info": {"id": "3"}},
            "syllabus|syllabus": {"checksum": "old", "canvas_info": {"id": "4"}},
        },
    })
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "new"): resource("page", "new", {"title": "New", "body": ""}),
        ("quiz", "changed"): resource(
            "quiz", "changed", {"title": "Changed", "description": ""},
        ),
    }
    caplog.set_level(logging.INFO, logger="MDXCANVAS")

    deploy_to_canvas(object(), "UTC", resources, DeploymentReport(), tmp_path, dryrun=True)

    assert calls == []
    assert store.saves == []
    assert messages(caplog, "Planned ") == ["Planned 4 actions"]
    plan_rows = messages(caplog, "Plan ")
    assert [row.split()[1].rstrip(":") for row in plan_rows] == [
        "assignment", "page", "quiz", "syllabus",
    ]
    expected_counts = {
        "assignment": (0, 0, 1, 0),
        "page": (1, 0, 0, 0),
        "quiz": (0, 1, 0, 0),
        "syllabus": (0, 0, 0, 1),
    }
    for row in plan_rows:
        resource_type = row.split()[1].rstrip(":")
        assert all(
            f"{kind}={count}" in row
            for kind, count in zip(
                ("create", "update", "delete", "untrack"),
                expected_counts[resource_type],
            )
        )
    assert progress_records(caplog) == []
    assert messages(caplog, "Deployment completed ") == []


def test_empty_dry_run_logs_zero_action_plan(monkeypatch, tmp_path, caplog):
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, build_builtin_handlers())
    caplog.set_level(logging.INFO, logger="MDXCANVAS")

    deploy_to_canvas(object(), "UTC", {}, DeploymentReport(), tmp_path, dryrun=True)

    assert messages(caplog, "Planned ") == ["Planned 0 actions"]
    assert messages(caplog, "Plan ") == []


def test_live_progress_follows_resolution_order_while_report_follows_plan_order(
        monkeypatch, tmp_path, caplog):
    second_finished = threading.Event()
    handlers = build_builtin_handlers()

    def create(_context, item):
        if item["id"] == "first":
            assert second_finished.wait(timeout=2)
        else:
            second_finished.set()
        return DeploymentResult({"id": f"canvas-{item['id']}"})

    original = handlers["page"]
    handlers["page"] = HandlerSpec(
        create,
        original.update,
        original.delete,
        prepare_cycle_breaker=original.prepare_cycle_breaker,
    )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", resource_id): resource(
            "page", resource_id, {"title": resource_id, "body": ""},
        )
        for resource_id in ("first", "second")
    }
    report = DeploymentReport()
    caplog.set_level(logging.INFO, logger="MDXCANVAS")

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    action_messages = [record.getMessage() for record in progress_records(caplog)]
    assert action_messages == [
        "1/2: create page second",
        "2/2: create page first",
    ]
    assert [
        item["resource_id"] for item in report.report["deployment"]["changes_made"]
    ] == ["first", "second"]
    completion = messages(caplog, "Deployment completed ")
    assert len(completion) == 1
    assert re.fullmatch(
        r"Deployment completed in \d+(?:\.\d+)?s: successful=2 failed=0 blocked=0",
        completion[0],
    )


def test_failure_and_blocked_progress_have_safe_levels_and_final_totals(
        monkeypatch, tmp_path, caplog):
    calls = []
    handlers = build_builtin_handlers()

    def create(_context, item):
        calls.append(item["id"])
        if item["id"] == "parent":
            raise RuntimeError("TOP-SECRET failure body")
        return DeploymentResult({"id": f"canvas-{item['id']}"})

    for resource_type in ("page", "assignment", "quiz"):
        original = handlers[resource_type]
        handlers[resource_type] = HandlerSpec(
            create,
            original.update,
            original.delete,
            prepare_cycle_breaker=original.prepare_cycle_breaker,
        )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "parent"): resource("page", "parent", {"title": "P", "body": ""}),
        ("assignment", "child"): resource("assignment", "child", {
            "name": "C", "description": "__@@page||parent||id@@__",
        }),
        ("quiz", "unrelated"): resource(
            "quiz", "unrelated", {"title": "Q", "description": ""},
        ),
    }
    report = DeploymentReport()
    caplog.set_level(logging.INFO, logger="MDXCANVAS")

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    assert "child" not in calls
    action_records = progress_records(caplog)
    assert len(action_records) == 3
    assert {record.getMessage().split(":", 1)[0] for record in action_records} == {
        "1/3", "2/3", "3/3",
    }
    failed = next(record for record in action_records if record.getMessage().endswith("create page parent FAILED"))
    blocked = next(record for record in action_records if record.getMessage().endswith("create assignment child BLOCKED"))
    succeeded = next(record for record in action_records if record.getMessage().endswith("create quiz unrelated"))
    assert failed.levelno == logging.ERROR
    assert blocked.levelno == logging.INFO
    assert succeeded.levelno == logging.INFO
    assert "TOP-SECRET" not in caplog.text
    completion = messages(caplog, "Deployment completed ")
    assert len(completion) == 1
    assert re.fullmatch(
        r"Deployment completed in \d+(?:\.\d+)?s: successful=1 failed=1 blocked=1",
        completion[0],
    )
    assert len(store.saves) == 1
    assert [error["resource_id"] for error in report.report["deployment"]["errors"]] == [
        "child", "parent",
    ]
