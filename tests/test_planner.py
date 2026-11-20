import copy
from pathlib import Path

import pytest

from mdxcanvas.deploy.actions import Create, Update
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deploy.executor import execute_dag
from mdxcanvas.deploy.handlers import build_builtin_handlers
from mdxcanvas.deploy.planner import plan_deployment


def resource(resource_type, resource_id, data):
    return {
        "type": resource_type,
        "id": resource_id,
        "data": data,
        "content_path": "course.md",
    }


def tracked(resources, tmp_path):
    return {
        "mdxcanvas_version": "0.8.0",
        "resources": {
            f"{rtype}|{rid}": {
                "checksum": compute_md5(value["data"], tmp_path),
                "canvas_info": {"id": f"canvas-{rid}"},
            }
            for (rtype, rid), value in resources.items()
        },
    }


def public(plan):
    return [change.public() for change in plan.expected_changes]


@pytest.mark.parametrize("change", ["unchanged", "new", "modified"])
@pytest.mark.parametrize("opt_in", [None, False, True])
def test_update_opt_in_propagates_transitively(tmp_path, change, opt_in):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid, "body": "original"})
        for rid in ["producer", "consumer", "postprocessor", "unrelated"]
    }
    resources[("page", "consumer")]["data"]["body"] = "__@@page||producer||id@@__"
    if opt_in is not None:
        resources[("page", "consumer")]["reapply_on_update"] = opt_in
    resources[("page", "postprocessor")]["data"]["body"] = "__@@page||consumer||id@@__"
    resources[("page", "postprocessor")]["reapply_on_update"] = True
    ledger = tracked(resources, tmp_path)
    if change == "new":
        del ledger["resources"]["page|producer"]
    elif change == "modified":
        resources[("page", "producer")]["data"]["body"] = "changed"
    original = copy.deepcopy(resources)

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert resources == original
    if change == "unchanged":
        assert not plan.nodes
        return
    if change == "modified" and not opt_in:
        assert [item.resource_id for item in plan.expected_changes] == ["producer"]
        return
    assert {item.resource_id for item in plan.expected_changes} == {
        "producer", "consumer", "postprocessor",
    }
    completed = set()
    prerequisites = {"consumer": "producer", "postprocessor": "consumer"}

    def run(node):
        rid = node.planned_change.resource_id
        if rid in prerequisites:
            assert prerequisites[rid] in completed
        completed.add(rid)

    result = execute_dag(plan.nodes, run)
    assert not result.failures
    assert not result.blocked
    assert completed == {"producer", "consumer", "postprocessor"}


@pytest.mark.parametrize("opt_in", [False, True])
def test_references_order_independently_changed_consumer(tmp_path, opt_in):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["producer", "consumer"]
    }
    resources[("page", "consumer")]["data"]["body"] = "__@@page||producer||id@@__"
    resources[("page", "consumer")]["reapply_on_update"] = opt_in
    ledger = tracked(resources, tmp_path)
    for entry in ledger["resources"].values():
        entry["checksum"] = "old"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)
    completed = []
    result = execute_dag(plan.nodes, lambda node: completed.append(node.planned_change.resource_id))

    assert not result.failures
    assert completed == ["producer", "consumer"]


def test_dependency_failure_blocks_postprocessing(tmp_path):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["producer", "consumer"]
    }
    resources[("page", "consumer")]["data"]["body"] = "__@@page||producer||id@@__"
    resources[("page", "consumer")]["reapply_on_update"] = True
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["page|producer"]["checksum"] = "old"
    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    def run(node):
        assert node.planned_change.resource_id == "producer"
        raise RuntimeError("Deployment failed")

    result = execute_dag(plan.nodes, run)
    assert len(result.failures) == 1
    assert len(result.blocked) == 1


def test_update_dependency_cycles_fail_during_planning(tmp_path):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["a", "b"]
    }
    resources[("page", "a")]["data"]["body"] = "__@@page||b||id@@__"
    resources[("page", "b")]["data"]["body"] = "__@@page||a||id@@__"
    resources[("page", "b")]["reapply_on_update"] = True
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["page|a"]["checksum"] = "old"

    with pytest.raises(ValueError, match="cycle"):
        plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)


def test_missing_reference_fails_during_planning(tmp_path):
    resources = {("page", "consumer"): resource("page", "consumer", {"body": "__@@page||missing||id@@__"})}
    resources[("page", "consumer")]["reapply_on_update"] = True

    with pytest.raises(ValueError, match="Missing field"):
        plan_deployment(resources, tracked({}, tmp_path), build_builtin_handlers(), tmp_path)


def test_postprocessor_waits_for_full_deployment_of_cyclic_references(tmp_path):
    resources = {
        ("page", "a"): resource("page", "a", {"body": "__@@page||b||id@@__"}),
        ("page", "b"): resource("page", "b", {"body": "__@@page||a||id@@__"}),
        ("page", "postprocessor"): resource("page", "postprocessor", {"body": "Postprocess"}),
    }
    resources[("page", "postprocessor")]["data"]["body"] = "__@@page||a||id@@__ __@@page||b||id@@__"
    resources[("page", "postprocessor")]["reapply_on_update"] = True
    plan = plan_deployment(resources, tracked({}, tmp_path), build_builtin_handlers(), tmp_path)
    updated = set()

    def run(node):
        if node.planned_change.resource_id == "postprocessor":
            assert updated == {"a", "b"}
        elif isinstance(node.action, Update):
            updated.add(node.planned_change.resource_id)

    result = execute_dag(plan.nodes, run)
    assert not result.failures
    assert not result.blocked


@pytest.mark.parametrize("no_cleanup", [False, True])
def test_deleted_dependency_precedes_transitive_postprocessing(tmp_path, no_cleanup):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["producer", "consumer", "postprocessor"]
    }
    resources[("page", "consumer")]["data"]["body"] = "__@@page||producer||id@@__"
    resources[("page", "postprocessor")]["data"]["body"] = "__@@page||consumer||id@@__"
    resources[("page", "postprocessor")]["reapply_on_update"] = True
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["page|consumer"]["dependencies"] = [["page", "producer"]]
    del resources[("page", "producer")]
    resources[("page", "consumer")]["data"]["body"] = "Removed"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path, no_cleanup=no_cleanup)
    completed = []
    result = execute_dag(plan.nodes, lambda node: completed.append(node.planned_change.resource_id))

    assert not result.failures
    assert not result.blocked
    assert completed == (["consumer", "postprocessor"] if no_cleanup else ["producer", "consumer", "postprocessor"])
    assert any(change.change.value == "stale" for change in plan.expected_changes) is (not no_cleanup)


@pytest.mark.parametrize("flag", [None, "true", 1, []])
def test_reapply_on_update_requires_boolean(tmp_path, flag):
    resources = {("page", "consumer"): resource("page", "consumer", {"title": "Consumer"})}
    resources[("page", "consumer")]["reapply_on_update"] = flag

    with pytest.raises(ValueError, match="reapply_on_update must be a boolean"):
        plan_deployment(resources, tracked({}, tmp_path), build_builtin_handlers(), tmp_path)


def test_reapply_flag_does_not_change_checksum_or_create_a_reference(tmp_path):
    resources = {("page", "consumer"): resource("page", "consumer", {"title": "Consumer"})}
    ledger = tracked(resources, tmp_path)
    resources[("page", "consumer")]["reapply_on_update"] = True
    resources[("page", "consumer")]["content_path"] = "__@@page||missing||id@@__"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert not plan.nodes


def test_old_dependency_does_not_trigger_on_update_after_relationship_removed(tmp_path):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["producer", "consumer"]
    }
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["page|consumer"]["dependencies"] = [["page", "producer"]]
    ledger["resources"]["page|producer"]["checksum"] = "old"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert [change.resource_id for change in plan.expected_changes] == ["producer"]


def test_deleted_consumers_are_not_reapplied(tmp_path):
    resources = {
        ("page", rid): resource("page", rid, {"title": rid})
        for rid in ["producer", "consumer"]
    }
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["page|consumer"]["dependencies"] = [["page", "producer"]]

    plan = plan_deployment({}, ledger, build_builtin_handlers(), tmp_path)

    assert len(plan.expected_changes) == 2
    assert all(change.change.value == "stale" for change in plan.expected_changes)


def test_deletion_parent_cycles_fail_during_planning(tmp_path):
    ledger = {"resources": {
        "module_item|a": {"canvas_info": {"id": "a", "parent": {"type": "module_item", "id": "b"}}},
        "module_item|b": {"canvas_info": {"id": "b", "parent": {"type": "module_item", "id": "a"}}},
    }}

    with pytest.raises(ValueError, match="cycle"):
        plan_deployment({}, ledger, build_builtin_handlers(), tmp_path)


def test_replacement_create_propagates_through_transitive_consumers(tmp_path):
    resources = {
        ("file", "asset"): resource("file", "asset", {"path": "new", "canvas_folder": None}),
        ("zip", "bundle"): resource("zip", "bundle", {
            "zip_file_name": "bundle.zip",
            "zip_contents": {"asset": "__@@file||asset||id@@__"},
            "canvas_folder": None,
        }),
        ("page", "page"): resource("page", "page", {
            "title": "Page", "body": "__@@zip||bundle||id@@__",
        }),
    }
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["file|asset"]["checksum"] = "old"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert public(plan) == [
        {"change": "modified", "resource_type": "file", "resource_id": "asset"},
        {"change": "modified", "resource_type": "zip", "resource_id": "bundle"},
        {"change": "modified", "resource_type": "page", "resource_id": "page"},
    ]
    assert [type(node.action) for node in plan.nodes] == [Create, Create, Update]


def test_mixed_page_syllabus_cycle_preserves_inputs_and_runs_all_shells_first(tmp_path):
    resources = {
        ("page", "page"): resource("page", "page", {
            "title": "Page", "body": "__@@syllabus||syllabus||id@@__",
        }),
        ("syllabus", "syllabus"): resource("syllabus", "syllabus", {
            "content": "__@@page||page||id@@__",
        }),
    }
    original = copy.deepcopy(resources)

    plan = plan_deployment(
        resources,
        {"mdxcanvas_version": "0.8.0", "resources": {}},
        build_builtin_handlers(),
        tmp_path,
    )

    assert resources == original
    assert [change.public() for change in plan.expected_changes] == [
        {"change": "new", "resource_type": "page", "resource_id": "page"},
        {"change": "modified", "resource_type": "page", "resource_id": "page"},
        {"change": "new", "resource_type": "syllabus", "resource_id": "syllabus"},
        {"change": "modified", "resource_type": "syllabus", "resource_id": "syllabus"},
    ]
    assert [type(node.action) for node in plan.nodes] == [Create, Update, Create, Update]
    assert plan.nodes[0].action.resource["data"]["body"] == ""
    assert plan.nodes[1].action.resource["data"]["body"] == "__@@syllabus||syllabus||id@@__"
    assert plan.nodes[2].action.resource["data"]["content"] == ""
    assert plan.nodes[3].action.resource["data"]["content"] == "__@@page||page||id@@__"

    shells_finished = set()

    def run(node):
        if isinstance(node.action, Create):
            shells_finished.add(node.planned_change.resource_type)
        else:
            assert shells_finished == {"page", "syllabus"}
        return node.plan_order

    result = execute_dag(plan.nodes, run)
    assert not result.failures


def test_supported_cycle_runs_every_shell_before_any_full_update(tmp_path):
    resources = {
        ("page", "a"): resource("page", "a", {"title": "A", "body": "__@@page||b||id@@__"}),
        ("page", "b"): resource("page", "b", {"title": "B", "body": "__@@page||a||id@@__"}),
    }
    plan = plan_deployment(
        resources,
        {"mdxcanvas_version": "0.8.0", "resources": {}},
        build_builtin_handlers(),
        tmp_path,
    )
    shells_finished = set()

    def run(node):
        if isinstance(node.action, Create):
            assert node.action.resource["data"]["body"] == ""
            shells_finished.add(node.planned_change.resource_id)
        else:
            assert shells_finished == {"a", "b"}
        return node.key

    result = execute_dag(plan.nodes, run)

    assert not result.failures
    assert [change["change"] for change in public(plan)] == ["new", "modified", "new", "modified"]


@pytest.mark.parametrize(
    "rtype,data",
    [
        ("announcement", {"title": "Self", "message": "__@@announcement||self||id@@__"}),
        ("file", {"path": "__@@file||self||id@@__", "canvas_folder": None}),
    ],
)
def test_unsupported_or_replacement_create_cycle_fails_before_execution(tmp_path, rtype, data):
    resources = {(rtype, "self"): resource(rtype, "self", data)}

    with pytest.raises(ValueError, match="cycle|breaker"):
        plan_deployment(
            resources,
            {"mdxcanvas_version": "0.8.0", "resources": {}},
            build_builtin_handlers(),
            tmp_path,
        )
