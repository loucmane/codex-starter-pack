"""Bounded human and machine rendering for gate results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import (
    BLOCKED,
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    DEFAULT_SAMPLE_SIZE,
    READY,
    VERBOSE_MAX_BYTES,
    VERBOSE_MAX_LINES,
    VERBOSE_SAMPLE_SIZE,
    WARN,
    Check,
)


def summarize_state(checks: list[Check]) -> str:
    if any(check.status == BLOCKED for check in checks):
        return BLOCKED
    if any(check.status == WARN for check in checks):
        return WARN
    return READY


def quick_text(state: str, task_id: str | None, checks: list[Check]) -> str:
    """Render the stable one-line machine contract without writing stdout."""

    blocked = [check.message for check in checks if check.status == BLOCKED]
    warnings = [check.message for check in checks if check.status == WARN]
    parts = [state]
    if task_id:
        parts.append(f"task={task_id}")
    if blocked:
        parts.append(f"blocked={len(blocked)}")
        parts.append(f"first={blocked[0]}")
    elif warnings:
        parts.append(f"warnings={len(warnings)}")
        parts.append(f"first={warnings[0]}")
    return " | ".join(parts)


def print_quick(state: str, task_id: str | None, checks: list[Check]) -> None:
    print(quick_text(state, task_id, checks))


def _clip_utf8(value: str, maximum: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum:
        return value
    clipped = encoded[: max(0, maximum - 3)]
    while clipped:
        try:
            return clipped.decode("utf-8") + "…"
        except UnicodeDecodeError:
            clipped = clipped[:-1]
    return ""


def _select_checks(checks: list[Check], sample_size: int) -> list[Check]:
    ordered = [
        check for status in (BLOCKED, WARN, READY) for check in checks if check.status == status
    ]
    if len(ordered) <= sample_size:
        return ordered
    head = (sample_size + 1) // 2
    tail = sample_size - head
    return ordered[:head] + (ordered[-tail:] if tail else [])


def _emit_bounded(lines: list[str], *, max_lines: int, max_bytes: int) -> None:
    selected: list[str] = []
    used = 0
    for line in lines[:max_lines]:
        remaining = max_bytes - used
        if remaining <= 1:
            break
        rendered = (line + "\n").encode("utf-8")
        if len(rendered) <= remaining:
            selected.append(line)
            used += len(rendered)
            continue
        selected.append(_clip_utf8(line, remaining - 1))
        break
    print("\n".join(selected))


def print_full(
    root: Path,
    state: str,
    task_id: str | None,
    checks: list[Check],
    *,
    adapter: str = "aegis",
    verbose: bool = False,
    all_output: bool = False,
) -> None:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z %z")
    lines = [
        f"# {adapter.upper()} READINESS - {now}",
        f"STATE: {state}",
        f"TASK: {task_id or 'unknown'}",
        f"ROOT: {root}",
        "",
        "## Checks",
    ]
    prefixes = {READY: "[ok]", WARN: "[warn]", BLOCKED: "[blocked]"}
    if all_output:
        selected_checks = checks
        max_lines = max(1, len(checks) + 32)
        max_bytes = max(1, sum(len(check.message.encode("utf-8")) for check in checks) + 16_384)
        message_limit = None
    else:
        sample_size = VERBOSE_SAMPLE_SIZE if verbose else DEFAULT_SAMPLE_SIZE
        max_lines = VERBOSE_MAX_LINES if verbose else DEFAULT_MAX_LINES
        max_bytes = VERBOSE_MAX_BYTES if verbose else DEFAULT_MAX_BYTES
        message_limit = 1_200 if verbose else 600
        selected_checks = _select_checks(checks, sample_size)
    for check in selected_checks:
        message = (
            check.message if message_limit is None else _clip_utf8(check.message, message_limit)
        )
        lines.append(f"{prefixes[check.status]} {message}")

    counts = {
        READY: sum(check.status == READY for check in checks),
        WARN: sum(check.status == WARN for check in checks),
        BLOCKED: sum(check.status == BLOCKED for check in checks),
    }
    lines.append(
        f"Counts: total={len(checks)}, ready={counts[READY]}, warn={counts[WARN]}, "
        f"blocked={counts[BLOCKED]}"
    )
    omitted = len(checks) - len(selected_checks)
    if omitted:
        lines.append(
            f"Truncated: {omitted} checks omitted from stdout; no check state was discarded."
        )
    lines.append(
        "Artifacts: .aegis/state/current-work.json, plans/current, sessions/current, "
        "docs/ai/work-tracking/active/"
    )

    if state == BLOCKED:
        lines.extend(
            [
                "",
                "## Remediation",
                "- Start or repair the workflow before Claude performs persistent mutations.",
                "- Required state: aligned work branch, authoritative work identity, sessions/current, plans/current, and one ACTIVE tracker for the same work.",
                "- Use the project kickoff workflow instead of writing files or memory by hand.",
            ]
        )
    lines.append("Next: ./.aegis/bin/aegis next --target-dir .")
    if omitted:
        lines.append("Full stdout: rerun readiness.sh with --all.")
    _emit_bounded(lines, max_lines=max_lines, max_bytes=max_bytes)
