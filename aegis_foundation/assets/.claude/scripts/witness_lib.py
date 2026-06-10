"""Aegis delivery witness v0 (capsule program PR-3.5).

Deterministic, zero-LLM boundary check computed from ledger + git + scope records
(spec section 5.1). Its output is the generated delivery report — the replacement for
the old hand-fed closeout. The teeth move HERE, before anything is retired.

Stdlib-only, no aegis_foundation imports (same standalone contract as ledger_lib /
brief_lib). CI-mode honesty: the out-of-worktree ledger does not travel to CI, so
``ci_mode`` evaluates the git+config-derivable checks and reports the ledger-dependent
verification check as ``not_derivable_in_ci`` instead of pretending.
"""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WITNESS_SCHEMA_VERSION = "1"
WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"
BRIEF_REL = ".aegis/brief.json"
TASKS_JSON_REL = ".taskmaster/tasks/tasks.json"
TASK_BRANCH_RE = re.compile(r"task-?(\d+)", re.IGNORECASE)
DONE_FLIP_ADDED_RE = re.compile(r'^\+\s*"status":\s*"done"', re.MULTILINE)
TEST_PATH_PATTERNS = ("tests/*", "test/*", "*_test.*", "*.test.*", "test_*")


def _parse_ts(value: Any):
    """Parse an ISO timestamp tolerating Z and offset forms; None on failure."""

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], cwd: Path, timeout: float = 10) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return result.returncode, result.stdout


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _load_ledger_lib():
    script = Path(__file__).resolve().parent / "ledger_lib.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_witness_ledger_lib", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_events(root: Path) -> list[dict[str, Any]]:
    ledger_lib = _load_ledger_lib()
    if ledger_lib is None:
        return []
    try:
        ledger = ledger_lib.open_ledger(cwd=root)
        try:
            return ledger.read()
        finally:
            ledger.close()
    except Exception:  # noqa: BLE001 - CI and fresh machines have no store.
        return []


def _resolve_base(root: Path, base: str | None) -> str:
    candidates = [base] if base else []
    candidates += ["origin/main", "main", "origin/master", "master"]
    for candidate in candidates:
        if not candidate:
            continue
        rc, _ = _run(["git", "rev-parse", "--verify", "--quiet", candidate], root)
        if rc == 0:
            return candidate
    return "HEAD"


def _diff_files(root: Path, base: str) -> list[tuple[str, str]]:
    rc, output = _run(["git", "diff", "--name-status", f"{base}...HEAD"], root)
    if rc != 0:
        return []
    files: list[tuple[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append((parts[0].strip()[:1], parts[-1].strip()))
    return files


def _matches_glob(path: str, glob: str) -> bool:
    if glob.endswith("/"):
        return path.startswith(glob)
    return fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(Path(path).name, glob)


def _is_test_path(path: str) -> bool:
    return any(_matches_glob(path, pattern) for pattern in TEST_PATH_PATTERNS) or "/tests/" in path


def _scope_for_branch(
    root: Path, branch: str, events: list[dict[str, Any]], brief: dict[str, Any]
) -> dict[str, Any]:
    scopes = [
        event
        for event in events
        if event.get("event_type") == "scope"
        and event.get("branch") == branch
        and not event.get("extra", {}).get("nudge")
    ]
    confirmed = [event for event in scopes if event.get("extra", {}).get("confirmed")]
    chosen = (confirmed or scopes)[-1] if (confirmed or scopes) else None
    match = TASK_BRANCH_RE.search(branch or "")
    task_id = None
    globs: list[str] = []
    source = "none"
    if chosen is not None:
        task_id = chosen.get("extra", {}).get("task_id")
        globs = [g for g in chosen.get("extra", {}).get("path_globs", []) if isinstance(g, str)]
        source = "scope_record_confirmed" if chosen.get("extra", {}).get("confirmed") else "scope_record_inferred"
    if task_id is None and match:
        task_id = match.group(1)
        source = source if source != "none" else "branch_convention"
    if not globs:
        roots = brief.get("source_roots")
        globs = [g for g in roots if isinstance(g, str)] if isinstance(roots, list) else []
    witness_config = brief.get("witness") if isinstance(brief.get("witness"), dict) else {}
    always = witness_config.get("always_in_scope")
    if isinstance(always, list):
        globs = globs + [g for g in always if isinstance(g, str)]
    return {"task_id": task_id, "path_globs": globs, "source": source}


def run_witness(root: str | Path, *, base: str | None = None, ci_mode: bool = False) -> dict[str, Any]:
    """Run the four deterministic delivery checks; never raises."""

    target = Path(root).resolve()
    rc, branch_out = _run(["git", "branch", "--show-current"], target)
    branch = branch_out.strip() if rc == 0 else ""
    if not branch:
        # PR CI checks out a detached merge ref; GITHUB_HEAD_REF carries the branch.
        branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    rc, head_out = _run(["git", "rev-parse", "--short", "HEAD"], target)
    head = head_out.strip() if rc == 0 else None
    resolved_base = _resolve_base(target, base)
    diff = _diff_files(target, resolved_base)
    brief = _read_json(target / BRIEF_REL)
    brief = brief if isinstance(brief, dict) else {}
    events = [] if ci_mode else _read_events(target)
    scope = _scope_for_branch(target, branch, events, brief)
    checks: dict[str, Any] = {}

    checks["scope_mapping"] = {
        "passed": scope["task_id"] is not None,
        "task_id": scope["task_id"],
        "source": scope["source"],
        "detail": "branch must map to a scope record or the task-NN convention",
    }

    deleted_tests = [path for status, path in diff if status == "D" and _is_test_path(path)]
    if ci_mode and not scope["path_globs"]:
        # The scope config (brief.json) is typically untracked per the gitignore rider,
        # so CI may have no globs to account against. Be honest rather than fail
        # everything — but test deletions are git-derivable and ALWAYS escalate.
        checks["diff_accounting"] = {
            "passed": not deleted_tests,
            "status": "globs_not_derivable_in_ci",
            "files_in_diff": len(diff),
            "deleted_tests_escalated": deleted_tests,
            "detail": (
                "no scope config available in CI (brief.json is untracked); glob "
                "accounting is owned by the local witness report — test deletions "
                "still escalate"
            ),
        }
    else:
        unaccounted = [
            path for _status, path in diff if not any(_matches_glob(path, glob) for glob in scope["path_globs"])
        ]
        checks["diff_accounting"] = {
            "passed": not unaccounted and not deleted_tests,
            "files_in_diff": len(diff),
            "globs": scope["path_globs"],
            "unaccounted": unaccounted[:20],
            "deleted_tests_escalated": deleted_tests,
            "detail": "every diff file must match the scope globs; test deletions escalate to human review",
        }

    if ci_mode:
        checks["verification_at_head"] = {
            "passed": True,
            "status": "not_derivable_in_ci",
            "detail": (
                "the out-of-worktree ledger does not travel to CI; the local "
                "aegis witness report is the authoritative artifact for this check"
            ),
        }
    else:
        gates = brief.get("gates") if isinstance(brief.get("gates"), dict) else {}
        required = [
            f"{package}:{gate}"
            for package, package_gates in sorted(gates.items())
            if isinstance(package_gates, dict)
            for gate in sorted(package_gates)
        ]
        verifications = [event for event in events if event.get("event_type") == "verification"]
        rc_time, head_time_out = _run(["git", "show", "-s", "--format=%cI", "HEAD"], target)
        head_time = head_time_out.strip() if rc_time == 0 else ""
        missing: list[str] = []
        for key in required:
            package, gate = key.split(":", 1)
            # Spec 5.1: runs on record AT (or after) the head commit — commit equality
            # or a pass recorded after the head commit existed both count.
            ok = any(
                event.get("extra", {}).get("package") == package
                and event.get("extra", {}).get("gate") == gate
                and event.get("exit_class") == "pass"
                and (
                    event.get("extra", {}).get("commit") == head
                    or (
                        _parse_ts(head_time) is not None
                        and _parse_ts(event.get("ts")) is not None
                        and _parse_ts(event.get("ts")) >= _parse_ts(head_time)
                    )
                )
                for event in verifications
            )
            if not ok:
                missing.append(key)
        checks["verification_at_head"] = {
            "passed": not missing,
            "required": required,
            "missing_pass_at_head": missing,
            "head": head,
            "detail": "registered gates need pass runs on record at the head commit",
        }

    rc, worktree_diff = _run(["git", "diff", "--", TASKS_JSON_REL], target)
    uncommitted_flip = bool(rc == 0 and DONE_FLIP_ADDED_RE.search(worktree_diff or ""))
    checks["done_flip_containment"] = {
        "passed": not uncommitted_flip,
        "uncommitted_done_flip": uncommitted_flip,
        "detail": "any task flipped done must have a containing commit (the stranded-#73 class)",
    }

    checks["ci_greenness"] = {
        "passed": True,
        "status": "delegated",
        "detail": "native required checks own CI greenness; the witness never re-implements it",
    }

    escalations = list(checks["diff_accounting"]["deleted_tests_escalated"])
    passed = all(check.get("passed") for check in checks.values())
    report = {
        "schema_version": WITNESS_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "mode": "ci" if ci_mode else "local",
        "branch": branch,
        "base": resolved_base,
        "head_commit": head,
        "checks": checks,
        "escalations": escalations,
        "passed": passed,
    }
    try:
        report_path = target / WITNESS_REPORT_REL
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    except OSError:
        pass
    return report


def render_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Aegis delivery witness — {report.get('branch')} @ {report.get('head_commit')} "
        f"({report.get('mode')} mode, base {report.get('base')})",
    ]
    for name, check in report.get("checks", {}).items():
        verdict = "PASS" if check.get("passed") else "FAIL"
        status = check.get("status")
        suffix = f" [{status}]" if status else ""
        lines.append(f"- {name}: {verdict}{suffix}")
        if not check.get("passed"):
            for key in ("unaccounted", "deleted_tests_escalated", "missing_pass_at_head"):
                if check.get(key):
                    lines.append(f"  - {key}: {check[key]}")
    if report.get("escalations"):
        lines.append(f"- ESCALATION (human review required): {report['escalations']}")
    lines.append(f"Result: {'PASS' if report.get('passed') else 'FAIL'} — report at {WITNESS_REPORT_REL}")
    return "\n".join(lines) + "\n"


__all__ = ["WITNESS_REPORT_REL", "render_report", "run_witness"]
