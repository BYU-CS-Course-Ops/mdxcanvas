from copy import deepcopy
from pathlib import Path

import pytest

import mdxcanvas
from mdxcanvas.deploy.actions import DeploymentResult, HandlerSpec
from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deployment_report import DeploymentReport
from mdxcanvas.resources import CanvasResource, get_key


class Store:
    def __init__(self, resources: dict):
        self.value = {"mdxcanvas_version": mdxcanvas.__version__, "resources": resources}

    def load(self) -> dict:
        return deepcopy(self.value)

    def save(self, value: dict):
        self.value = deepcopy(value)


def page(key: str, dependencies: list[str]) -> CanvasResource:
    return CanvasResource(
        type="page", id=key, content_path="course.md",
        data={"title": f"New {key}", "body": " ".join(
            f'{get_key("page", dependency, "title")}:{get_key("page", dependency, "uri")}'
            for dependency in dependencies
        )},
    )


@pytest.mark.parametrize("existing, failure", [
    (existing, failure)
    for existing in [(), ("a",), ("a", "b", "c")]
    for failure in [None, "create", "first", "refresh"]
    if not (failure == "create" and len(existing) == 3)
    and not (failure == "first" and not existing)
])
def test_cycle_refreshes_links_and_recovers_partial_deployment(
        monkeypatch, tmp_path: Path, existing: tuple[str, ...], failure: str | None):
    resources = {
        ("page", "root"): page("root", []),
        ("page", "a"): page("a", ["b", "c", "root"]),
        ("page", "b"): page("b", ["a"]),
        ("page", "c"): page("c", ["a"]),
        ("page", "observer"): page("observer", ["a", "b", "c"]),
    }
    ledger = {}
    remote = {}
    for key in (*existing, "root", "observer"):
        remote[key] = {"title": f"Old {key}", "body": "Old links"}
        ledger[f"page|{key}"] = {
            "checksum": "old", "dependencies": [],
            "canvas_info": {"id": key, "title": f"Old {key}", "uri": f"/old/{key}"},
        }
    store = Store(ledger)
    calls: list[tuple[str, str]] = []
    update_counts: dict[str, int] = {}
    failed = False

    def result(key: str) -> DeploymentResult:
        return DeploymentResult({
            "id": key, "title": remote[key]["title"], "uri": f"/new/{key}",
        })

    def create(_context, resource: CanvasResource) -> DeploymentResult:
        nonlocal failed
        key = resource["id"]
        assert key not in remote, "Retry must reuse previously created identities"
        if failure == "create" and not failed:
            failed = True
            raise RuntimeError("Shell failed")
        remote[key] = deepcopy(resource["data"])
        calls.append(("create", key))
        return result(key)

    def update(_context, resource: CanvasResource, info: dict) -> DeploymentResult:
        nonlocal failed
        key = resource["id"]
        assert info["id"] == key
        update_counts[key] = update_counts.get(key, 0) + 1
        if key in {"a", "b", "c"}:
            # Both external prerequisites and newly created identities must be available.
            if key == "a":
                assert remote["root"]["title"] == "New root"
            assert all(member in remote for member in ["a", "b", "c"])
            target_count = 1 if key not in existing else 2
            should_fail = (
                failure == "first" and key in existing and update_counts[key] == 1
            ) or (failure == "refresh" and update_counts[key] == target_count)
            if should_fail and not failed:
                failed = True
                raise RuntimeError("Update failed")
        if key == "observer":
            for member, dependencies in [("a", ["b", "c", "root"]), ("b", ["a"]), ("c", ["a"])]:
                assert remote[member]["body"] == " ".join(f"New {dep}:/new/{dep}" for dep in dependencies)
        remote[key] = deepcopy(resource["data"])
        calls.append(("update", key))
        return result(key)

    def shell(resource: CanvasResource) -> CanvasResource:
        copied = deepcopy(resource)
        copied["data"]["body"] = ""
        return copied

    handlers = {"page": HandlerSpec(create, update, lambda *_args: True, prepare_cycle_breaker=shell)}
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.build_builtin_handlers", lambda: handlers)
    original = deepcopy(resources)
    report = deploy_to_canvas(object(), "UTC", resources, DeploymentReport(), tmp_path)
    assert resources == original

    if failed:
        assert report.report["deployment"]["errors"]
        for key in ["a", "b", "c"]:
            entry = store.value["resources"].get(f"page|{key}")
            if entry:
                assert entry["checksum"] is None
        assert ("update", "observer") not in calls
        report = deploy_to_canvas(object(), "UTC", resources, DeploymentReport(), tmp_path)

    assert not report.report["deployment"]["errors"]
    for (rtype, key), resource in resources.items():
        assert store.value["resources"][f"{rtype}|{key}"]["checksum"] == compute_md5(resource["data"], tmp_path)
    assert sum(operation == "create" for operation, _key in calls) == 3 - len(existing)
    calls.clear()
    report = deploy_to_canvas(object(), "UTC", resources, DeploymentReport(), tmp_path)
    assert not report.report["deployment"]["errors"]
    assert not calls


@pytest.mark.parametrize("cyclic", [False, True])
def test_rename_refreshes_unchanged_linking_pages_without_opt_in(monkeypatch, tmp_path, cyclic):
    resources = {
        ("page", "target"): page("target", ["linker"] if cyclic else []),
        ("page", "linker"): page("linker", ["target"]),
    }
    ledger = {
        f"page|{key}": {
            "checksum": compute_md5(value["data"], tmp_path),
            "canvas_info": {"id": key, "title": f"New {key}", "uri": f"/old/{key}"},
        }
        for (_rtype, key), value in resources.items()
    }
    store = Store(ledger)
    resources[("page", "target")]["data"]["title"] = "Renamed"
    deployed = {}
    calls = []

    def update(_context, value: CanvasResource, info: dict) -> DeploymentResult:
        key = value["id"]
        assert info["id"] == key
        deployed[key] = deepcopy(value["data"])
        calls.append(key)
        return DeploymentResult({"id": key, "title": value["data"]["title"], "uri": f"/new/{key}"})

    def unexpected_create(*_args):
        pytest.fail("An existing page must update in place")

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.build_builtin_handlers", lambda: {
        "page": HandlerSpec(unexpected_create, update, lambda *_args: True),
    })
    report = deploy_to_canvas(object(), "UTC", resources, DeploymentReport(), tmp_path)

    assert not report.report["deployment"]["errors"]
    assert deployed["linker"]["body"] == "Renamed:/new/target"
    if cyclic:
        assert deployed["target"]["body"] == "New linker:/new/linker"
        assert calls.count("target") == calls.count("linker") == 2
    else:
        assert calls == ["target", "linker"]


@pytest.mark.parametrize("existing", [False, True])
def test_self_reference_is_refreshed(monkeypatch, tmp_path, existing):
    resource = page("self", ["self"])
    ledger = {"page|self": {
        "checksum": "old", "canvas_info": {"id": "self", "title": "Old", "uri": "/old/self"},
    }} if existing else {}
    store = Store(ledger)
    bodies = []

    def apply(_context, value: CanvasResource, _info=None) -> DeploymentResult:
        bodies.append(value["data"]["body"])
        return DeploymentResult({"id": "self", "title": "New self", "uri": "/new/self"})

    def shell(value: CanvasResource) -> CanvasResource:
        copied = deepcopy(value)
        copied["data"]["body"] = ""
        return copied

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: store)
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.build_builtin_handlers", lambda: {
        "page": HandlerSpec(apply, apply, lambda *_args: True, prepare_cycle_breaker=None if existing else shell),
    })
    report = deploy_to_canvas(object(), "UTC", {("page", "self"): resource}, DeploymentReport(), tmp_path)

    assert not report.report["deployment"]["errors"]
    assert bodies == (["Old:/old/self", "New self:/new/self"] if existing else ["", "New self:/new/self"])
