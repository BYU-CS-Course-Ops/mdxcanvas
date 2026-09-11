import json
from copy import deepcopy
from pathlib import Path
from typing import Mapping

from .actions import (ActionNode, AbsencePolicy, Create, Delete, DeploymentPlan, HandlerSpec,
                      ModifiedAction, PlannedChange, Transition, Update)
from .algorithms import tarjan_scc
from .checksums import compute_md5
from ..resources import CanvasResource, iter_keys


class PlanningError(ValueError):
    def __init__(self, message: str, *, resource=None):
        super().__init__(message)
        self.resource = resource


def _references(resource: CanvasResource):
    return list(iter_keys(json.dumps(resource)))


def plan_deployment(resources: Mapping[tuple[str, str], CanvasResource], ledger: Mapping,
                    handlers: Mapping[str, HandlerSpec], deploy_root: Path,
                    *, no_cleanup: bool = False) -> DeploymentPlan:
    desired = deepcopy(dict(resources))
    entries = ledger["resources"]
    decoded = {tuple(raw.split("|", 1)): deepcopy(entry) for raw, entry in entries.items()}
    dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
    referenced = set()

    for key, resource in desired.items():
        dependencies[key] = set()
        for _token, resource_type, resource_id, field in _references(resource):
            dependency = resource_type, resource_id
            dependencies[key].add(dependency)
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

    # Replacement creates force every direct and transitive consumer to be reapplied.
    queue = [key for key, action in actions.items() if isinstance(action, Create)]
    while queue:
        producer = queue.pop(0)
        for consumer in sorted(desired):
            if producer in dependencies.get(consumer, set()) and consumer not in transitions:
                add(consumer, Transition.MODIFIED)
                if isinstance(actions[consumer], Create):
                    queue.append(consumer)

    if not no_cleanup:
        for key in sorted(set(decoded) - set(desired) - referenced):
            if key[0] not in handlers:
                raise PlanningError(f"Unsupported resource type {key[0]}")
            add(key, Transition.STALE)

    # Action dependency graph: consumers wait only for identity-producing creates.
    predecessors = {key: set() for key in actions}
    for consumer, refs in dependencies.items():
        if consumer not in actions:
            continue
        for producer in refs:
            if isinstance(actions.get(producer), Create):
                predecessors[consumer].add(producer)

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
    graph = {key: set(predecessors[key]) for key in actions if not isinstance(actions[key], Delete)}
    for component in tarjan_scc(graph):
        if len(component) > 1 or (component and component[0] in graph.get(component[0], set())):
            cyclic.append(sorted(component))

    expanded = set()
    cycle_nodes = []
    for component in cyclic:
        for key in component:
            if transitions[key].change is not Transition.NEW or not isinstance(actions[key], Create):
                raise PlanningError(f"Unsupported replacement-create dependency cycle: {component}")
            if handlers[key[0]].prepare_cycle_breaker is None:
                raise PlanningError(f"No cycle breaker for {key[0]} {key[1]}")
        shells = []
        for key in component:
            try:
                shell = handlers[key[0]].prepare_cycle_breaker(desired[key])
            except Exception as error:
                raise PlanningError(
                    f"Cycle breaker failed for {key[0]} {key[1]} ({type(error).__name__})"
                ) from error
            shell_key = f"shell:{key[0]}|{key[1]}"
            shell_change = transitions[key]
            external = {dep for dep in predecessors[key] if dep not in component}
            shells.append((key, shell_key, shell, shell_change, external))
        shell_keys = frozenset(item[1] for item in shells)
        for key, shell_key, shell, change, external in shells:
            cycle_nodes.append((shell_key, external, Create(shell, compute_md5(shell["data"], deploy_root)), change))
            full_change = PlannedChange(Transition.MODIFIED, key[0], key[1], change.source)
            full_key = f"full:{key[0]}|{key[1]}"
            cycle_nodes.append((full_key, shell_keys, Update(desired[key], checksums[key]), full_change))
            expanded.add(key)

    raw_nodes = []
    expected = []
    key_to_node = {key: f"action:{key[0]}|{key[1]}" for key in actions if key not in expanded}
    for node_key, _deps, _action, change in cycle_nodes:
        if node_key.startswith("shell:"):
            key_to_node[change.key] = node_key
    for key in sorted(actions, key=lambda item: list(transitions).index(item)):
        if key in expanded:
            continue
        change = transitions[key]
        expected.append(change)
        raw_nodes.append((key_to_node[key], {key_to_node[p] for p in predecessors[key] if p in key_to_node}, actions[key], change))
    for node_key, deps, action, change in cycle_nodes:
        expected.append(change)
        converted = {key_to_node.get(dep, dep if isinstance(dep, str) else f"action:{dep[0]}|{dep[1]}") for dep in deps}
        raw_nodes.append((node_key, converted, action, change))

    nodes = tuple(ActionNode(key, frozenset(deps), index, action, change)
                  for index, (key, deps, action, change) in enumerate(raw_nodes))
    return DeploymentPlan(nodes, tuple(expected))
