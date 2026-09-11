import importlib
import threading
from dataclasses import dataclass

import pytest
from canvasapi.exceptions import RateLimitExceeded

from mdxcanvas.deploy.executor import retry_rate_limit


@dataclass(frozen=True)
class Node:
    key: str
    predecessors: frozenset[str]
    plan_order: int
    action: str


def execute_dag(nodes, callback, *, max_workers=4, on_resolved=None):
    executor = importlib.import_module("mdxcanvas.deploy.executor")
    if on_resolved is None:
        return executor.execute_dag(nodes, callback, max_workers=max_workers)
    return executor.execute_dag(
        nodes, callback, max_workers=max_workers, on_resolved=on_resolved,
    )


def test_empty_graph_has_no_work():
    result = execute_dag([], lambda _node: pytest.fail("unexpected callback"))

    assert result.values == {}
    assert result.failures == {}
    assert result.blocked == {}


def test_independent_nodes_run_concurrently_and_results_follow_plan_order():
    both_started = threading.Barrier(2, timeout=2)

    def callback(node):
        both_started.wait()
        return node.action.upper()

    nodes = [
        Node("second", frozenset(), 1, "second"),
        Node("first", frozenset(), 0, "first"),
    ]
    result = execute_dag(nodes, callback, max_workers=2)

    assert list(result.values) == ["first", "second"]
    assert result.values == {"first": "FIRST", "second": "SECOND"}


def test_resolution_observer_keeps_completion_order_when_wait_returns_multiple_done(
        monkeypatch):
    executor = importlib.import_module("mdxcanvas.deploy.executor")
    second_finished = threading.Event()
    original_wait = executor.wait

    def callback(node):
        if node.key == "first":
            assert second_finished.wait(timeout=2)
        else:
            second_finished.set()
        return node.key

    def wait_until_all_are_done(futures, **kwargs):
        done, not_done = original_wait(futures, **kwargs)
        if len(done) < len(futures):
            done, not_done = original_wait(futures)
        return done, not_done

    monkeypatch.setattr(executor, "wait", wait_until_all_are_done)
    resolved = []
    nodes = [
        Node("first", frozenset(), 0, "first"),
        Node("second", frozenset(), 1, "second"),
    ]

    result = execute_dag(
        nodes, callback, max_workers=2,
        on_resolved=lambda node, status, _value: resolved.append((node.key, status)),
    )

    assert resolved == [("second", "success"), ("first", "success")]
    assert list(result.values) == ["first", "second"]


def test_dependent_starts_only_after_predecessor_callback_bookkeeping_finishes():
    bookkeeping_finished = threading.Event()

    def callback(node):
        if node.key == "parent":
            bookkeeping_finished.set()
        else:
            assert bookkeeping_finished.is_set()
        return node.key

    nodes = [
        Node("child", frozenset({"parent"}), 1, "child"),
        Node("parent", frozenset(), 0, "parent"),
    ]

    result = execute_dag(nodes, callback, max_workers=2)

    assert list(result.values) == ["parent", "child"]


def test_failure_blocks_descendants_but_unrelated_work_settles():
    calls = []

    def callback(node):
        calls.append(node.key)
        if node.key == "failed":
            raise RuntimeError("boom")
        return node.key

    nodes = [
        Node("failed", frozenset(), 0, "failed"),
        Node("blocked", frozenset({"failed"}), 1, "blocked"),
        Node("unrelated", frozenset(), 2, "unrelated"),
    ]
    result = execute_dag(nodes, callback, max_workers=2)

    assert "blocked" not in calls
    assert "unrelated" in calls
    assert isinstance(result.failures["failed"], RuntimeError)
    assert type(result.blocked["blocked"]).__name__ == "DependencyFailed"
    assert list(result.failures) == ["failed"]
    assert list(result.blocked) == ["blocked"]


def test_resolution_observer_reports_each_success_failure_and_block_once():
    release_success = threading.Event()
    failed = threading.Event()
    calls = []
    resolved = []

    def callback(node):
        calls.append(node.key)
        if node.key == "failed":
            failed.set()
            raise RuntimeError("boom")
        if node.key == "success":
            assert failed.wait(timeout=2)
            release_success.wait(timeout=2)
        return node.key.upper()

    def on_resolved(node, status, value):
        resolved.append((node.key, status, value))
        if node.key == "blocked":
            release_success.set()

    nodes = [
        Node("failed", frozenset(), 0, "failed"),
        Node("blocked", frozenset({"failed"}), 1, "blocked"),
        Node("success", frozenset(), 2, "success"),
    ]
    result = execute_dag(nodes, callback, max_workers=2, on_resolved=on_resolved)

    assert calls.count("failed") == 1
    assert calls.count("success") == 1
    assert "blocked" not in calls
    assert [(key, status) for key, status, _value in resolved] == [
        ("failed", "failed"),
        ("blocked", "blocked"),
        ("success", "success"),
    ]
    assert isinstance(resolved[0][2], RuntimeError)
    assert type(resolved[1][2]).__name__ == "DependencyFailed"
    assert resolved[2][2] == "SUCCESS"
    assert list(result.values) == ["success"]
    assert list(result.failures) == ["failed"]
    assert list(result.blocked) == ["blocked"]


def test_unexpected_coordinator_fault_waits_for_running_callbacks(monkeypatch):
    executor = importlib.import_module("mdxcanvas.deploy.executor")
    callback_started = threading.Event()
    release_callback = threading.Event()
    callback_finished = threading.Event()
    coordinator_faulted = threading.Event()
    raised = []

    def callback(_node):
        callback_started.set()
        release_callback.wait(timeout=2)
        callback_finished.set()

    def fail_wait(*_args, **_kwargs):
        assert callback_started.wait(timeout=2)
        coordinator_faulted.set()
        raise RuntimeError("coordinator fault")

    monkeypatch.setattr(executor, "wait", fail_wait)

    def run():
        try:
            executor.execute_dag([Node("node", frozenset(), 0, "node")], callback)
        except Exception as error:
            raised.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    assert coordinator_faulted.wait(timeout=2)
    assert thread.is_alive()
    assert not callback_finished.is_set()

    release_callback.set()
    thread.join(timeout=2)

    assert callback_finished.is_set()
    assert not thread.is_alive()
    assert len(raised) == 1
    assert str(raised[0]) == "coordinator fault"


def test_keyboard_interrupt_waits_for_running_callbacks(monkeypatch):
    executor = importlib.import_module("mdxcanvas.deploy.executor")
    callback_started = threading.Event()
    release_callback = threading.Event()
    callback_finished = threading.Event()
    coordinator_interrupted = threading.Event()
    interrupt = KeyboardInterrupt()
    raised = []

    def callback(_node):
        callback_started.set()
        release_callback.wait(timeout=2)
        callback_finished.set()

    def interrupt_wait(*_args, **_kwargs):
        assert callback_started.wait(timeout=2)
        coordinator_interrupted.set()
        raise interrupt

    monkeypatch.setattr(executor, "wait", interrupt_wait)

    def run():
        try:
            executor.execute_dag([Node("node", frozenset(), 0, "node")], callback)
        except BaseException as error:
            raised.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    assert coordinator_interrupted.wait(timeout=2)
    assert thread.is_alive()
    assert not callback_finished.is_set()

    release_callback.set()
    thread.join(timeout=2)

    assert callback_finished.is_set()
    assert not thread.is_alive()
    assert raised == [interrupt]


def test_rate_limit_retry_succeeds_and_exhaustion_raises(monkeypatch):
    monkeypatch.setattr("mdxcanvas.deploy.executor.time.sleep", lambda _seconds: None)
    calls = []

    def eventually_succeeds():
        calls.append("call")
        if len(calls) == 1:
            raise RateLimitExceeded("limited")
        return "done"

    assert retry_rate_limit(eventually_succeeds, max_retries=2, cooldown_seconds=0) == "done"
    assert len(calls) == 2

    failures = []

    def always_fails():
        failures.append("call")
        raise RateLimitExceeded("limited")

    with pytest.raises(RateLimitExceeded):
        retry_rate_limit(always_fails, max_retries=2, cooldown_seconds=0)
    assert len(failures) == 3


@pytest.mark.parametrize(
    "nodes",
    [
        [Node("same", frozenset(), 0, "a"), Node("same", frozenset(), 1, "b")],
        [Node("child", frozenset({"missing"}), 0, "child")],
        [Node("self", frozenset({"self"}), 0, "self")],
        [
            Node("a", frozenset({"b"}), 0, "a"),
            Node("b", frozenset({"a"}), 1, "b"),
        ],
    ],
)
def test_invalid_graph_is_rejected_before_any_work(nodes):
    calls = []

    with pytest.raises(ValueError):
        execute_dag(nodes, lambda node: calls.append(node.key))

    assert calls == []
