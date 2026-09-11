import threading
from types import SimpleNamespace

import pytest

from mdxcanvas.erasecanvas import main as erase


class Course:
    id = 10
    name = "Test"

    def update(self, **_kwargs):
        pass

    def get_quizzes(self):
        return [SimpleNamespace(kind="quiz")]

    def get_assignments(self):
        return [SimpleNamespace(kind="assignment")]

    def get_assignment_groups(self):
        return [SimpleNamespace(kind="group")]

    def get_pages(self):
        return []

    def get_modules(self):
        return []

    def get_folders(self):
        return []

    def get_discussion_topics(self, **_kwargs):
        return []


def test_erase_preserves_quiz_assignment_group_dependency_order(monkeypatch):
    course = Course()
    calls = []
    monkeypatch.setattr(erase, "get_course", lambda *_args: course)

    def delete(items, item_type=None):
        items = list(items)
        if items:
            calls.append(items[0].kind)

    monkeypatch.setattr(erase, "parallel_delete", delete)

    erase.main("token", {"CANVAS_API_URL": "url", "CANVAS_COURSE_ID": 10}, True)

    assert calls.index("quiz") < calls.index("assignment") < calls.index("group")


def test_erase_waits_for_running_unrelated_work_before_raising(monkeypatch):
    course = Course()
    unrelated_finished = threading.Event()
    monkeypatch.setattr(erase, "get_course", lambda *_args: course)

    def delete(items, item_type=None):
        items = list(items)
        if items and items[0].kind == "quiz":
            raise RuntimeError("delete failed")

    monkeypatch.setattr(erase, "parallel_delete", delete)
    monkeypatch.setattr(erase, "delete_all_files", lambda _course: unrelated_finished.set())

    with pytest.raises(RuntimeError, match="delete failed"):
        erase.main("token", {"CANVAS_API_URL": "url", "CANVAS_COURSE_ID": 10}, True)

    assert unrelated_finished.is_set()
