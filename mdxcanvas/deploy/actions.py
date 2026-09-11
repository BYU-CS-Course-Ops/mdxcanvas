from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from ..resources import CanvasResource, ResourceInfo

ResourceKey = tuple[str, str]


class Transition(str, Enum):
    NEW = "new"
    MODIFIED = "modified"
    STALE = "stale"


class Outcome(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    UNTRACKED = "untracked"
    ALREADY_ABSENT = "already_absent"


class ActionKind(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ModifiedAction(str, Enum):
    UPDATE = "update"
    CREATE = "create"


class AbsencePolicy(str, Enum):
    DELETE = "delete"
    UNTRACK = "untrack"


@dataclass(frozen=True)
class PlannedChange:
    change: Transition
    resource_type: str
    resource_id: str
    source: str | None = None

    @property
    def key(self) -> ResourceKey:
        return self.resource_type, self.resource_id

    def public(self) -> dict[str, str]:
        return {
            "change": self.change.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
        }


@dataclass(frozen=True)
class Create:
    resource: CanvasResource
    checksum: str


@dataclass(frozen=True)
class Update:
    resource: CanvasResource
    checksum: str


@dataclass(frozen=True)
class Delete:
    resource_type: str
    resource_id: str
    canvas_info: ResourceInfo
    absence_policy: AbsencePolicy


@dataclass(frozen=True)
class ActionNode:
    key: str
    predecessors: frozenset[str]
    plan_order: int
    action: Create | Update | Delete
    planned_change: PlannedChange


@dataclass(frozen=True)
class DeploymentPlan:
    nodes: tuple[ActionNode, ...]
    expected_changes: tuple[PlannedChange, ...]


@dataclass(frozen=True)
class DeploymentContext:
    course: Any
    deploy_root: Path
    timezone: str


@dataclass(frozen=True)
class ReviewInfo:
    name: str
    url: str | None


@dataclass(frozen=True)
class DeploymentResult:
    canvas_info: ResourceInfo
    url: str | None = None
    review: ReviewInfo | None = None


CreateHandler = Callable[[DeploymentContext, CanvasResource], DeploymentResult]
UpdateHandler = Callable[[DeploymentContext, CanvasResource, ResourceInfo], DeploymentResult]
DeleteHandler = Callable[[DeploymentContext, str, ResourceInfo], bool]
CycleBreaker = Callable[[CanvasResource], CanvasResource]


@dataclass(frozen=True)
class HandlerSpec:
    create: CreateHandler
    update: UpdateHandler
    delete: DeleteHandler | None = None
    modified_action: ModifiedAction = ModifiedAction.UPDATE
    absence_policy: AbsencePolicy = AbsencePolicy.DELETE
    prepare_cycle_breaker: CycleBreaker | None = None


def validate_handlers(handlers: Mapping[str, HandlerSpec]):
    for resource_type, spec in handlers.items():
        if not resource_type or not callable(spec.create) or not callable(spec.update):
            raise ValueError(f"Invalid handler specification for {resource_type!r}")
        if spec.absence_policy is AbsencePolicy.DELETE and not callable(spec.delete):
            raise ValueError(f"Delete handler required for {resource_type}")
