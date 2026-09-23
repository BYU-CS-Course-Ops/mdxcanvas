from pathlib import Path

import pytest

from mdxcanvas.deploy.assignment import deploy_assignment


class FakeCategory:
    def __init__(self, name, id):
        self.name = name
        self.id = id


class FakeAssignment:
    def __init__(self):
        self.id = 99
        self.name = 'Probe'
        self.html_url = 'https://example.edu/a/99'


class FakeCourse:
    def __init__(self, categories=()):
        self.id = 1
        self.created = []
        self._categories = [FakeCategory(n, i) for n, i in categories]

    def get_group_categories(self):
        return list(self._categories)

    def create_assignment(self, assignment):
        self.created.append(assignment)
        return FakeAssignment()


def test_group_category_name_becomes_the_id_canvas_wants():
    """The name was passed straight through and the assignment API ignores it,
    so the assignment deployed ungrouped while the deploy reported success."""
    course = FakeCourse(categories=[('Project Teams', 12816)])

    deploy_assignment(course, {'name': 'Probe', 'group_category': 'Project Teams'}, Path('.'))

    sent = course.created[0]
    assert sent['group_category_id'] == 12816
    assert 'group_category' not in sent


def test_an_unmatched_group_category_is_an_error():
    """Silently creating one is how a course ends up with two categories
    differing by a space, and the error has to name what does exist so a typo
    is obvious."""
    course = FakeCourse(categories=[('Project Teams', 12816)])

    with pytest.raises(ValueError) as caught:
        deploy_assignment(course, {'name': 'Probe', 'group_category': 'Project teams'}, Path('.'))

    message = str(caught.value)
    assert "'Project teams'" in message
    assert "'Project Teams'" in message
    assert course.created == []


def test_an_assignment_without_a_group_category_is_unchanged():
    course = FakeCourse()

    deploy_assignment(course, {'name': 'Probe'}, Path('.'))

    assert course.created == [{'name': 'Probe'}]
