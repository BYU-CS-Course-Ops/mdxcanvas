import json
from copy import deepcopy
from pathlib import Path
from typing import Mapping

from .actions import (ActionNode, AbsencePolicy, Create, Delete, DeploymentPlan, HandlerSpec,
                      ModifiedAction, PlannedChange, ResourceKey, Transition, Update)
from .algorithms import tarjan_scc
from .checksums import compute_md5
from ..resources import CanvasResource, iter_keys


# These exported values can change even when the producer keeps its Canvas identity.
UPDATE_PROPAGATING_FIELDS = frozenset({"title", "uri", "url", "page_url"})


class PlanningError(ValueError):
    def __init__(self, message: str, *, resource=None):
        super().__init__(message)
        self.resource = resource


def _references(resource: CanvasResource):
    return list(iter_keys(json.dumps(resource["data"])))


def plan_deployment(resources: Mapping[tuple[str, str], CanvasResource], ledger: Mapping,
                    handlers: Mapping[str, HandlerSpec], deploy_root: Path,
                    *, no_cleanup: bool = False) -> DeploymentPlan:
    desired = deepcopy(dict(resources))
    entries = ledger["resources"]
    decoded = {tuple(raw.split("|", 1)): deepcopy(entry) for raw, entry in entries.items()}
    dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
    update_dependencies: dict[ResourceKey, set[ResourceKey]] = {}
    referenced = set()

    for key, resource in desired.items():
        if not isinstance(resource.get("reapply_on_update", False), bool):
            raise PlanningError("reapply_on_update must be a boolean", resource=resource)
        dependencies[key] = set()
        update_dependencies[key] = set()
        for _token, resource_type, resource_id, field in _references(resource):
            dependency = resource_type, resource_id
            dependencies[key].add(dependency)
            if resource.get("reapply_on_update", False) or field in UPDATE_PROPAGATING_FIELDS:
                update_dependencies[key].add(dependency)
            referenced.add(dependency)
            if dependency not in desired:
                info = decoded.get(dependency, {}).get("canvas_info")
                if not info or not info.get("id") or not info.get(field):
                    source = resource.get("content_path")
                    raise PlanningError(
                        f"Missing field '{field}' in {resource_type} {resource_id}; "
                        f"referenced by {key[0]} {key[1]} in {source}",
                        resource=resource,
                    )

    transitions: dict[tuple[str, str], PlannedChange] = {}
    actions = {}
    checksums = {}

    def add(key, transition):
        if key in transitions:
            return
        resource_type, resource_id = key
        spec = handlers.get(resource_type)
        if spec is None:
            raise PlanningError(f"Unsupported resource type {resource_type}")
        source = desired.get(key, {}).get("content_path")
        change = PlannedChange(transition, resource_type, resource_id, source)
        transitions[key] = change
        if transition is Transition.STALE:
            info = decoded[key]["canvas_info"]
            actions[key] = Delete(resource_type, resource_id, info, spec.absence_policy)
        else:
            resource = desired[key]
            checksum = checksums[key]
            if transition is Transition.NEW or spec.modified_action is ModifiedAction.CREATE:
                actions[key] = Create(resource, checksum)
            else:
                actions[key] = Update(resource, checksum)

    for key in sorted(desired):
        resource_type, _ = key
        if resource_type not in handlers:
            raise PlanningError(f"Unsupported resource type {resource_type}")
        checksums[key] = compute_md5(desired[key]["data"], deploy_root)
        old = decoded.get(key)
        if old is None:
            add(key, Transition.NEW)
        else:
            info = old.get("canvas_info")
            if old.get("checksum") is not None and (not info or not info.get("id")):
                raise PlanningError(f"Tracked {resource_type} {key[1]} has checksum but no Canvas identity")
            if old.get("checksum") != checksums[key]:
                add(key, Transition.MODIFIED)

    if not no_cleanup:
        for key in sorted(set(decoded) - set(desired) - referenced):
            if key[0] not in handlers:
                raise PlanningError(f"Unsupported resource type {key[0]}")
            add(key, Transition.STALE)

    # Creates invalidate all references. Updates propagate across opted-in or mutable-field edges.
    queue = list(actions)
    while queue:
        producer = queue.pop(0)
        for consumer in sorted(desired):
            invalidated = producer in dependencies[consumer] and (
                isinstance(actions[producer], Create)
                or (isinstance(actions[producer], Update) and producer in update_dependencies[consumer])
            )
            if invalidated and consumer not in transitions:
                add(consumer, Transition.MODIFIED)
                queue.append(consumer)

    # Scheduled consumers wait for all referenced actions, including in-place updates.
    predecessors = {key: set() for key in actions}
    for consumer, refs in dependencies.items():
        if consumer not in actions:
            continue
        for producer in refs:
            if producer in actions:
                predecessors[consumer].add(producer)
        # Removed references no longer appear in data, but their deletions must finish first.
        previous = decoded.get(consumer, {}).get("dependencies", [])
        predecessors[consumer].update(
            tuple(producer) for producer in previous
            if isinstance(actions.get(tuple(producer)), Delete)
        )

    # Stale children are removed before their stale parents.
    stale_by_canvas_id = {}
    for key, action in actions.items():
        if isinstance(action, Delete):
            stale_by_canvas_id[(key[0], str(action.canvas_info["id"]))] = key
    for child, action in actions.items():
        if not isinstance(action, Delete):
            continue
        parent = action.canvas_info.get("parent")
        if isinstance(parent, dict):
            parent_key = stale_by_canvas_id.get((parent.get("type"), str(parent.get("id"))))
            if parent_key:
                predecessors[parent_key].add(child)

    cyclic = []
    graph = {key: set(predecessors[key]) for key in actions}
    for component in tarjan_scc(graph):
        if len(component) > 1 or (component and component[0] in graph.get(component[0], set())):
            cyclic.append(sorted(component))

    expanded = set()
    cycle_nodes = []
    for component in cyclic:
        for key in component:
            action = actions[key]
            if isinstance(action, Delete) or (
                isinstance(action, Create) and transitions[key].change is not Transition.NEW
            ):
                raise PlanningError(f"Unsupported replacement-create or deletion dependency cycle: {component}")
            if isinstance(action, Create) and handlers[key[0]].prepare_cycle_breaker is None:
                raise PlanningError(f"No cycle breaker for {key[0]} {key[1]}")
        first_keys = {key: f"first:{key[0]}|{key[1]}" for key in component}
        new_keys = {key for key in component if isinstance(actions[key], Create)}
        for key in component:
            change = transitions[key]
            external = {dep for dep in predecessors[key] if dep not in component}
            if key in new_keys:
                try:
                    shell = handlers[key[0]].prepare_cycle_breaker(desired[key])
                except Exception as error:
                    raise PlanningError(
                        f"Cycle breaker failed for {key[0]} {key[1]} ({type(error).__name__})"
                    ) from error
                # A shell must not need identities that this cycle has yet to create.
                if any((rtype, rid) in component for _, rtype, rid, _ in _references(shell)):
                    raise PlanningError(f"Cycle breaker left internal references in {key[0]} {key[1]}")
                first_action = Create(shell, None)
            else:
                # Existing identities allow full updates, once all new identities exist.
                external.update(first_keys[producer] for producer in new_keys)
                first_action = Update(desired[key], None)
            cycle_nodes.append((first_keys[key], external, first_action, change))
            full_change = PlannedChange(Transition.MODIFIED, key[0], key[1], change.source)
            full_key = f"full:{key[0]}|{key[1]}"
            cycle_nodes.append((full_key, set(first_keys.values()), Update(desired[key], checksums[key]), full_change))
            expanded.add(key)

    raw_nodes = []
    expected = []
    key_to_node = {key: f"action:{key[0]}|{key[1]}" for key in actions if key not in expanded}
    def dependency_node(producer: ResourceKey | str) -> str:
        if isinstance(producer, str):
            return producer
        # External consumers wait for the full update, not just a cycle-breaking shell.
        if producer in expanded:
            return f"full:{producer[0]}|{producer[1]}"
        return key_to_node[producer]

    for key in sorted(actions, key=lambda item: list(transitions).index(item)):
        if key in expanded:
            continue
        change = transitions[key]
        expected.append(change)
        raw_nodes.append((key_to_node[key], {dependency_node(p) for p in predecessors[key]}, actions[key], change))
    for node_key, deps, action, change in cycle_nodes:
        expected.append(change)
        converted = {dependency_node(dep) for dep in deps}
        raw_nodes.append((node_key, converted, action, change))

    nodes = tuple(ActionNode(key, frozenset(deps), index, action, change)
                  for index, (key, deps, action, change) in enumerate(raw_nodes))
    return DeploymentPlan(nodes, tuple(expected), tuple(frozenset(component) for component in cyclic))
