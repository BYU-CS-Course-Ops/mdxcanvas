from pathlib import Path

from canvasapi.course import Course

from ..resources import AssignmentInfo


def deploy_assignment(course: Course, assignment_info: dict, _: Path) -> tuple[AssignmentInfo, None]:
    # TODO - update group_category (name) to group_category_id
    #  Is this necessary to support?

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
