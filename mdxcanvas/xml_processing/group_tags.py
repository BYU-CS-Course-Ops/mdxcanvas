from typing import TypedDict, List

from bs4.element import Tag

from .attributes import Attribute, make_id_list_parser, parse_settings, parse_int
from ..resources import ResourceManager, CanvasResource, get_key
from ..processing_context import get_current_file_str


class AssignmentGroupRules(TypedDict, total=False):
    drop_lowest: int
    drop_highest: int
    never_drop: List[int]


def _extract_rules_from_group_data(group_data: dict) -> dict:
    rules: AssignmentGroupRules = {}

    if group_data.get('drop_lowest'):
        rules['drop_lowest'] = group_data.pop('drop_lowest')

    if group_data.get('drop_highest'):
        rules['drop_highest'] = group_data.pop('drop_highest')

    if group_data.get('never_drop'):
        rules['never_drop'] = group_data.pop('never_drop')

    if rules:
        group_data['rules'] = rules

    return group_data


class AssignmentGroupTagProcessor:
    """
    Processes <assignment-groups> tags and converts them to Canvas assignment group resources.

    Usage:
        <assignment-groups>
            <group id="g1" name="Group 1" weight="25" drop_lowest="5" />
            <group id="g2" name="Group 2" weight="75" drop_highest="3" never_drop="assign1,assign2" />
        </assignment-groups>
    """

    def __init__(self, resource_manager: ResourceManager):
        self._resources = resource_manager

    def __call__(self, group_tag: Tag) -> None:
        self._parse_assignment_group(group_tag)

    def _parse_assignment_group(self, tag: Tag) -> None:
        """
        Parse a single assignment group tag and add it to the resource manager.

        Args:
            tag: The assignment group tag to parse
        """
        attribute_fields = [
            Attribute('id', required=True),
            Attribute('name', required=True),
            Attribute('weight', new_name='group_weight', parser=parse_int),
            Attribute('never_drop', parser=make_id_list_parser('assignment')),
            Attribute('drop_lowest', parser=parse_int),
            Attribute('drop_highest', parser=parse_int),
            Attribute('position', parser=parse_int)
            # TODO: Find additional attributes to support
        ]

        group_data = parse_settings(tag, attribute_fields)
        group_data = _extract_rules_from_group_data(group_data)

        assignment_group = CanvasResource(
            type='assignment_group',
            id=group_data.pop('id'),
            data=group_data,
            content_path=get_current_file_str()
        )

        self._resources.add_resource(assignment_group)


class GroupCategoryTagProcessor:
    """
    Processes <group-category> tags into Canvas group category resources.

    A category is how students are teamed up for a kind of work; the groups
    inside it, and their membership, are managed in Canvas rather than declared
    here, because membership changes with enrolment.

    Usage:
        <group-category id="teams" name="Project Teams" self_signup="enabled"
                        group_limit="4" />

    An assignment joins one by id:

        <assignment id="a1" title="Project" group_category="teams" />
    """

    def __init__(self, resource_manager: ResourceManager):
        self._resources = resource_manager

    def __call__(self, category_tag: Tag) -> None:
        attribute_fields = [
            Attribute('id', required=True),
            Attribute('name', required=True),
            # 'enabled' or 'restricted'; restricted confines sign-up to a section.
            Attribute('self_signup'),
            Attribute('group_limit', parser=parse_int),
            # 'first' or 'random'. Canvas rejects it without self_signup.
            Attribute('auto_leader'),
        ]

        category_data = parse_settings(category_tag, attribute_fields)

        self._resources.add_resource(CanvasResource(
            type='group_category',
            id=category_data.pop('id'),
            data=category_data,
            content_path=get_current_file_str()
        ))
