from pathlib import Path
from typing import Mapping

from canvasapi.course import Course
from canvasapi.exceptions import ResourceDoesNotExist
from canvasapi.module import ModuleItem

from ..our_logging import get_logger
from ..resources import CanvasResource, ModuleInfo, ModuleItemInfo, iter_keys


def get_module_item(course: Course, module_id: int | str | None, module_item_id: int | str) -> ModuleItem | None:
    if canvas_module := course.get_module(module_id):
        return canvas_module.get_module_item(module_item_id)

    return None


def deploy_module_item(course: Course, module_item_data: dict, _: Path) -> tuple[ModuleItemInfo, None]:
    canvas_module = course.get_module(module_item_data['module_id'])
    if canvas_module is None:
        raise ValueError(f'Unable to find module {module_item_data["module_id"]}')

    if module_item_data.get('canvas_id') and (
            module_item := canvas_module.get_module_item(module_item_data['canvas_id'])):
        module_item.edit(module_item=module_item_data)
    else:
        module_item = canvas_module.create_module_item(module_item=module_item_data)

    return ModuleItemInfo(
        id=module_item.id,
        parent={'type': 'module', 'id': str(module_item.module_id)},
        uri=f'/courses/{course.id}#module_{canvas_module.id}',
        url=f'{course.canvas._Canvas__requester.original_url}/courses/{course.id}#module_{canvas_module.id}'
    ), None


def find_misplaced_module_items(course: Course, resources: Mapping[tuple[str, str], CanvasResource],
                                ledger: Mapping) -> set[tuple[str, str]]:
    """Return the module items to rewrite because their module's order on Canvas no longer
    matches the source: Canvas was rearranged by hand, or an earlier deploy left it scrambled.

    Only items the ledger tracks are compared, so new items and items added by hand in
    Canvas do not count as drift. Every tracked item of a drifted module is returned, so
    the deploy rewrites the whole module in source order."""
    entries = ledger["resources"]
    by_module: dict[str, list[tuple[int, tuple[str, str], str]]] = {}
    for key, resource in resources.items():
        if key[0] != "module_item":
            continue
        info = entries.get(f"module_item|{key[1]}", {}).get("canvas_info") or {}
        module_refs = list(iter_keys(str(resource["data"].get("module_id", ""))))
        if not info.get("id") or len(module_refs) != 1:
            continue
        module_rid = module_refs[0][2]
        by_module.setdefault(module_rid, []).append((resource["data"]["position"], key, str(info["id"])))

    misplaced = set()
    for module_rid, items in sorted(by_module.items()):
        module_info = entries.get(f"module|{module_rid}", {}).get("canvas_info") or {}
        if not module_info.get("id"):
            continue
        try:
            canvas_items = course.get_module(module_info["id"]).get_module_items()
            on_canvas = [str(item.id) for item in sorted(canvas_items, key=lambda item: item.position)]
        except ResourceDoesNotExist:
            continue
        tracked = {canvas_id for _, _, canvas_id in items}
        actual = [canvas_id for canvas_id in on_canvas if canvas_id in tracked]
        desired = [canvas_id for _, _, canvas_id in sorted(items) if canvas_id in actual]
        if actual != desired:
            get_logger().info("Module %s is out of order in Canvas; rewriting its items in source order", module_rid)
            misplaced.update(key for _, key, _ in items)
    return misplaced


def deploy_module(course: Course, module_data: dict, _: Path) -> tuple[ModuleInfo, None]:
    if module_id := module_data.get('canvas_id'):
        canvas_module = course.get_module(module_id)
        if 'published' not in module_data:
            module_data['published'] = canvas_module.published
        canvas_module.edit(module=module_data)
    else:
        canvas_module = course.create_module(module=module_data)

    module_object_info: ModuleInfo = {
        'id': canvas_module.id,
        'title': canvas_module.name,
        'uri': f'/courses/{course.id}#module_{canvas_module.id}',
        'url': f'{course.canvas._Canvas__requester.original_url}/courses/{course.id}#module_{canvas_module.id}'
    }

    return module_object_info, None
