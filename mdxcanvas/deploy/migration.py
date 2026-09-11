from copy import deepcopy
from collections.abc import Mapping

import mdxcanvas

CANONICAL_LEDGER_FAMILY = (0, 8)
KNOWN_TYPES = {
    "announcement", "assignment", "assignment_group", "course_settings", "file", "mermaid",
    "module", "module_item", "navigation", "override", "page", "quarto-slides", "quiz",
    "quiz_question", "quiz_question_order", "syllabus", "zip",
}
PARENTS = {
    "module_item": ("module_id", "module"),
    "quiz_question": ("quiz_id", "quiz"),
    "override": ("assignment_id", "assignment"),
}


class LedgerError(ValueError):
    pass


def _version(value) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise LedgerError("Ledger has no valid mdxcanvas_version")
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise LedgerError(f"Malformed ledger version: {value!r}")
    return tuple(map(int, parts))  # type: ignore[return-value]


def _validate(envelope: Mapping):
    resources = envelope.get("resources")
    if not isinstance(resources, Mapping):
        raise LedgerError("Ledger resources must be a mapping")
    for raw_key, entry in resources.items():
        if not isinstance(raw_key, str) or "|" not in raw_key:
            raise LedgerError(f"Malformed ledger resource key: {raw_key!r}")
        resource_type, resource_id = raw_key.split("|", 1)
        if resource_type not in KNOWN_TYPES:
            raise LedgerError(f"Unsupported ledger resource type: {resource_type!r}")
        if not resource_id and resource_type != "course_settings":
            raise LedgerError(f"Empty ledger resource id for {resource_type}")
        if not isinstance(entry, Mapping):
            raise LedgerError(f"Ledger entry {raw_key!r} must be a mapping")
        checksum = entry.get("checksum")
        if checksum is not None and not isinstance(checksum, str):
            raise LedgerError(f"Ledger checksum for {raw_key!r} must be a string")
        canvas_info = entry.get("canvas_info")
        if not isinstance(canvas_info, Mapping):
            raise LedgerError(f"Ledger canvas_info for {raw_key!r} must be a mapping")
        canvas_id = canvas_info.get("id")
        if isinstance(canvas_id, bool) or not isinstance(canvas_id, (str, int, float)) or str(canvas_id) == "":
            raise LedgerError(f"Ledger canvas_info for {raw_key!r} has no usable id")
        if resource_type in PARENTS:
            parent = canvas_info.get("parent")
            expected = PARENTS[resource_type][1]
            if not isinstance(parent, Mapping) or parent.get("type") != expected or not isinstance(parent.get("id"), str) or not parent["id"]:
                raise LedgerError(f"Ledger canvas_info for {raw_key!r} has invalid parent metadata")


def migrate_ledger(loaded) -> tuple[dict, bool]:
    if not isinstance(loaded, Mapping):
        raise LedgerError("Ledger must be a mapping")
    version = _version(loaded.get("mdxcanvas_version"))
    current_version = _version(mdxcanvas.__version__)
    if version > current_version:
        recorded_version = loaded.get("mdxcanvas_version")
        raise LedgerError(
            f"Ledger version {recorded_version} is newer than running MDXCanvas "
            f"{mdxcanvas.__version__}; upgrade MDXCanvas to at least {recorded_version}."
        )

    migrated = deepcopy(dict(loaded))
    if version[:2] == current_version[:2] == CANONICAL_LEDGER_FAMILY:
        _validate(migrated)
        changed = version != current_version
        if changed:
            migrated["mdxcanvas_version"] = mdxcanvas.__version__
        return migrated, changed

    if version[:2] != (0, 7):
        raise LedgerError(f"Unsupported historical ledger version: {loaded.get('mdxcanvas_version')}")

    resources = migrated.get("resources")
    if not isinstance(resources, Mapping):
        raise LedgerError("Ledger resources must be a mapping")
    for raw_key, entry in resources.items():
        if not isinstance(raw_key, str) or "|" not in raw_key:
            continue
        resource_type = raw_key.split("|", 1)[0]
        if resource_type not in PARENTS:
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("canvas_info"), dict):
            continue
        info = entry["canvas_info"]
        legacy_field, parent_type = PARENTS[resource_type]
        if "parent" not in info:
            if legacy_field not in info or info[legacy_field] in (None, ""):
                raise LedgerError(f"Missing parent metadata for {raw_key}")
            info["parent"] = {"type": parent_type, "id": str(info.pop(legacy_field))}
        else:
            parent = info["parent"]
            if isinstance(parent, dict) and parent.get("id") not in (None, ""):
                parent["id"] = str(parent["id"])
            info.pop(legacy_field, None)
    migrated["mdxcanvas_version"] = mdxcanvas.__version__
    _validate(migrated)
    return migrated, True
