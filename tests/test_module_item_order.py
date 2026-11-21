"""Module items land in the order the source lists them.

Canvas places a module item at a position and shifts its neighbors, so an
item's position is only right if every item before it has already been placed.
These tests run a plan against a module that shifts and closes gaps the way
Canvas does, and check the order it ends in. A module already out of order in
Canvas is repaired by the next deploy, even when the source has not changed.
"""
from types import SimpleNamespace

from mdxcanvas.deploy.actions import Delete
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deploy.executor import execute_dag
from mdxcanvas.deploy.handlers import build_builtin_handlers
from mdxcanvas.deploy.module import find_misplaced_module_items
from mdxcanvas.deploy.planner import plan_deployment


def module_items(module_id, order):
    """Module item resources as the module tag emits them: each references the one before it."""
    resources = {
        ("module", module_id): {
            "type": "module", "id": module_id, "data": {"name": "Module"}, "content_path": "course.md",
        },
    }
    previous = None
    for position, name in enumerate(order, start=1):
        item_id = f"{module_id}|{name}"
        resources[("module_item", item_id)] = {
            "type": "module_item",
            "id": item_id,
            "data": {
                "type": "SubHeader",
                "title": name,
                "position": position,
                "module_id": f"__@@module||{module_id}||id@@__",
                "_comments": {
                    "previous_module_item": f"__@@module_item||{previous}||id@@__" if previous else "",
                },
            },
            "content_path": "course.md",
        }
        previous = item_id
    return resources


def ledger_for(resources, tmp_path):
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


def deploy_to_simulated_module(plan, canvas_order):
    """Run the plan against a module that behaves like Canvas: placing an item at a
    position shifts its neighbors, and deleting an item closes the gap."""

    def apply(node):
        action = node.action
        if isinstance(action, Delete):
            canvas_order.remove(action.resource_id.split("|", 1)[1])
            return
        data = action.resource["data"]
        if "position" not in data:
            return
        name = data["title"]
        if name in canvas_order:
            canvas_order.remove(name)
        canvas_order.insert(data["position"] - 1, name)

    result = execute_dag(plan.nodes, apply, max_workers=1)
    assert not result.failures
    return canvas_order


def test_reordered_items_land_in_source_order(tmp_path):
    ledger = ledger_for(module_items("m", ["a", "b", "c", "d"]), tmp_path)
    desired = module_items("m", ["d", "c", "a", "b"])

    plan = plan_deployment(desired, ledger, build_builtin_handlers(), tmp_path)

    assert deploy_to_simulated_module(plan, ["a", "b", "c", "d"]) == ["d", "c", "a", "b"]


def test_an_inserted_item_and_moved_items_land_in_source_order(tmp_path):
    ledger = ledger_for(module_items("m", ["a", "b", "c", "d"]), tmp_path)
    desired = module_items("m", ["a", "n", "b", "d", "c"])

    plan = plan_deployment(desired, ledger, build_builtin_handlers(), tmp_path)

    assert deploy_to_simulated_module(plan, ["a", "b", "c", "d"]) == ["a", "n", "b", "d", "c"]


def test_moves_wait_for_removed_items(tmp_path):
    ledger = ledger_for(module_items("m", ["a", "gone", "b", "c", "d"]), tmp_path)
    desired = module_items("m", ["d", "c", "a", "b"])

    plan = plan_deployment(desired, ledger, build_builtin_handlers(), tmp_path)

    assert deploy_to_simulated_module(plan, ["a", "gone", "b", "c", "d"]) == ["d", "c", "a", "b"]


def course_showing(module_id, canvas_order):
    """A course whose module lists the named items in this order, as Canvas reports them."""
    items = [SimpleNamespace(id=f"canvas-{module_id}|{name}", position=position)
             for position, name in enumerate(canvas_order, start=1)]
    module = SimpleNamespace(get_module_items=lambda: list(reversed(items)))
    return SimpleNamespace(get_module=lambda canvas_id: module)


def test_a_module_in_source_order_has_no_drift(tmp_path):
    resources = module_items("m", ["a", "b", "c"])

    assert find_misplaced_module_items(
        course_showing("m", ["a", "b", "c"]), resources, ledger_for(resources, tmp_path)) == set()


def test_a_scrambled_module_rewrites_every_tracked_item(tmp_path):
    resources = module_items("m", ["a", "b", "c"])

    assert find_misplaced_module_items(
        course_showing("m", ["a", "c", "b"]), resources, ledger_for(resources, tmp_path),
    ) == {("module_item", "m|a"), ("module_item", "m|b"), ("module_item", "m|c")}


def test_items_added_in_canvas_or_not_yet_deployed_are_not_drift(tmp_path):
    ledger = ledger_for(module_items("m", ["a", "b"]), tmp_path)
    resources = module_items("m", ["a", "new", "b"])

    assert find_misplaced_module_items(
        course_showing("m", ["hand-added", "a", "b"]), resources, ledger) == set()


def test_a_deploy_with_no_source_change_repairs_a_scrambled_module(tmp_path):
    resources = module_items("m", ["a", "b", "c", "d"])
    ledger = ledger_for(resources, tmp_path)
    scrambled = ["c", "a", "d", "b"]

    drifted = find_misplaced_module_items(course_showing("m", scrambled), resources, ledger)
    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path, drifted=frozenset(drifted))

    assert deploy_to_simulated_module(plan, scrambled) == ["a", "b", "c", "d"]
