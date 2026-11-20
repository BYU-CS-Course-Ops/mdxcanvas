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


def _renames(resource: CanvasResource, canvas_info: Mapping | None) -> bool:
    """Whether an update changes the title Canvas reported, and with it a page's uri.

    Pages, quizzes and announcements carry their title as `title`; assignments
    and modules as `name`. When either side is unknown, assume a rename.
    """
    data = resource.get("data") or {}
    new_title = data.get("title", data.get("name"))
    old_title = (canvas_info or {}).get("title")
    return new_title is None or old_title is None or new_title != old_title


def plan_deployment(resources: Mapping[tuple[str, str], CanvasResource], ledger: Mapping,
                    handlers: Mapping[str, HandlerSpec], deploy_root: Path,
                    *, no_cleanup: bool = False) -> DeploymentPlan:
    desired = deepcopy(dict(resources))
    entries = ledger["resources"]
    decoded = {tuple(raw.split("|", 1)): deepcopy(entry) for raw, entry in entries.items()}
    dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
    # Fields other than the Canvas id that each consumer reads from each producer,
    # such as a course-link's title and uri. An update can change these.
    mutable_reads: dict[tuple[str, str], dict[tuple[str, str], set[str]]] = {}
    referenced = set()

    for key, resource in desired.items():
        dependencies[key] = set()
        mutable_reads[key] = {}
        for _token, resource_type, resource_id, field in _references(resource):
            dependency = resource_type, resource_id
            dependencies[key].add(dependency)
            if field != "id":
                mutable_reads[key].setdefault(dependency, set()).add(field)
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
    # An update keeps the Canvas id, but a rename changes the title and can change
    # the uri, so a renaming update reapplies the consumers that read those.
    # Other updates reapply nothing: re-sending a quiz that has submissions asks
    # an instructor to save it again by hand.
    renamed = {
        key for key, action in actions.items()
        if isinstance(action, Update) and _renames(desired[key], decoded.get(key, {}).get("canvas_info"))
    }
    queue = list(actions)
    while queue:
        producer = queue.pop(0)
        replaced = isinstance(actions[producer], Create)
        for consumer in sorted(desired):
            if consumer in transitions or producer not in dependencies.get(consumer, set()):
                continue
            if replaced or (producer in renamed and producer in mutable_reads[consumer]):
                add(consumer, Transition.MODIFIED)
                if isinstance(actions[consumer], Create):
                    queue.append(consumer)

    if not no_cleanup:
        for key in sorted(set(decoded) - set(desired) - referenced):
            if key[0] not in handlers:
                raise PlanningError(f"Unsupported resource type {key[0]}")
            add(key, Transition.STALE)

    # Action dependency graph: consumers wait for identity-producing creates, and
    # for renames whose title or uri they read.
    predecessors = {key: set() for key in actions}
    update_edges = set()
    for consumer, refs in dependencies.items():
        if consumer not in actions:
            continue
        for producer in refs:
            if isinstance(actions.get(producer), Create):
                predecessors[consumer].add(producer)
            elif producer in renamed and producer != consumer and producer in mutable_reads[consumer]:
                predecessors[consumer].add(producer)
                update_edges.add((consumer, producer))

    # Two updates that read each other's fields cannot both go second. Drop the
    # update edges inside such a cycle and send them in either order; only cycles
    # of replacement creates need the shell expansion below.
    if update_edges:
        update_graph = {key: set(predecessors[key]) for key in actions}
        for component in tarjan_scc(update_graph):
            if len(component) > 1:
                members = set(component)
                for consumer, producer in update_edges:
                    if consumer in members and producer in members:
                        predecessors[consumer].discard(producer)

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
