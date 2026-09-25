from pathlib import Path

from canvasapi.course import Course

from ..resources import AssignmentGroupInfo, GroupCategoryInfo


def _should_enable_weighted_grades(group_data: dict) -> bool:
    return 'group_weight' in group_data


def deploy_group(course: Course, group_data: dict, _: Path) -> tuple[AssignmentGroupInfo, None]:
    if group_id := group_data.get('canvas_id'):
        group = course.get_assignment_group(group_id)
    else:
        group = course.create_assignment_group(name=group_data["name"])

    group.edit(**group_data)
    if _should_enable_weighted_grades(group_data):
        course.update(course={
            'apply_assignment_group_weights': True,
        })

    group_object_info: AssignmentGroupInfo = {
        'id': group.id
    }

    return group_object_info, None


def deploy_group_category(course: Course, category_data: dict, _: Path) -> tuple[GroupCategoryInfo, None]:
    """Create or update a student group category.

    The groups inside it, and their membership, are left to Canvas: membership
    changes with enrolment and does not belong in version control.
    """
    settings = {k: v for k, v in category_data.items() if k != 'canvas_id'}

    if category_id := category_data.get('canvas_id'):
        category = course.get_group_categories()
        category = next((c for c in category if c.id == category_id), None)
        if category is None:
            raise ValueError(f"group category {category_id} no longer exists in this course")
        category.update(**settings)
    else:
        category = course.create_group_category(**settings)

    category_object_info: GroupCategoryInfo = {
        'id': category.id
    }

    return category_object_info, None
