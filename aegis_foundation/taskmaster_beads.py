#!/usr/bin/env python3
"""Convert, migrate, and exactly reconcile a Taskmaster snapshot with Beads.

The deterministic converter remains independent from its guarded operational
runner. It validates the complete Taskmaster graph before emitting anything,
uses explicit stable Beads IDs, and writes all artifacts atomically. Re-running
it against identical input produces byte-identical output and no file rewrites.

The reconciliation API is also database-independent: callers pass the bytes
returned by ``bd export``.  It fails closed unless the export is the exact
manifest population, including identity, graph, mapped fields, and provenance.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import graphlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


CONVERTER_VERSION = "1.2.0"
MANIFEST_SCHEMA = "taskmaster-to-beads-manifest/v3"
MAPPING_SCHEMA = "taskmaster-to-beads-mapping/v2"
RECONCILIATION_SCHEMA = "taskmaster-beads-reconciliation/v3"
MIGRATION_RUN_SCHEMA = "taskmaster-beads-operational-migration/v2"
RECONCILIATION_RUN_SCHEMA = "taskmaster-beads-operational-reconciliation/v1"
LOCKED_TOOLCHAIN_SCHEMA = "gas-city-locked-operation-toolchain/v1"
TARGET_BEADS_VERSION = "1.1.0"
TARGET_DOLT_VERSION = "2.2.0"
DEFAULT_PREFIX = "ags"
ARTIFACT_NAMES = (
    "issues.jsonl",
    "blockers.jsonl",
    "hierarchy.jsonl",
    "manifest.json",
)

STATUS_MAP = {
    "pending": "open",
    "in-progress": "in_progress",
    "blocked": "blocked",
    "deferred": "deferred",
    "done": "closed",
    "cancelled": "closed",
}
PRIORITY_MAP = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
TOP_REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "description": str,
    "details": str,
    "testStrategy": str,
    "priority": str,
    "dependencies": list,
    "status": str,
    "subtasks": list,
}
SUBTASK_REQUIRED_FIELDS = {
    "id": int,
    "title": str,
    "description": str,
    "details": str,
    "dependencies": list,
    "status": str,
    "parentId": str,
}
TOP_OPTIONAL_FIELDS = {
    "complexity": int,
    "recommendedSubtasks": int,
    "expansionPrompt": str,
    "updatedAt": str,
}
SUBTASK_OPTIONAL_FIELDS = {
    "parentTaskId": int,
    "testStrategy": (str, type(None)),
    "updatedAt": str,
}
DECIMAL_ID_RE = re.compile(r"[1-9][0-9]*\Z")
FULL_SUBTASK_ID_RE = re.compile(r"([1-9][0-9]*)\.([1-9][0-9]*)\Z")


class ConversionError(ValueError):
    """Raised when a source snapshot cannot be converted without guessing."""


class ReconciliationError(ValueError):
    """Raised when migration evidence or a Beads export is not exactly equivalent."""


class OperationalMigrationError(RuntimeError):
    """Raised when an operational migration invariant fails closed."""


@dataclasses.dataclass(frozen=True)
class CommandResult:
    """Captured command result used by the dependency-injected runner."""

    returncode: int
    stdout: bytes = dataclasses.field(repr=False)
    stderr: bytes = dataclasses.field(default=b"", repr=False)


class MigrationCommandRunner(Protocol):
    """Execute one argument-vector command with optional standard-input bytes.

    Authentication must be configured in the runner environment. The
    operational migration API intentionally has no password or token argument.
    """

    def run(
        self,
        argv: Sequence[str],
        *,
        stdin: bytes | None = None,
    ) -> CommandResult: ...


class MigrationEvidenceSink(Protocol):
    """Persist one non-secret, immutable migration checkpoint."""

    def __call__(self, relative_name: str, content: bytes) -> None:
        """Store ``content`` under a safe run-relative evidence name."""


class SubprocessMigrationCommandRunner:
    """Subprocess runner with environment-only authentication and redacted repr."""

    def __init__(
        self,
        environment: Mapping[str, str] | None = None,
        *,
        timeout_seconds: int = 900,
    ) -> None:
        if type(timeout_seconds) is not int or timeout_seconds < 1:
            raise ValueError("timeout_seconds must be a positive integer")
        self._environment = dict(environment or {})
        self._timeout_seconds = timeout_seconds

    def __repr__(self) -> str:
        return "SubprocessMigrationCommandRunner(environment=<redacted>)"

    def run(
        self,
        argv: Sequence[str],
        *,
        stdin: bytes | None = None,
    ) -> CommandResult:
        environment = os.environ.copy()
        environment.update(self._environment)
        completed = subprocess.run(
            list(argv),
            input=stdin,
            capture_output=True,
            check=False,
            env=environment,
            timeout=self._timeout_seconds,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclasses.dataclass(frozen=True)
class DoltConnection:
    """Non-secret Dolt connection coordinates.

    The corresponding password must be supplied to the command runner through
    its environment (normally DOLT_CLI_PASSWORD and BEADS_DOLT_PASSWORD), never
    through this value object.
    """

    host: str
    port: int
    user: str
    database: str
    no_tls: bool = False


@dataclasses.dataclass(frozen=True)
class OperationalMigrationResult:
    """Deterministic evidence returned after an exact, idempotent migration."""

    conversion: ConversionResult
    first_export: bytes
    final_export: bytes
    report: Mapping[str, Any]


@dataclasses.dataclass(frozen=True)
class Node:
    source_id: str
    bead_id: str
    source_index: tuple[int, ...]
    parent_source_id: str | None
    title: str
    description: str
    details: str
    test_strategy: str | None
    source_status: str
    target_status: str
    source_priority: str
    target_priority: int
    priority_source: str
    issue_type: str
    raw: Mapping[str, Any]
    raw_sha256: str
    issue_projection_sha256: str


@dataclasses.dataclass(frozen=True)
class Blocker:
    blocked_source_id: str
    blocker_source_id: str
    blocked_id: str
    blocker_id: str
    source_reference: str | int
    source_reference_type: str


@dataclasses.dataclass(frozen=True)
class ConversionResult:
    artifacts: Mapping[str, bytes]
    manifest: Mapping[str, Any]
    issues: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    hierarchy: tuple[Mapping[str, Any], ...]


def _reject_duplicate_object_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConversionError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_conversion_constant(value: str) -> None:
    raise ConversionError(f"non-finite JSON number is not allowed: {value}")


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if type(value) is int:
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _jsonl_bytes(records: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_json_bytes(record) for record in records)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_value(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _require_exact_type(value: Any, expected: type | tuple[type, ...], path: str) -> None:
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    if type(value) not in expected_types:
        names = " or ".join(item.__name__ for item in expected_types)
        raise ConversionError(
            f"{path} must be {names}; observed {_json_type_name(value)}"
        )


def _require_fields(
    record: Mapping[str, Any],
    required: Mapping[str, type | tuple[type, ...]],
    optional: Mapping[str, type | tuple[type, ...]],
    path: str,
) -> None:
    for field, expected in required.items():
        if field not in record:
            raise ConversionError(f"{path}.{field} is required")
        _require_exact_type(record[field], expected, f"{path}.{field}")
    for field, expected in optional.items():
        if field in record:
            _require_exact_type(record[field], expected, f"{path}.{field}")


def _validate_rfc3339(value: str, path: str) -> None:
    if not value.endswith("Z"):
        raise ConversionError(f"{path} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ConversionError(f"{path} is not a valid RFC3339 timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ConversionError(f"{path} must be UTC")


def _source_sort_key(source_id: str) -> tuple[int, int, int]:
    if "." in source_id:
        parent, child = source_id.split(".", 1)
        return (int(parent), 1, int(child))
    return (int(source_id), 0, 0)


def _bead_id(source_id: str, prefix: str) -> str:
    if "." in source_id:
        parent, child = source_id.split(".", 1)
        return f"{prefix}-{int(parent):04d}.{int(child)}"
    return f"{prefix}-{int(source_id):04d}"


def _field_state(record: Mapping[str, Any], field: str) -> str:
    if field not in record:
        return "missing"
    value = record[field]
    if value is None:
        return "null"
    if value == "":
        return "empty"
    if value == []:
        return "empty"
    return "value"


def _field_inventory(records: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    fields = sorted({field for record in records for field in record})
    inventory: dict[str, Any] = {}
    for field in fields:
        values = [record[field] for record in records if field in record]
        types = collections.Counter(_json_type_name(value) for value in values)
        inventory[field] = {
            "present": len(values),
            "absent": len(records) - len(values),
            "types": dict(sorted(types.items())),
            "null": sum(value is None for value in values),
            "empty_string": sum(value == "" for value in values),
            "empty_array": sum(value == [] for value in values),
        }
    return inventory


def _issue_projection(raw: Mapping[str, Any], *, top_level: bool) -> Mapping[str, Any]:
    if top_level:
        return {key: value for key, value in raw.items() if key != "subtasks"}
    return dict(raw)


def _legacy_metadata(
    node: Node,
    *,
    source_sha256: str,
    tag: str,
) -> Mapping[str, Any]:
    optional_fields: dict[str, Any] = {}
    optional_names = (
        TOP_OPTIONAL_FIELDS
        if node.parent_source_id is None
        else SUBTASK_OPTIONAL_FIELDS
    )
    for field in sorted(optional_names):
        if field in node.raw:
            optional_fields[field] = node.raw[field]
    if node.parent_source_id is not None:
        optional_fields["parentId"] = node.raw.get("parentId")

    return {
        "migration": {
            "mapping_schema": MAPPING_SCHEMA,
            "converter_version": CONVERTER_VERSION,
            "source_system": "taskmaster",
            "source_tag": tag,
            "source_sha256": source_sha256,
            "source_id": node.source_id,
            "source_index": list(node.source_index),
            "source_record_sha256": node.raw_sha256,
            "source_issue_projection_sha256": node.issue_projection_sha256,
            "source_status": node.source_status,
            "source_priority": node.source_priority,
            "priority_source": node.priority_source,
            "parent_source_id": node.parent_source_id,
            "field_states": {
                "details": _field_state(node.raw, "details"),
                "testStrategy": _field_state(node.raw, "testStrategy"),
                "updatedAt": _field_state(node.raw, "updatedAt"),
            },
            "optional_fields": optional_fields,
        }
    }


def _status_close_fields(source_status: str, snapshot_time: str) -> Mapping[str, str]:
    if source_status == "done":
        return {"closed_at": snapshot_time, "close_reason": "migrated:done"}
    if source_status == "cancelled":
        return {
            "closed_at": snapshot_time,
            "close_reason": "cancelled in Taskmaster",
        }
    if source_status == "in-progress":
        return {"started_at": snapshot_time}
    return {}


def _semantic_issue_projection(
    issues: Sequence[Mapping[str, Any]],
) -> Sequence[Mapping[str, Any]]:
    id_to_external = {str(issue["id"]): str(issue["external_ref"]) for issue in issues}
    volatile = {
        "created_at",
        "updated_at",
        "closed_at",
        "started_at",
        "created_by",
        "dependency_count",
        "dependent_count",
        "comment_count",
    }
    result: list[Mapping[str, Any]] = []
    for issue in issues:
        projected = {key: value for key, value in issue.items() if key not in volatile}
        projected["id"] = id_to_external[str(issue["id"])]
        dependencies: list[Mapping[str, Any]] = []
        for dependency in issue.get("dependencies", []):
            dependencies.append(
                {
                    "issue_id": id_to_external[str(dependency["issue_id"])],
                    "depends_on_id": id_to_external[str(dependency["depends_on_id"])],
                    "type": dependency["type"],
                }
            )
        if dependencies:
            projected["dependencies"] = sorted(
                dependencies,
                key=lambda item: (item["issue_id"], item["depends_on_id"], item["type"]),
            )
        else:
            projected.pop("dependencies", None)
        result.append(projected)
    return sorted(result, key=lambda item: str(item["id"]))


def build_artifacts(
    source_bytes: bytes,
    *,
    tag: str = "master",
    prefix: str = DEFAULT_PREFIX,
    expected_source_sha256: str | None = None,
) -> ConversionResult:
    """Validate and convert one immutable Taskmaster JSON byte stream."""

    if not re.fullmatch(r"[a-z][a-z0-9-]*", prefix):
        raise ConversionError("prefix must match [a-z][a-z0-9-]*")
    source_sha256 = _sha256_bytes(source_bytes)
    if expected_source_sha256 and source_sha256 != expected_source_sha256:
        raise ConversionError(
            "source SHA-256 mismatch: "
            f"expected {expected_source_sha256}, observed {source_sha256}"
        )
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConversionError("source is not valid UTF-8") from exc
    try:
        payload = json.loads(
            source_text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_conversion_constant,
        )
    except json.JSONDecodeError as exc:
        raise ConversionError(f"invalid Taskmaster JSON: {exc}") from exc
    if type(payload) is not dict:
        raise ConversionError("Taskmaster root must be an object")
    if tag not in payload:
        raise ConversionError(f"Taskmaster tag {tag!r} is missing")
    tag_data = payload[tag]
    if type(tag_data) is not dict:
        raise ConversionError(f"Taskmaster tag {tag!r} must be an object")
    tasks = tag_data.get("tasks")
    metadata = tag_data.get("metadata")
    if type(tasks) is not list:
        raise ConversionError(f"Taskmaster tag {tag!r}.tasks must be an array")
    if type(metadata) is not dict:
        raise ConversionError(f"Taskmaster tag {tag!r}.metadata must be an object")
    metadata_types: Mapping[str, type] = {
        "version": str,
        "lastModified": str,
        "taskCount": int,
        "completedCount": int,
        "tags": list,
    }
    for field, expected in metadata_types.items():
        if field not in metadata:
            raise ConversionError(f"Taskmaster metadata.{field} is required")
        _require_exact_type(metadata[field], expected, f"$.{tag}.metadata.{field}")
    if any(type(item) is not str for item in metadata["tags"]):
        raise ConversionError("Taskmaster metadata.tags must contain only strings")
    if tag not in metadata["tags"]:
        raise ConversionError(f"Taskmaster metadata.tags does not declare {tag!r}")
    snapshot_time = metadata["lastModified"]
    _validate_rfc3339(snapshot_time, f"$.{tag}.metadata.lastModified")

    top_ids: list[str] = []
    top_by_id: dict[str, Mapping[str, Any]] = {}
    top_index_by_id: dict[str, int] = {}
    child_records: list[Mapping[str, Any]] = []
    child_by_full_id: dict[str, Mapping[str, Any]] = {}
    child_index_by_full_id: dict[str, tuple[int, int]] = {}
    parent_by_child: dict[str, str] = {}
    raw_parent_id_undefined = 0
    raw_parent_task_id_present = 0

    for top_index, task in enumerate(tasks):
        path = f"$.{tag}.tasks[{top_index}]"
        if type(task) is not dict:
            raise ConversionError(f"{path} must be an object")
        _require_fields(task, TOP_REQUIRED_FIELDS, TOP_OPTIONAL_FIELDS, path)
        source_id = task["id"]
        if not DECIMAL_ID_RE.fullmatch(source_id):
            raise ConversionError(f"{path}.id must be a canonical positive decimal string")
        if not task["title"]:
            raise ConversionError(f"{path}.title must not be empty")
        if source_id in top_by_id:
            raise ConversionError(f"duplicate top-level Taskmaster ID: {source_id}")
        if task["status"] not in STATUS_MAP:
            raise ConversionError(f"{path}.status is unsupported: {task['status']!r}")
        if "updatedAt" in task:
            _validate_rfc3339(task["updatedAt"], f"{path}.updatedAt")
        top_ids.append(source_id)
        top_by_id[source_id] = task
        top_index_by_id[source_id] = top_index

        local_ids: set[int] = set()
        for child_index, child in enumerate(task["subtasks"]):
            child_path = f"{path}.subtasks[{child_index}]"
            if type(child) is not dict:
                raise ConversionError(f"{child_path} must be an object")
            _require_fields(
                child,
                SUBTASK_REQUIRED_FIELDS,
                SUBTASK_OPTIONAL_FIELDS,
                child_path,
            )
            child_id = child["id"]
            if child_id <= 0:
                raise ConversionError(f"{child_path}.id must be positive")
            if not child["title"]:
                raise ConversionError(f"{child_path}.title must not be empty")
            if child_id in local_ids:
                raise ConversionError(f"duplicate subtask ID {source_id}.{child_id}")
            local_ids.add(child_id)
            full_id = f"{source_id}.{child_id}"
            if full_id in child_by_full_id:
                raise ConversionError(f"duplicate full subtask ID: {full_id}")
            if child["status"] not in STATUS_MAP:
                raise ConversionError(
                    f"{child_path}.status is unsupported: {child['status']!r}"
                )
            if child.get("parentId") == "undefined":
                raw_parent_id_undefined += 1
            if "parentTaskId" in child:
                raw_parent_task_id_present += 1
                if child["parentTaskId"] != int(source_id):
                    raise ConversionError(
                        f"{child_path}.parentTaskId={child['parentTaskId']} "
                        f"does not match enclosing task {source_id}"
                    )
            if "updatedAt" in child:
                _validate_rfc3339(child["updatedAt"], f"{child_path}.updatedAt")
            child_records.append(child)
            child_by_full_id[full_id] = child
            child_index_by_full_id[full_id] = (top_index, child_index)
            parent_by_child[full_id] = source_id

        expected_local_ids = set(range(1, len(task["subtasks"]) + 1))
        if local_ids != expected_local_ids:
            raise ConversionError(
                f"subtask IDs under {source_id} must be contiguous 1..n; "
                f"observed {sorted(local_ids)}"
            )

    if not top_ids:
        raise ConversionError("Taskmaster snapshot contains no tasks")

    if metadata.get("taskCount") != len(tasks):
        raise ConversionError(
            "metadata.taskCount does not match tasks array: "
            f"{metadata.get('taskCount')!r} != {len(tasks)}"
        )
    completed_top = sum(task["status"] == "done" for task in tasks)
    if metadata.get("completedCount") != completed_top:
        raise ConversionError(
            "metadata.completedCount does not match done top-level tasks: "
            f"{metadata.get('completedCount')!r} != {completed_top}"
        )

    duplicate_subtask_titles = {
        title: count
        for title, count in sorted(
            collections.Counter(child["title"] for child in child_records).items()
        )
        if count > 1
    }
    anomalies: list[Mapping[str, Any]] = []
    numeric_top_ids = sorted(int(source_id) for source_id in top_ids)
    missing_ids = sorted(
        set(range(numeric_top_ids[0], numeric_top_ids[-1] + 1))
        - set(numeric_top_ids)
    )
    if missing_ids:
        anomalies.append(
            {
                "code": "non_dense_top_ids",
                "severity": "info",
                "missing_ids": missing_ids,
            }
        )
    inversions = []
    for index in range(1, len(top_ids)):
        if int(top_ids[index]) < int(top_ids[index - 1]):
            inversions.append(
                {
                    "source_index": index,
                    "previous_id": top_ids[index - 1],
                    "current_id": top_ids[index],
                }
            )
    if inversions:
        anomalies.append(
            {
                "code": "source_order_not_numeric",
                "severity": "info",
                "inversions": inversions,
            }
        )

    for source_id in top_ids:
        task = top_by_id[source_id]
        non_done = [
            {"id": f"{source_id}.{child['id']}", "status": child["status"]}
            for child in task["subtasks"]
            if child["status"] != "done"
        ]
        active = [
            item
            for item in non_done
            if item["status"] in {"pending", "in-progress", "blocked"}
        ]
        if task["status"] == "done" and non_done:
            anomalies.append(
                {
                    "code": "parent_done_with_non_done_children",
                    "severity": "warning",
                    "source_id": source_id,
                    "children": non_done,
                    "preservation": "preserve source statuses without normalization",
                }
            )
        elif task["status"] in {"deferred", "cancelled"} and active:
            anomalies.append(
                {
                    "code": "nonactive_parent_with_active_children",
                    "severity": "warning",
                    "source_id": source_id,
                    "parent_status": task["status"],
                    "children": active,
                    "preservation": "preserve source statuses without normalization",
                }
            )

    nodes: list[Node] = []
    unknown_priorities: list[Mapping[str, Any]] = []
    for source_id in sorted(top_ids, key=_source_sort_key):
        task = top_by_id[source_id]
        source_priority = task["priority"]
        target_priority = PRIORITY_MAP.get(source_priority, 4)
        if source_priority not in PRIORITY_MAP:
            unknown_priorities.append(
                {"source_id": source_id, "source_priority": source_priority}
            )
        top_index = top_index_by_id[source_id]
        nodes.append(
            Node(
                source_id=source_id,
                bead_id=_bead_id(source_id, prefix),
                source_index=(top_index,),
                parent_source_id=None,
                title=task["title"],
                description=task["description"],
                details=task["details"],
                test_strategy=task["testStrategy"],
                source_status=task["status"],
                target_status=STATUS_MAP[task["status"]],
                source_priority=source_priority,
                target_priority=target_priority,
                priority_source="explicit",
                issue_type="epic" if task["subtasks"] else "task",
                raw=task,
                raw_sha256=_sha256_value(task),
                issue_projection_sha256=_sha256_value(
                    _issue_projection(task, top_level=True)
                ),
            )
        )
        for child in sorted(task["subtasks"], key=lambda item: item["id"]):
            full_id = f"{source_id}.{child['id']}"
            child_indexes = child_index_by_full_id[full_id]
            nodes.append(
                Node(
                    source_id=full_id,
                    bead_id=_bead_id(full_id, prefix),
                    source_index=child_indexes,
                    parent_source_id=source_id,
                    title=child["title"],
                    description=child["description"],
                    details=child["details"],
                    test_strategy=child.get("testStrategy"),
                    source_status=child["status"],
                    target_status=STATUS_MAP[child["status"]],
                    source_priority=source_priority,
                    target_priority=target_priority,
                    priority_source="parent",
                    issue_type="task",
                    raw=child,
                    raw_sha256=_sha256_value(child),
                    issue_projection_sha256=_sha256_value(
                        _issue_projection(child, top_level=False)
                    ),
                )
            )

    if unknown_priorities:
        anomalies.append(
            {
                "code": "unknown_priorities_mapped_to_p4",
                "severity": "warning",
                "issues": unknown_priorities,
            }
        )

    node_by_source = {node.source_id: node for node in nodes}
    if len(node_by_source) != len(nodes):
        raise ConversionError("normalized Taskmaster IDs are not unique")

    blockers: list[Blocker] = []
    predecessors: dict[str, set[str]] = {source_id: set() for source_id in node_by_source}
    for source_id in top_ids:
        task = top_by_id[source_id]
        seen: set[str] = set()
        for dependency in task["dependencies"]:
            if type(dependency) is not str or not DECIMAL_ID_RE.fullmatch(dependency):
                raise ConversionError(
                    f"top-level dependency on {source_id} must be a canonical decimal string; "
                    f"observed {dependency!r}"
                )
            blocker_source = dependency
            if blocker_source not in top_by_id:
                raise ConversionError(
                    f"Task {source_id} depends on missing top-level task {blocker_source}"
                )
            if blocker_source == source_id:
                raise ConversionError(f"Task {source_id} depends on itself")
            if blocker_source in seen:
                raise ConversionError(
                    f"Task {source_id} repeats dependency {blocker_source}"
                )
            seen.add(blocker_source)
            predecessors[source_id].add(blocker_source)
            blockers.append(
                Blocker(
                    blocked_source_id=source_id,
                    blocker_source_id=blocker_source,
                    blocked_id=node_by_source[source_id].bead_id,
                    blocker_id=node_by_source[blocker_source].bead_id,
                    source_reference=dependency,
                    source_reference_type="top-string",
                )
            )

        local_ids = {child["id"] for child in task["subtasks"]}
        for child in task["subtasks"]:
            child_source = f"{source_id}.{child['id']}"
            seen_child: set[str] = set()
            for dependency in child["dependencies"]:
                if type(dependency) is int:
                    if dependency not in local_ids:
                        raise ConversionError(
                            f"Subtask {child_source} depends on missing local subtask "
                            f"{source_id}.{dependency}"
                        )
                    blocker_source = f"{source_id}.{dependency}"
                    reference_type = "subtask-local-number"
                elif type(dependency) is str:
                    match = FULL_SUBTASK_ID_RE.fullmatch(dependency)
                    if not match:
                        raise ConversionError(
                            f"Subtask {child_source} has ambiguous bare-string dependency "
                            f"{dependency!r}; use a JSON number for a local sibling or a "
                            "dotted full subtask ID"
                        )
                    if match.group(1) != source_id:
                        raise ConversionError(
                            f"Subtask {child_source} has unsupported cross-parent dependency "
                            f"{dependency!r}"
                        )
                    blocker_source = dependency
                    reference_type = "subtask-full-string"
                    if blocker_source not in child_by_full_id:
                        raise ConversionError(
                            f"Subtask {child_source} depends on missing subtask {blocker_source}"
                        )
                else:
                    raise ConversionError(
                        f"Subtask {child_source} dependency must be an integer or dotted string; "
                        f"observed {_json_type_name(dependency)}"
                    )
                if blocker_source == child_source:
                    raise ConversionError(f"Subtask {child_source} depends on itself")
                if blocker_source in seen_child:
                    raise ConversionError(
                        f"Subtask {child_source} repeats dependency {blocker_source}"
                    )
                seen_child.add(blocker_source)
                predecessors[child_source].add(blocker_source)
                blockers.append(
                    Blocker(
                        blocked_source_id=child_source,
                        blocker_source_id=blocker_source,
                        blocked_id=node_by_source[child_source].bead_id,
                        blocker_id=node_by_source[blocker_source].bead_id,
                        source_reference=dependency,
                        source_reference_type=reference_type,
                    )
                )

    try:
        topological_order = tuple(graphlib.TopologicalSorter(predecessors).static_order())
    except graphlib.CycleError as exc:
        cycle = list(exc.args[1]) if len(exc.args) > 1 else []
        raise ConversionError(f"Taskmaster dependency graph contains a cycle: {cycle}") from exc
    if len(topological_order) != len(nodes):
        raise ConversionError("topological validation introduced unexpected dependency nodes")

    blockers.sort(
        key=lambda item: (
            _source_sort_key(item.blocked_source_id),
            _source_sort_key(item.blocker_source_id),
            item.source_reference_type,
        )
    )
    hierarchy_records: list[Mapping[str, Any]] = []
    for node in nodes:
        if node.parent_source_id is None:
            continue
        hierarchy_records.append(
            {
                "child_id": node.bead_id,
                "parent_id": node_by_source[node.parent_source_id].bead_id,
                "relationship": "parent-child",
                "source_child_id": node.source_id,
                "source_parent_id": node.parent_source_id,
            }
        )
    hierarchy_records.sort(key=lambda item: _source_sort_key(str(item["source_child_id"])))

    blocker_records: list[Mapping[str, Any]] = [
        {
            "blocked_id": item.blocked_id,
            "blocker_id": item.blocker_id,
            "relationship": "blocks",
            "source_blocked_id": item.blocked_source_id,
            "source_blocker_id": item.blocker_source_id,
            "source_reference": item.source_reference,
            "source_reference_type": item.source_reference_type,
        }
        for item in blockers
    ]
    blockers_by_issue: dict[str, list[Blocker]] = collections.defaultdict(list)
    parent_by_issue: dict[str, str] = {}
    dependent_counts: collections.Counter[str] = collections.Counter()
    for blocker in blockers:
        blockers_by_issue[blocker.blocked_source_id].append(blocker)
        dependent_counts[blocker.blocker_source_id] += 1
    for hierarchy in hierarchy_records:
        parent_by_issue[str(hierarchy["source_child_id"])] = str(hierarchy["parent_id"])

    issues: list[Mapping[str, Any]] = []
    for node in nodes:
        labels = ["legacy:taskmaster", f"legacy:status:{node.source_status}"]
        if node.priority_source == "parent":
            labels.append("legacy:priority:inherited")
        if node.source_status == "cancelled":
            labels.append("migration:cancelled")
        if node.source_priority not in PRIORITY_MAP:
            labels.append("legacy:priority:unknown")

        issue: dict[str, Any] = {
            "_type": "issue",
            "id": node.bead_id,
            "title": node.title,
            "description": node.description,
            "status": node.target_status,
            "priority": node.target_priority,
            "issue_type": node.issue_type,
            "created_at": snapshot_time,
            "created_by": "taskmaster-migration",
            "updated_at": snapshot_time,
            "external_ref": f"taskmaster:{tag}:{node.source_id}",
            "source_system": "taskmaster",
            "metadata": _legacy_metadata(
                node,
                source_sha256=source_sha256,
                tag=tag,
            ),
            "labels": sorted(labels),
            "dependency_count": len(blockers_by_issue[node.source_id]),
            "dependent_count": dependent_counts[node.source_id],
            "comment_count": 0,
        }
        if node.details:
            issue["design"] = node.details
        if node.test_strategy:
            issue["acceptance_criteria"] = node.test_strategy
        issue.update(_status_close_fields(node.source_status, snapshot_time))

        embedded_dependencies = []
        for blocker in blockers_by_issue[node.source_id]:
            embedded_dependencies.append(
                {
                    "issue_id": node.bead_id,
                    "depends_on_id": blocker.blocker_id,
                    "type": "blocks",
                    "created_at": snapshot_time,
                    "created_by": "taskmaster-migration",
                    "metadata": "{}",
                }
            )
        parent_id = parent_by_issue.get(node.source_id)
        if parent_id is not None:
            embedded_dependencies.append(
                {
                    "issue_id": node.bead_id,
                    "depends_on_id": parent_id,
                    "type": "parent-child",
                    "created_at": snapshot_time,
                    "created_by": "taskmaster-migration",
                    "metadata": "{}",
                }
            )
        if embedded_dependencies:
            issue["dependencies"] = embedded_dependencies
        issues.append(issue)

    id_map: list[Mapping[str, Any]] = []
    for node in nodes:
        id_map.append(
            {
                "source_id": node.source_id,
                "bead_id": node.bead_id,
                "external_ref": f"taskmaster:{tag}:{node.source_id}",
                "source_index": list(node.source_index),
                "parent_source_id": node.parent_source_id,
                "issue_type": node.issue_type,
                "source_record_sha256": node.raw_sha256,
                "source_issue_projection_sha256": node.issue_projection_sha256,
            }
        )

    status_counts = collections.Counter(node.source_status for node in nodes)
    target_status_counts = collections.Counter(node.target_status for node in nodes)
    top_priority_counts = collections.Counter(task["priority"] for task in tasks)
    effective_priority_counts = collections.Counter(
        f"P{node.target_priority}" for node in nodes
    )
    issue_type_counts = collections.Counter(node.issue_type for node in nodes)
    dependency_reference_types = collections.Counter(
        blocker.source_reference_type for blocker in blockers
    )

    logical_graph = {
        "nodes": [
            {
                "source_id": node.source_id,
                "parent_source_id": node.parent_source_id,
                "title": node.title,
                "description": node.description,
                "details": node.details,
                "testStrategy": node.test_strategy,
                "source_status": node.source_status,
                "target_status": node.target_status,
                "source_priority": node.source_priority,
                "target_priority": node.target_priority,
                "priority_source": node.priority_source,
                "issue_type": node.issue_type,
                "source_issue_projection_sha256": node.issue_projection_sha256,
            }
            for node in nodes
        ],
        "blockers": [
            {
                "blocked_source_id": item.blocked_source_id,
                "blocker_source_id": item.blocker_source_id,
                "source_reference_type": item.source_reference_type,
            }
            for item in blockers
        ],
        "hierarchy": [
            {
                "source_child_id": item["source_child_id"],
                "source_parent_id": item["source_parent_id"],
            }
            for item in hierarchy_records
        ],
    }

    issues_bytes = _jsonl_bytes(issues)
    blockers_bytes = _jsonl_bytes(blocker_records)
    hierarchy_bytes = _jsonl_bytes(hierarchy_records)
    semantic_projection = _semantic_issue_projection(issues)
    semantic_projection_sha256 = _sha256_value(semantic_projection)
    id_map_sha256 = _sha256_value(id_map)
    logical_graph_sha256 = _sha256_value(logical_graph)
    artifact_digests = {
        "issues.jsonl": _sha256_bytes(issues_bytes),
        "blockers.jsonl": _sha256_bytes(blockers_bytes),
        "hierarchy.jsonl": _sha256_bytes(hierarchy_bytes),
    }
    artifact_set_sha256 = _sha256_value(artifact_digests)

    warning_count = sum(item["severity"] == "warning" for item in anomalies)
    info_count = sum(item["severity"] == "info" for item in anomalies)
    manifest_core: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "converter_version": CONVERTER_VERSION,
        "source": {
            "logical_name": f"taskmaster:{tag}",
            "sha256": source_sha256,
            "tag": tag,
            "metadata": metadata,
        },
        "target": {
            "system": "beads",
            "version": TARGET_BEADS_VERSION,
            "id_prefix": prefix,
            "id_format": f"{prefix}-<top:04d>[.<child>]",
            "hierarchy_encoding": (
                "dependencies embedded on child issues with type=parent-child; "
                "dotted IDs and hierarchy.jsonl provide independent verification evidence"
            ),
            "blocker_encoding": "dependencies embedded on blocked issues with type=blocks",
        },
        "counts": {
            "top_level_tasks": len(tasks),
            "subtasks": len(child_records),
            "issues": len(nodes),
            "epics": issue_type_counts.get("epic", 0),
            "tasks": issue_type_counts.get("task", 0),
            "top_level_dependency_references": sum(
                len(task["dependencies"]) for task in tasks
            ),
            "subtask_dependency_references": sum(
                len(child["dependencies"]) for child in child_records
            ),
            "blocker_relationships": len(blockers),
            "hierarchy_relationships": len(hierarchy_records),
            "total_dependency_relationships": len(blockers) + len(hierarchy_records),
            "source_statuses": dict(sorted(status_counts.items())),
            "target_statuses": dict(sorted(target_status_counts.items())),
            "top_level_priorities": dict(sorted(top_priority_counts.items())),
            "effective_target_priorities": dict(sorted(effective_priority_counts.items())),
            "dependency_reference_types": dict(
                sorted(dependency_reference_types.items())
            ),
        },
        "mappings": {
            "statuses": STATUS_MAP,
            "priorities": {
                **{key: f"P{value}" for key, value in PRIORITY_MAP.items()},
                "unknown": "P4 with legacy:priority:unknown label",
                "subtask_without_priority": "inherit enclosing top-level priority",
            },
            "fields": {
                "title": "title",
                "description": "description",
                "details": "design",
                "testStrategy": "acceptance_criteria",
                "updatedAt": "metadata.migration.optional_fields.updatedAt",
                "complexity": "metadata.migration.optional_fields.complexity",
                "recommendedSubtasks": "metadata.migration.optional_fields.recommendedSubtasks",
                "expansionPrompt": "metadata.migration.optional_fields.expansionPrompt",
            },
            "cancelled": {
                "status": "closed",
                "close_reason": "cancelled in Taskmaster",
                "label": "migration:cancelled",
            },
            "dependency_orientation": (
                "Taskmaster A.dependencies=[B] becomes Beads A depends_on B "
                "(B blocks A)"
            ),
            "subtask_dependency_resolution": {
                "json_number": "local sibling under the same parent",
                "dotted_string": "full same-parent subtask ID",
                "bare_string": "rejected as ambiguous",
            },
        },
        "validation": {
            "status": "pass",
            "checks": {
                "duplicate_json_keys_rejected": True,
                "metadata_counts_match": True,
                "ids_unique": True,
                "subtask_ids_contiguous": True,
                "optional_parentTaskId_matches_container": True,
                "dependency_endpoints_resolve": True,
                "duplicate_dependencies_absent": True,
                "self_dependencies_absent": True,
                "explicit_dependency_graph_acyclic": True,
                "timestamps_rfc3339_utc": True,
                "canonical_output_order": True,
            },
            "topological_node_count": len(topological_order),
            "legacy_parentId_undefined": raw_parent_id_undefined,
            "legacy_parentTaskId_present_and_matching": raw_parent_task_id_present,
            "field_inventory": {
                "top_level": _field_inventory(tasks),
                "subtasks": _field_inventory(child_records),
            },
            "observations": {
                "duplicate_subtask_titles": duplicate_subtask_titles,
                "source_order_preserved_in_id_map": True,
                "canonical_creation_order": "numeric top ID, parent before numeric child ID",
            },
            "anomaly_summary": {
                "warnings": warning_count,
                "info": info_count,
            },
        },
        "anomalies": sorted(
            anomalies,
            key=lambda item: (
                str(item["code"]),
                _source_sort_key(str(item.get("source_id", "1"))),
            ),
        ),
        "id_map": id_map,
        "idempotency": {
            "deterministic": True,
            "identity_field": "external_ref",
            "rerun_contract": {
                "created": 0,
                "updated": 0,
                "deleted": 0,
                "relationships_added": 0,
                "duplicates": 0,
                "existing_records_unchanged": len(nodes),
                "beads_import_note": (
                    "Beads v1.1.0 reports unchanged fixed-timestamp rows as stale-skipped "
                    "or tie-kept depending on backend timestamp precision"
                ),
            },
            "semantic_projection_excludes": [
                "created_at",
                "updated_at",
                "closed_at",
                "started_at",
                "created_by",
                "dependency audit fields",
                "derived dependency/comment counts",
            ],
        },
    }
    manifest_core_sha256 = _sha256_value(manifest_core)
    manifest = dict(manifest_core)
    manifest["digests"] = {
        "source_sha256": source_sha256,
        "logical_graph_sha256": logical_graph_sha256,
        "id_map_sha256": id_map_sha256,
        "semantic_idempotency_projection_sha256": semantic_projection_sha256,
        "manifest_core_sha256": manifest_core_sha256,
        "artifact_set_sha256": artifact_set_sha256,
        "artifacts": artifact_digests,
    }
    manifest_bytes = _pretty_json_bytes(manifest)
    artifacts = {
        "issues.jsonl": issues_bytes,
        "blockers.jsonl": blockers_bytes,
        "hierarchy.jsonl": hierarchy_bytes,
        "manifest.json": manifest_bytes,
    }
    return ConversionResult(
        artifacts=artifacts,
        manifest=manifest,
        issues=tuple(issues),
        blockers=tuple(blocker_records),
        hierarchy=tuple(hierarchy_records),
    )


def write_artifacts(output_dir: Path, artifacts: Mapping[str, bytes]) -> Mapping[str, Any]:
    """Atomically write changed artifacts and leave byte-identical files untouched."""

    artifact_names = set(artifacts)
    expected_names = set(ARTIFACT_NAMES)
    if artifact_names != expected_names:
        raise ConversionError(
            "artifact set must be exact; "
            f"missing={sorted(expected_names - artifact_names)}, "
            f"unexpected={sorted(artifact_names - expected_names)}"
        )
    for name in ARTIFACT_NAMES:
        if type(artifacts[name]) is not bytes:
            raise ConversionError(f"generated artifact {name} must be bytes")

    output_dir.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    unchanged: list[str] = []
    for name in ARTIFACT_NAMES:
        if name not in artifacts:
            raise ConversionError(f"missing generated artifact: {name}")
        destination = output_dir / name
        content = artifacts[name]
        if destination.is_file() and destination.read_bytes() == content:
            unchanged.append(name)
            continue
        if destination.exists() and not destination.is_file():
            raise ConversionError(f"artifact path is not a regular file: {destination}")
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{name}.",
            dir=output_dir,
        )
        try:
            with os.fdopen(file_descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, destination)
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
        changed.append(name)
    if changed:
        try:
            directory_descriptor = os.open(output_dir, os.O_RDONLY)
        except OSError:
            directory_descriptor = None
        if directory_descriptor is not None:
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    return {
        "changed_files": changed,
        "unchanged_files": unchanged,
    }


def _reject_reconciliation_duplicate_keys(
    pairs: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReconciliationError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_reconciliation_constant(value: str) -> None:
    raise ReconciliationError(f"non-finite JSON number is not allowed: {value}")


def _load_json_object_bytes(content: bytes, label: str) -> Mapping[str, Any]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReconciliationError(f"{label} is not valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_reconciliation_duplicate_keys,
            parse_constant=_reject_reconciliation_constant,
        )
    except json.JSONDecodeError as exc:
        raise ReconciliationError(f"{label} is not valid JSON: {exc}") from exc
    if type(value) is not dict:
        raise ReconciliationError(f"{label} must contain one JSON object")
    return value


def _load_jsonl_bytes(content: bytes, label: str) -> list[Mapping[str, Any]]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ReconciliationError(f"{label} is not valid UTF-8") from exc
    records: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            raise ReconciliationError(f"{label}:{line_number}: blank JSONL line")
        try:
            value = json.loads(
                line,
                object_pairs_hook=_reject_reconciliation_duplicate_keys,
                parse_constant=_reject_reconciliation_constant,
            )
        except json.JSONDecodeError as exc:
            raise ReconciliationError(
                f"{label}:{line_number}: invalid JSON: {exc}"
            ) from exc
        if type(value) is not dict:
            raise ReconciliationError(
                f"{label}:{line_number}: record must be an object"
            )
        records.append(value)
    return records


def _require_reconciliation_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise ReconciliationError(f"{path} must be an object")
    return value


def _require_reconciliation_list(value: Any, path: str) -> list[Any]:
    if type(value) is not list:
        raise ReconciliationError(f"{path} must be an array")
    return value


def _require_reconciliation_string(value: Any, path: str) -> str:
    if type(value) is not str or not value:
        raise ReconciliationError(f"{path} must be a non-empty string")
    return value


def _exact_value_matches(observed: Any, expected: Any) -> bool:
    return type(observed) is type(expected) and observed == expected


def _index_issues(
    issues: Sequence[Mapping[str, Any]],
    *,
    label: str,
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    external_to_id: dict[str, str] = {}
    for index, issue in enumerate(issues):
        path = f"{label}[{index}]"
        issue_id = _require_reconciliation_string(issue.get("id"), f"{path}.id")
        external_ref = _require_reconciliation_string(
            issue.get("external_ref"),
            f"{path}.external_ref",
        )
        if issue.get("_type") != "issue":
            raise ReconciliationError(f"{issue_id}: _type must be 'issue'")
        if issue_id in by_id:
            raise ReconciliationError(f"duplicate issue id: {issue_id}")
        if external_ref in external_to_id:
            raise ReconciliationError(f"duplicate external_ref: {external_ref}")
        by_id[issue_id] = issue
        external_to_id[external_ref] = issue_id
    return by_id, external_to_id


def _dependency_sets(
    issues: Sequence[Mapping[str, Any]],
    *,
    allowed_ids: set[str],
    label: str,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    blockers: set[tuple[str, str]] = set()
    hierarchy: set[tuple[str, str]] = set()
    all_edges: set[tuple[str, str, str]] = set()
    for issue in issues:
        issue_id = _require_reconciliation_string(issue.get("id"), f"{label}.id")
        dependencies = issue.get("dependencies", [])
        if type(dependencies) is not list:
            raise ReconciliationError(f"{issue_id}: dependencies must be an array")
        for index, dependency_value in enumerate(dependencies):
            dependency = _require_reconciliation_mapping(
                dependency_value,
                f"{issue_id}.dependencies[{index}]",
            )
            blocked_id = _require_reconciliation_string(
                dependency.get("issue_id"),
                f"{issue_id}.dependencies[{index}].issue_id",
            )
            blocker_id = _require_reconciliation_string(
                dependency.get("depends_on_id"),
                f"{issue_id}.dependencies[{index}].depends_on_id",
            )
            relationship = _require_reconciliation_string(
                dependency.get("type"),
                f"{issue_id}.dependencies[{index}].type",
            )
            if blocked_id != issue_id:
                raise ReconciliationError(
                    f"{issue_id}: dependency issue_id is {blocked_id!r}"
                )
            if blocker_id not in allowed_ids:
                raise ReconciliationError(
                    f"{issue_id}: dependency endpoint is not in the manifest: {blocker_id}"
                )
            if relationship not in {"blocks", "parent-child"}:
                raise ReconciliationError(
                    f"{issue_id}: unsupported dependency type: {relationship!r}"
                )
            edge = (blocked_id, blocker_id, relationship)
            if edge in all_edges:
                raise ReconciliationError(f"duplicate dependency edge: {edge}")
            all_edges.add(edge)
            if relationship == "blocks":
                blockers.add((blocked_id, blocker_id))
            else:
                hierarchy.add((blocked_id, blocker_id))
    return blockers, hierarchy


def _relationship_evidence(
    blockers: Sequence[Mapping[str, Any]],
    hierarchy: Sequence[Mapping[str, Any]],
    *,
    allowed_ids: set[str],
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    blocker_edges: set[tuple[str, str]] = set()
    for index, record in enumerate(blockers):
        path = f"blockers.jsonl[{index}]"
        blocked_id = _require_reconciliation_string(
            record.get("blocked_id"),
            f"{path}.blocked_id",
        )
        blocker_id = _require_reconciliation_string(
            record.get("blocker_id"),
            f"{path}.blocker_id",
        )
        if record.get("relationship") != "blocks":
            raise ReconciliationError(f"{path}.relationship must be 'blocks'")
        if blocked_id not in allowed_ids or blocker_id not in allowed_ids:
            raise ReconciliationError(f"{path} has an endpoint outside the manifest")
        edge = (blocked_id, blocker_id)
        if edge in blocker_edges:
            raise ReconciliationError(f"duplicate blocker evidence edge: {edge}")
        blocker_edges.add(edge)

    hierarchy_edges: set[tuple[str, str]] = set()
    for index, record in enumerate(hierarchy):
        path = f"hierarchy.jsonl[{index}]"
        child_id = _require_reconciliation_string(
            record.get("child_id"),
            f"{path}.child_id",
        )
        parent_id = _require_reconciliation_string(
            record.get("parent_id"),
            f"{path}.parent_id",
        )
        if record.get("relationship") != "parent-child":
            raise ReconciliationError(f"{path}.relationship must be 'parent-child'")
        if child_id not in allowed_ids or parent_id not in allowed_ids:
            raise ReconciliationError(f"{path} has an endpoint outside the manifest")
        if not child_id.startswith(parent_id + "."):
            raise ReconciliationError(
                f"{path} contradicts the deterministic dotted hierarchy"
            )
        edge = (child_id, parent_id)
        if edge in hierarchy_edges:
            raise ReconciliationError(f"duplicate hierarchy evidence edge: {edge}")
        hierarchy_edges.add(edge)
    return blocker_edges, hierarchy_edges


def _validate_expected_artifacts(
    source_bytes: bytes,
    artifacts: Mapping[str, bytes],
    *,
    expected_source_sha256: str | None,
) -> tuple[
    Mapping[str, Any],
    list[Mapping[str, Any]],
    dict[str, Mapping[str, Any]],
    dict[str, str],
    set[tuple[str, str]],
    set[tuple[str, str]],
]:
    artifact_names = set(artifacts)
    expected_names = set(ARTIFACT_NAMES)
    if artifact_names != expected_names:
        missing = sorted(expected_names - artifact_names)
        unexpected = sorted(artifact_names - expected_names)
        raise ReconciliationError(
            f"artifact set is not exact; missing={missing}, unexpected={unexpected}"
        )
    for name in ARTIFACT_NAMES:
        if type(artifacts[name]) is not bytes:
            raise ReconciliationError(f"artifact {name} must be bytes")

    manifest = _load_json_object_bytes(artifacts["manifest.json"], "manifest.json")
    expected_issues = _load_jsonl_bytes(artifacts["issues.jsonl"], "issues.jsonl")
    blockers = _load_jsonl_bytes(artifacts["blockers.jsonl"], "blockers.jsonl")
    hierarchy = _load_jsonl_bytes(artifacts["hierarchy.jsonl"], "hierarchy.jsonl")

    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ReconciliationError(
            f"unsupported manifest schema: {manifest.get('schema_version')!r}"
        )
    if manifest.get("converter_version") != CONVERTER_VERSION:
        raise ReconciliationError(
            f"unsupported converter version: {manifest.get('converter_version')!r}"
        )
    target = _require_reconciliation_mapping(manifest.get("target"), "manifest.target")
    if target.get("system") != "beads" or target.get("version") != TARGET_BEADS_VERSION:
        raise ReconciliationError("manifest target does not match the locked Beads version")

    source_sha256 = _sha256_bytes(source_bytes)
    source = _require_reconciliation_mapping(manifest.get("source"), "manifest.source")
    digests = _require_reconciliation_mapping(
        manifest.get("digests"),
        "manifest.digests",
    )
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise ReconciliationError(
            "source SHA-256 mismatch: "
            f"expected {expected_source_sha256}, observed {source_sha256}"
        )
    if source.get("sha256") != source_sha256:
        raise ReconciliationError("manifest source SHA-256 does not match source bytes")
    if digests.get("source_sha256") != source_sha256:
        raise ReconciliationError(
            "manifest digest source SHA-256 does not match source bytes"
        )

    artifact_digests = {
        name: _sha256_bytes(artifacts[name])
        for name in ("issues.jsonl", "blockers.jsonl", "hierarchy.jsonl")
    }
    if digests.get("artifacts") != artifact_digests:
        raise ReconciliationError("persisted migration artifact digest mismatch")
    if digests.get("artifact_set_sha256") != _sha256_value(artifact_digests):
        raise ReconciliationError("migration artifact-set digest mismatch")

    manifest_core = dict(manifest)
    manifest_core.pop("digests", None)
    if digests.get("manifest_core_sha256") != _sha256_value(manifest_core):
        raise ReconciliationError("manifest core digest mismatch")

    id_map_value = manifest.get("id_map")
    id_map = _require_reconciliation_list(id_map_value, "manifest.id_map")
    if digests.get("id_map_sha256") != _sha256_value(id_map):
        raise ReconciliationError("manifest id-map digest mismatch")

    expected_by_id, expected_external_to_id = _index_issues(
        expected_issues,
        label="issues.jsonl",
    )
    manifest_by_id: dict[str, str] = {}
    manifest_external_refs: set[str] = set()
    manifest_source_ids: set[str] = set()
    for index, entry_value in enumerate(id_map):
        entry = _require_reconciliation_mapping(
            entry_value,
            f"manifest.id_map[{index}]",
        )
        source_id = _require_reconciliation_string(
            entry.get("source_id"),
            f"manifest.id_map[{index}].source_id",
        )
        bead_id = _require_reconciliation_string(
            entry.get("bead_id"),
            f"manifest.id_map[{index}].bead_id",
        )
        external_ref = _require_reconciliation_string(
            entry.get("external_ref"),
            f"manifest.id_map[{index}].external_ref",
        )
        if source_id in manifest_source_ids:
            raise ReconciliationError(f"duplicate manifest source_id: {source_id}")
        if bead_id in manifest_by_id:
            raise ReconciliationError(f"duplicate manifest bead_id: {bead_id}")
        if external_ref in manifest_external_refs:
            raise ReconciliationError(
                f"duplicate manifest external_ref: {external_ref}"
            )
        manifest_source_ids.add(source_id)
        manifest_external_refs.add(external_ref)
        manifest_by_id[bead_id] = external_ref

    expected_identity = {
        issue_id: str(issue["external_ref"])
        for issue_id, issue in expected_by_id.items()
    }
    if manifest_by_id != expected_identity:
        raise ReconciliationError("manifest id_map does not exactly match issues.jsonl")
    if set(expected_external_to_id) != manifest_external_refs:
        raise ReconciliationError("manifest external_ref population is not exact")

    counts = _require_reconciliation_mapping(manifest.get("counts"), "manifest.counts")
    if counts.get("issues") != len(expected_issues):
        raise ReconciliationError("manifest issue count does not match issues.jsonl")
    expected_status_counts = dict(
        sorted(collections.Counter(issue.get("status") for issue in expected_issues).items())
    )
    if counts.get("target_statuses") != expected_status_counts:
        raise ReconciliationError(
            "manifest target status counts do not match issues.jsonl"
        )
    expected_priority_counts = dict(
        sorted(
            collections.Counter(
                f"P{issue.get('priority')}" for issue in expected_issues
            ).items()
        )
    )
    if counts.get("effective_target_priorities") != expected_priority_counts:
        raise ReconciliationError("manifest priority counts do not match issues.jsonl")

    allowed_ids = set(expected_by_id)
    evidence_blockers, evidence_hierarchy = _relationship_evidence(
        blockers,
        hierarchy,
        allowed_ids=allowed_ids,
    )
    expected_blockers, expected_hierarchy = _dependency_sets(
        expected_issues,
        allowed_ids=allowed_ids,
        label="issues.jsonl",
    )
    if expected_blockers != evidence_blockers:
        raise ReconciliationError(
            "issues.jsonl blocker graph differs from blockers.jsonl"
        )
    if expected_hierarchy != evidence_hierarchy:
        raise ReconciliationError(
            "issues.jsonl hierarchy differs from hierarchy.jsonl"
        )
    if counts.get("blocker_relationships") != len(evidence_blockers):
        raise ReconciliationError("manifest blocker count does not match evidence")
    if counts.get("hierarchy_relationships") != len(evidence_hierarchy):
        raise ReconciliationError("manifest hierarchy count does not match evidence")
    if counts.get("total_dependency_relationships") != (
        len(evidence_blockers) + len(evidence_hierarchy)
    ):
        raise ReconciliationError(
            "manifest total relationship count does not match evidence"
        )

    semantic_digest = _sha256_value(_semantic_issue_projection(expected_issues))
    if digests.get("semantic_idempotency_projection_sha256") != semantic_digest:
        raise ReconciliationError("expected semantic projection digest mismatch")

    return (
        manifest,
        expected_issues,
        expected_by_id,
        expected_external_to_id,
        evidence_blockers,
        evidence_hierarchy,
    )


def verify_export(
    export_bytes: bytes,
    *,
    source_bytes: bytes,
    artifacts: Mapping[str, bytes],
    expected_source_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Verify that a complete Beads export is exactly the migration manifest.

    The export is treated as the complete target database population. Extra
    issues are contamination, even when they have no Taskmaster external
    reference. This prevents subset-only verification from approving a reused
    or incorrectly selected Dolt database.
    """

    (
        manifest,
        expected_issues,
        expected_by_id,
        expected_external_to_id,
        expected_blockers,
        expected_hierarchy,
    ) = _validate_expected_artifacts(
        source_bytes,
        artifacts,
        expected_source_sha256=expected_source_sha256,
    )
    exported_issues = _load_jsonl_bytes(export_bytes, "beads-export.jsonl")
    exported_by_id, exported_external_to_id = _index_issues(
        exported_issues,
        label="beads-export.jsonl",
    )

    expected_ids = set(expected_by_id)
    exported_ids = set(exported_by_id)
    expected_refs = set(expected_external_to_id)
    exported_refs = set(exported_external_to_id)
    if exported_ids != expected_ids or exported_refs != expected_refs:
        raise ReconciliationError(
            "contaminated target or incomplete export; "
            f"unexpected_ids={sorted(exported_ids - expected_ids)}, "
            f"missing_ids={sorted(expected_ids - exported_ids)}, "
            f"unexpected_external_refs={sorted(exported_refs - expected_refs)}, "
            f"missing_external_refs={sorted(expected_refs - exported_refs)}"
        )
    if len(exported_issues) != len(expected_issues):
        raise ReconciliationError(
            "contaminated target: exported row count is not the exact manifest count"
        )

    provenance_fields = (
        "mapping_schema",
        "converter_version",
        "source_system",
        "source_tag",
        "source_sha256",
        "source_id",
        "source_index",
        "source_record_sha256",
        "source_issue_projection_sha256",
        "source_status",
        "source_priority",
        "priority_source",
        "parent_source_id",
        "field_states",
        "optional_fields",
    )
    for issue_id in sorted(expected_ids):
        expected_issue = expected_by_id[issue_id]
        exported_issue = exported_by_id[issue_id]
        expected_ref = expected_issue["external_ref"]
        if exported_issue.get("external_ref") != expected_ref:
            raise ReconciliationError(f"{issue_id}: external_ref identity drift")
        if exported_external_to_id[str(expected_ref)] != issue_id:
            raise ReconciliationError(
                f"{issue_id}: external_ref is mapped to another issue"
            )
        for field in ("status", "priority"):
            if not _exact_value_matches(
                exported_issue.get(field),
                expected_issue.get(field),
            ):
                raise ReconciliationError(f"{issue_id}: {field} mapping drift")
        if exported_issue.get("source_system") != "taskmaster":
            raise ReconciliationError(f"{issue_id}: source_system provenance drift")

        expected_metadata = _require_reconciliation_mapping(
            expected_issue.get("metadata"),
            f"{issue_id}.expected.metadata",
        )
        exported_metadata = _require_reconciliation_mapping(
            exported_issue.get("metadata"),
            f"{issue_id}.metadata",
        )
        expected_migration = _require_reconciliation_mapping(
            expected_metadata.get("migration"),
            f"{issue_id}.expected.metadata.migration",
        )
        exported_migration = _require_reconciliation_mapping(
            exported_metadata.get("migration"),
            f"{issue_id}.metadata.migration",
        )
        for field in provenance_fields:
            if not _exact_value_matches(
                exported_migration.get(field),
                expected_migration.get(field),
            ):
                raise ReconciliationError(
                    f"{issue_id}: migration provenance drift in {field}"
                )

    exported_blockers, exported_hierarchy = _dependency_sets(
        exported_issues,
        allowed_ids=expected_ids,
        label="beads-export.jsonl",
    )
    if exported_blockers != expected_blockers:
        raise ReconciliationError(
            "exported blocker graph does not match the manifest"
        )
    if exported_hierarchy != expected_hierarchy:
        raise ReconciliationError(
            "exported hierarchy graph does not match the manifest"
        )

    semantic_projection = _semantic_issue_projection(exported_issues)
    semantic_digest = _sha256_value(semantic_projection)
    manifest_digests = _require_reconciliation_mapping(
        manifest.get("digests"),
        "manifest.digests",
    )
    expected_semantic_digest = manifest_digests.get(
        "semantic_idempotency_projection_sha256"
    )
    if semantic_digest != expected_semantic_digest:
        raise ReconciliationError(
            "exported semantic projection drift: "
            f"expected {expected_semantic_digest}, observed {semantic_digest}"
        )

    status_counts = collections.Counter(
        str(issue["status"]) for issue in exported_issues
    )
    priority_counts = collections.Counter(
        f"P{issue['priority']}" for issue in exported_issues
    )
    source_sha256 = _sha256_bytes(source_bytes)
    return {
        "schema_version": RECONCILIATION_SCHEMA,
        "status": "pass",
        "source_sha256": source_sha256,
        "export_sha256": _sha256_bytes(export_bytes),
        "semantic_projection_sha256": semantic_digest,
        "manifest_core_sha256": manifest_digests["manifest_core_sha256"],
        "counts": {
            "exported_issues_total": len(exported_issues),
            "manifest_issues_total": len(expected_issues),
            "unique_ids": len(exported_by_id),
            "unique_external_refs": len(exported_external_to_id),
            "blocker_relationships": len(exported_blockers),
            "hierarchy_relationships": len(exported_hierarchy),
            "provenance_rows": len(exported_issues),
            "non_manifest_issues": 0,
            "non_manifest_external_refs": 0,
        },
        "status_counts": dict(sorted(status_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
    }


def reconcile_export(
    source_bytes: bytes,
    export_bytes: bytes,
    *,
    tag: str = "master",
    prefix: str = DEFAULT_PREFIX,
    expected_source_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Regenerate migration evidence and exactly reconcile one Beads export."""

    conversion = build_artifacts(
        source_bytes,
        tag=tag,
        prefix=prefix,
        expected_source_sha256=expected_source_sha256,
    )
    return verify_export(
        export_bytes,
        source_bytes=source_bytes,
        artifacts=conversion.artifacts,
        expected_source_sha256=expected_source_sha256,
    )


_SENSITIVE_ARG_FLAGS = {
    "-p",
    "--password",
    "--passwd",
    "--token",
    "--api-key",
    "--apikey",
}


def _reject_sensitive_argv(argv: Sequence[str]) -> None:
    for argument in argv:
        normalized = argument.lower()
        if normalized in _SENSITIVE_ARG_FLAGS or any(
            normalized.startswith(flag + "=")
            for flag in _SENSITIVE_ARG_FLAGS
            if flag.startswith("--")
        ):
            raise OperationalMigrationError(
                "credential-bearing command arguments are forbidden"
            )


def _run_migration_command(
    runner: MigrationCommandRunner,
    argv: Sequence[str],
    *,
    step: str,
    stdin: bytes | None = None,
) -> CommandResult:
    if not argv or any(type(argument) is not str or not argument for argument in argv):
        raise OperationalMigrationError(f"{step} has an invalid argument vector")
    _reject_sensitive_argv(argv)
    try:
        result = runner.run(tuple(argv), stdin=stdin)
    except Exception:
        raise OperationalMigrationError(f"{step} could not execute") from None
    if (
        type(result) is not CommandResult
        or type(result.returncode) is not int
        or type(result.stdout) is not bytes
        or type(result.stderr) is not bytes
    ):
        raise OperationalMigrationError(f"{step} returned an invalid command result")
    if result.returncode != 0:
        # Command output is deliberately not copied into the exception. Provider
        # and database CLIs may echo environment-derived connection details.
        raise OperationalMigrationError(
            f"{step} failed with exit code {result.returncode}"
        )
    return result


def _parse_command_object(result: CommandResult, *, step: str) -> Mapping[str, Any]:
    try:
        return _load_json_object_bytes(result.stdout, f"{step} output")
    except ReconciliationError:
        raise OperationalMigrationError(f"{step} returned invalid JSON") from None


def _require_command_int(value: Mapping[str, Any], field: str, *, step: str) -> int:
    observed = value.get(field)
    if type(observed) is not int or observed < 0:
        raise OperationalMigrationError(
            f"{step} returned an invalid {field} count"
        )
    return observed


def _require_command_id_list(
    value: Mapping[str, Any],
    field: str,
    *,
    step: str,
    required: bool,
) -> list[str]:
    if field not in value:
        if required:
            raise OperationalMigrationError(f"{step} omitted {field}")
        return []
    rows = value[field]
    if type(rows) is not list or any(type(item) is not str or not item for item in rows):
        raise OperationalMigrationError(f"{step} returned invalid {field}")
    if len(set(rows)) != len(rows):
        raise OperationalMigrationError(f"{step} returned duplicate IDs in {field}")
    return rows


def _validate_import_result(
    value: Mapping[str, Any],
    *,
    step: str,
    mode: str,
    expected_ids: set[str],
) -> Mapping[str, Any]:
    issue_count = len(expected_ids)
    created = _require_command_int(value, "created", step=step)
    skipped = _require_command_int(value, "skipped", step=step)
    ids = _require_command_id_list(
        value,
        "ids",
        step=step,
        required=mode in {"first", "second"},
    )
    stale = _require_command_id_list(
        value,
        "stale_skipped_ids",
        step=step,
        required=False,
    )
    ties = _require_command_id_list(
        value,
        "tie_kept_local_ids",
        step=step,
        required=False,
    )
    updated = value.get("updated_issues", [])
    if type(updated) is not list:
        raise OperationalMigrationError(f"{step} returned invalid updated_issues")
    if updated:
        raise OperationalMigrationError(f"{step} unexpectedly updated existing issues")

    if mode == "dry-run":
        if value.get("dry_run") is not True:
            raise OperationalMigrationError("dry-run import did not confirm dry_run=true")
        if created != issue_count or skipped != 0:
            raise OperationalMigrationError(
                "dry-run import count drift from the frozen manifest"
            )
        if ids or stale or ties:
            raise OperationalMigrationError(
                "dry-run import unexpectedly classified existing issues"
            )
    elif mode == "first":
        if created != issue_count or skipped != 0:
            raise OperationalMigrationError(
                "first import count drift from the frozen manifest"
            )
        if set(ids) != expected_ids or len(ids) != issue_count:
            raise OperationalMigrationError(
                "first import identity set does not match the manifest"
            )
        if stale or ties:
            raise OperationalMigrationError(
                "first import unexpectedly encountered existing issues"
            )
    elif mode == "second":
        # Beads 1.1.0 reports every accepted upsert as ``created`` even when
        # timestamp ties preserve every local column. The authoritative no-op
        # proofs therefore remain the byte-exact export and Dolt HEAD checks
        # below, while this response check proves the complete identity set was
        # processed without stale/tie classifications or field updates.
        if created != issue_count or skipped != 0:
            raise OperationalMigrationError(
                "second import count drift from the idempotent contract"
            )
        if set(ids) != expected_ids or len(ids) != issue_count:
            raise OperationalMigrationError(
                "second import identity set does not match the manifest"
            )
        if stale or ties:
            raise OperationalMigrationError(
                "second import unexpectedly classified existing issues"
            )
    else:  # pragma: no cover - internal programming guard.
        raise OperationalMigrationError(f"unknown import validation mode: {mode}")

    return {
        "schema_version": value.get("schema_version"),
        "created": created,
        "skipped": skipped,
        "dry_run": value.get("dry_run") is True,
        "ids_count": len(ids),
        "stale_skipped_ids_count": len(stale),
        "tie_kept_local_ids_count": len(ties),
        "updated_issues_count": len(updated),
    }


def _validate_dolt_connection(connection: DoltConnection) -> None:
    if (
        type(connection.host) is not str
        or not connection.host
        or any(character.isspace() or ord(character) < 32 for character in connection.host)
    ):
        raise OperationalMigrationError("Dolt host is invalid")
    if type(connection.port) is not int or not 1 <= connection.port <= 65535:
        raise OperationalMigrationError("Dolt port is invalid")
    for label, value in (
        ("user", connection.user),
        ("database", connection.database),
    ):
        if type(value) is not str or re.fullmatch(r"[A-Za-z0-9_]+", value) is None:
            raise OperationalMigrationError(f"Dolt {label} is invalid")
    if type(connection.no_tls) is not bool:
        raise OperationalMigrationError("Dolt no_tls must be boolean")


def _dolt_main_head(
    runner: MigrationCommandRunner,
    *,
    executable: str,
    connection: DoltConnection,
    step: str,
) -> str:
    argv = [
        executable,
        "--host",
        connection.host,
        "--port",
        str(connection.port),
        "--user",
        connection.user,
        "--use-db",
        connection.database,
    ]
    if connection.no_tls:
        argv.append("--no-tls")
    argv.extend(
        [
            "sql",
            "--result-format",
            "json",
            "--query",
            "SELECT HASHOF('main') AS head;",
        ]
    )
    result = _run_migration_command(runner, argv, step=step)
    value = _parse_command_object(result, step=step)
    rows = value.get("rows")
    if type(rows) is not list or len(rows) != 1 or type(rows[0]) is not dict:
        raise OperationalMigrationError(f"{step} did not return one main-head row")
    head = rows[0].get("head")
    if type(head) is not str or re.fullmatch(r"[a-z0-9]{20,128}", head) is None:
        raise OperationalMigrationError(f"{step} returned an invalid main head")
    return head


def _dolt_empty_target_attestation(
    runner: MigrationCommandRunner,
    *,
    executable: str,
    connection: DoltConnection,
) -> Mapping[str, int]:
    """Prove the initialized target has one clean branch and no issue rows."""

    return _dolt_target_state_attestation(
        runner,
        executable=executable,
        connection=connection,
        expected_issue_count=0,
        step="empty-target Dolt attestation",
    )


def _dolt_target_state_attestation(
    runner: MigrationCommandRunner,
    *,
    executable: str,
    connection: DoltConnection,
    expected_issue_count: int,
    step: str,
) -> Mapping[str, int]:
    """Capture the complete stable state relevant to migration reconciliation."""

    if type(expected_issue_count) is not int or expected_issue_count < 0:
        raise OperationalMigrationError("expected issue count is invalid")
    if type(step) is not str or not step:
        raise OperationalMigrationError("Dolt attestation step is invalid")

    query = (
        "SELECT "
        "(SELECT COUNT(*) FROM issues) AS issue_count, "
        "(SELECT COUNT(*) FROM dolt_status) AS working_set_changes, "
        "(SELECT COUNT(*) FROM dolt_status "
        "WHERE table_name = 'config' AND status = 'modified' AND staged = 0) "
        "AS expected_config_changes, "
        "(SELECT COUNT(*) FROM dolt_status "
        "WHERE NOT (table_name = 'config' AND status = 'modified' AND staged = 0)) "
        "AS unexpected_working_changes, "
        "(SELECT COUNT(*) FROM dolt_branches) AS branch_count, "
        "(SELECT COUNT(*) FROM dolt_branches WHERE name = 'main') AS main_branch_count, "
        "(SELECT COUNT(*) FROM dolt_log) AS commit_count;"
    )
    argv = [
        executable,
        "--host",
        connection.host,
        "--port",
        str(connection.port),
        "--user",
        connection.user,
        "--use-db",
        connection.database,
    ]
    if connection.no_tls:
        argv.append("--no-tls")
    argv.extend(["sql", "--result-format", "json", "--query", query])
    value = _parse_command_object(
        _run_migration_command(runner, argv, step=step),
        step=step,
    )
    rows = value.get("rows")
    if type(rows) is not list or len(rows) != 1 or type(rows[0]) is not dict:
        raise OperationalMigrationError(f"{step} did not return one row")
    expected = {
        "issue_count": expected_issue_count,
        # Beads 1.1.0 leaves exactly its config table modified after server-mode
        # initialization. The first auto-committed import deliberately captures
        # this pinned bootstrap state together with the migrated issues.
        "working_set_changes": 1,
        "expected_config_changes": 1,
        "unexpected_working_changes": 0,
        "branch_count": 1,
        "main_branch_count": 1,
    }
    observed: dict[str, int] = {}
    for name in (*expected, "commit_count"):
        raw = rows[0].get(name)
        if type(raw) is int:
            normalized = raw
        elif type(raw) is str and re.fullmatch(r"[0-9]+", raw):
            normalized = int(raw)
        else:
            raise OperationalMigrationError(f"{step} returned invalid {name}")
        observed[name] = normalized
    if any(observed[name] != required for name, required in expected.items()):
        raise OperationalMigrationError(
            f"{step} found an unexpected issue count, unexpected working changes, "
            "or extra branches"
        )
    if observed["commit_count"] < 1:
        raise OperationalMigrationError(f"{step} found no initialized schema history")
    return observed


def _exact_export_verification(
    export_bytes: bytes,
    *,
    source_bytes: bytes,
    conversion: ConversionResult,
    source_sha256: str,
    step: str,
) -> Mapping[str, Any]:
    try:
        return verify_export(
            export_bytes,
            source_bytes=source_bytes,
            artifacts=conversion.artifacts,
            expected_source_sha256=source_sha256,
        )
    except ReconciliationError:
        raise OperationalMigrationError(
            f"{step} failed exact export reconciliation"
        ) from None


def _canonical_operational_export(export_bytes: bytes, *, step: str) -> bytes:
    """Canonicalize Beads export order without discarding authoritative fields.

    Beads 1.1.0 can reorder a dependency array after an otherwise no-op upsert
    while leaving Dolt ``main`` unchanged. Dependency order has no graph
    semantics, so records are ordered by ID and dependencies by their complete
    canonical JSON value. Every field and dependency byte value is retained.
    """

    try:
        records = _load_jsonl_bytes(export_bytes, f"{step} export")
    except ReconciliationError:
        raise OperationalMigrationError(f"{step} export is invalid JSONL") from None
    normalized: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identity = record.get("id")
        if type(identity) is not str or not identity:
            raise OperationalMigrationError(f"{step} export contains an invalid ID")
        if identity in normalized:
            raise OperationalMigrationError(f"{step} export contains a duplicate ID")
        copy = dict(record)
        dependencies = copy.get("dependencies")
        if dependencies is not None:
            if type(dependencies) is not list or any(
                type(dependency) is not dict for dependency in dependencies
            ):
                raise OperationalMigrationError(
                    f"{step} export contains invalid dependencies"
                )
            copy["dependencies"] = sorted(
                dependencies,
                key=_canonical_json_bytes,
            )
        normalized[identity] = copy
    return _jsonl_bytes(normalized[identity] for identity in sorted(normalized))


def _validated_locked_toolchain(
    value: Mapping[str, Any],
    *,
    bd_executable: str,
    dolt_executable: str,
) -> Mapping[str, Any]:
    """Validate the trusted lock attestation supplied by the operator boundary."""

    if type(value) is not dict or set(value) != {
        "schema_version",
        "runtime_lock_path",
        "runtime_lock_sha256",
        "tools",
    }:
        raise OperationalMigrationError("locked toolchain attestation fields are not exact")
    lock_path = value.get("runtime_lock_path")
    lock_digest = value.get("runtime_lock_sha256")
    tools = value.get("tools")
    if (
        value.get("schema_version") != LOCKED_TOOLCHAIN_SCHEMA
        or type(lock_path) is not str
        or not Path(lock_path).is_absolute()
        or type(lock_digest) is not str
        or re.fullmatch(r"[0-9a-f]{64}", lock_digest) is None
        or type(tools) is not dict
        or set(tools) != {"bd", "dolt"}
    ):
        raise OperationalMigrationError("locked toolchain attestation is invalid")
    expected = {
        "bd": (bd_executable, TARGET_BEADS_VERSION),
        "dolt": (dolt_executable, TARGET_DOLT_VERSION),
    }
    normalized: dict[str, Any] = {}
    for name, (executable, version) in expected.items():
        record = tools.get(name)
        if (
            type(record) is not dict
            or set(record) != {"path", "version", "binary_sha256"}
            or record.get("path") != executable
            or not Path(executable).is_absolute()
            or record.get("version") != version
            or type(record.get("binary_sha256")) is not str
            or re.fullmatch(r"[0-9a-f]{64}", record["binary_sha256"]) is None
        ):
            raise OperationalMigrationError(
                f"locked toolchain attestation does not bind the exact {name} executable"
            )
        normalized[name] = dict(record)
    return {
        "schema_version": LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock_path,
        "runtime_lock_sha256": lock_digest,
        "tools": normalized,
    }


def run_operational_migration(
    source_bytes: bytes,
    *,
    expected_source_sha256: str,
    target_directory: Path,
    dolt: DoltConnection,
    runner: MigrationCommandRunner,
    locked_toolchain: Mapping[str, Any],
    tag: str = "master",
    prefix: str = DEFAULT_PREFIX,
    bd_executable: str = "bd",
    dolt_executable: str = "dolt",
    evidence_sink: MigrationEvidenceSink | None = None,
) -> OperationalMigrationResult:
    """Execute the guarded two-pass Taskmaster-to-Beads migration.

    The caller must construct the command runner with Beads and Dolt
    credentials in its environment. This function never accepts credentials,
    writes artifact files itself, or places secret material in command arguments
    or reports. When supplied, ``evidence_sink`` is called before and after each
    mutating boundary so the operator can retain immutable recovery evidence even
    if a later reconciliation step fails.
    """

    if type(source_bytes) is not bytes:
        raise OperationalMigrationError("frozen Taskmaster snapshot must be bytes")
    if re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256) is None:
        raise OperationalMigrationError("expected source SHA-256 is invalid")
    if type(bd_executable) is not str or not bd_executable:
        raise OperationalMigrationError("bd executable is invalid")
    if type(dolt_executable) is not str or not dolt_executable:
        raise OperationalMigrationError("Dolt executable is invalid")
    toolchain = _validated_locked_toolchain(
        locked_toolchain,
        bd_executable=bd_executable,
        dolt_executable=dolt_executable,
    )
    _validate_dolt_connection(dolt)

    target_path = Path(target_directory)
    if not target_path.is_absolute():
        raise OperationalMigrationError("Beads target directory must be absolute")
    try:
        target_path = target_path.resolve(strict=True)
    except OSError:
        raise OperationalMigrationError("Beads target directory does not exist") from None
    if not target_path.is_dir() or not (target_path / ".beads").is_dir():
        raise OperationalMigrationError(
            "Beads target must be an initialized project with a .beads directory"
        )

    # Conversion and the caller-supplied freeze hash are validated before any
    # target command can run.
    conversion = build_artifacts(
        source_bytes,
        tag=tag,
        prefix=prefix,
        expected_source_sha256=expected_source_sha256,
    )
    if evidence_sink is not None:
        for artifact_name in ARTIFACT_NAMES:
            evidence_sink(
                f"conversion/{artifact_name}",
                conversion.artifacts[artifact_name],
            )
    issue_count = conversion.manifest["counts"]["issues"]
    if type(issue_count) is not int or issue_count <= 0:
        raise OperationalMigrationError("conversion produced an invalid issue count")
    expected_ids = {
        str(entry["bead_id"]) for entry in conversion.manifest["id_map"]
    }
    if len(expected_ids) != issue_count:
        raise OperationalMigrationError(
            "conversion manifest does not contain an exact identity set"
        )
    issues_jsonl = conversion.artifacts["issues.jsonl"]

    version_result = _run_migration_command(
        runner,
        [bd_executable, "--version"],
        step="Beads version preflight",
    )
    try:
        version_text = version_result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise OperationalMigrationError(
            "Beads version preflight returned invalid UTF-8"
        ) from None
    if re.fullmatch(r"bd version 1\.1\.0 \([0-9a-f]+\)", version_text) is None:
        raise OperationalMigrationError("Beads version preflight did not match 1.1.0")
    dolt_version_result = _run_migration_command(
        runner,
        [dolt_executable, "version"],
        step="Dolt version preflight",
    )
    try:
        dolt_version_text = dolt_version_result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise OperationalMigrationError(
            "Dolt version preflight returned invalid UTF-8"
        ) from None
    if dolt_version_text != f"dolt version {TARGET_DOLT_VERSION}":
        raise OperationalMigrationError(
            f"Dolt version preflight did not match {TARGET_DOLT_VERSION}"
        )

    export_argv = [
        bd_executable,
        "--readonly",
        "-C",
        str(target_path),
        "export",
        "--all",
    ]
    preflight_export = _run_migration_command(
        runner,
        export_argv,
        step="empty-target export preflight",
    ).stdout
    try:
        preexisting = _load_jsonl_bytes(preflight_export, "preflight export")
    except ReconciliationError:
        raise OperationalMigrationError(
            "empty-target export preflight returned invalid JSONL"
        ) from None
    if preexisting:
        raise OperationalMigrationError(
            "empty-target export preflight found a contaminated target"
        )
    preflight_attestation = _dolt_empty_target_attestation(
        runner,
        executable=dolt_executable,
        connection=dolt,
    )
    if evidence_sink is not None:
        evidence_sink(
            "checkpoints/empty-target.json",
            _pretty_json_bytes(
                {
                    "schema_version": MIGRATION_RUN_SCHEMA,
                    "status": "pass",
                    "phase": "empty-target",
                    **preflight_attestation,
                }
            ),
        )
    preflight_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="preflight Dolt main-head capture",
    )

    import_base = [
        bd_executable,
        "--json",
        "--dolt-auto-commit",
        "on",
        "-C",
        str(target_path),
        "import",
    ]
    dry_run_value = _parse_command_object(
        _run_migration_command(
            runner,
            [*import_base, "--dry-run", "-"],
            step="Beads import dry-run",
            stdin=issues_jsonl,
        ),
        step="Beads import dry-run",
    )
    dry_run_summary = _validate_import_result(
        dry_run_value,
        step="Beads import dry-run",
        mode="dry-run",
        expected_ids=expected_ids,
    )
    post_dry_run_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="post-dry-run Dolt main-head capture",
    )
    if post_dry_run_head != preflight_head:
        raise OperationalMigrationError("Beads import dry-run changed the Dolt main head")

    first_import_value = _parse_command_object(
        _run_migration_command(
            runner,
            [*import_base, "-"],
            step="first Beads import",
            stdin=issues_jsonl,
        ),
        step="first Beads import",
    )
    first_import_summary = _validate_import_result(
        first_import_value,
        step="first Beads import",
        mode="first",
        expected_ids=expected_ids,
    )

    first_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="first Dolt main-head capture",
    )
    if first_head == preflight_head:
        raise OperationalMigrationError(
            "first Beads import did not advance the Dolt main head"
        )
    if evidence_sink is not None:
        evidence_sink(
            "checkpoints/first-import.json",
            _pretty_json_bytes(
                {
                    "schema_version": MIGRATION_RUN_SCHEMA,
                    "status": "mutation-observed",
                    "phase": "first-import",
                    "source_sha256": expected_source_sha256,
                    "preflight_dolt_main_head": preflight_head,
                    "first_dolt_main_head": first_head,
                    "import": first_import_summary,
                }
            ),
        )

    first_export = _run_migration_command(
        runner,
        export_argv,
        step="first post-import export",
    ).stdout
    if evidence_sink is not None:
        evidence_sink("exports/first.jsonl", first_export)
    first_verification = _exact_export_verification(
        first_export,
        source_bytes=source_bytes,
        conversion=conversion,
        source_sha256=expected_source_sha256,
        step="first post-import export",
    )
    first_canonical_export = _canonical_operational_export(
        first_export,
        step="first post-import",
    )
    second_import_value = _parse_command_object(
        _run_migration_command(
            runner,
            [*import_base, "-"],
            step="second Beads import",
            stdin=issues_jsonl,
        ),
        step="second Beads import",
    )
    second_import_summary = _validate_import_result(
        second_import_value,
        step="second Beads import",
        mode="second",
        expected_ids=expected_ids,
    )

    final_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="second Dolt main-head capture",
    )
    if evidence_sink is not None:
        evidence_sink(
            "checkpoints/second-import.json",
            _pretty_json_bytes(
                {
                    "schema_version": MIGRATION_RUN_SCHEMA,
                    "status": "mutation-observed",
                    "phase": "second-import",
                    "source_sha256": expected_source_sha256,
                    "first_dolt_main_head": first_head,
                    "final_dolt_main_head": final_head,
                    "import": second_import_summary,
                }
            ),
        )

    final_export = _run_migration_command(
        runner,
        export_argv,
        step="second post-import export",
    ).stdout
    if evidence_sink is not None:
        evidence_sink("exports/final.jsonl", final_export)
    final_verification = _exact_export_verification(
        final_export,
        source_bytes=source_bytes,
        conversion=conversion,
        source_sha256=expected_source_sha256,
        step="second post-import export",
    )
    final_canonical_export = _canonical_operational_export(
        final_export,
        step="second post-import",
    )
    if first_canonical_export != final_canonical_export:
        raise OperationalMigrationError(
            "second import changed the byte-exact canonical Beads export"
        )
    if first_head != final_head:
        raise OperationalMigrationError(
            "second import changed the Dolt main head"
        )

    export_sha256 = _sha256_bytes(final_canonical_export)
    report: Mapping[str, Any] = {
        "schema_version": MIGRATION_RUN_SCHEMA,
        "status": "pass",
        "source": {
            "sha256": expected_source_sha256,
            "tag": tag,
        },
        "target": {
            "directory": str(target_path),
            "database": dolt.database,
            "beads_version": TARGET_BEADS_VERSION,
        },
        "locked_toolchain": toolchain,
        "counts": {
            "preexisting_records": 0,
            "manifest_issues": issue_count,
            "blocker_relationships": conversion.manifest["counts"][
                "blocker_relationships"
            ],
            "hierarchy_relationships": conversion.manifest["counts"][
                "hierarchy_relationships"
            ],
        },
        "artifact_digests": conversion.manifest["digests"],
        "empty_target_attestation": preflight_attestation,
        "dry_run": dry_run_summary,
        "first_import": first_import_summary,
        "first_verification": first_verification,
        "second_import": second_import_summary,
        "final_verification": final_verification,
        "idempotency": {
            "status": "pass",
            "canonical_export_sha256": export_sha256,
            "first_raw_export_sha256": _sha256_bytes(first_export),
            "final_raw_export_sha256": _sha256_bytes(final_export),
            "preflight_dolt_main_head": preflight_head,
            "post_dry_run_dolt_main_head": post_dry_run_head,
            "first_dolt_main_head": first_head,
            "final_dolt_main_head": final_head,
            "dry_run_head_unchanged": True,
            "first_import_advanced_main": True,
            "export_unchanged": True,
            "raw_export_unchanged": first_export == final_export,
            "dolt_main_head_unchanged": True,
        },
        "credential_transport": "runner-environment-only",
    }
    return OperationalMigrationResult(
        conversion=conversion,
        first_export=first_export,
        final_export=final_export,
        report=report,
    )


def run_operational_reconciliation(
    source_bytes: bytes,
    *,
    expected_source_sha256: str,
    target_directory: Path,
    dolt: DoltConnection,
    runner: MigrationCommandRunner,
    locked_toolchain: Mapping[str, Any],
    tag: str = "master",
    prefix: str = DEFAULT_PREFIX,
    bd_executable: str = "bd",
    dolt_executable: str = "dolt",
    evidence_sink: MigrationEvidenceSink | None = None,
) -> OperationalMigrationResult:
    """Prove an existing migration is exact without mutating its Dolt state.

    This is intentionally distinct from the one-way empty-target migration.
    It accepts only the exact graph re-derived from the frozen Taskmaster
    snapshot, performs a pinned bd dry-run through standard input, and proves
    the Dolt head, working set, branch set, and canonical export are unchanged
    before returning a repeatable zero-mutation receipt.
    """

    if type(source_bytes) is not bytes:
        raise OperationalMigrationError("frozen Taskmaster snapshot must be bytes")
    if re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256) is None:
        raise OperationalMigrationError("expected source SHA-256 is invalid")
    if type(bd_executable) is not str or not bd_executable:
        raise OperationalMigrationError("bd executable is invalid")
    if type(dolt_executable) is not str or not dolt_executable:
        raise OperationalMigrationError("Dolt executable is invalid")
    toolchain = _validated_locked_toolchain(
        locked_toolchain,
        bd_executable=bd_executable,
        dolt_executable=dolt_executable,
    )
    _validate_dolt_connection(dolt)

    target_path = Path(target_directory)
    if not target_path.is_absolute():
        raise OperationalMigrationError("Beads target directory must be absolute")
    try:
        target_path = target_path.resolve(strict=True)
    except OSError:
        raise OperationalMigrationError("Beads target directory does not exist") from None
    if not target_path.is_dir() or not (target_path / ".beads").is_dir():
        raise OperationalMigrationError(
            "Beads target must be an initialized project with a .beads directory"
        )

    conversion = build_artifacts(
        source_bytes,
        tag=tag,
        prefix=prefix,
        expected_source_sha256=expected_source_sha256,
    )
    if evidence_sink is not None:
        for artifact_name in ARTIFACT_NAMES:
            evidence_sink(f"conversion/{artifact_name}", conversion.artifacts[artifact_name])
    issue_count = conversion.manifest["counts"]["issues"]
    if type(issue_count) is not int or issue_count <= 0:
        raise OperationalMigrationError("conversion produced an invalid issue count")
    expected_ids = {str(entry["bead_id"]) for entry in conversion.manifest["id_map"]}
    if len(expected_ids) != issue_count:
        raise OperationalMigrationError(
            "conversion manifest does not contain an exact identity set"
        )

    version_result = _run_migration_command(
        runner,
        [bd_executable, "--version"],
        step="Beads reconciliation version preflight",
    )
    try:
        version_text = version_result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise OperationalMigrationError(
            "Beads reconciliation version preflight returned invalid UTF-8"
        ) from None
    if re.fullmatch(r"bd version 1\.1\.0 \([0-9a-f]+\)", version_text) is None:
        raise OperationalMigrationError("Beads reconciliation requires exact bd 1.1.0")
    dolt_version_result = _run_migration_command(
        runner,
        [dolt_executable, "version"],
        step="Dolt reconciliation version preflight",
    )
    try:
        dolt_version_text = dolt_version_result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise OperationalMigrationError(
            "Dolt reconciliation version preflight returned invalid UTF-8"
        ) from None
    if dolt_version_text != f"dolt version {TARGET_DOLT_VERSION}":
        raise OperationalMigrationError(
            f"Dolt reconciliation requires exact Dolt {TARGET_DOLT_VERSION}"
        )

    before_state = _dolt_target_state_attestation(
        runner,
        executable=dolt_executable,
        connection=dolt,
        expected_issue_count=issue_count,
        step="pre-reconciliation Dolt attestation",
    )
    before_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="pre-reconciliation Dolt main-head capture",
    )
    export_argv = [
        bd_executable,
        "--readonly",
        "-C",
        str(target_path),
        "export",
        "--all",
    ]
    first_export = _run_migration_command(
        runner,
        export_argv,
        step="pre-reconciliation Beads export",
    ).stdout
    first_verification = _exact_export_verification(
        first_export,
        source_bytes=source_bytes,
        conversion=conversion,
        source_sha256=expected_source_sha256,
        step="pre-reconciliation Beads export",
    )
    first_canonical = _canonical_operational_export(
        first_export,
        step="pre-reconciliation",
    )
    if evidence_sink is not None:
        evidence_sink("exports/first.jsonl", first_export)
        evidence_sink(
            "checkpoints/preflight-state.json",
            _pretty_json_bytes(
                {
                    "schema_version": RECONCILIATION_RUN_SCHEMA,
                    "status": "exact",
                    "phase": "preflight",
                    "source_sha256": expected_source_sha256,
                    "dolt_main_head": before_head,
                    "state": before_state,
                }
            ),
        )

    issues_jsonl = conversion.artifacts["issues.jsonl"]
    dry_run_value = _parse_command_object(
        _run_migration_command(
            runner,
            [
                bd_executable,
                "--json",
                "--dolt-auto-commit",
                "on",
                "-C",
                str(target_path),
                "import",
                "--dry-run",
                "-",
            ],
            step="reconciliation Beads import dry-run",
            stdin=issues_jsonl,
        ),
        step="reconciliation Beads import dry-run",
    )
    dry_run_summary = _validate_import_result(
        dry_run_value,
        step="reconciliation Beads import dry-run",
        mode="dry-run",
        expected_ids=expected_ids,
    )
    post_dry_state = _dolt_target_state_attestation(
        runner,
        executable=dolt_executable,
        connection=dolt,
        expected_issue_count=issue_count,
        step="post-dry-run Dolt attestation",
    )
    post_dry_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="post-dry-run Dolt main-head capture",
    )
    if post_dry_state != before_state or post_dry_head != before_head:
        raise OperationalMigrationError(
            "reconciliation dry-run changed the Dolt head or working state"
        )
    if evidence_sink is not None:
        evidence_sink(
            "checkpoints/post-dry-run-state.json",
            _pretty_json_bytes(
                {
                    "schema_version": RECONCILIATION_RUN_SCHEMA,
                    "status": "unchanged",
                    "phase": "post-dry-run",
                    "source_sha256": expected_source_sha256,
                    "dolt_main_head": post_dry_head,
                    "state": post_dry_state,
                    "dry_run": dry_run_summary,
                }
            ),
        )

    final_export = _run_migration_command(
        runner,
        export_argv,
        step="final reconciliation Beads export",
    ).stdout
    final_verification = _exact_export_verification(
        final_export,
        source_bytes=source_bytes,
        conversion=conversion,
        source_sha256=expected_source_sha256,
        step="final reconciliation Beads export",
    )
    final_canonical = _canonical_operational_export(
        final_export,
        step="final reconciliation",
    )
    final_state = _dolt_target_state_attestation(
        runner,
        executable=dolt_executable,
        connection=dolt,
        expected_issue_count=issue_count,
        step="final reconciliation Dolt attestation",
    )
    final_head = _dolt_main_head(
        runner,
        executable=dolt_executable,
        connection=dolt,
        step="final reconciliation Dolt main-head capture",
    )
    if final_state != before_state or final_head != before_head:
        raise OperationalMigrationError(
            "reconciliation changed the Dolt head or working state"
        )
    if final_canonical != first_canonical:
        raise OperationalMigrationError("reconciliation changed the canonical Beads export")
    if evidence_sink is not None:
        evidence_sink("exports/final.jsonl", final_export)
        evidence_sink(
            "checkpoints/final-state.json",
            _pretty_json_bytes(
                {
                    "schema_version": RECONCILIATION_RUN_SCHEMA,
                    "status": "unchanged",
                    "phase": "final",
                    "source_sha256": expected_source_sha256,
                    "dolt_main_head": final_head,
                    "state": final_state,
                }
            ),
        )

    canonical_sha256 = _sha256_bytes(final_canonical)
    report: Mapping[str, Any] = {
        "schema_version": RECONCILIATION_RUN_SCHEMA,
        "status": "pass",
        "action": "already-reconciled",
        "source": {"sha256": expected_source_sha256, "tag": tag},
        "target": {
            "directory": str(target_path),
            "database": dolt.database,
            "beads_version": TARGET_BEADS_VERSION,
        },
        "locked_toolchain": toolchain,
        "counts": {
            "preexisting_records": issue_count,
            "manifest_issues": issue_count,
            "blocker_relationships": conversion.manifest["counts"]["blocker_relationships"],
            "hierarchy_relationships": conversion.manifest["counts"]["hierarchy_relationships"],
        },
        "artifact_digests": conversion.manifest["digests"],
        "state_before": before_state,
        "state_after_dry_run": post_dry_state,
        "state_after": final_state,
        "dry_run": dry_run_summary,
        "first_verification": first_verification,
        "final_verification": final_verification,
        "idempotency": {
            "status": "pass",
            "mutation_count": 0,
            "canonical_export_sha256": canonical_sha256,
            "first_raw_export_sha256": _sha256_bytes(first_export),
            "final_raw_export_sha256": _sha256_bytes(final_export),
            "dolt_main_head_before": before_head,
            "dolt_main_head_after_dry_run": post_dry_head,
            "dolt_main_head_after": final_head,
            "dry_run_head_unchanged": True,
            "dolt_state_unchanged": True,
            "export_unchanged": True,
            "raw_export_unchanged": first_export == final_export,
        },
        "credential_transport": "runner-environment-only",
    }
    return OperationalMigrationResult(
        conversion=conversion,
        first_export=first_export,
        final_export=final_export,
        report=report,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Taskmaster tasks.json")
    parser.add_argument("--output-dir", required=True, type=Path, help="Artifact directory")
    parser.add_argument("--tag", default="master", help="Taskmaster tag to convert")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Explicit Beads ID prefix")
    parser.add_argument(
        "--expected-source-sha256",
        help="Fail if the immutable input hash differs",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        source_bytes = args.input.read_bytes()
        result = build_artifacts(
            source_bytes,
            tag=args.tag,
            prefix=args.prefix,
            expected_source_sha256=args.expected_source_sha256,
        )
        write_result = write_artifacts(args.output_dir, result.artifacts)
    except (OSError, ConversionError) as exc:
        parser.exit(2, f"taskmaster_to_beads: error: {exc}\n")

    summary = {
        "status": "pass",
        "input": str(args.input),
        "output_dir": str(args.output_dir),
        "counts": result.manifest["counts"],
        "digests": result.manifest["digests"],
        **write_result,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
