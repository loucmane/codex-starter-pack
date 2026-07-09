"""Legacy S:W:H:E projections from the passive Aegis ledger.

The projection surface is intentionally small and deterministic: old workflow
files remain readable views, while the append-only ledger remains the evidence
source. Projection writes only inside a generated marker block so human-authored
history is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

BEGIN_MARKER = "<!-- AEGIS:BEGIN generated-sweh-projection -->"
END_MARKER = "<!-- AEGIS:END generated-sweh-projection -->"
STATE_PREFIX = "<!-- AEGIS:projection-state "
STATE_SUFFIX = " -->"

DEFAULT_EVENT_TYPES = {
    "checkpoint",
    "delivery",
    "scope",
    "session_begin",
    "session_end",
    "task_truth",
    "tool_failure",
    "verification",
}

ACTIVE_WORK_TRACKING_FILES = (
    "TRACKER.md",
    "FINDINGS.md",
    "IMPLEMENTATION.md",
    "CHANGELOG.md",
    "DECISIONS.md",
    "HANDOFF.md",
)


@dataclass(frozen=True)
class ProjectionResult:
    """Result of rendering/applying a legacy S:W:H:E projection."""

    output_path: Path
    event_count: int
    last_event_id: str | None
    changed: bool
    section: str


def _extra(event: Mapping[str, Any]) -> Mapping[str, Any]:
    extra = event.get("extra")
    return extra if isinstance(extra, Mapping) else {}


def _short(value: Any, default: str = "unknown", limit: int = 80) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        text = default
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1] + "..."
    return text


def _event_work(event: Mapping[str, Any]) -> str:
    extra = _extra(event)
    work_id = extra.get("work_id")
    if work_id:
        return _short(work_id, limit=80)
    task_id = extra.get("task_id") or extra.get("task")
    if isinstance(task_id, Mapping):
        task_id = task_id.get("id")
    if task_id:
        return f"task-{_short(task_id, limit=40)}"
    branch = event.get("branch")
    if branch:
        return _short(branch, limit=80)
    cwd = event.get("cwd")
    return _short(Path(str(cwd)).name if cwd else None, default="unknown", limit=80)


def _event_handler(event: Mapping[str, Any]) -> str:
    event_type = str(event.get("event_type") or "unknown")
    if event_type == "verification":
        return "verify"
    if event_type == "delivery":
        return "delivery"
    if event_type == "task_truth":
        return "task-truth"
    if event_type == "scope":
        return "scope"
    if event_type in {"session_begin", "session_end"}:
        return "session"
    if event_type == "checkpoint":
        return "checkpoint"
    if event_type == "tool_failure":
        return "failure"
    if event_type == "mutation":
        tool = _short(event.get("tool_name"), default="mutation", limit=40)
        return tool.lower().replace(" ", "-")
    if event_type == "gate_decision":
        return "legacy-shadow"
    return _short(event.get("handler") or event_type, limit=40)


def _paths_summary(event: Mapping[str, Any]) -> str:
    paths = event.get("paths")
    if not isinstance(paths, Sequence) or isinstance(paths, (str, bytes)):
        return ""
    normalized = [_short(path, limit=80) for path in paths if str(path).strip()]
    if not normalized:
        return ""
    visible = ", ".join(normalized[:3])
    if len(normalized) > 3:
        visible += f", +{len(normalized) - 3} more"
    return visible


def _event_summary(event: Mapping[str, Any]) -> str:
    event_type = str(event.get("event_type") or "unknown")
    extra = _extra(event)
    if event_type == "verification":
        package = _short(extra.get("package"), default="app", limit=40)
        gate = _short(extra.get("gate"), default="verification", limit=40)
        exit_class = _short(event.get("exit_class") or extra.get("exit_class"), default="unknown", limit=20)
        commit = _short(extra.get("commit"), default="unknown commit", limit=16)
        return f"{package}:{gate} verification recorded as {exit_class} at {commit}."
    if event_type == "delivery":
        action = _short(extra.get("action") or event.get("tool_name"), default="delivery", limit=60)
        return f"Delivery event recorded: {action}."
    if event_type == "task_truth":
        task = _short(extra.get("task_id") or extra.get("task"), default="task truth", limit=50)
        status = _short(extra.get("status") or extra.get("to_status"), default="changed", limit=40)
        return f"Task truth recorded for {task}: {status}."
    if event_type == "scope":
        task = _short(extra.get("task_id"), default="unknown task", limit=50)
        globs = extra.get("path_globs")
        suffix = ""
        if isinstance(globs, Sequence) and not isinstance(globs, (str, bytes)) and globs:
            suffix = f" Paths: {', '.join(_short(item, limit=60) for item in globs[:3])}."
        return f"Scope recorded for {task}.{suffix}"
    if event_type == "session_begin":
        source = _short(extra.get("source"), default="session start", limit=40)
        return f"Session began via {source}."
    if event_type == "session_end":
        return "Session end recorded."
    if event_type == "checkpoint":
        return "Deterministic checkpoint recorded."
    if event_type == "tool_failure":
        tool = _short(event.get("tool_name"), default="tool", limit=40)
        paths = _paths_summary(event)
        if paths:
            return f"{tool} failure recorded for paths: {paths}."
        return f"{tool} failure recorded."
    if event_type == "mutation":
        tool = _short(event.get("tool_name"), default="mutation", limit=40)
        paths = _paths_summary(event)
        if paths:
            return f"{tool} mutation recorded for paths: {paths}."
        return f"{tool} mutation recorded."
    if event_type == "gate_decision":
        verdict = _short(extra.get("verdict") or event.get("outcome"), default="decision", limit=40)
        reason = _short(extra.get("reason"), default="no reason recorded", limit=80)
        return f"Legacy shadow gate decision recorded: {verdict} ({reason})."
    return f"{_short(event_type, default='event', limit=40)} event recorded."


def projectable_events(
    events: Iterable[Mapping[str, Any]],
    *,
    include_mutations: bool = False,
    include_gate_decisions: bool = False,
    limit: int | None = None,
) -> list[Mapping[str, Any]]:
    """Return events worth projecting into human-readable S:W:H:E docs."""

    selected: list[Mapping[str, Any]] = []
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        if event_type in DEFAULT_EVENT_TYPES:
            selected.append(event)
        elif include_mutations and event_type == "mutation":
            selected.append(event)
        elif include_gate_decisions and event_type == "gate_decision":
            selected.append(event)
    if limit is not None and limit >= 0:
        selected = selected[-limit:]
    return selected


def render_entry(event: Mapping[str, Any]) -> str:
    """Render one ledger event as a single S:W:H:E bullet."""

    session = _short(event.get("session_id"), limit=80)
    work = _event_work(event)
    handler = _event_handler(event)
    event_id = _short(event.get("event_id"), default="unknown", limit=12)
    summary = _event_summary(event)
    return f"- [S:{session} W:{work} H:{handler} E:ledger:{event_id}] {summary}"


def render_section(events: Sequence[Mapping[str, Any]]) -> str:
    """Render a complete generated S:W:H:E section."""

    last_event_id = str(events[-1].get("event_id")) if events else None
    state = {
        "event_count": len(events),
        "last_event_id": last_event_id,
        "schema": "legacy-shadow-sweh-projection-v1",
    }
    lines = [
        BEGIN_MARKER,
        f"{STATE_PREFIX}{json.dumps(state, sort_keys=True)}{STATE_SUFFIX}",
        "",
        "## Generated S:W:H:E Projection",
        "",
        "_Generated from the passive Aegis ledger. Human-authored content outside this block is preserved._",
        "",
    ]
    if events:
        lines.extend(render_entry(event) for event in events)
    else:
        lines.append("- No projectable ledger events found.")
    lines.extend(["", END_MARKER, ""])
    return "\n".join(lines)


def apply_generated_section(original: str, section: str) -> tuple[str, bool]:
    """Replace or append the generated projection section."""

    start = original.find(BEGIN_MARKER)
    end = original.find(END_MARKER)
    if start != -1 and end != -1 and end > start:
        end += len(END_MARKER)
        if end < len(original) and original[end : end + 1] == "\n":
            end += 1
        updated = original[:start] + section + original[end:]
    else:
        sep = "" if not original else "\n\n"
        updated = original.rstrip() + sep + section
    return updated, updated != original


def project_to_file(
    events: Sequence[Mapping[str, Any]],
    output_path: Path,
    *,
    dry_run: bool = False,
) -> ProjectionResult:
    """Project selected events into ``output_path``."""

    section = render_section(events)
    original = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    updated, changed = apply_generated_section(original, section)
    if not dry_run and changed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(updated, encoding="utf-8")
    return ProjectionResult(
        output_path=output_path,
        event_count=len(events),
        last_event_id=str(events[-1].get("event_id")) if events else None,
        changed=changed,
        section=section,
    )


def active_surface_paths(target_dir: Path) -> list[Path]:
    """Resolve existing legacy session/plan/work-tracking surfaces for projection."""

    root = target_dir.resolve()
    candidates: list[Path] = []
    current_work_path = root / ".aegis" / "state" / "current-work.json"
    if current_work_path.exists():
        try:
            current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current_work = {}
        paths = current_work.get("paths") if isinstance(current_work, Mapping) else {}
        if isinstance(paths, Mapping):
            for key in ("session", "plan"):
                rel_path = str(paths.get(key) or "").strip()
                if rel_path:
                    candidates.append(root / rel_path)
            work_rel = str(paths.get("work_tracking") or "").strip()
            if work_rel:
                candidates.extend(root / work_rel / filename for filename in ACTIVE_WORK_TRACKING_FILES)

    candidates.extend(root / rel_path for rel_path in ("sessions/current", "plans/current"))

    existing: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate.exists():
            continue
        key = candidate.resolve()
        if key in seen:
            continue
        seen.add(key)
        existing.append(candidate)
    return existing


__all__ = [
    "ACTIVE_WORK_TRACKING_FILES",
    "BEGIN_MARKER",
    "END_MARKER",
    "ProjectionResult",
    "active_surface_paths",
    "apply_generated_section",
    "project_to_file",
    "projectable_events",
    "render_entry",
    "render_section",
]
