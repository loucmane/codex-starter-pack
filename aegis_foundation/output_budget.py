"""Context-budgeted presentation for agent-facing Aegis commands.

The functions in this module are deliberately downstream of detection and report
generation.  They accept complete payloads, calculate exact aggregate counts, and
sample only the stdout representation.  Stored state and report artifacts therefore
remain the authoritative source of full detail.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_MAX_LINES = 60
DEFAULT_MAX_BYTES = 8 * 1024
DEFAULT_SAMPLE_SIZE = 5
VERBOSE_MAX_LINES = 120
VERBOSE_MAX_BYTES = 32 * 1024
VERBOSE_SAMPLE_SIZE = 20

CATEGORY_FIELDS = (
    "status",
    "reason",
    "category",
    "kind",
    "event_type",
    "verdict",
    "label",
    "mode",
    "hook",
    "tool_name",
)

CORE_SCALAR_KEYS = (
    "status",
    "ok",
    "installed",
    "passed",
    "read_only",
    "dry_run",
    "report_written",
    "state_updated",
    "migration_required",
    "summary",
    "state",
    "current_state",
    "phase",
    "mode",
    "action",
    "task_id",
    "work_id",
    "branch",
    "base",
    "head_commit",
    "source_commit",
    "schema_version",
    "version",
    "total",
)

PRIORITY_KEYS = CORE_SCALAR_KEYS + (
    "result",
    "error",
    "details",
    "report",
    "install",
    "plan",
    "operations",
    "checks",
    "workflow_guidance",
    "events",
    "results",
    "failures",
    "regressions",
    "standing_gaps",
    "improvements",
    "pending_event_ids",
    "next_action",
    "suggested_mcp_call",
)

_SIMPLE_PATH_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class OutputMode:
    """A named stdout budget."""

    name: str
    max_lines: int | None
    max_bytes: int | None
    sample_size: int | None
    max_string_chars: int | None


DEFAULT_MODE = OutputMode(
    "default",
    DEFAULT_MAX_LINES,
    DEFAULT_MAX_BYTES,
    DEFAULT_SAMPLE_SIZE,
    512,
)
VERBOSE_MODE = OutputMode(
    "verbose",
    VERBOSE_MAX_LINES,
    VERBOSE_MAX_BYTES,
    VERBOSE_SAMPLE_SIZE,
    2_048,
)
ALL_MODE = OutputMode("all", None, None, None, None)


@dataclass
class CollectionStat:
    kinds: Counter[str] = field(default_factory=Counter)
    instances: int = 0
    items: int = 0
    maximum: int = 0


@dataclass
class CategoryStat:
    total: int = 0
    values: Counter[str] = field(default_factory=Counter)
    overflow: int = 0


@dataclass
class PayloadAnalysis:
    collections: dict[str, CollectionStat] = field(default_factory=dict)
    categories: dict[str, CategoryStat] = field(default_factory=dict)


def mode_from_args(args: Any) -> OutputMode:
    """Resolve the common ``--verbose``/``--all`` flags from an argparse namespace."""

    if bool(getattr(args, "all_output", False)):
        return ALL_MODE
    if bool(getattr(args, "verbose", False)):
        return VERBOSE_MODE
    return DEFAULT_MODE


def _child_path(path: str, key: object) -> str:
    text = str(key)
    if _SIMPLE_PATH_KEY.fullmatch(text):
        return f"{path}.{text}"
    return f"{path}[{json.dumps(text, ensure_ascii=False)}]"


def _category_label(value: Any) -> str:
    if isinstance(value, str):
        label = value
    elif value is None or isinstance(value, (bool, int, float)):
        label = json.dumps(value, ensure_ascii=False)
    else:
        return ""
    if len(label) <= 160:
        return label
    digest = hashlib.sha256(label.encode("utf-8", errors="replace")).hexdigest()[:10]
    return f"{label[:140]}…#{digest}"


def analyze_payload(payload: Any, *, max_category_values: int = 256) -> PayloadAnalysis:
    """Calculate exact cardinalities without retaining high-cardinality raw values."""

    analysis = PayloadAnalysis()

    def visit(value: Any, path: str, depth: int) -> None:
        if depth > 64:
            return
        if isinstance(value, Mapping):
            stat = analysis.collections.setdefault(path, CollectionStat())
            stat.kinds["object"] += 1
            stat.instances += 1
            stat.items += len(value)
            stat.maximum = max(stat.maximum, len(value))
            for key, item in value.items():
                field_name = str(key)
                if field_name in CATEGORY_FIELDS:
                    label = _category_label(item)
                    if label:
                        category = analysis.categories.setdefault(field_name, CategoryStat())
                        category.total += 1
                        if label in category.values or len(category.values) < max_category_values:
                            category.values[label] += 1
                        else:
                            category.overflow += 1
                visit(item, _child_path(path, key), depth + 1)
            return
        if isinstance(value, (list, tuple)):
            stat = analysis.collections.setdefault(path, CollectionStat())
            stat.kinds["array"] += 1
            stat.instances += 1
            stat.items += len(value)
            stat.maximum = max(stat.maximum, len(value))
            for item in value:
                visit(item, f"{path}[]", depth + 1)

    visit(payload, "$", 0)
    return analysis


def _clip_string(value: str, limit: int | None) -> tuple[str, bool]:
    if limit is None or len(value) <= limit:
        return value, False
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:10]
    suffix = f"…#{digest}"
    return value[: max(0, limit - len(suffix))] + suffix, True


def _priority(key: object) -> tuple[int, str]:
    text = str(key)
    try:
        return PRIORITY_KEYS.index(text), text
    except ValueError:
        return len(PRIORITY_KEYS), text


def _project_payload(
    value: Any,
    *,
    path: str,
    sample_size: int,
    dict_limit: int | None,
    max_string_chars: int,
    truncations: list[dict[str, Any]],
    root: bool = False,
    depth: int = 0,
) -> Any:
    if depth > 32:
        truncations.append(
            {"path": path, "kind": "depth", "total": depth, "shown": 32, "omitted": 1}
        )
        return "<maximum projection depth reached>"

    if isinstance(value, str):
        clipped, changed = _clip_string(value, max_string_chars)
        if changed:
            truncations.append(
                {
                    "path": path,
                    "kind": "string",
                    "total": len(value),
                    "shown": len(clipped),
                    "omitted": len(value) - len(clipped),
                }
            )
        return clipped
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        items = list(value.items())

        def is_scalar(item: tuple[object, Any]) -> bool:
            candidate = item[1]
            return candidate is None or isinstance(candidate, (str, bool, int, float))

        scalar = [item for item in items if is_scalar(item)]
        nested = [item for item in items if not is_scalar(item)]
        # Scalar compatibility is preserved at every envelope level (including the
        # MCP result/error wrapper). A hard ceiling protects stdout from adversarial
        # objects with thousands of scalar keys; omissions remain explicit.
        scalar_ceiling = 64 if root else 32
        scalar_limit = (
            len(scalar) if dict_limit is None else min(scalar_ceiling, max(8, dict_limit * 4))
        )
        selected = sorted(scalar, key=lambda item: _priority(item[0]))[:scalar_limit]
        selected_keys = {str(key) for key, _ in selected}
        nested_shown = 0
        nested_limit = len(nested) if dict_limit is None else dict_limit
        for key, item in sorted(nested, key=lambda pair: _priority(pair[0])):
            if nested_shown >= nested_limit:
                break
            if str(key) not in selected_keys:
                selected.append((key, item))
                selected_keys.add(str(key))
                nested_shown += 1
        if len(selected) < len(items):
            truncations.append(
                {
                    "path": path,
                    "kind": "object",
                    "total": len(items),
                    "shown": len(selected),
                    "omitted": len(items) - len(selected),
                }
            )
        return {
            str(key): _project_payload(
                item,
                path=_child_path(path, key),
                sample_size=sample_size,
                dict_limit=dict_limit,
                max_string_chars=max_string_chars,
                truncations=truncations,
                depth=depth + 1,
            )
            for key, item in selected
        }
    if isinstance(value, (list, tuple)):
        shown = list(value[:sample_size])
        if len(shown) < len(value):
            truncations.append(
                {
                    "path": path,
                    "kind": "array",
                    "total": len(value),
                    "shown": len(shown),
                    "omitted": len(value) - len(shown),
                }
            )
        return [
            _project_payload(
                item,
                path=f"{path}[]",
                sample_size=sample_size,
                dict_limit=dict_limit,
                max_string_chars=max_string_chars,
                truncations=truncations,
                depth=depth + 1,
            )
            for item in shown
        ]
    return str(value)


def _collection_records(
    analysis: PayloadAnalysis, *, limit: int
) -> tuple[list[dict[str, Any]], int]:
    ordered = sorted(
        analysis.collections.items(),
        key=lambda item: (
            0 if item[1].kinds.get("array") else 1,
            -item[1].items,
            item[0],
        ),
    )
    records = [
        {
            "path": path,
            "kinds": dict(sorted(stat.kinds.items())),
            "instances": stat.instances,
            "items": stat.items,
            "maximum": stat.maximum,
        }
        for path, stat in ordered[:limit]
    ]
    return records, max(0, len(ordered) - len(records))


def _category_records(
    analysis: PayloadAnalysis, *, field_limit: int, value_limit: int
) -> tuple[dict[str, Any], int]:
    records: dict[str, Any] = {}
    fields = sorted(analysis.categories.items(), key=lambda item: (-item[1].total, item[0]))
    for field_name, stat in fields[:field_limit]:
        values = sorted(stat.values.items(), key=lambda item: (-item[1], item[0]))
        shown = values[:value_limit]
        shown_count = sum(count for _, count in shown)
        records[field_name] = {
            "total": stat.total,
            "values": {label: count for label, count in shown},
            "other": stat.total - shown_count,
        }
    return records, max(0, len(fields) - len(records))


def _extract_command(value: Any, depth: int = 0) -> str | None:
    if depth > 5:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and (
            " " in stripped or stripped.startswith(("aegis", "./", "git", "python", "task-master"))
        ):
            return stripped
        return None
    if isinstance(value, Mapping):
        for key in ("command", "suggested_command", "copyable_command", "cli"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for key in ("suggested_cli", "next_action", "remediation", "guidance"):
            candidate = _extract_command(value.get(key), depth + 1)
            if candidate:
                return candidate
    return None


def extract_next_action(payload: Any, explicit: str | None = None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    if isinstance(payload, Mapping):
        return _extract_command(payload)
    return None


def _unique_clipped(values: Iterable[str], *, limit: int, chars: int = 240) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text, _ = _clip_string(str(value), chars)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")


def _set_actual(metadata: dict[str, Any], rendered: bytes) -> None:
    metadata["actual"] = {
        "lines": rendered.count(b"\n"),
        "bytes": len(rendered),
    }


def _serialize_with_actual(projected: dict[str, Any]) -> bytes:
    metadata = projected["_aegis_output"]
    rendered = _json_bytes(projected)
    for _ in range(5):
        before = metadata.get("actual")
        _set_actual(metadata, rendered)
        rendered = _json_bytes(projected)
        if metadata.get("actual") == before:
            break
    _set_actual(metadata, rendered)
    return _json_bytes(projected)


def _metadata(
    *,
    command: str,
    mode: OutputMode,
    analysis: PayloadAnalysis,
    truncations: Sequence[dict[str, Any]],
    artifact_paths: Sequence[str],
    next_action: str | None,
    record_limit: int,
    value_limit: int,
) -> dict[str, Any]:
    collections, omitted_collection_paths = _collection_records(analysis, limit=record_limit)
    categories, omitted_category_fields = _category_records(
        analysis,
        field_limit=min(record_limit, len(CATEGORY_FIELDS)),
        value_limit=value_limit,
    )
    shown_truncations = list(truncations[:record_limit])
    return {
        "command": command,
        "detail_mode": mode.name,
        "limits": {"lines": mode.max_lines, "bytes": mode.max_bytes},
        "actual": {"lines": 0, "bytes": 0},
        "collection_counts": collections,
        "collection_paths_total": len(analysis.collections),
        "collection_paths_omitted": omitted_collection_paths,
        "category_counts": categories,
        "category_fields_total": len(analysis.categories),
        "category_fields_omitted": omitted_category_fields,
        "truncations": shown_truncations,
        "truncations_total": len(truncations),
        "truncations_omitted": max(0, len(truncations) - len(shown_truncations)),
        "artifact_paths": _unique_clipped(artifact_paths, limit=value_limit),
        "next_action": next_action,
        "full_output": "Rerun the same command with --all --json for intentional full stdout.",
    }


def _core_projection(payload: Mapping[str, Any], *, max_string_chars: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in CORE_SCALAR_KEYS:
        value = payload.get(key)
        if value is None or isinstance(value, (str, bool, int, float)):
            if key not in payload:
                continue
            if isinstance(value, str):
                value, _ = _clip_string(value, max_string_chars)
            result[key] = value
    return result


def render_json(
    payload: Mapping[str, Any],
    *,
    command: str,
    mode: OutputMode = DEFAULT_MODE,
    artifact_paths: Sequence[str] = (),
    next_action: str | None = None,
) -> str:
    """Render a valid JSON payload under the selected context budget."""

    if mode is ALL_MODE or mode.name == "all":
        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    assert mode.max_bytes is not None
    assert mode.sample_size is not None
    assert mode.max_string_chars is not None
    analysis = analyze_payload(payload)
    resolved_next = extract_next_action(payload, next_action)

    sample_size = mode.sample_size
    dict_limit: int | None = None
    record_limit = max(6, mode.sample_size * 2)
    value_limit = max(3, mode.sample_size)
    while sample_size >= 0:
        truncations: list[dict[str, Any]] = []
        projected_raw = _project_payload(
            payload,
            path="$",
            sample_size=sample_size,
            dict_limit=dict_limit,
            max_string_chars=mode.max_string_chars,
            truncations=truncations,
            root=True,
        )
        projected = projected_raw if isinstance(projected_raw, dict) else {"value": projected_raw}
        projected["_aegis_output"] = _metadata(
            command=command,
            mode=mode,
            analysis=analysis,
            truncations=truncations,
            artifact_paths=artifact_paths,
            next_action=resolved_next,
            record_limit=record_limit,
            value_limit=value_limit,
        )
        rendered = _serialize_with_actual(projected)
        if len(rendered) <= mode.max_bytes:
            return rendered.decode("utf-8")
        if dict_limit is None:
            dict_limit = max(1, sample_size)
            continue
        if sample_size == 0:
            break
        sample_size //= 2
        dict_limit = sample_size
        record_limit = max(3, record_limit // 2)
        value_limit = max(2, value_limit // 2)

    # Minimal valid envelope: retain compatibility-critical top-level scalars and exact
    # aggregate totals, but discard all samples before ever risking invalid JSON.
    minimal = _core_projection(payload, max_string_chars=256)
    total_collection_items = sum(stat.items for stat in analysis.collections.values())
    minimal["_aegis_output"] = {
        "command": command,
        "detail_mode": mode.name,
        "limits": {"lines": mode.max_lines, "bytes": mode.max_bytes},
        "actual": {"lines": 0, "bytes": 0},
        "minimal_projection": True,
        "collection_paths_total": len(analysis.collections),
        "collection_items_total": total_collection_items,
        "category_fields_total": len(analysis.categories),
        "truncations_total": max(1, len(analysis.collections)),
        "artifact_paths": _unique_clipped(artifact_paths, limit=3, chars=160),
        "next_action": _clip_string(resolved_next, 320)[0] if resolved_next else None,
        "full_output": "Rerun the same command with --all --json for intentional full stdout.",
    }
    rendered = _serialize_with_actual(minimal)
    if len(rendered) > mode.max_bytes:
        # This can only be reached with unusually large compatibility scalars.  Dropping
        # them is safer than emitting over-budget or malformed JSON; status remains.
        status = minimal.get("status")
        minimal = {
            "status": status,
            "_aegis_output": {
                "command": command,
                "detail_mode": mode.name,
                "limits": {"lines": mode.max_lines, "bytes": mode.max_bytes},
                "actual": {"lines": 0, "bytes": 0},
                "minimal_projection": True,
                "collection_paths_total": len(analysis.collections),
                "collection_items_total": total_collection_items,
                "artifact_paths": _unique_clipped(artifact_paths, limit=2, chars=120),
                "full_output": "Rerun the same command with --all --json.",
            },
        }
        rendered = _serialize_with_actual(minimal)
    return rendered.decode("utf-8")


def _text_size(lines: Sequence[str]) -> tuple[int, int]:
    rendered = "\n".join(lines).rstrip("\n") + "\n"
    return len(lines), len(rendered.encode("utf-8"))


def _clip_utf8(value: str, maximum: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum:
        return value
    if maximum <= 1:
        return ""
    clipped = encoded[: maximum - 1]
    while clipped:
        try:
            return clipped.decode("utf-8") + "…"
        except UnicodeDecodeError:
            clipped = clipped[:-1]
    return ""


def _text_footer(
    *,
    command: str,
    mode: OutputMode,
    analysis: PayloadAnalysis,
    source_lines: int,
    source_bytes: int,
    artifact_paths: Sequence[str],
    next_action: str | None,
    truncated: bool,
) -> list[str]:
    largest = sorted(
        analysis.collections.items(),
        key=lambda item: (
            0 if item[1].kinds.get("array") else 1,
            -item[1].items,
            item[0],
        ),
    )[:3]
    counts = ", ".join(f"{path}={stat.items}" for path, stat in largest) or "none"
    lines = [
        f"Output budget: {command}/{mode.name}; source={source_lines} lines/{source_bytes} bytes; collections: {counts}",
    ]
    if truncated:
        lines.append("Truncated: yes; representative details only.")
    artifacts = _unique_clipped(artifact_paths, limit=3, chars=180)
    if artifacts:
        lines.append(f"Artifacts: {', '.join(artifacts)}")
    if next_action:
        lines.append(f"Next: {_clip_string(next_action, 360)[0]}")
    if truncated:
        lines.append("Full stdout: rerun the same command with --all.")
    return lines


def render_text(
    text: str,
    payload: Mapping[str, Any],
    *,
    command: str,
    mode: OutputMode = DEFAULT_MODE,
    artifact_paths: Sequence[str] = (),
    next_action: str | None = None,
) -> str:
    """Preserve command wording while enforcing hard line and UTF-8 byte limits."""

    if mode is ALL_MODE or mode.name == "all":
        return text
    assert mode.max_lines is not None and mode.max_bytes is not None
    analysis = analyze_payload(payload)
    source = text.rstrip("\n").splitlines() or [""]
    source_bytes = len((text if text.endswith("\n") else text + "\n").encode("utf-8"))
    resolved_next = extract_next_action(payload, next_action)
    footer_next = resolved_next if not resolved_next or resolved_next not in text else None

    truncated = len(source) > mode.max_lines or source_bytes > mode.max_bytes
    footer = _text_footer(
        command=command,
        mode=mode,
        analysis=analysis,
        source_lines=len(source),
        source_bytes=source_bytes,
        artifact_paths=artifact_paths,
        next_action=footer_next,
        truncated=truncated,
    )
    keep = max(1, mode.max_lines - len(footer))
    selected = source[:keep]
    candidate = selected + footer
    lines_count, bytes_count = _text_size(candidate)

    if lines_count > mode.max_lines or bytes_count > mode.max_bytes:
        truncated = True
        footer = _text_footer(
            command=command,
            mode=mode,
            analysis=analysis,
            source_lines=len(source),
            source_bytes=source_bytes,
            artifact_paths=artifact_paths,
            next_action=footer_next,
            truncated=True,
        )
        keep = max(1, mode.max_lines - len(footer))
        selected = source[:keep]
        candidate = selected + footer

    while len(selected) > 1 and _text_size(candidate)[1] > mode.max_bytes:
        selected.pop()
        candidate = selected + footer

    if _text_size(candidate)[1] > mode.max_bytes:
        footer_bytes = _text_size(footer)[1]
        available = max(64, mode.max_bytes - footer_bytes - 1)
        selected = [_clip_utf8(source[0], available)]
        candidate = selected + footer

    while len(footer) > 1 and _text_size(candidate)[1] > mode.max_bytes:
        footer.pop(1)
        candidate = selected + footer

    if _text_size(candidate)[1] > mode.max_bytes:
        candidate = [
            _clip_utf8(source[0], max(64, mode.max_bytes - 180)),
            f"Output budget: {mode.name}; source={len(source)} lines/{source_bytes} bytes; truncated=yes.",
            "Full stdout: rerun the same command with --all.",
        ]
    return "\n".join(candidate).rstrip("\n") + "\n"


__all__ = [
    "ALL_MODE",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_MAX_LINES",
    "DEFAULT_MODE",
    "DEFAULT_SAMPLE_SIZE",
    "OutputMode",
    "VERBOSE_MAX_BYTES",
    "VERBOSE_MAX_LINES",
    "VERBOSE_MODE",
    "VERBOSE_SAMPLE_SIZE",
    "analyze_payload",
    "extract_next_action",
    "mode_from_args",
    "render_json",
    "render_text",
]
