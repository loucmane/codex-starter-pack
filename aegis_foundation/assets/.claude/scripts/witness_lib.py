"""Quiet deterministic Aegis delivery witness.

The witness is a zero-LLM boundary check computed from Git, the passive ledger,
and the declared scope configuration. Complete evidence is written to generated
artifacts while agent-facing output remains concise and is subsequently routed
through Aegis's shared context-budget renderer.

This module is stdlib-only and intentionally import-independent from the
Aegis package so installed hook/runtime assets retain their fallback contract.
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

WITNESS_SCHEMA_VERSION = "2"
WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"
DELIVERY_REPORT_REL = ".aegis/reports/delivery-report.md"
BRIEF_REL = ".aegis/brief.json"
TASKS_JSON_REL = ".taskmaster/tasks/tasks.json"

EXIT_CLASS_PASS = "pass"
EXIT_CLASS_FAIL = "fail"
EXIT_CLASS_UNSUPPORTED = "unsupported"
EXIT_CLASS_NOT_DERIVABLE_IN_CI = "not_derivable_in_ci"
EXIT_CODE_BY_CLASS = {
    EXIT_CLASS_PASS: 0,
    EXIT_CLASS_FAIL: 1,
    EXIT_CLASS_UNSUPPORTED: 2,
    EXIT_CLASS_NOT_DERIVABLE_IN_CI: 0,
}

TASK_BRANCH_RE = re.compile(r"task-?(\d+)", re.IGNORECASE)
DONE_FLIP_ADDED_RE = re.compile(
    r'^\+(?!\+\+).*"status"\s*:\s*"done"',
    re.MULTILINE,
)
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
TEST_PATH_PATTERNS = ("tests/*", "test/*", "*_test.*", "*.test.*", "test_*")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], cwd: Path, timeout: float = 10) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
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


def _read_events(root: Path, branch: str) -> dict[str, Any]:
    """Read branch evidence without creating or migrating the ledger store."""

    ledger_lib = _load_ledger_lib()
    if ledger_lib is None:
        return {
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "ledger_lib_unavailable",
            "events": [],
        }
    try:
        context = ledger_lib.repository_context(root)
        repository = context.get("repository_identity")
        worktree = context.get("worktree_root")
        ledger = ledger_lib.open_ledger(cwd=root, read_only=True)
        try:
            store = getattr(ledger, "path", None) or getattr(ledger, "directory", None)
            if store is not None and not Path(store).exists():
                return {
                    "status": EXIT_CLASS_UNSUPPORTED,
                    "reason": "ledger_store_unavailable",
                    "repository_identity": repository,
                    "worktree_root": worktree,
                    "events": [],
                }
            events = ledger.read(branch=branch) if branch else []
        finally:
            ledger.close()
    except Exception as exc:  # noqa: BLE001 - capability gap, never a witness crash.
        return {
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "ledger_store_unavailable",
            "error_type": type(exc).__name__,
            "events": [],
        }

    filtered = [
        event
        for event in events
        if (not event.get("repository_identity") or event.get("repository_identity") == repository)
        and (not event.get("worktree_root") or event.get("worktree_root") == worktree)
    ]
    return {
        "status": "available",
        "reason": None,
        "repository_identity": repository,
        "worktree_root": worktree,
        "events": filtered,
        "rows_read": len(events),
        "rows_selected": len(filtered),
    }


def _resolve_base(root: Path, base: str | None) -> str | None:
    candidates = [base] if base else []
    candidates += ["origin/main", "main", "origin/master", "master"]
    for candidate in candidates:
        if not candidate:
            continue
        rc, _ = _run(["git", "rev-parse", "--verify", "--quiet", candidate], root)
        if rc == 0:
            return candidate
    return None


def _diff_entries(root: Path, base: str | None) -> tuple[list[dict[str, Any]], str | None]:
    if not base:
        return [], "base_ref_unavailable"
    rc, output = _run(
        ["git", "diff", "--name-status", "-z", "--find-renames", f"{base}...HEAD"],
        root,
    )
    if rc != 0:
        return [], "git_diff_unavailable"
    tokens = output.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    entries: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        raw_status = tokens[index]
        index += 1
        if not raw_status:
            continue
        path_count = 2 if raw_status[:1] in {"R", "C"} else 1
        if index + path_count > len(tokens):
            return [], "git_diff_malformed"
        paths = tokens[index : index + path_count]
        index += path_count
        entries.append(
            {
                "status": raw_status[:1],
                "status_detail": raw_status,
                "paths": paths,
            }
        )
    return entries, None


def _matches_glob(path: str, glob: str) -> bool:
    if glob.endswith("/"):
        return path.startswith(glob)
    return fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(Path(path).name, glob)


def _is_test_path(path: str) -> bool:
    return any(_matches_glob(path, pattern) for pattern in TEST_PATH_PATTERNS) or "/tests/" in path


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _scope_for_branch(
    branch: str,
    events: list[dict[str, Any]],
    brief: dict[str, Any],
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
    scope_event_id = None
    if chosen is not None:
        task_id = chosen.get("extra", {}).get("task_id")
        globs = [
            value
            for value in chosen.get("extra", {}).get("path_globs", [])
            if isinstance(value, str) and value
        ]
        source = (
            "scope_record_confirmed"
            if chosen.get("extra", {}).get("confirmed")
            else "scope_record_inferred"
        )
        scope_event_id = chosen.get("event_id")
    if task_id is None and match:
        task_id = match.group(1)
        source = source if source != "none" else "branch_convention"
    if not globs:
        roots = brief.get("source_roots")
        globs = (
            [value for value in roots if isinstance(value, str) and value]
            if isinstance(roots, list)
            else []
        )
    witness_config = brief.get("witness") if isinstance(brief.get("witness"), dict) else {}
    always = witness_config.get("always_in_scope")
    if isinstance(always, list):
        globs += [value for value in always if isinstance(value, str) and value]
    return {
        "task_id": str(task_id) if task_id is not None else None,
        "path_globs": _dedupe(globs),
        "source": source,
        "scope_event_id": scope_event_id,
    }


def _account_diff(entries: list[dict[str, Any]], globs: list[str]) -> dict[str, Any]:
    paths: list[dict[str, Any]] = []
    unaccounted: list[str] = []
    deleted_tests: list[str] = []
    for entry in entries:
        entry_paths = entry["paths"]
        for offset, path in enumerate(entry_paths):
            matches = [glob for glob in globs if _matches_glob(path, glob)]
            if not matches:
                unaccounted.append(path)
            role = "current"
            if entry["status"] in {"R", "C"}:
                role = "previous" if offset == 0 else "current"
            paths.append(
                {
                    "status": entry["status"],
                    "status_detail": entry["status_detail"],
                    "role": role,
                    "path": path,
                    "accounted": bool(matches),
                    "matching_globs": matches,
                }
            )
        if entry["status"] == "D":
            deleted_tests += [path for path in entry_paths if _is_test_path(path)]
        elif entry["status"] == "R" and len(entry_paths) == 2:
            previous, current = entry_paths
            if _is_test_path(previous) and not _is_test_path(current):
                deleted_tests.append(previous)
    return {
        "entries": entries,
        "paths": paths,
        "unaccounted": _dedupe(unaccounted),
        "deleted_tests_escalated": _dedupe(deleted_tests),
    }


def _commit_resolves_to_head(root: Path, candidate: Any, head_full: str | None) -> bool:
    value = str(candidate or "").strip()
    if not head_full or not COMMIT_RE.fullmatch(value):
        return False
    rc, resolved = _run(["git", "rev-parse", "--verify", f"{value}^{{commit}}"], root)
    return rc == 0 and resolved.strip() == head_full


def _verification_check(
    root: Path,
    *,
    branch: str,
    head_full: str | None,
    brief: dict[str, Any],
    brief_available: bool,
    ledger_result: dict[str, Any],
    ci_mode: bool,
) -> dict[str, Any]:
    if ci_mode:
        return {
            "passed": True,
            "status": EXIT_CLASS_NOT_DERIVABLE_IN_CI,
            "required": [],
            "matched": [],
            "missing_pass_at_head": [],
            "detail": (
                "the out-of-worktree ledger does not travel to CI; the local witness "
                "artifact owns verification-at-HEAD"
            ),
        }
    if not head_full:
        return {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "head_unavailable",
            "detail": "verification-at-HEAD requires a resolvable current commit",
        }
    if ledger_result.get("status") != "available":
        return {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": ledger_result.get("reason"),
            "detail": "the local passive ledger is required for verification-at-HEAD",
        }
    if not brief_available or not isinstance(brief.get("gates"), dict):
        return {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "gate_configuration_unavailable",
            "detail": "the local brief must declare the verification gate map",
        }

    gates = brief["gates"]
    required = [
        f"{package}:{gate}"
        for package, package_gates in sorted(gates.items())
        if isinstance(package_gates, dict)
        for gate in sorted(package_gates)
    ]
    events = ledger_result.get("events", [])
    verifications = [event for event in events if event.get("event_type") == "verification"]
    missing: list[str] = []
    matched: list[dict[str, Any]] = []
    for key in required:
        package, gate = key.split(":", 1)
        match = next(
            (
                event
                for event in reversed(verifications)
                if event.get("extra", {}).get("package") == package
                and event.get("extra", {}).get("gate") == gate
                and event.get("exit_class") == EXIT_CLASS_PASS
                and _commit_resolves_to_head(
                    root,
                    event.get("extra", {}).get("commit") or event.get("head"),
                    head_full,
                )
            ),
            None,
        )
        if match is None:
            missing.append(key)
            continue
        matched.append(
            {
                "gate": key,
                "event_id": match.get("event_id"),
                "recorded_head": match.get("head"),
                "recorded_commit": match.get("extra", {}).get("commit"),
                "worktree_root": match.get("worktree_root"),
                "agent_id": match.get("agent_id"),
                "parent_agent_id": match.get("parent_agent_id"),
            }
        )
    return {
        "passed": not missing,
        "status": EXIT_CLASS_PASS if not missing else EXIT_CLASS_FAIL,
        "required": required,
        "matched": matched,
        "missing_pass_at_head": missing,
        "head_full": head_full,
        "branch": branch,
        "detail": "every registered gate needs a passing event tied to the exact current HEAD",
    }


def _done_flip_check(root: Path, base: str | None) -> dict[str, Any]:
    rc, pending_diff = _run(["git", "diff", "HEAD", "--", TASKS_JSON_REL], root)
    if rc != 0:
        return {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "task_diff_unavailable",
            "detail": "task-flip containment needs a readable HEAD-to-worktree diff",
        }
    pending = len(DONE_FLIP_ADDED_RE.findall(pending_diff or ""))
    committed = 0
    if base:
        rc, committed_diff = _run(
            ["git", "diff", f"{base}...HEAD", "--", TASKS_JSON_REL],
            root,
        )
        if rc == 0:
            committed = len(DONE_FLIP_ADDED_RE.findall(committed_diff or ""))
    return {
        "passed": pending == 0,
        "status": EXIT_CLASS_PASS if pending == 0 else EXIT_CLASS_FAIL,
        "uncommitted_done_flip": pending > 0,
        "uncommitted_done_flip_count": pending,
        "contained_done_flip_count": committed,
        "detail": "a done flip must be contained by a commit on the delivery branch",
    }


def _classify(checks: dict[str, Any], *, ci_mode: bool) -> str:
    if any(check.get("passed") is False for check in checks.values()):
        return EXIT_CLASS_FAIL
    if any(check.get("status") == EXIT_CLASS_UNSUPPORTED for check in checks.values()):
        return EXIT_CLASS_UNSUPPORTED
    if ci_mode and any(
        check.get("status") == EXIT_CLASS_NOT_DERIVABLE_IN_CI for check in checks.values()
    ):
        return EXIT_CLASS_NOT_DERIVABLE_IN_CI
    return EXIT_CLASS_PASS


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _markdown(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_delivery_report(report: dict[str, Any]) -> str:
    """Render the complete deterministic PR-ready artifact."""

    lines = [
        "# Aegis Delivery Report",
        "",
        (
            f"- **Result:** {report.get('exit_class')} "
            f"(process exit {report.get('process_exit_code')})"
        ),
        f"- **Mode:** {report.get('mode')}",
        f"- **Branch:** {report.get('branch') or '(unavailable)'}",
        f"- **HEAD:** {report.get('head_commit_full') or '(unavailable)'}",
        f"- **Base:** {report.get('base') or '(unavailable)'}",
        "",
        "## Checks",
        "",
        "| Check | Status | Passed | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for name, check in report.get("checks", {}).items():
        lines.append(
            f"| {_markdown(name)} | {_markdown(check.get('status'))} | "
            f"{_markdown(check.get('passed'))} | {_markdown(check.get('detail'))} |"
        )

    scope = report.get("scope", {})
    lines += [
        "",
        "## Scope",
        "",
        f"- Task: {scope.get('task_id') or '(unmapped)'}",
        f"- Source: {scope.get('source') or 'none'}",
        f"- Scope event: {scope.get('scope_event_id') or '(none)'}",
        "- Path globs:",
    ]
    lines += [f"  - {glob}" for glob in scope.get("path_globs", [])] or ["  - _(none)_"]

    accounting = report.get("checks", {}).get("diff_accounting", {})
    lines += [
        "",
        "## Complete Diff Accounting",
        "",
        "| Git status | Role | Path | Accounted | Matching scope |",
        "| --- | --- | --- | --- | --- |",
    ]
    path_rows = accounting.get("paths", [])
    if path_rows:
        for item in path_rows:
            matches = ", ".join(item.get("matching_globs", [])) or "—"
            lines.append(
                f"| {_markdown(item.get('status_detail'))} | {_markdown(item.get('role'))} | "
                f"{_markdown(item.get('path'))} | {_markdown(item.get('accounted'))} | "
                f"{_markdown(matches)} |"
            )
    else:
        lines.append("| — | — | _(no changed paths)_ | true | — |")

    verification = report.get("checks", {}).get("verification_at_head", {})
    lines += ["", "## Verification At HEAD", ""]
    lines.append(
        "- Required gates: "
        + (", ".join(str(item) for item in verification.get("required", [])) or "_(none)_")
    )
    lines.append(
        "- Missing passing gates: "
        + (
            ", ".join(str(item) for item in verification.get("missing_pass_at_head", []))
            or "_(none)_"
        )
    )
    for item in verification.get("matched", []):
        lines.append(
            f"- {item.get('gate')} -> event {item.get('event_id')}, "
            f"worktree {item.get('worktree_root') or '(legacy)'}"
        )

    containment = report.get("checks", {}).get("done_flip_containment", {})
    lines += [
        "",
        "## Task And CI Boundary",
        "",
        f"- Uncommitted done flips: {containment.get('uncommitted_done_flip_count', 0)}",
        f"- Contained done flips: {containment.get('contained_done_flip_count', 0)}",
        "- Native CI: delegated to the repository's required checks.",
    ]
    escalations = report.get("escalations", [])
    lines += ["", "## Escalations", ""]
    lines += [f"- {item}" for item in escalations] or ["- None."]
    lines += [
        "",
        "## Rollback",
        "",
        (
            "Revert the Task 241 witness change and resume the previous witness plus "
            "the manual shipping checklist. No ledger or legacy workflow data needs repair."
        ),
        "",
    ]
    return "\n".join(lines)


def run_witness(
    root: str | Path,
    *,
    base: str | None = None,
    ci_mode: bool = False,
) -> dict[str, Any]:
    """Run the deterministic delivery boundary; never raises for missing capabilities."""

    target = Path(root).resolve()
    rc, branch_out = _run(["git", "branch", "--show-current"], target)
    branch = branch_out.strip() if rc == 0 else ""
    if not branch:
        branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    rc, head_short_out = _run(["git", "rev-parse", "--short", "HEAD"], target)
    head_short = head_short_out.strip() if rc == 0 else None
    rc, head_full_out = _run(["git", "rev-parse", "HEAD"], target)
    head_full = head_full_out.strip() if rc == 0 else None
    resolved_base = _resolve_base(target, base)
    diff_entries, diff_error = _diff_entries(target, resolved_base)

    brief_value = _read_json(target / BRIEF_REL)
    brief_available = isinstance(brief_value, dict)
    brief = brief_value if brief_available else {}
    ledger_result = (
        {
            "status": EXIT_CLASS_NOT_DERIVABLE_IN_CI,
            "reason": "ledger_not_available_in_ci",
            "events": [],
        }
        if ci_mode
        else _read_events(target, branch)
    )
    scope = _scope_for_branch(branch, ledger_result.get("events", []), brief)
    checks: dict[str, Any] = {}

    repository_ready = bool(branch and head_full and resolved_base and not diff_error)
    checks["repository_state"] = {
        "passed": True if repository_ready else None,
        "status": EXIT_CLASS_PASS if repository_ready else EXIT_CLASS_UNSUPPORTED,
        "reason": (
            diff_error if diff_error else (None if repository_ready else "git_state_unavailable")
        ),
        "branch": branch,
        "head_full": head_full,
        "base": resolved_base,
        "worktree_root": ledger_result.get("worktree_root") or target.as_posix(),
        "repository_identity": ledger_result.get("repository_identity"),
        "detail": "branch, HEAD, base ref, and complete diff inventory must be derivable",
    }

    if not branch:
        checks["scope_mapping"] = {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "task_id": None,
            "source": "none",
            "detail": "scope mapping requires the local branch or GITHUB_HEAD_REF",
        }
    else:
        checks["scope_mapping"] = {
            "passed": scope["task_id"] is not None,
            "status": EXIT_CLASS_PASS if scope["task_id"] is not None else EXIT_CLASS_FAIL,
            "task_id": scope["task_id"],
            "source": scope["source"],
            "scope_event_id": scope["scope_event_id"],
            "detail": "the branch must map to a scope record or the task-NN convention",
        }

    accounting = _account_diff(diff_entries, scope["path_globs"])
    deleted_tests = accounting["deleted_tests_escalated"]
    if diff_error:
        checks["diff_accounting"] = {
            **accounting,
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": diff_error,
            "detail": "complete Git diff accounting is unavailable",
        }
    elif not scope["path_globs"]:
        if deleted_tests:
            checks["diff_accounting"] = {
                **accounting,
                "passed": False,
                "status": EXIT_CLASS_FAIL,
                "reason": "test_deletion",
                "detail": "scope globs are unavailable, but test deletion remains a hard failure",
            }
        elif ci_mode:
            checks["diff_accounting"] = {
                **accounting,
                "passed": True,
                "status": EXIT_CLASS_NOT_DERIVABLE_IN_CI,
                "reason": "scope_globs_not_available_in_ci",
                "detail": (
                    "local scope globs do not travel to CI; git-derivable escalations still run"
                ),
            }
        else:
            checks["diff_accounting"] = {
                **accounting,
                "passed": None,
                "status": EXIT_CLASS_UNSUPPORTED,
                "reason": "scope_globs_unavailable",
                "detail": "local diff accounting requires declared scope globs",
            }
    else:
        diff_passed = not accounting["unaccounted"] and not deleted_tests
        checks["diff_accounting"] = {
            **accounting,
            "passed": diff_passed,
            "status": EXIT_CLASS_PASS if diff_passed else EXIT_CLASS_FAIL,
            "files_in_diff": len(diff_entries),
            "paths_in_diff": len(accounting["paths"]),
            "globs": scope["path_globs"],
            "detail": "every old/new diff path must match scope; test deletion escalates",
        }

    checks["verification_at_head"] = _verification_check(
        target,
        branch=branch,
        head_full=head_full,
        brief=brief,
        brief_available=brief_available,
        ledger_result=ledger_result,
        ci_mode=ci_mode,
    )
    checks["done_flip_containment"] = _done_flip_check(target, resolved_base)
    checks["ci_greenness"] = {
        "passed": True,
        "status": "delegated",
        "detail": "native required checks own CI greenness; the witness does not re-implement it",
    }

    exit_class = _classify(checks, ci_mode=ci_mode)
    report: dict[str, Any] = {
        "schema_version": WITNESS_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "mode": "ci" if ci_mode else "local",
        "branch": branch,
        "base": resolved_base,
        "head_commit": head_short,
        "head_commit_full": head_full,
        "scope": scope,
        "ledger_capability": {
            key: value for key, value in ledger_result.items() if key not in {"events"}
        },
        "checks": checks,
        "escalations": deleted_tests,
        "exit_class": exit_class,
        "process_exit_code": EXIT_CODE_BY_CLASS[exit_class],
        "passed": exit_class in {EXIT_CLASS_PASS, EXIT_CLASS_NOT_DERIVABLE_IN_CI},
        "artifacts": [
            {"path": WITNESS_REPORT_REL, "format": "json", "complete": True},
            {"path": DELIVERY_REPORT_REL, "format": "markdown", "complete": True},
        ],
    }
    try:
        _atomic_write(target / DELIVERY_REPORT_REL, render_delivery_report(report))
        _atomic_write(
            target / WITNESS_REPORT_REL,
            json.dumps(report, indent=2, sort_keys=True) + "\n",
        )
    except OSError as exc:
        checks["artifact_write"] = {
            "passed": None,
            "status": EXIT_CLASS_UNSUPPORTED,
            "reason": "artifact_write_failed",
            "error_type": type(exc).__name__,
            "detail": "complete witness artifacts could not be written",
        }
        exit_class = _classify(checks, ci_mode=ci_mode)
        report["exit_class"] = exit_class
        report["process_exit_code"] = EXIT_CODE_BY_CLASS[exit_class]
        report["passed"] = exit_class in {
            EXIT_CLASS_PASS,
            EXIT_CLASS_NOT_DERIVABLE_IN_CI,
        }
    return report


def render_report(report: dict[str, Any]) -> str:
    """Render a stable one-screen summary; complete lists stay in artifacts."""

    lines = [
        f"Aegis witness: {str(report.get('exit_class') or 'unsupported').upper()} "
        f"({report.get('mode')} mode)",
        (
            f"Branch: {report.get('branch') or '(unavailable)'} @ "
            f"{report.get('head_commit') or '(unavailable)'}; "
            f"base={report.get('base') or '(unavailable)'}"
        ),
    ]
    for name, check in report.get("checks", {}).items():
        status = str(check.get("status") or "unknown").upper()
        lines.append(f"- {name}: {status}")
        if name == "diff_accounting":
            lines.append(
                "  "
                f"paths={len(check.get('paths', []))}; "
                f"unaccounted={len(check.get('unaccounted', []))}; "
                f"test_escalations={len(check.get('deleted_tests_escalated', []))}"
            )
        elif name == "verification_at_head":
            lines.append(
                "  "
                f"required={len(check.get('required', []))}; "
                f"missing={len(check.get('missing_pass_at_head', []))}"
            )
    lines += [
        f"Result: {str(report.get('exit_class') or 'unsupported').upper()} "
        f"(exit {report.get('process_exit_code', 2)})",
        f"Artifacts: {WITNESS_REPORT_REL}, {DELIVERY_REPORT_REL}",
    ]
    return "\n".join(lines) + "\n"


def exit_code(report: dict[str, Any]) -> int:
    value = report.get("process_exit_code")
    if isinstance(value, int):
        return value
    exit_class = str(report.get("exit_class") or "")
    if exit_class in EXIT_CODE_BY_CLASS:
        return EXIT_CODE_BY_CLASS[exit_class]
    return 0 if report.get("passed") else 1


__all__ = [
    "DELIVERY_REPORT_REL",
    "EXIT_CLASS_FAIL",
    "EXIT_CLASS_NOT_DERIVABLE_IN_CI",
    "EXIT_CLASS_PASS",
    "EXIT_CLASS_UNSUPPORTED",
    "EXIT_CODE_BY_CLASS",
    "WITNESS_REPORT_REL",
    "exit_code",
    "render_delivery_report",
    "render_report",
    "run_witness",
]
