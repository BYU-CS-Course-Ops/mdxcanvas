import copy
import importlib
from dataclasses import FrozenInstanceError

import pytest

from mdxcanvas.deploy.quiz import deploy_quiz


BUILTIN_TYPES = {
    "announcement",
    "assignment",
    "assignment_group",
    "course_settings",
    "file",
    "mermaid",
    "module",
    "module_item",
    "navigation",
    "override",
    "page",
    "quarto-slides",
    "quiz",
    "quiz_question",
    "quiz_question_order",
    "syllabus",
    "zip",
}


def build_builtin_handlers():
    module = importlib.import_module("mdxcanvas.deploy.handlers")
    return module.build_builtin_handlers()


def enum_value(value):
    return getattr(value, "value", value)


def test_builtin_handler_mapping_is_fresh_and_complete():
    first = build_builtin_handlers()
    second = build_builtin_handlers()

    assert first is not second
    assert set(first) == BUILTIN_TYPES
    assert all(spec.create and spec.update for spec in first.values())


def test_replacement_create_and_untrack_policies_are_data_driven():
    handlers = build_builtin_handlers()

    replacement_create = {
        resource_type
        for resource_type, spec in handlers.items()
        if enum_value(spec.modified_action).lower() == "create"
    }
    untracked = {
        resource_type
        for resource_type, spec in handlers.items()
        if enum_value(spec.absence_policy).lower() == "untrack"
    }

    assert replacement_create == {"file", "zip", "mermaid", "quarto-slides"}
    assert untracked == {
        "course_settings",
        "navigation",
        "quiz_question_order",
        "syllabus",
    }
    for resource_type, spec in handlers.items():
        if resource_type not in untracked:
            assert spec.delete is not None


def test_legacy_deployer_review_tuple_becomes_immutable_metadata_without_url_inference():
    handlers = importlib.import_module("mdxcanvas.deploy.handlers")

    reviewed = handlers._result(
        "quiz",
        ({"id": "10", "url": "https://outcome"}, ("Original title", None)),
    )
    ordinary = handlers._result(
        "page",
        ({"id": "11", "url": "https://outcome-only"}, None),
    )
    file_result = handlers._result(
        "file",
        ({"id": "12", "url": "https://canvas/files/12/download"}, None),
    )

    assert reviewed.url == "https://outcome"
    assert reviewed.review.name == "Original title"
    assert reviewed.review.url is None
    with pytest.raises(FrozenInstanceError):
        reviewed.review.name = "changed"
    assert ordinary.url == "https://outcome-only"
    assert ordinary.review is None
    assert file_result.url == "https://canvas/files/12/download"


def test_submitted_quiz_review_uses_pre_edit_title_and_nullable_safe_url(tmp_path):
    class SubmittedQuiz:
        id = "10"
        title = "Original title"
        published = True

        def get_submissions(self):
            return [object()]

        def edit(self, *, quiz):
            self.title = quiz["title"]

    quiz = SubmittedQuiz()

    class Course:
        id = "20"

        def get_quiz(self, quiz_id):
            assert quiz_id == "10"
            return quiz

    canvas_info, review = deploy_quiz(
        Course(), {"canvas_id": "10", "title": "Updated title"}, tmp_path,
    )

    assert canvas_info["title"] == "Updated title"
    assert review == ("Original title", None)


def test_cycle_breakers_are_supported_only_for_documented_types_and_are_pure():
    handlers = build_builtin_handlers()
    with_breakers = {
        resource_type
        for resource_type, spec in handlers.items()
        if spec.prepare_cycle_breaker is not None
    }
    assert with_breakers == {"assignment", "page", "quiz", "syllabus"}

    fields = {
        "assignment": "description",
        "page": "body",
        "quiz": "description",
        "syllabus": "content",
    }
    for resource_type, field in fields.items():
        resource = {
            "type": resource_type,
            "id": "resource",
            "data": {field: "__@@page||other||id@@__", "keep": "value"},
            "content_path": "course.md",
        }
        original = copy.deepcopy(resource)

        shell = handlers[resource_type].prepare_cycle_breaker(resource)

        assert resource == original
        assert shell is not resource
        assert shell["data"] is not resource["data"]
        assert shell["data"][field] == ""
        assert shell["data"]["keep"] == "value"
