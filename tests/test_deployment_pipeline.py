import threading
from copy import deepcopy
from types import SimpleNamespace

import pytest

import mdxcanvas
from mdxcanvas.deploy.actions import DeploymentResult, HandlerSpec
from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deploy.handlers import build_builtin_handlers
from mdxcanvas.deployment_report import DeploymentReport


def resource(rtype, rid, data):
    return {"type": rtype, "id": rid, "data": data, "content_path": "course.md"}


class Store:
    def __init__(self, envelope, save_error=None):
        self.envelope = deepcopy(envelope)
        self.save_error = save_error
        self.saves = []

    def load(self):
        return deepcopy(self.envelope)

    def save(self, envelope):
        self.saves.append(deepcopy(envelope))
        if self.save_error:
            raise self.save_error


def install(monkeypatch, store, handlers):
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.build_builtin_handlers", lambda: handlers)


def result(resource):
    return DeploymentResult({"id": f"canvas-{resource['id']}"})


@pytest.mark.parametrize("dryrun, expected_saves", [(False, 1), (True, 0)])
def test_older_canonical_version_advances_only_during_deployment(
        monkeypatch, tmp_path, dryrun, expected_saves):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, build_builtin_handlers())
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", {}, report, tmp_path, dryrun=dryrun)

    assert report.report["deployment"]["expected_changes"] == []
    assert report.report["deployment"]["changes_made"] == []
    assert report.report["deployment"]["errors"] == []
    assert len(store.saves) == expected_saves
    if store.saves:
        assert store.saves[0]["mdxcanvas_version"] == mdxcanvas.__version__
        assert store.saves[0]["resources"] == {}


@pytest.mark.parametrize("dryrun", [False, True])
def test_newer_ledger_stops_before_copy_planning_execution_or_save(monkeypatch, tmp_path, dryrun):
    class NewerEnvelope(dict):
        def __deepcopy__(self, _memo):
            raise AssertionError("newer ledger entered writable state")

    class NewerStore:
        def __init__(self):
            self.envelope = NewerEnvelope({
                "mdxcanvas_version": "0.9.0",
                "resources": "future schema",
            })
            self.saves = []

        def load(self):
            return self.envelope

        def save(self, envelope):
            self.saves.append(envelope)

    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    store = NewerStore()
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr(
        "mdxcanvas.deploy.canvas_deploy.build_builtin_handlers",
        lambda: pytest.fail("handlers built after newer-ledger rejection"),
    )
    monkeypatch.setattr(
        "mdxcanvas.deploy.canvas_deploy.plan_deployment",
        lambda *_args, **_kwargs: pytest.fail("planner ran after newer-ledger rejection"),
    )
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", {}, report, tmp_path, dryrun=dryrun)

    assert report.report["processing"]["error"] == ""
    assert report.report["deployment"]["expected_changes"] == []
    assert report.report["deployment"]["changes_made"] == []
    assert len(report.report["deployment"]["errors"]) == 1
    error = report.report["deployment"]["errors"][0]
    assert error["stage"] == "planning"
    assert "0.9.0" in error["error"]
    assert "0.8.7" in error["error"]
    assert "upgrade" in error["error"].lower()
    assert "at least 0.9.0" in error["error"]
    assert report.has_errors is True
    assert store.envelope == {
        "mdxcanvas_version": "0.9.0",
        "resources": "future schema",
    }
    assert store.saves == []


def test_delete_already_absent_and_untrack_outcomes_follow_child_before_parent(monkeypatch, tmp_path):
    calls = []
    handlers = build_builtin_handlers()

    def delete(_context, rid, _info):
        calls.append(rid)
        return rid != "child"

    handlers["module_item"] = HandlerSpec(result, lambda *_args: None, delete=delete)
    handlers["module"] = HandlerSpec(result, lambda *_args: None, delete=delete)
    store = Store({
        "mdxcanvas_version": "0.8.0",
        "resources": {
            "module|parent": {"checksum": "x", "canvas_info": {"id": "20"}},
            "module_item|child": {
                "checksum": "x",
                "canvas_info": {"id": "21", "parent": {"type": "module", "id": "20"}},
            },
            "course_settings|": {"checksum": "x", "canvas_info": {"id": "course"}},
        },
    })
    install(monkeypatch, store, handlers)
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", {}, report, tmp_path)

    assert calls == ["child", "parent"]
    assert [change["outcome"] for change in report.report["deployment"]["changes_made"]] == [
        "untracked", "deleted", "already_absent",
    ]
    assert len(store.saves) == 1
    assert store.saves[0]["resources"] == {}


def test_delete_error_preserves_only_failed_ledger_entry(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()

    def fail_delete(*_args):
        raise RuntimeError("delete failed")

    handlers["page"] = HandlerSpec(result, lambda *_args: None, delete=fail_delete)
    store = Store({
        "mdxcanvas_version": "0.8.0",
        "resources": {
            "page|failed": {"checksum": "x", "canvas_info": {"id": "10"}},
            "course_settings|": {"checksum": "x", "canvas_info": {"id": "course"}},
        },
    })
    install(monkeypatch, store, handlers)
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", {}, report, tmp_path)

    assert len(store.saves) == 1
    assert set(store.saves[0]["resources"]) == {"page|failed"}
    assert [item["outcome"] for item in report.report["deployment"]["changes_made"]] == ["untracked"]
    assert report.report["deployment"]["errors"][0]["resource_id"] == "failed"


def test_failure_blocks_descendant_unrelated_work_persists_and_save_error_is_separate(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    calls = []

    def create(_context, item):
        calls.append(item["id"])
        if item["id"] == "parent":
            raise RuntimeError("Canvas failed")
        return result(item)

    for rtype in ("page", "assignment", "quiz"):
        old = handlers[rtype]
        handlers[rtype] = HandlerSpec(create, old.update, old.delete, prepare_cycle_breaker=old.prepare_cycle_breaker)
    store = Store(
        {"mdxcanvas_version": "0.8.0", "resources": {}},
        save_error=OSError("upload failed"),
    )
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "parent"): resource("page", "parent", {"title": "P", "body": ""}),
        ("assignment", "child"): resource("assignment", "child", {
            "name": "C", "description": "__@@page||parent||id@@__",
        }),
        ("quiz", "unrelated"): resource("quiz", "unrelated", {"title": "Q", "description": ""}),
    }
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    assert set(calls) == {"parent", "unrelated"}
    assert "child" not in calls
    assert report.report["content_to_review"] == []
    assert [item["resource_id"] for item in report.report["deployment"]["changes_made"]] == ["unrelated"]
    errors = report.report["deployment"]["errors"]
    assert [(item["stage"], item.get("resource_id")) for item in errors] == [
        ("deployment", "child"),
        ("deployment", "parent"),
        ("ledger_persistence", None),
    ]
    assert "DependencyFailed" in errors[0]["error"]
    assert len(store.saves) == 1
    assert set(store.saves[0]["resources"]) == {"quiz|unrelated"}


def test_review_reporting_uses_plan_order_and_handler_metadata_only(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    later_finished = threading.Event()

    def create(_context, item):
        if item["id"] == "first":
            assert later_finished.wait(timeout=2)
        else:
            later_finished.set()
        review = None
        if item["id"] in {"first", "second"}:
            review = SimpleNamespace(name="Shared target", url=None)
        return DeploymentResult(
            {"id": f"canvas-{item['id']}", "url": "https://ledger-only/private"},
            f"https://outcome/{item['id']}",
            review=review,
        )

    old = handlers["page"]
    handlers["page"] = HandlerSpec(
        create, old.update, old.delete, prepare_cycle_breaker=old.prepare_cycle_breaker,
    )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", rid): resource("page", rid, {"title": rid, "body": ""})
        for rid in ("first", "second", "without-review")
    }
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    changes = report.report["deployment"]["changes_made"]
    assert [change["resource_id"] for change in changes] == [
        "first", "second", "without-review",
    ]
    assert [change["url"] for change in changes] == [
        "https://outcome/first", "https://outcome/second", "https://outcome/without-review",
    ]
    assert changes[0]["review"] == {"name": "Shared target", "url": None}
    assert changes[1]["review"] == {"name": "Shared target", "url": None}
    assert "review" not in changes[2]
    assert report.report["content_to_review"] == [
        ["page", "Shared target", None],
    ]
    assert "content_to_review" not in store.saves[0]["resources"]["page|first"]
    assert "review" not in store.saves[0]["resources"]["page|first"]


def test_cycle_shell_and_full_results_retain_review_on_each_success(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    old = handlers["page"]

    def reviewed(item):
        return DeploymentResult(
            {"id": f"canvas-{item['id']}"},
            review=SimpleNamespace(name="Cycle review", url="https://safe/cycle"),
        )

    handlers["page"] = HandlerSpec(
        lambda _context, item: reviewed(item),
        lambda _context, item, _info: reviewed(item),
        old.delete,
        prepare_cycle_breaker=old.prepare_cycle_breaker,
    )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "a"): resource("page", "a", {"title": "A", "body": "__@@page||b||id@@__"}),
        ("page", "b"): resource("page", "b", {"title": "B", "body": "__@@page||a||id@@__"}),
    }
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    changes = report.report["deployment"]["changes_made"]
    assert len(changes) == 4
    assert all(change["review"] == {
        "name": "Cycle review", "url": "https://safe/cycle",
    } for change in changes)
    assert report.report["content_to_review"] == [
        ["page", "Cycle review", "https://safe/cycle"],
    ]


def test_bookkeeping_failure_does_not_retry_canvas_handler(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    calls = []

    class CannotCopy:
        def __deepcopy__(self, _memo):
            raise RuntimeError("bookkeeping failed")

    def create(_context, _item):
        calls.append("create")
        return DeploymentResult({"id": "10", "internal": CannotCopy()})

    old = handlers["page"]
    handlers["page"] = HandlerSpec(create, old.update, old.delete, prepare_cycle_breaker=old.prepare_cycle_breaker)
    store = Store({"mdxcanvas_version": "0.8.1", "resources": {}})
    install(monkeypatch, store, handlers)
    report = DeploymentReport()

    deploy_to_canvas(
        object(), "UTC",
        {("page", "page"): resource("page", "page", {"title": "P", "body": ""})},
        report, tmp_path,
    )

    assert calls == ["create"]
    assert store.saves == []
    assert report.report["deployment"]["errors"][0]["stage"] == "deployment"


@pytest.mark.parametrize("save_error", [None, OSError("save failed")])
def test_coordinator_error_preserves_completed_action_and_attempts_one_final_save(
        monkeypatch, tmp_path, save_error):
    handlers = build_builtin_handlers()
    old = handlers["page"]
    handlers["page"] = HandlerSpec(
        lambda _context, item: result(item),
        old.update,
        old.delete,
        prepare_cycle_breaker=old.prepare_cycle_breaker,
    )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}}, save_error=save_error)
    install(monkeypatch, store, handlers)

    def execute_then_fail(nodes, callback):
        callback(list(nodes)[0])
        raise RuntimeError("coordinator lost its ready queue")

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.execute_dag", execute_then_fail)
    report = DeploymentReport()

    deploy_to_canvas(
        object(), "UTC",
        {("page", "page"): resource("page", "page", {"title": "P", "body": ""})},
        report, tmp_path,
    )

    assert report.report["deployment"]["changes_made"] == [{
        "change": "new", "resource_type": "page", "resource_id": "page", "outcome": "created",
    }]
    errors = report.report["deployment"]["errors"]
    assert errors[0]["stage"] == "deployment"
    assert "coordinator lost its ready queue" in errors[0]["error"]
    assert len(store.saves) == 1
    assert store.saves[0]["resources"]["page|page"]["canvas_info"]["id"] == "canvas-page"
    if save_error:
        assert [error["stage"] for error in errors] == ["deployment", "ledger_persistence"]
        assert "save failed" in errors[1]["error"]
    else:
        assert [error["stage"] for error in errors] == ["deployment"]


@pytest.mark.parametrize("save_error", [None, OSError("save failed")])
def test_keyboard_interrupt_saves_completed_state_once_and_is_reraised(
        monkeypatch, tmp_path, save_error):
    handlers = build_builtin_handlers()
    old = handlers["page"]
    handlers["page"] = HandlerSpec(
        lambda _context, item: result(item),
        old.update,
        old.delete,
        prepare_cycle_breaker=old.prepare_cycle_breaker,
    )
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}}, save_error=save_error)
    install(monkeypatch, store, handlers)
    interrupt = KeyboardInterrupt()

    def execute_then_interrupt(nodes, callback):
        callback(list(nodes)[0])
        raise interrupt

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.execute_dag", execute_then_interrupt)
    report = DeploymentReport()

    with pytest.raises(KeyboardInterrupt) as raised:
        deploy_to_canvas(
            object(), "UTC",
            {("page", "page"): resource("page", "page", {"title": "P", "body": ""})},
            report, tmp_path,
        )

    assert raised.value is interrupt
    assert len(store.saves) == 1
    assert store.saves[0]["resources"]["page|page"]["canvas_info"]["id"] == "canvas-page"
    assert report.report["deployment"]["changes_made"][0]["resource_id"] == "page"
    assert report.report["deployment"]["errors"][0] == {
        "stage": "deployment",
        "error": "Deployment interrupted by user",
    }
    if save_error:
        assert report.report["deployment"]["errors"][1]["stage"] == "ledger_persistence"


def test_coordinator_error_before_observed_completion_still_attempts_one_save(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)

    def fail_before_callback(_nodes, _callback):
        raise RuntimeError("coordinator failed before submission")

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.execute_dag", fail_before_callback)
    report = DeploymentReport()

    deploy_to_canvas(
        object(), "UTC",
        {("page", "page"): resource("page", "page", {"title": "P", "body": ""})},
        report, tmp_path,
    )

    assert len(store.saves) == 1
    assert store.saves[0]["resources"] == {}
    assert report.report["deployment"]["errors"][0]["stage"] == "deployment"
    assert "coordinator failed before submission" in report.report["deployment"]["errors"][0]["error"]


def test_execution_reads_identity_snapshots_under_bookkeeping_lock_and_releases_before_handler(
        monkeypatch, tmp_path):
    real_lock = threading.Lock()

    class TrackingLock:
        owner = None

        def __enter__(self):
            real_lock.acquire()
            self.owner = threading.get_ident()
            return self

        def __exit__(self, *_args):
            self.owner = None
            real_lock.release()

        def held_by_current_thread(self):
            return self.owner == threading.get_ident()

    tracking_lock = TrackingLock()

    class CheckedResources(dict):
        execution_started = False

        def __deepcopy__(self, _memo):
            return self

        def _check(self):
            if self.execution_started and not tracking_lock.held_by_current_thread():
                raise AssertionError("shared ledger identity read outside bookkeeping lock")

        def __getitem__(self, key):
            self._check()
            return super().__getitem__(key)

        def get(self, key, default=None):
            self._check()
            return super().get(key, default)

        def __setitem__(self, key, value):
            self._check()
            return super().__setitem__(key, value)

        def pop(self, key, default=None):
            self._check()
            return super().pop(key, default)

    entries = CheckedResources({
        "page|target": {"checksum": "old", "canvas_info": {"id": "target-id"}},
        "page|reference": {"checksum": "same", "canvas_info": {"id": "ref-id"}},
    })
    store = Store({"mdxcanvas_version": "0.8.0", "resources": entries})
    handlers = build_builtin_handlers()
    old = handlers["page"]

    def update(_context, item, canvas_info):
        assert not tracking_lock.held_by_current_thread()
        assert item["data"]["body"] == "ref-id"
        assert canvas_info["id"] == "target-id"
        return result(item)

    handlers["page"] = HandlerSpec(
        old.create, update, old.delete, prepare_cycle_breaker=old.prepare_cycle_breaker,
    )
    install(monkeypatch, store, handlers)
    monkeypatch.setattr(
        "mdxcanvas.deploy.canvas_deploy.threading",
        SimpleNamespace(Lock=lambda: tracking_lock),
    )
    from mdxcanvas.deploy.executor import execute_dag as real_execute_dag

    def mark_execution(nodes, callback):
        entries.execution_started = True
        return real_execute_dag(nodes, callback)

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.execute_dag", mark_execution)
    report = DeploymentReport()

    deploy_to_canvas(
        object(), "UTC",
        {("page", "target"): resource(
            "page", "target", {"title": "P", "body": "__@@page||reference||id@@__"},
        )},
        report, tmp_path,
    )

    assert not report.report["deployment"]["errors"]
    assert report.report["deployment"]["changes_made"][0]["outcome"] == "updated"


def test_mixed_page_syllabus_cycle_runs_shells_first_and_persists_full_results(
        monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    calls = []

    def spec_for(resource_type):
        original = handlers[resource_type]

        def create(_context, item):
            calls.append(("create", resource_type, deepcopy(item["data"])))
            return DeploymentResult({"id": f"canvas-{resource_type}"})

        def update(_context, item, _info):
            calls.append(("update", resource_type, deepcopy(item["data"])))
            return DeploymentResult({"id": f"canvas-{resource_type}"})

        return HandlerSpec(
            create,
            update,
            original.delete,
            modified_action=original.modified_action,
            absence_policy=original.absence_policy,
            prepare_cycle_breaker=original.prepare_cycle_breaker,
        )

    handlers["page"] = spec_for("page")
    handlers["syllabus"] = spec_for("syllabus")
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "page"): resource("page", "page", {
            "title": "Page", "body": "__@@syllabus||syllabus||id@@__",
        }),
        ("syllabus", "syllabus"): resource("syllabus", "syllabus", {
            "content": "__@@page||page||id@@__",
        }),
    }
    original_resources = deepcopy(resources)
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    assert resources == original_resources
    assert {(operation, resource_type) for operation, resource_type, _ in calls[:2]} == {
        ("create", "page"), ("create", "syllabus"),
    }
    assert {(operation, resource_type) for operation, resource_type, _ in calls[2:]} == {
        ("update", "page"), ("update", "syllabus"),
    }
    full_payloads = {
        resource_type: data
        for operation, resource_type, data in calls
        if operation == "update"
    }
    assert full_payloads["page"]["body"] == "canvas-syllabus"
    assert full_payloads["syllabus"]["content"] == "canvas-page"
    assert [
        (item["resource_type"], item["outcome"])
        for item in report.report["deployment"]["changes_made"]
    ] == [
        ("page", "created"),
        ("page", "updated"),
        ("syllabus", "created"),
        ("syllabus", "updated"),
    ]
    assert report.report["deployment"]["errors"] == []
    assert len(store.saves) == 1
    saved = store.saves[0]["resources"]
    assert set(saved) == {"page|page", "syllabus|syllabus"}
    assert saved["page|page"] == {
        "checksum": compute_md5(resources[("page", "page")]["data"], tmp_path),
        "canvas_info": {"id": "canvas-page"},
    }
    assert saved["syllabus|syllabus"] == {
        "checksum": compute_md5(resources[("syllabus", "syllabus")]["data"], tmp_path),
        "canvas_info": {"id": "canvas-syllabus"},
    }


def test_syllabus_shell_survives_full_failure_and_rerun_plans_modified(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    calls = []

    def spec_for(resource_type):
        original = handlers[resource_type]

        def create(_context, item):
            calls.append(("create", resource_type))
            return DeploymentResult({"id": f"canvas-{resource_type}"})

        def update(_context, item, _info):
            calls.append(("update", resource_type))
            if resource_type == "syllabus":
                raise RuntimeError("syllabus full update failed")
            return DeploymentResult({"id": f"canvas-{resource_type}"})

        return HandlerSpec(
            create,
            update,
            original.delete,
            modified_action=original.modified_action,
            absence_policy=original.absence_policy,
            prepare_cycle_breaker=original.prepare_cycle_breaker,
        )

    handlers["page"] = spec_for("page")
    handlers["syllabus"] = spec_for("syllabus")
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "page"): resource("page", "page", {
            "title": "Page", "body": "__@@syllabus||syllabus||id@@__",
        }),
        ("syllabus", "syllabus"): resource("syllabus", "syllabus", {
            "content": "__@@page||page||id@@__",
        }),
    }
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    assert {(operation, resource_type) for operation, resource_type in calls[:2]} == {
        ("create", "page"), ("create", "syllabus"),
    }
    assert len(store.saves) == 1
    saved = store.saves[0]
    assert saved["resources"]["page|page"]["checksum"] == compute_md5(
        resources[("page", "page")]["data"], tmp_path,
    )
    assert saved["resources"]["syllabus|syllabus"]["checksum"] == compute_md5(
        {"content": ""}, tmp_path,
    )
    assert [
        (item["resource_type"], item["outcome"])
        for item in report.report["deployment"]["changes_made"]
    ] == [
        ("page", "created"),
        ("page", "updated"),
        ("syllabus", "created"),
    ]
    assert [error.get("resource_type") for error in report.report["deployment"]["errors"]] == [
        "syllabus",
    ]

    rerun_store = Store(saved)
    install(monkeypatch, rerun_store, handlers)
    rerun = DeploymentReport()
    deploy_to_canvas(object(), "UTC", resources, rerun, tmp_path, dryrun=True)

    assert rerun.report["deployment"]["expected_changes"] == [{
        "change": "modified", "resource_type": "syllabus", "resource_id": "syllabus",
    }]


def test_shell_success_full_failure_is_saved_and_rerun_is_modified(monkeypatch, tmp_path):
    handlers = build_builtin_handlers()
    old = handlers["page"]

    def create(_context, item):
        return result(item)

    def update(_context, item, _info):
        if item["id"] == "a":
            raise RuntimeError("full update failed")
        return result(item)

    handlers["page"] = HandlerSpec(create, update, old.delete, prepare_cycle_breaker=old.prepare_cycle_breaker)
    store = Store({"mdxcanvas_version": "0.8.0", "resources": {}})
    install(monkeypatch, store, handlers)
    resources = {
        ("page", "a"): resource("page", "a", {"title": "A", "body": "__@@page||b||id@@__"}),
        ("page", "b"): resource("page", "b", {"title": "B", "body": "__@@page||a||id@@__"}),
    }
    report = DeploymentReport()

    deploy_to_canvas(object(), "UTC", resources, report, tmp_path)

    assert len(store.saves) == 1
    saved = store.saves[0]
    assert set(saved["resources"]) == {"page|a", "page|b"}
    assert [item["outcome"] for item in report.report["deployment"]["changes_made"]] == [
        "created", "created", "updated",
    ]
    assert [item.get("resource_id") for item in report.report["deployment"]["errors"]] == ["a"]

    rerun_store = Store(saved)
    install(monkeypatch, rerun_store, handlers)
    rerun = DeploymentReport()
    deploy_to_canvas(object(), "UTC", resources, rerun, tmp_path, dryrun=True)

    assert rerun.report["deployment"]["expected_changes"] == [{
        "change": "modified", "resource_type": "page", "resource_id": "a",
    }]
