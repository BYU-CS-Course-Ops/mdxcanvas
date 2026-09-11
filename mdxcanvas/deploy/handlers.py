from copy import deepcopy
from typing import Callable

from canvasapi.exceptions import ResourceDoesNotExist

from .actions import (AbsencePolicy, DeploymentContext, DeploymentResult, HandlerSpec,
                      ModifiedAction, ReviewInfo, validate_handlers)
from .announcement import deploy_announcement
from .assignment import deploy_assignment
from .course_settings import deploy_settings
from .file import deploy_file
from .group import deploy_group
from .mermaid import deploy_mermaid
from .module import deploy_module, deploy_module_item, get_module_item
from .navigation import deploy_navigation
from .override import deploy_override, get_override
from .page import deploy_page
from .quarto_slides import deploy_quarto_slides
from .quiz import deploy_quiz, deploy_quiz_question, deploy_quiz_question_order, get_quiz_question
from .syllabus import deploy_syllabus
from .zip import deploy_zip


def _result(resource_type: str, value) -> DeploymentResult:
    canvas_info, review = value
    canvas_info = dict(canvas_info)
    if resource_type == "module_item" and "module_id" in canvas_info:
        canvas_info["parent"] = {"type": "module", "id": str(canvas_info.pop("module_id"))}
    elif resource_type == "quiz_question" and "quiz_id" in canvas_info:
        canvas_info["parent"] = {"type": "quiz", "id": str(canvas_info.pop("quiz_id"))}
    elif resource_type == "override" and "assignment_id" in canvas_info:
        canvas_info["parent"] = {"type": "assignment", "id": str(canvas_info.pop("assignment_id"))}
    review_info = ReviewInfo(*review) if review is not None else None
    return DeploymentResult(canvas_info, canvas_info.get("url"), review_info)


def _adapter(resource_type: str, deploy: Callable):
    def create(context: DeploymentContext, resource):
        copied = deepcopy(resource)
        return _result(resource_type, deploy(context.course, copied["data"], context.deploy_root))

    def update(context: DeploymentContext, resource, canvas_info):
        copied = deepcopy(resource)
        copied["data"]["canvas_id"] = canvas_info["id"]
        return _result(resource_type, deploy(context.course, copied["data"], context.deploy_root))

    return create, update


def _lookup(context: DeploymentContext, resource_type: str, canvas_info):
    canvas_id = canvas_info["id"]
    parent = canvas_info.get("parent") or {}
    if resource_type == "module_item":
        return get_module_item(context.course, parent.get("id"), canvas_id)
    if resource_type == "override":
        return get_override(context.course, parent.get("id"), canvas_id)
    if resource_type == "quiz_question":
        return get_quiz_question(context.course, parent.get("id"), canvas_id)
    if resource_type == "announcement":
        return context.course.get_discussion_topic(canvas_id)
    if resource_type in {"zip", "quarto-slides", "mermaid"}:
        return context.course.get_file(canvas_id)
    getter = getattr(context.course, f"get_{resource_type}")
    return getter(canvas_id)


def _delete(resource_type: str):
    def delete(context: DeploymentContext, _resource_id: str, canvas_info) -> bool:
        try:
            resource = _lookup(context, resource_type, canvas_info)
            if resource is None:
                return False
            resource.delete()
            return True
        except ResourceDoesNotExist:
            return False
    return delete


def _breaker(field: str):
    def prepare(resource):
        copied = deepcopy(resource)
        copied["data"][field] = ""
        return copied
    return prepare


def build_builtin_handlers() -> dict[str, HandlerSpec]:
    deployers = {
        "announcement": deploy_announcement,
        "assignment": deploy_assignment,
        "assignment_group": deploy_group,
        "course_settings": deploy_settings,
        "file": deploy_file,
        "mermaid": deploy_mermaid,
        "module": deploy_module,
        "module_item": deploy_module_item,
        "navigation": deploy_navigation,
        "override": deploy_override,
        "page": deploy_page,
        "quarto-slides": deploy_quarto_slides,
        "quiz": deploy_quiz,
        "quiz_question": deploy_quiz_question,
        "quiz_question_order": deploy_quiz_question_order,
        "syllabus": deploy_syllabus,
        "zip": deploy_zip,
    }
    replacements = {"file", "zip", "mermaid", "quarto-slides"}
    untracked = {"course_settings", "navigation", "quiz_question_order", "syllabus"}
    breakers = {
        "assignment": _breaker("description"),
        "page": _breaker("body"),
        "quiz": _breaker("description"),
        "syllabus": _breaker("content"),
    }
    handlers = {}
    for resource_type, deployer in deployers.items():
        create, update = _adapter(resource_type, deployer)
        handlers[resource_type] = HandlerSpec(
            create=create,
            update=update,
            delete=None if resource_type in untracked else _delete(resource_type),
            modified_action=ModifiedAction.CREATE if resource_type in replacements else ModifiedAction.UPDATE,
            absence_policy=AbsencePolicy.UNTRACK if resource_type in untracked else AbsencePolicy.DELETE,
            prepare_cycle_breaker=breakers.get(resource_type),
        )
    validate_handlers(handlers)
    return handlers
