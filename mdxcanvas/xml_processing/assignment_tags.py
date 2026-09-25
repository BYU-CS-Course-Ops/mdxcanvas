from bs4.element import Tag

from .attributes import make_id_parser, parse_settings, Attribute, parse_bool, parse_date, parse_list, parse_dict, \
    parse_int
from ..util import retrieve_contents
from ..resources import ResourceManager, CanvasResource
from .override_parsing import parse_overrides_container
from ..processing_context import get_current_file_str


class AssignmentTagProcessor:
    def __init__(self, resources: ResourceManager):
        self._resources = resources

    def __call__(self, assignment_tag: Tag):
        fields = [
            Attribute('id', required=True),
            Attribute('allowed_attempts', parser=lambda x: -1 if x == 'not_graded' else int(x)),
            Attribute('allowed_extensions', [], parse_list),
            Attribute('annotatable_attachment_id'),  # TODO keep?
            Attribute('assignment_group', parser=make_id_parser('assignment_group'), new_name='assignment_group_id'),
            Attribute('automatic_peer_reviews', False, parse_bool),
            Attribute('available_from', parser=parse_date, new_name='unlock_at'),
            Attribute('available_to', parser=parse_date, new_name='lock_at'),
            Attribute('due_at', parser=parse_date),
            Attribute('late_due', parser=parse_date),
            Attribute('external_tool_tag_attributes', {}, parser=parse_dict),
            Attribute('final_grader_id'),  # TODO - keep?
            Attribute('grade_group_students_individually', False, parse_bool),
            Attribute('grading_standard_id'),  # TODO - keep?
            Attribute('grading_type', 'points'),
            Attribute('grader_comments_visible_to_graders', False, parse_bool),
            Attribute('grader_count'),
            Attribute('grader_names_visible_to_final_grader', False, parse_bool),
            Attribute('graders_anonymous_to_graders', False, parse_bool),
            Attribute('group_category', parser=make_id_parser('group_category'),
                      new_name='group_category_id'),
            Attribute('hide_in_gradebook', False, parse_bool),
            Attribute('integration_data'),  # TODO - keep?
            Attribute('moderated_grading', False, parse_bool),
            Attribute('notify_of_update', False, parse_bool),
            Attribute('omit_from_final_grade', False, parse_bool),
            Attribute('only_visible_to_overrides', False, parse_bool),
            Attribute('peer_reviews', False, parse_bool),
            Attribute('points_possible', parser=parse_int),
            Attribute('position', parser=parse_int),
            Attribute('published', parser=parse_bool),
            Attribute('quiz_lti'),  # TODO - keep?
            Attribute('submission_types', parser=parse_list),  # TODO - keep?
            Attribute('title', new_name='name', required=True),
            Attribute('turnitin_enabled', False, parse_bool),  # TODO - keep?
            Attribute('turnitin_settings'),  # TODO - keep?
            Attribute('vericite_enabled', False, parse_bool),  # TODO - keep?
        ]

        settings = {
            "type": "assignment",
            "description": retrieve_contents(assignment_tag),
        }

        settings.update(parse_settings(assignment_tag, fields))

        rid = settings.pop('id')
        assignment = CanvasResource(
            type='assignment',
            id=rid,
            data=settings,
            content_path=get_current_file_str()
        )
        self._resources.add_resource(assignment)

        # Process <overrides> child tag if present
        for tag in assignment_tag.children:
            if isinstance(tag, Tag) and tag.name == "overrides":
                parse_overrides_container(tag, 'assignment', rid, self._resources)
