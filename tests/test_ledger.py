import copy
import importlib
from types import SimpleNamespace

import pytest

import mdxcanvas


CURRENT_VERSION = mdxcanvas.__version__


def migrate_ledger(envelope):
    migration = importlib.import_module("mdxcanvas.deploy.migration")
    return getattr(migration, "migrate_ledger")(envelope)


def canonical(resources=None, **extra):
    return {
        "mdxcanvas_version": CURRENT_VERSION,
        "resources": resources or {},
        **extra,
    }


def entry(canvas_id="1", checksum="sum", **canvas_fields):
    return {
        "checksum": checksum,
        "canvas_info": {"id": canvas_id, **canvas_fields},
    }


def test_07_migration_is_pure_deterministic_and_preserves_split_once_keys():
    loaded = {
        "mdxcanvas_version": "0.7.10",
        "resources": {
            "module_item|module|item": entry(module_id=20),
            "quiz_question_order|quiz|order": entry(quiz_id="30"),
            "course_settings|": entry(),
            "quiz_question|question": entry(quiz_id=30),
            "override|override": entry(assignment_id=40),
        },
        "future_metadata": {"keep": [1, 2]},
    }
    original = copy.deepcopy(loaded)

    first, changed = migrate_ledger(loaded)
    second, second_changed = migrate_ledger(first)

    assert loaded == original
    assert changed is True
    assert second_changed is False
    assert second == first
    assert first["mdxcanvas_version"] == CURRENT_VERSION
    assert list(first["resources"]) == list(loaded["resources"])
    assert first["future_metadata"] == loaded["future_metadata"]
    assert first["resources"]["module_item|module|item"]["canvas_info"] == {
        "id": "1",
        "parent": {"type": "module", "id": "20"},
    }
    assert first["resources"]["quiz_question|question"]["canvas_info"]["parent"] == {
        "type": "quiz",
        "id": "30",
    }
    assert first["resources"]["override|override"]["canvas_info"]["parent"] == {
        "type": "assignment",
        "id": "40",
    }


def test_07_migration_normalizes_existing_canonical_parent_id_to_string():
    loaded = {
        "mdxcanvas_version": "0.7.10",
        "resources": {
            "module_item|item": entry(parent={"type": "module", "id": 20}),
            "quiz_question|question": entry(parent={"type": "quiz", "id": 30}),
            "override|override": entry(parent={"type": "assignment", "id": 40}),
        },
    }

    migrated, changed = migrate_ledger(loaded)

    assert changed is True
    assert [
        value["canvas_info"]["parent"]["id"]
        for value in migrated["resources"].values()
    ] == ["20", "30", "40"]


def test_canonical_08_is_validated_without_mutating_input():
    loaded = canonical({
        "module_item|module|item": entry(parent={"type": "module", "id": "20"}),
        "quiz_question_order|quiz|order": entry(quiz_id="30"),
        "course_settings|": entry(),
    })
    original = copy.deepcopy(loaded)

    migrated, changed = migrate_ledger(loaded)

    assert changed is False
    assert migrated == original
    assert migrated is not loaded
    assert migrated["resources"] is not loaded["resources"]


@pytest.mark.parametrize("loaded_version", ["0.8.0", "0.8.3"])
def test_older_canonical_08_is_validated_and_advanced_without_rewriting_data(
        monkeypatch, loaded_version):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    loaded = {
        "mdxcanvas_version": loaded_version,
        "resources": {
            "page|welcome": entry(canvas_id="10"),
            "module_item|module|item": entry(
                canvas_id="20", parent={"type": "module", "id": "2"},
            ),
            "quiz_question_order|quiz|order": entry(canvas_id="30", quiz_id="3"),
            "course_settings|": entry(canvas_id="course"),
        },
        "future_metadata": {"keep": [1, 2]},
    }
    original = copy.deepcopy(loaded)

    migrated, changed = migrate_ledger(loaded)

    assert loaded == original
    assert changed is True
    assert migrated["mdxcanvas_version"] == mdxcanvas.__version__
    assert migrated["resources"] == original["resources"]
    assert migrated["future_metadata"] == original["future_metadata"]


def test_older_canonical_08_is_validated_before_version_advancement(monkeypatch):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")

    with pytest.raises(ValueError, match="resources must be a mapping"):
        migrate_ledger({"mdxcanvas_version": "0.8.0", "resources": []})


@pytest.mark.parametrize("recorded_version", ["0.8.8", "0.9.0", "1.0.0"])
def test_newer_ledger_requires_upgrade_before_schema_validation(monkeypatch, recorded_version):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")

    with pytest.raises(ValueError) as raised:
        migrate_ledger({
            "mdxcanvas_version": recorded_version,
            "resources": "shape-known-only-to-newer-mdxcanvas",
        })

    message = str(raised.value)
    assert recorded_version in message
    assert mdxcanvas.__version__ in message
    assert "upgrade" in message.lower()
    assert f"at least {recorded_version}" in message


def test_newer_version_gate_does_not_copy_or_inspect_future_resource_schema(monkeypatch):
    class ExplodingFutureSchema:
        def __deepcopy__(self, _memo):
            raise AssertionError("future resource schema was copied")

    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")

    with pytest.raises(ValueError, match="newer than running"):
        migrate_ledger({
            "mdxcanvas_version": "0.9.0",
            "resources": ExplodingFutureSchema(),
        })


def test_malformed_version_fails_before_copying_resource_payload():
    class ExplodingFutureSchema:
        def __deepcopy__(self, _memo):
            raise AssertionError("resource payload was copied")

    with pytest.raises(ValueError, match="Malformed ledger version"):
        migrate_ledger({
            "mdxcanvas_version": "future",
            "resources": ExplodingFutureSchema(),
        })


@pytest.mark.parametrize(
    "loaded",
    [
        [],
        {},
        {"page|p": entry()},
        {"mdxcanvas_version": "not-a-version", "resources": {}},
        {"mdxcanvas_version": "0.6.15", "resources": {}},
        {"mdxcanvas_version": "0.8.0", "resources": []},
        canonical({"missing-separator": entry()}),
        canonical({"|empty-type": entry()}),
        canonical({"page|": entry()}),
        canonical({"unknown|id": entry()}),
        canonical({"page|id": []}),
        canonical({"page|id": {"checksum": "sum", "canvas_info": []}}),
        canonical({"page|id": {"checksum": 123, "canvas_info": {"id": "1"}}}),
        canonical({"page|id": {"checksum": "sum", "canvas_info": {"id": {}}}}),
        canonical({"module_item|id": entry()}),
        canonical({"quiz_question|id": entry(parent={"type": "module", "id": "2"})}),
    ],
)
def test_unsupported_or_malformed_supported_ledgers_are_rejected(loaded):
    with pytest.raises((TypeError, ValueError)):
        migrate_ledger(loaded)


def test_identity_without_checksum_is_valid_canonical_state():
    migrated, changed = migrate_ledger(canonical({
        "page|page": {"canvas_info": {"id": "10"}},
    }))

    assert changed is False
    assert migrated["resources"]["page|page"] == {"canvas_info": {"id": "10"}}


def test_missing_ledger_uses_official_version_at_load_time(monkeypatch, tmp_path):
    checksums = importlib.import_module("mdxcanvas.deploy.checksums")
    writes = []
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    monkeypatch.setattr(checksums, "get_file", lambda *_args: None)
    monkeypatch.setattr(checksums, "deploy_file", lambda *_args, **_kwargs: writes.append(True))

    envelope = checksums.MD5Sums(SimpleNamespace(), tmp_path).load()

    assert envelope == {"mdxcanvas_version": mdxcanvas.__version__, "resources": {}}
    assert writes == []


def test_official_version_is_current_and_validated_at_migration_time(monkeypatch):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    loaded = {
        "mdxcanvas_version": mdxcanvas.__version__,
        "resources": {"page|page": entry()},
    }

    migrated, changed = migrate_ledger(loaded)

    assert changed is False
    assert migrated == loaded
    assert migrated is not loaded
    with pytest.raises(ValueError):
        migrate_ledger({
            "mdxcanvas_version": mdxcanvas.__version__,
            "resources": [],
        })


def test_07_migration_advances_to_official_version_at_call_time(monkeypatch):
    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    loaded = {
        "mdxcanvas_version": "0.7.10",
        "resources": {
            "module_item|item": entry(module_id=20),
            "quiz_question|question": entry(quiz_id=30),
            "override|override": entry(assignment_id=40),
        },
    }

    migrated, changed = migrate_ledger(loaded)

    assert changed is True
    assert migrated["mdxcanvas_version"] == mdxcanvas.__version__
    assert [
        value["canvas_info"]["parent"]
        for value in migrated["resources"].values()
    ] == [
        {"type": "module", "id": "20"},
        {"type": "quiz", "id": "30"},
        {"type": "assignment", "id": "40"},
    ]


def test_migrated_official_version_is_persisted_with_raw_keys(monkeypatch, tmp_path):
    checksums = importlib.import_module("mdxcanvas.deploy.checksums")
    uploads = []

    class FixedTemporaryDirectory:
        def __enter__(self):
            return str(tmp_path)

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(mdxcanvas, "__version__", "0.8.7")
    monkeypatch.setattr(checksums, "TemporaryDirectory", FixedTemporaryDirectory)
    monkeypatch.setattr(checksums, "deploy_file", lambda _course, data, _root: uploads.append(data))
    migrated, changed = migrate_ledger({
        "mdxcanvas_version": "0.7.10",
        "resources": {
            "module_item|module|item": entry(module_id=20),
            "course_settings|": entry(),
        },
    })

    checksums.MD5Sums(SimpleNamespace(), tmp_path).save(migrated)

    saved = __import__("json").loads((tmp_path / "_md5sums.json").read_text())
    assert changed is True
    assert len(uploads) == 1
    assert saved["mdxcanvas_version"] == mdxcanvas.__version__
    assert list(saved["resources"]) == ["module_item|module|item", "course_settings|"]


def test_ledger_load_is_read_only_and_missing_file_initializes_canonical_state(monkeypatch, tmp_path):
    checksums = importlib.import_module("mdxcanvas.deploy.checksums")
    writes = []
    monkeypatch.setattr(checksums, "get_file", lambda *_args: None)
    monkeypatch.setattr(checksums, "deploy_file", lambda *_args, **_kwargs: writes.append(True))

    store = checksums.MD5Sums(SimpleNamespace(), tmp_path)
    envelope = store.load()

    assert envelope == canonical()
    assert writes == []


def test_ledger_save_is_explicit_and_preserves_raw_resource_keys(monkeypatch, tmp_path):
    checksums = importlib.import_module("mdxcanvas.deploy.checksums")
    uploads = []

    class FixedTemporaryDirectory:
        def __enter__(self):
            return str(tmp_path)

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(checksums, "TemporaryDirectory", FixedTemporaryDirectory)
    monkeypatch.setattr(checksums, "deploy_file", lambda _course, data, _root: uploads.append(data))
    store = checksums.MD5Sums(SimpleNamespace(), tmp_path)
    envelope = canonical({
        "module_item|module|item": entry(parent={"type": "module", "id": "20"}),
        "quiz_question_order|quiz|order": entry(quiz_id="30"),
        "course_settings|": entry(),
    })

    store.save(envelope)

    assert len(uploads) == 1
    assert uploads[0]["canvas_folder"] == "_md5s"
    saved = __import__("json").loads((tmp_path / "_md5sums.json").read_text())
    assert list(saved["resources"]) == list(envelope["resources"])
    assert saved == envelope
