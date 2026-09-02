from importlib import import_module
from pathlib import Path

import pytest


class FakeTab:
    def __init__(self, tab_id, label, position, hidden=False, *, include_hidden=True):
        self.id = tab_id
        self.label = label
        self.position = position
        if include_hidden:
            self.hidden = hidden
        self.updates = []
        self.failure = None

    def update(self, **changes):
        self.updates.append(changes)
        if self.failure:
            raise self.failure
        for name, value in changes.items():
            setattr(self, name, value)
        return self


class FakeCourse:
    def __init__(self, tabs):
        self.id = 42
        self.tabs = tabs
        self.get_tabs_calls = 0

    def get_tabs(self):
        self.get_tabs_calls += 1
        return self.tabs


class LazyTabPages:
    def __init__(self, pages):
        self.pages = pages
        self.exhausted = False

    def __iter__(self):
        for page in self.pages:
            yield from page
        self.exhausted = True


def navigation_deployer():
    try:
        return import_module("mdxcanvas.deploy.navigation").deploy_navigation
    except ModuleNotFoundError:
        pytest.fail("mdxcanvas.deploy.navigation has not been implemented")


def deploy(course, names):
    return navigation_deployer()(course, {"tabs": names}, Path("."))


def tab(tab_id, label, position, hidden=False, **kwargs):
    return FakeTab(tab_id, label, position, hidden, **kwargs)


def all_updates(tabs):
    return [(item.label, update) for item in tabs for update in item.updates]


def test_listed_tabs_are_packed_after_home_and_unlisted_tabs_are_hidden():
    tabs = [
        tab("home", "Home", 1),
        tab("assignments", "Assignments", 2),
        tab("pages", "Pages", 3),
        tab("settings", "Settings", 4),
        tab("context_external_tool_7", "External Tool", 5, hidden=True),
    ]
    course = FakeCourse(tabs)

    info, review = deploy(course, ["External Tool", "Assignments"])

    assert course.get_tabs_calls == 1
    assert info == {"id": "42"}
    assert review is None
    assert all_updates(tabs) == [
        ("Pages", {"hidden": True}),
        ("External Tool", {"hidden": False, "position": 2}),
    ]
    assert tabs[0].updates == []
    assert tabs[3].updates == []


def test_empty_navigation_hides_every_manageable_visible_tab_and_skips_hidden_tabs():
    tabs = [
        tab("home", "Home", 1),
        tab("assignments", "Assignments", 2),
        tab("pages", "Pages", 3, hidden=True),
        tab("settings", "Settings", 4),
    ]

    deploy(FakeCourse(tabs), [])

    assert all_updates(tabs) == [("Assignments", {"hidden": True})]


def test_already_matching_navigation_and_omitted_hidden_attribute_skip_updates():
    tabs = [
        tab("home", "Home", 1),
        tab("assignments", "Assignments", 2, include_hidden=False),
        tab("tool", "Tool", 3),
        tab("pages", "Pages", 4, hidden=True),
        tab("settings", "Settings", 5),
    ]

    deploy(FakeCourse(tabs), ["Assignments", "Tool"])

    assert all_updates(tabs) == []


def test_complete_lazy_tab_inventory_is_materialized_once_before_matching():
    first = [tab("home", "Home", 1), tab("pages", "Pages", 2)]
    second = [tab("tool", "External Tool", 3), tab("settings", "Settings", 4)]
    pages = LazyTabPages([first, second])
    course = FakeCourse(pages)

    deploy(course, ["External Tool"])

    assert course.get_tabs_calls == 1
    assert pages.exhausted is True
    assert second[0].updates == [{"position": 2}]


@pytest.mark.parametrize(
    ("tabs", "names", "diagnostic"),
    [
        (
            [tab("home", "Home", 1), tab("pages", "Pages", 2)],
            ["pages"],
            "pages",
        ),
        (
            [tab("home", "Home", 1), tab("pages", "Pages", 2)],
            ["Missing"],
            "Missing",
        ),
        (
            [tab("home", "Home", 1), tab("pages", "Pages", 2), tab("tool", "Pages", 3)],
            ["Pages"],
            "Pages",
        ),
        (
            [tab("home", "Home", 1), tab("pages", "Pages", 2)],
            ["Home"],
            "Home",
        ),
        (
            [tab("home", "Home", 1), tab("settings", "Settings", 2)],
            ["Settings"],
            "Settings",
        ),
    ],
)
def test_invalid_references_fail_before_any_tab_update(tabs, names, diagnostic):
    with pytest.raises(Exception) as exc_info:
        deploy(FakeCourse(tabs), names)

    assert diagnostic in str(exc_info.value)
    assert all_updates(tabs) == []


def test_all_requested_references_are_validated_before_the_first_update():
    tabs = [
        tab("home", "Home", 1),
        tab("pages", "Pages", 2),
        tab("tool", "Tool", 3, hidden=True),
    ]

    with pytest.raises(Exception, match="Missing"):
        deploy(FakeCourse(tabs), ["Tool", "Missing"])

    assert all_updates(tabs) == []


def test_duplicate_requested_names_fail_before_any_tab_update():
    tabs = [tab("home", "Home", 1), tab("pages", "Pages", 2)]

    with pytest.raises(Exception, match="Pages"):
        deploy(FakeCourse(tabs), ["Pages", "Pages"])

    assert all_updates(tabs) == []


@pytest.mark.parametrize("missing_attribute", ["id", "label", "position"])
def test_malformed_canvas_tab_data_fails_before_any_update(missing_attribute):
    tabs = [tab("home", "Home", 1), tab("pages", "Pages", 2)]
    delattr(tabs[1], missing_attribute)

    with pytest.raises(Exception, match=missing_attribute):
        deploy(FakeCourse(tabs), ["Pages"])

    assert all(not item.updates for item in tabs)


@pytest.mark.parametrize(
    "invalid_position",
    [1.0, 1.5, float("nan"), float("inf"), True, 0, -1],
)
def test_unusable_home_position_fails_before_any_update(invalid_position):
    tabs = [
        tab("home", "Home", invalid_position),
        tab("tool", "Tool", 2, hidden=True),
    ]

    with pytest.raises(Exception, match="position"):
        deploy(FakeCourse(tabs), ["Tool"])

    assert all_updates(tabs) == []


def test_ambiguous_match_on_a_later_page_fails_before_any_update():
    first_page = [tab("home", "Home", 1), tab("pages", "Pages", 2)]
    later_page = [tab("tool", "Pages", 3), tab("settings", "Settings", 4)]
    course = FakeCourse(LazyTabPages([first_page, later_page]))

    with pytest.raises(Exception, match="Pages"):
        deploy(course, ["Pages"])

    assert course.tabs.exhausted is True
    assert all_updates(first_page + later_page) == []


def test_failure_stops_serial_updates_without_rollback():
    tabs = [
        tab("home", "Home", 1),
        tab("pages", "Pages", 2),
        tab("a", "A", 3, hidden=True),
        tab("b", "B", 4, hidden=True),
        tab("settings", "Settings", 5),
    ]
    tabs[3].failure = RuntimeError("Canvas update failed")

    with pytest.raises(RuntimeError, match="Canvas update failed"):
        deploy(FakeCourse(tabs), ["A", "B"])

    assert tabs[2].updates == [{"hidden": False, "position": 2}]
    assert tabs[3].updates == [{"hidden": False, "position": 3}]
    assert tabs[1].updates == []
    assert tabs[2].hidden is False
