"""Group categories are declared, not looked up.

`group_category` used to carry a category *name* straight to an API that takes
`group_category_id`, so it was discarded and the assignment deployed ungrouped.
Resolving the name against whatever happened to exist in Canvas would have fixed
the symptom while leaving the source dependent on manual UI state, which is the
opposite of how `assignment_group` works. So a category is a declared resource
and an assignment references one by its source id.
"""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from mdxcanvas.deploy.group import deploy_group_category
from mdxcanvas.resources import ResourceManager, get_key
from mdxcanvas.xml_processing.assignment_tags import AssignmentTagProcessor
from mdxcanvas.xml_processing.group_tags import GroupCategoryTagProcessor


def _tag(xml: str, name: str):
    return BeautifulSoup(xml, 'html.parser').find(name)


class FakeCategory:
    def __init__(self, id=12816):
        self.id = id
        self.updates = []

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self


class FakeCourse:
    def __init__(self, existing=()):
        self.id = 1
        self.created = []
        self._existing = list(existing)

    def get_group_categories(self):
        return list(self._existing)

    def create_group_category(self, **kwargs):
        self.created.append(kwargs)
        return FakeCategory()


def test_a_declared_category_becomes_a_resource():
    resources = ResourceManager()
    GroupCategoryTagProcessor(resources)(_tag("""
    <group-category id="teams" name="Project Teams" self_signup="enabled" group_limit="4" />
    """, 'group-category'))

    (rtype, rid), resource = next(iter(resources.items()))
    assert (rtype, rid) == ('group_category', 'teams')
    assert resource['data'] == {
        'name': 'Project Teams',
        'self_signup': 'enabled',
        'group_limit': 4,
    }


def test_an_assignment_references_the_category_by_source_id():
    """The id is a placeholder resolved at deploy, exactly as assignment_group
    does it. The course never writes a Canvas id or a category name."""
    resources = ResourceManager()
    AssignmentTagProcessor(resources)(_tag("""
    <assignment id="a1" title="Project" group_category="teams">Build something.</assignment>
    """, 'assignment'))

    data = next(iter(resources.values()))['data']
    assert data['group_category_id'] == get_key('group_category', 'teams', 'id')
    assert 'group_category' not in data


def test_deploying_a_category_creates_it():
    course = FakeCourse()

    info, _ = deploy_group_category(course, {'name': 'Project Teams', 'group_limit': 4}, Path('.'))

    assert course.created == [{'name': 'Project Teams', 'group_limit': 4}]
    assert info['id'] == 12816


def test_deploying_a_known_category_updates_it_in_place():
    existing = FakeCategory(id=555)
    course = FakeCourse(existing=[existing])

    deploy_group_category(course, {'canvas_id': 555, 'name': 'Renamed'}, Path('.'))

    assert course.created == []
    assert existing.updates == [{'name': 'Renamed'}]


def test_a_category_that_vanished_from_canvas_is_an_error():
    """Better than silently creating a second one under the same name."""
    course = FakeCourse(existing=[FakeCategory(id=555)])

    with pytest.raises(ValueError, match="no longer exists"):
        deploy_group_category(course, {'canvas_id': 999, 'name': 'Gone'}, Path('.'))
