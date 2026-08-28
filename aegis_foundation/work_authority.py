"""Normalize current bead authority and legacy Taskmaster work records.

Gas City beads are the current task authority.  Taskmaster remains a supported
read-only input for repositories whose historical Aegis evidence still uses it.
The adapter never shells out, mutates either system, or infers a bead database;
callers provide an explicit, frozen bead JSON/JSONL snapshot when beads apply.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

SCHEMA_VERSION = "1"
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
BEAD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*-[a-z0-9][a-z0-9-]*(?:\.[1-9][0-9]*)*$")
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(?:authorization|credential|password|passwd|secret|token|api[_-]?key)"
)
SAFE_METADATA_PREFIXES = ("aegis.", "gc.", "prd.")


class WorkAuthorityError(RuntimeError):
    """Raised when work authority cannot be read without ambiguity."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: Any, *, limit: int) -> str:
    result = " ".join(str(value or "").split())
    return result[:limit]


def _natural_id_key(value: str) -> tuple[Any, ...]:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"[.-]", value))


def _normalize_task_id(value: Any, parent_id: str | None = None) -> str:
    raw = str(value or "").strip()
    if parent_id and raw and "." not in raw:
        return f"{parent_id}.{raw}"
    return raw


def _taskmaster_items(root: Path, *, max_items: int) -> tuple[list[dict[str, Any]], str]:
    path = root / ".taskmaster" / "tasks" / "tasks.json"
    if not path.is_file():
        return [], ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkAuthorityError(
            f"invalid Taskmaster source {path.relative_to(root)}: {exc}"
        ) from exc
    if isinstance(payload, Mapping) and isinstance(payload.get("master"), Mapping):
        raw_tasks = payload["master"].get("tasks", [])
    elif isinstance(payload, Mapping):
        raw_tasks = payload.get("tasks", [])
    else:
        raw_tasks = []
    records: list[dict[str, Any]] = []

    def visit(task: Any, parent_id: str | None = None) -> None:
        if not isinstance(task, Mapping):
            return
        task_id = _normalize_task_id(task.get("id"), parent_id)
        if not task_id:
            return
        raw_dependencies = task.get("dependencies")
        dependencies = raw_dependencies if isinstance(raw_dependencies, list) else []
        normalized_dependencies = sorted(
            {_normalize_task_id(item, parent_id) for item in dependencies if str(item).strip()},
            key=_natural_id_key,
        )
        records.append(
            {
                "id": task_id,
                "authority": "taskmaster",
                "kind": "task",
                "issue_type": "subtask" if parent_id else "task",
                "parent_id": parent_id,
                "title": _text(task.get("title"), limit=240),
                "status": _text(task.get("status"), limit=40) or "unknown",
                "priority": _text(task.get("priority"), limit=40) or "unknown",
                "assignee": "",
                "updated_at": "",
                "dependencies": [
                    {"id": dependency, "type": "blocks"} for dependency in normalized_dependencies
                ],
                "description": _text(task.get("description"), limit=2_000),
                "labels": [],
                "metadata": {},
                "content_included": True,
            }
        )
        for child in task.get("subtasks", []) if isinstance(task.get("subtasks"), list) else []:
            visit(child, task_id)

    for raw_task in raw_tasks if isinstance(raw_tasks, list) else []:
        visit(raw_task)
    if len(records) > max_items:
        raise WorkAuthorityError(
            f"Taskmaster projection exceeds task limit ({len(records)} > {max_items})"
        )
    records.sort(key=lambda item: _natural_id_key(item["id"]))
    return records, hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_json(content: str, *, label: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise WorkAuthorityError(f"duplicate JSON key in {label}: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise WorkAuthorityError(f"non-finite JSON number in {label}: {value}")

    try:
        return json.loads(
            content,
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except WorkAuthorityError:
        raise
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise WorkAuthorityError(f"invalid {label}: {exc}") from exc


def _bead_payload(path: Path) -> list[Mapping[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise WorkAuthorityError(f"bead snapshot must be a regular non-symlink file: {path}")
    size = path.stat().st_size
    if size > MAX_SNAPSHOT_BYTES:
        raise WorkAuthorityError(
            f"bead snapshot exceeds size limit ({size} > {MAX_SNAPSHOT_BYTES})"
        )
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise WorkAuthorityError(f"unable to read bead snapshot {path}: {exc}") from exc
    stripped = content.lstrip()
    if not stripped:
        return []
    payload: Any | None = None
    if stripped.startswith("["):
        payload = _strict_json(content, label=f"bead snapshot {path}")
    elif stripped.startswith("{"):
        try:
            payload = _strict_json(content, label=f"bead snapshot {path}")
        except WorkAuthorityError as exc:
            if "Extra data" not in str(exc):
                raise
    if payload is not None:
        if isinstance(payload, Mapping):
            for key in ("beads", "issues", "records"):
                if isinstance(payload.get(key), list):
                    payload = payload[key]
                    break
            else:
                # A one-record JSONL export is also a valid single JSON object.
                payload = [payload]
        if not isinstance(payload, list):
            raise WorkAuthorityError(
                "bead snapshot must be an array or contain beads/issues/records"
            )
        records = payload
    else:
        records = [
            _strict_json(line, label=f"bead snapshot {path} line {line_number}")
            for line_number, line in enumerate(content.splitlines(), 1)
            if line.strip()
        ]
    if not all(isinstance(record, Mapping) for record in records):
        raise WorkAuthorityError("every bead snapshot record must be an object")
    return list(records)


def _priority(value: Any) -> str:
    if isinstance(value, int) and 0 <= value <= 4:
        return f"P{value}"
    text = _text(value, limit=20)
    if re.fullmatch(r"[Pp]?[0-4]", text):
        return "P" + text[-1]
    return text or "unknown"


def _safe_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, Any] = {}
    for raw_key, raw_value in sorted(value.items(), key=lambda item: str(item[0])):
        key = str(raw_key)
        if not key.startswith(SAFE_METADATA_PREFIXES) or SENSITIVE_KEY_PATTERN.search(key):
            continue
        if isinstance(raw_value, (str, int, float, bool)) or raw_value is None:
            result[key] = _text(raw_value, limit=500) if isinstance(raw_value, str) else raw_value
    return result


def _dependencies(value: Any, *, bead_id: str) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise WorkAuthorityError(f"bead {bead_id} dependencies must be an array")
    result: set[tuple[str, str]] = set()
    for raw in value:
        if not isinstance(raw, Mapping):
            raise WorkAuthorityError(f"bead {bead_id} dependency must be an object")
        target = str(raw.get("depends_on_id", raw.get("id", ""))).strip()
        relationship = str(raw.get("type", raw.get("dependency_type", "blocks"))).strip()
        if not BEAD_ID_PATTERN.fullmatch(target):
            raise WorkAuthorityError(f"bead {bead_id} has unsafe dependency id {target!r}")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", relationship):
            raise WorkAuthorityError(f"bead {bead_id} has unsafe dependency type {relationship!r}")
        result.add((relationship, target))
    return [{"id": target, "type": relationship} for relationship, target in sorted(result)]


def _bead_items(
    path: Path,
    *,
    include_content: bool,
    max_items: int,
) -> tuple[list[dict[str, Any]], str]:
    raw_records = _bead_payload(path)
    if len(raw_records) > max_items:
        raise WorkAuthorityError(
            f"bead projection exceeds work-item limit ({len(raw_records)} > {max_items})"
        )
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_records:
        if raw.get("_type") not in (None, "issue"):
            continue
        bead_id = str(raw.get("id") or "").strip()
        if not BEAD_ID_PATTERN.fullmatch(bead_id):
            raise WorkAuthorityError(f"unsafe bead id: {bead_id!r}")
        if bead_id in seen:
            raise WorkAuthorityError(f"duplicate bead id: {bead_id}")
        seen.add(bead_id)
        parent_id = str(raw.get("parent_id") or "").strip() or None
        if parent_id is not None and not BEAD_ID_PATTERN.fullmatch(parent_id):
            raise WorkAuthorityError(f"bead {bead_id} has unsafe parent id {parent_id!r}")
        labels = raw.get("labels")
        if labels is None:
            normalized_labels: list[str] = []
        elif isinstance(labels, list) and all(isinstance(label, str) for label in labels):
            normalized_labels = sorted(
                {_text(label, limit=100) for label in labels if label.strip()}
            )
        else:
            raise WorkAuthorityError(f"bead {bead_id} labels must be an array of strings")
        title = _text(raw.get("title"), limit=240) if include_content else ""
        description = _text(raw.get("description"), limit=2_000) if include_content else ""
        records.append(
            {
                "id": bead_id,
                "authority": "beads",
                "kind": "bead",
                "issue_type": _text(raw.get("issue_type", raw.get("type")), limit=40) or "task",
                "parent_id": parent_id,
                "title": title,
                "status": _text(raw.get("status"), limit=40) or "unknown",
                "priority": _priority(raw.get("priority")),
                "assignee": (
                    _text(raw.get("assignee", raw.get("owner")), limit=160)
                    if include_content
                    else ""
                ),
                "updated_at": _text(raw.get("updated_at", raw.get("updated")), limit=80),
                "dependencies": _dependencies(raw.get("dependencies"), bead_id=bead_id),
                "description": description,
                "labels": normalized_labels if include_content else [],
                "metadata": _safe_metadata(raw.get("metadata")),
                "content_included": include_content,
            }
        )
    records.sort(key=lambda item: item["id"])
    return records, hashlib.sha256(path.read_bytes()).hexdigest()


def collect_work_authority(
    root: str | Path,
    *,
    bead_snapshot: str | Path | None = None,
    include_bead_content: bool = False,
    max_items: int = 2_000,
) -> dict[str, Any]:
    """Return one unambiguous normalized work-authority snapshot.

    An explicit bead snapshot always wins.  Without one, Taskmaster is read as
    a legacy compatibility source.  No implicit bead discovery or subprocess
    call is allowed at this boundary.
    """

    repository = Path(root).expanduser().resolve()
    if bead_snapshot is not None:
        source = Path(bead_snapshot).expanduser()
        if not source.is_absolute():
            source = (Path.cwd() / source).absolute()
        records, raw_digest = _bead_items(
            source,
            include_content=include_bead_content,
            max_items=max_items,
        )
        authority = "beads"
        source_kind = "explicit-bead-snapshot"
    else:
        records, raw_digest = _taskmaster_items(repository, max_items=max_items)
        authority = "taskmaster" if records or raw_digest else "none"
        source_kind = "legacy-taskmaster" if authority == "taskmaster" else "none"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "authority": authority,
        "source_kind": source_kind,
        "raw_source_digest": raw_digest,
        "content_policy": {
            "bead_titles_labels_descriptions": bool(include_bead_content),
            "bead_assignees": bool(include_bead_content),
        },
        "items": records,
    }
    payload["source_digest"] = _digest(payload)
    return payload


__all__ = [
    "BEAD_ID_PATTERN",
    "MAX_SNAPSHOT_BYTES",
    "SCHEMA_VERSION",
    "WorkAuthorityError",
    "collect_work_authority",
]
