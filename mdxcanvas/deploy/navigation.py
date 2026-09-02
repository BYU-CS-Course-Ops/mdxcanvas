from numbers import Integral
from pathlib import Path
from typing import Any

from canvasapi.course import Course

from ..resources import NavigationData, NavigationInfo

_FIXED_TAB_IDS = {"home", "settings"}


def _required_attribute(tab: Any, name: str):
    if not hasattr(tab, name):
        raise ValueError(f"Canvas tab is missing required attribute '{name}'")
    value = getattr(tab, name)
    if value is None or (isinstance(value, str) and not value):
        raise ValueError(f"Canvas tab has invalid required attribute '{name}'")
    return value


def _validate_snapshot(tabs: list[Any]):
    for tab in tabs:
        _required_attribute(tab, "id")
        _required_attribute(tab, "label")
        position = _required_attribute(tab, "position")
        if isinstance(position, bool) or not isinstance(position, Integral) or position < 1:
            raise ValueError("Canvas tab has invalid required attribute 'position'")


def _resolve_requested_tabs(tabs: list[Any], labels: list[str]) -> list[Any]:
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise ValueError(f"Duplicate navigation tab name(s): {', '.join(duplicates)}")

    resolved = []
    for label in labels:
        matches = [tab for tab in tabs if tab.label == label]
        if not matches:
            raise ValueError(f"Navigation tab {label!r} was not found")
        if len(matches) > 1:
            raise ValueError(f"Navigation tab {label!r} is ambiguous")

        tab = matches[0]
        if tab.id in _FIXED_TAB_IDS:
            raise ValueError(f"Navigation tab {label!r} cannot manage {tab.id.title()}")
        resolved.append(tab)

    return resolved


def _move_simulated_tab(ordered: list[Any], tab: Any, target_position: int, positions: dict[int, int]):
    ordered.remove(tab)
    ordered.insert(min(target_position - 1, len(ordered)), tab)
    positions.update({id(item): position for position, item in enumerate(ordered, start=1)})


def deploy_navigation(
        course: Course,
        data: NavigationData,
        _: Path
) -> tuple[NavigationInfo, None]:
    tabs = list(course.get_tabs())
    _validate_snapshot(tabs)

    ordered = sorted(tabs, key=lambda tab: tab.position)
    home_tabs = [tab for tab in ordered if tab.id == "home"]
    if len(home_tabs) != 1:
        raise ValueError("Canvas navigation must contain exactly one Home tab")

    requested = _resolve_requested_tabs(ordered, data["tabs"])
    requested_ids = {id(tab) for tab in requested}
    manageable = [tab for tab in ordered if tab.id not in _FIXED_TAB_IDS]
    home_position = home_tabs[0].position
    positions = {id(tab): tab.position for tab in ordered}

    for offset, tab in enumerate(requested, start=1):
        target_position = home_position + offset
        changes = {}
        if getattr(tab, "hidden", False):
            changes["hidden"] = False
        if positions[id(tab)] != target_position:
            changes["position"] = target_position

        if changes:
            tab.update(**changes)
        if "position" in changes:
            _move_simulated_tab(ordered, tab, target_position, positions)

    for tab in manageable:
        if id(tab) not in requested_ids and not getattr(tab, "hidden", False):
            tab.update(hidden=True)

    return NavigationInfo(id=str(course.id)), None
