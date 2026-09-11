from pathlib import Path

from canvasapi.course import Course
from canvasapi.module import ModuleItem

from ..resources import ModuleInfo, ModuleItemInfo


def get_module_item(course: Course, module_id: int | str | None, module_item_id: int | str) -> ModuleItem | None:
    if canvas_module := course.get_module(module_id):
        return canvas_module.get_module_item(module_item_id)

    return None


def deploy_module_item(course: Course, module_item_data: dict, _: Path) -> tuple[ModuleItemInfo, None]:
    canvas_module = course.get_module(module_item_data['module_id'])
    if canvas_module is None:
        raise ValueError(f'Unable to find module {module_item_data["module_id"]}')

    if module_item_data['canvas_id'] and (
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
