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
