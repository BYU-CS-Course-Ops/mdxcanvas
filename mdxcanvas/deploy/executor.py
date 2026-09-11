import heapq
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from canvasapi.exceptions import CanvasException, RateLimitExceeded

from ..our_logging import get_logger


class DependencyFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class DagResult:
    values: dict[str, Any]
    failures: dict[str, Exception]
    blocked: dict[str, Exception]


def retry_rate_limit(call: Callable[[], Any], *, key: Any = None,
                     max_retries: int = 3, cooldown_seconds: float = 2.0) -> Any:
    if max_retries < 0 or cooldown_seconds < 0:
        raise ValueError("Retry limits must be non-negative")
    for attempt in range(max_retries + 1):
        try:
            return call()
        except (RateLimitExceeded, CanvasException) as error:
            rate_limited = isinstance(error, RateLimitExceeded) or "status code 429" in getattr(error, "message",
                                                                                                str(error))
            if not rate_limited or attempt == max_retries:
                raise
            get_logger().warning("Rate limited while processing %r; retrying", key)
            time.sleep(cooldown_seconds)
    raise AssertionError("retry loop exited unexpectedly")


def _validate(nodes: list[Any]) -> dict[str, Any]:
    by_key: dict[str, Any] = {}
    for node in nodes:
        if node.key in by_key:
            raise ValueError(f"Duplicate DAG node key: {node.key}")
        by_key[node.key] = node
    for node in nodes:
        unknown = set(node.predecessors) - by_key.keys()
        if unknown:
            raise ValueError(f"Unknown DAG predecessor(s): {sorted(unknown)}")
        if node.key in node.predecessors:
            raise ValueError(f"DAG self-loop: {node.key}")
    indegree = {key: len(node.predecessors) for key, node in by_key.items()}
    successors = {key: set() for key in by_key}
    for node in nodes:
        for predecessor in node.predecessors:
            successors[predecessor].add(node.key)
    ready = [key for key, count in indegree.items() if count == 0]
    seen = 0
    while ready:
        key = ready.pop()
        seen += 1
        for successor in successors[key]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    if seen != len(nodes):
        raise ValueError("DAG contains a cycle")
    return by_key


def execute_dag(
        nodes: Iterable[Any], callback: Callable[[Any], Any], *, max_workers: int = 8,
        on_resolved: Callable[[Any, str, Any], Any] | None = None,
) -> DagResult:
    nodes = list(nodes)
    by_key = _validate(nodes)
    order = {node.key: node.plan_order for node in nodes}
    successors = {key: set() for key in by_key}
    remaining = {key: len(node.predecessors) for key, node in by_key.items()}
    for node in nodes:
        for predecessor in node.predecessors:
            successors[predecessor].add(node.key)

    ready = [(order[key], key) for key, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    values: dict[str, Any] = {}
    failures: dict[str, Exception] = {}
    blocked: dict[str, Exception] = {}
    pending = set(by_key)

    def block_descendants(key: str):
        for successor in sorted(successors[key], key=order.get):
            if successor not in pending:
                continue
            pending.remove(successor)
            blocked[successor] = DependencyFailed("Not attempted because a prerequisite action failed")
            if on_resolved is not None:
                on_resolved(by_key[successor], "blocked", blocked[successor])
            block_descendants(successor)

    completion_order: dict[str, int] = {}
    completion_lock = threading.Lock()
    next_completion = 0

    def invoke(key: str):
        nonlocal next_completion
        try:
            return callback(by_key[key])
        finally:
            with completion_lock:
                completion_order[key] = next_completion
                next_completion += 1

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        running = {}
        while ready or running:
            while ready and len(running) < max_workers:
                _, key = heapq.heappop(ready)
                if key not in pending:
                    continue
                pending.remove(key)
                future = pool.submit(invoke, key)
                running[future] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in sorted(done, key=lambda item: completion_order[running[item]]):
                key = running.pop(future)
                try:
                    values[key] = future.result()
                except Exception as error:
                    failures[key] = error
                    if on_resolved is not None:
                        on_resolved(by_key[key], "failed", error)
                    block_descendants(key)
                    continue
                if on_resolved is not None:
                    on_resolved(by_key[key], "success", values[key])
                for successor in sorted(successors[key], key=order.get):
                    if successor not in pending:
                        continue
                    remaining[successor] -= 1
                    if remaining[successor] == 0:
                        heapq.heappush(ready, (order[successor], successor))

    ordered = lambda mapping: {key: mapping[key] for key in sorted(mapping, key=order.get)}
    return DagResult(ordered(values), ordered(failures), ordered(blocked))
