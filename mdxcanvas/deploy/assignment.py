from pathlib import Path

from canvasapi.course import Course

from ..resources import AssignmentInfo


def resolve_group_category(course: Course, assignment_info: dict) -> dict:
    """Swap the group category's name for the id Canvas wants.

    A course names the category; the assignment API takes `group_category_id`
    and ignores anything else, so the name was accepted, discarded, and the
    assignment deployed ungrouped. Students then submit individually on work
    meant to be submitted as a group.

    An unmatched name is an error rather than a new category: creating one
    silently is how a course ends up with two categories differing by a space.
    """
    name = assignment_info.get('group_category')
    if not name:
        return assignment_info

    resolved = {k: v for k, v in assignment_info.items() if k != 'group_category'}
    by_name = {category.name: category.id for category in course.get_group_categories()}
    if name not in by_name:
        known = ', '.join(repr(n) for n in sorted(by_name)) or 'none'
        raise ValueError(
            f"group_category {name!r} matches no group category in this course.\n"
            f" existing categories: {known}\n"
            f" Create it in Canvas first; mdxcanvas will not create one for you."
        )
    resolved['group_category_id'] = by_name[name]
    return resolved


def deploy_assignment(course: Course, assignment_info: dict, _: Path) -> tuple[AssignmentInfo, None]:
    assignment_info = resolve_group_category(course, assignment_info)

    if assignment_id := assignment_info.get('canvas_id'):
        canvas_assignment = course.get_assignment(assignment_id)
        canvas_assignment.edit(assignment=assignment_info)
    else:
        canvas_assignment = course.create_assignment(assignment=assignment_info)

    assignment_object_info: AssignmentInfo = {
        'id': canvas_assignment.id,
        'title': canvas_assignment.name,
        'uri': f'/courses/{course.id}/assignments/{canvas_assignment.id}',

        # Following fields have been observed to be missing in some cases
        'url': getattr(canvas_assignment, 'html_url', None)
    }

    return assignment_object_info, None
