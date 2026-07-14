"""Package-style Aegis CLI entrypoint.

The command surface intentionally delegates to ``scripts._aegis_installer`` so the
repository-local ``scripts/codex-task aegis`` wrapper and package-style ``aegis`` wrapper
share the same deterministic installer behavior.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from aegis_foundation import legacy_projection, mcp_registration, output_budget
from aegis_foundation.resources import packaged_asset_root
from aegis_foundation.version import __version__
from scripts import _aegis_installer

BRIEF_REASON_CHOICES = (
    "session-start",
    "session-resume",
    "post-merge",
    "task-status-change",
    "orientation",
    "pre-delivery",
    "verification",
    "risk-register-change",
    "manual",
)


def _dump_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _add_output_budget_arguments(
    parser: argparse.ArgumentParser,
    *,
    add_json: bool = False,
    json_help: str = "Print structured JSON output.",
) -> None:
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument(
        "--verbose",
        action="store_true",
        help="Print a larger but still bounded diagnostic sample (120 lines / 32 KiB).",
    )
    detail.add_argument(
        "--all",
        dest="all_output",
        action="store_true",
        help="Print intentional full detail without a renderer cap.",
    )
    if add_json:
        parser.add_argument("--json", action="store_true", help=json_help)


def _print_budgeted_json(
    payload: Mapping[str, Any],
    args: argparse.Namespace,
    *,
    command: str,
    artifact_paths: Sequence[str] = (),
    next_action: str | None = None,
) -> None:
    print(
        output_budget.render_json(
            payload,
            command=command,
            mode=output_budget.mode_from_args(args),
            artifact_paths=artifact_paths,
            next_action=next_action,
        ),
        end="",
    )


def _print_budgeted_text(
    text: str,
    payload: Mapping[str, Any],
    args: argparse.Namespace,
    *,
    command: str,
    artifact_paths: Sequence[str] = (),
    next_action: str | None = None,
) -> None:
    print(
        output_budget.render_text(
            text,
            payload,
            command=command,
            mode=output_budget.mode_from_args(args),
            artifact_paths=artifact_paths,
            next_action=next_action,
        ),
        end="",
    )


def _candidate_source_roots(explicit_source_root: str | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit_source_root:
        candidates.append(Path(explicit_source_root))
    env_source_root = os.environ.get("AEGIS_SOURCE_ROOT")
    if env_source_root:
        candidates.append(Path(env_source_root))
    for parent in Path(__file__).resolve().parents:
        candidates.append(parent)
    return candidates


def _looks_like_source_root(path: Path) -> bool:
    return (
        (path / "schemas" / "aegis" / "foundation-manifest.schema.json").is_file()
        and (path / "scripts" / "_aegis_installer.py").is_file()
        and (path / ".claude" / "scripts" / "pretooluse-gate.sh").is_file()
    )


@contextmanager
def _resolve_source_root(explicit_source_root: str | None):
    for candidate in _candidate_source_roots(explicit_source_root):
        source_root = candidate.expanduser().resolve()
        if _looks_like_source_root(source_root):
            yield source_root
            return
    with packaged_asset_root() as source_root:
        if _looks_like_source_root(source_root):
            yield source_root
            return
    raise _aegis_installer.AegisError("Unable to resolve Aegis source or packaged assets.")


def _agents_from_args(args: argparse.Namespace) -> list[str]:
    return list(getattr(args, "agent", None) or [])


def handle_inspect(args: argparse.Namespace) -> int:
    payload = _aegis_installer.inspect_project(
        args.target_dir,
        profile=args.profile,
        invoking_agent=_aegis_installer.invoking_agent_from_environment(),
    )
    _dump_json(payload)
    return 0


def handle_plan_install(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.plan_install(
            args.target_dir,
            source_root=source_root,
            profile=args.profile,
            primary_agent=args.primary_agent,
            agents=_agents_from_args(args),
        )
    _dump_json(payload)
    return 0


def handle_init(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.initialize_project(
            args.target_dir,
            source_root=source_root,
            profile=args.profile,
            primary_agent=args.primary_agent,
            agents=_agents_from_args(args),
            verify_after_install=not args.no_verify,
        )
    _dump_json(payload)
    if payload.get("status") in {"refused", "failed"}:
        print("Aegis init failed or was refused", file=sys.stderr)
        return 1
    return 0


def handle_status(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.status(
            args.target_dir,
            source_root=source_root,
            invoking_agent=_aegis_installer.invoking_agent_from_environment(),
        )
    _print_budgeted_json(
        payload,
        args,
        command="status",
        artifact_paths=(
            _aegis_installer.AEGIS_MANIFEST_REL,
            _aegis_installer.AEGIS_CURRENT_WORK_REL,
            _aegis_installer.AEGIS_PENDING_TRACKING_REL,
            _aegis_installer.AEGIS_VERIFY_REPORT_REL,
            _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
        ),
        next_action="./.aegis/bin/aegis next --target-dir .",
    )
    return 0


def handle_update(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.project_update(
            args.target_dir,
            source_root=source_root,
            apply=args.apply,
        )
    _print_budgeted_json(
        payload,
        args,
        command="update",
        artifact_paths=(
            _aegis_installer.AEGIS_PLAN_REPORT_REL,
            _aegis_installer.AEGIS_UPDATE_REPORT_REL,
            _aegis_installer.AEGIS_VERIFY_REPORT_REL,
        ),
        next_action="./.aegis/bin/aegis status --target-dir .",
    )
    return 1 if payload.get("status") in {"failed", "refused"} else 0


def _load_ledger_lib(source_root: Path):
    """Import ledger_lib from the runtime source root, same pattern as aegis hook."""

    script = source_root / ".claude" / "scripts" / "ledger_lib.py"
    spec = importlib.util.spec_from_file_location("_aegis_cli_ledger_lib", script)
    if spec is None or spec.loader is None:
        raise _aegis_installer.AegisError(f"unable to load ledger_lib from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_brief_lib(source_root: Path):
    script = source_root / ".claude" / "scripts" / "brief_lib.py"
    spec = importlib.util.spec_from_file_location("_aegis_cli_brief_lib", script)
    if spec is None or spec.loader is None:
        raise _aegis_installer.AegisError(f"unable to load brief_lib from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _refresh_capsule_if_stale(
    source_root: Path, target_dir: str, *, reason: str
) -> dict[str, Any] | None:
    """Refresh the computed capsule at workflow boundaries only when stale."""

    try:
        brief_lib = _load_brief_lib(source_root)
        status = brief_lib.capsule_status(target_dir)
        if status.get("fresh"):
            return {"refreshed": False, "reason": reason, "status": status}
        capsule = brief_lib.compile_capsule(target_dir, reason=reason)
        brief_lib.write_capsule(target_dir, capsule, brief_lib.render_markdown(capsule))
        return {"refreshed": True, "reason": reason, "status": status}
    except Exception as exc:  # noqa: BLE001 - boundary refresh is advisory, never a gate.
        return {"refreshed": False, "reason": reason, "error": str(exc)}


def _project_legacy_sweh(
    ledger_lib: Any,
    target_dir: str | Path,
    output_paths: Sequence[Path],
    *,
    dry_run: bool = False,
    read_limit: int = 500,
    limit: int = 25,
    include_mutations: bool = False,
    include_gate_decisions: bool = False,
) -> tuple[dict[str, Any], list[legacy_projection.ProjectionResult]]:
    """Project selected ledger events into legacy S:W:H:E markdown surfaces."""

    target = Path(target_dir).resolve()
    ledger = ledger_lib.open_ledger(cwd=target, read_only=True)
    try:
        events = ledger.read(limit=read_limit)
    finally:
        ledger.close()
    selected = legacy_projection.projectable_events(
        events,
        include_mutations=include_mutations,
        include_gate_decisions=include_gate_decisions,
        limit=limit,
    )
    deduped: list[Path] = []
    seen: set[Path] = set()
    for output_path in output_paths:
        key = output_path.resolve() if output_path.exists() else output_path
        if key in seen:
            continue
        seen.add(key)
        deduped.append(output_path)
    results = [
        legacy_projection.project_to_file(selected, output_path, dry_run=dry_run)
        for output_path in deduped
    ]
    payload = {
        "status": "preview" if dry_run else "applied",
        "output_path": results[0].output_path.as_posix() if len(results) == 1 else None,
        "output_paths": [result.output_path.as_posix() for result in results],
        "event_count": len(selected),
        "last_event_id": str(selected[-1].get("event_id")) if selected else None,
        "changed": any(result.changed for result in results),
        "changed_paths": [result.output_path.as_posix() for result in results if result.changed],
        "dry_run": dry_run,
        "include_mutations": include_mutations,
        "include_gate_decisions": include_gate_decisions,
    }
    return payload, results


def _scope_ledger_context(target: Path) -> dict[str, str | None]:
    """Resolve stable session/work identity from the active Aegis envelope."""

    current_work_path = target / ".aegis" / "state" / "current-work.json"
    try:
        current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"session_id": None, "work_id": None}
    if not isinstance(current_work, dict):
        return {"session_id": None, "work_id": None}

    task = current_work.get("task") if isinstance(current_work.get("task"), dict) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), dict) else {}
    task_id = str(task.get("id") or "").strip()
    slug = str(task.get("slug") or "").strip()
    session_rel = str(paths.get("session") or "").strip()
    session_id = Path(session_rel).stem if session_rel else task_id or None

    if str(current_work.get("mode") or "").strip() == "observation" and slug:
        work_id = f"observe-{slug}"
    elif task_id and slug:
        work_id = f"task-{task_id}-{slug}"
    elif task_id:
        work_id = f"task-{task_id}"
    else:
        work_id = None
    return {"session_id": session_id, "work_id": work_id}


def _boundary_fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _normalized_witness_checks(report: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    checks = report.get("checks") if isinstance(report.get("checks"), Mapping) else {}
    normalized: dict[str, dict[str, Any]] = {}
    for name, raw_check in sorted(checks.items()):
        check = raw_check if isinstance(raw_check, Mapping) else {}
        normalized[str(name)] = {
            "passed": bool(check.get("passed")),
            "status": str(check.get("status") or "") or None,
        }
    return normalized


def _record_boundary_event(
    source_root: Path,
    target: Path,
    *,
    event_type: str,
    branch: str,
    outcome: str,
    handler: str,
    extra: Mapping[str, Any],
    paths: Sequence[str] = (),
) -> tuple[Any, dict[str, Any]]:
    """Append one normalized boundary event unless its state was already recorded."""

    ledger_lib = _load_ledger_lib(source_root)
    scope_context = _scope_ledger_context(target)
    normalized_extra = dict(extra)
    normalized_extra["boundary_kind"] = event_type
    if scope_context["work_id"]:
        normalized_extra["work_id"] = scope_context["work_id"]
    fingerprint_payload = {
        key: value for key, value in normalized_extra.items() if key != "boundary_fingerprint"
    }
    fingerprint_payload["branch"] = branch
    fingerprint = _boundary_fingerprint(fingerprint_payload)
    normalized_extra["boundary_fingerprint"] = fingerprint

    ledger = ledger_lib.open_ledger(cwd=target)
    try:
        existing = ledger.read(event_type=event_type)
        for event in reversed(existing):
            event_extra = event.get("extra") if isinstance(event.get("extra"), Mapping) else {}
            if (
                str(event.get("branch") or "") == branch
                and event_extra.get("boundary_kind") == event_type
                and event_extra.get("boundary_fingerprint") == fingerprint
            ):
                return ledger_lib, {
                    "status": "unchanged",
                    "event_id": event.get("event_id"),
                    "event_type": event_type,
                    "boundary_fingerprint": fingerprint,
                }

        invoking_agent = _aegis_installer.invoking_agent_from_environment()
        recorded = ledger.append(
            {
                "branch": branch,
                "cwd": target.as_posix(),
                "event_type": event_type,
                "session_id": scope_context["session_id"],
                "agent_id": invoking_agent,
                "agent_type": invoking_agent,
                "handler": handler,
                "paths": list(paths),
                "outcome": outcome,
                "exit_class": outcome,
                "payload_digest": fingerprint,
                "extra": normalized_extra,
            }
        )
        return ledger_lib, {
            "status": "recorded",
            "event_id": recorded.get("event_id"),
            "event_type": event_type,
            "boundary_fingerprint": fingerprint,
        }
    finally:
        ledger.close()


def _project_boundary_event(
    ledger_lib: Any,
    target: Path,
    *,
    read_limit: int = 500,
    limit: int = 25,
) -> dict[str, Any]:
    surfaces = legacy_projection.active_surface_paths(target)
    if not surfaces:
        return {
            "status": "skipped",
            "reason": "no existing active legacy surfaces",
            "output_paths": [],
            "changed": False,
        }
    try:
        payload, _results = _project_legacy_sweh(
            ledger_lib,
            target,
            surfaces,
            read_limit=read_limit,
            limit=limit,
        )
        return payload
    except Exception as exc:  # noqa: BLE001 - projection is advisory at boundaries.
        return {
            "status": "warning",
            "reason": str(exc),
            "error_type": type(exc).__name__,
            "output_paths": [path.as_posix() for path in surfaces],
            "changed": False,
        }


def _record_witness_boundary(
    source_root: Path,
    target: Path,
    report: Mapping[str, Any],
    *,
    report_path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    checks = _normalized_witness_checks(report)
    passed = bool(report.get("passed"))
    extra = {
        "action": "witness",
        "base": report.get("base"),
        "checks": checks,
        "escalations": list(report.get("escalations") or []),
        "head_commit": report.get("head_commit"),
        "mode": report.get("mode"),
        "passed": passed,
        "report_path": report_path,
    }
    ledger_lib, boundary = _record_boundary_event(
        source_root,
        target,
        event_type="witness",
        branch=str(report.get("branch") or ""),
        outcome="pass" if passed else "fail",
        handler="aegis:witness",
        extra=extra,
        paths=[report_path],
    )
    return boundary, _project_boundary_event(ledger_lib, target)


def _record_delivery_boundary(
    source_root: Path,
    target: Path,
    snapshot: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pr = snapshot.get("pr") if isinstance(snapshot.get("pr"), Mapping) else {}
    checks = snapshot.get("checks") if isinstance(snapshot.get("checks"), Mapping) else {}
    extra = {
        "action": snapshot.get("action"),
        "upstream": snapshot.get("upstream"),
        "head_commit": snapshot.get("head_commit"),
        "pr_number": pr.get("number"),
        "url": pr.get("url"),
        "state": pr.get("state"),
        "is_draft": bool(pr.get("isDraft")) if pr else None,
        "merge_state": pr.get("mergeStateStatus"),
        "merged_at": pr.get("mergedAt"),
        "closed_at": pr.get("closedAt"),
        "checks_state": checks.get("state"),
    }
    ledger_lib, boundary = _record_boundary_event(
        source_root,
        target,
        event_type="delivery",
        branch=str(snapshot.get("branch") or ""),
        outcome="pass",
        handler="aegis:delivery-sync",
        extra=extra,
    )
    return boundary, _project_boundary_event(ledger_lib, target)


def _load_witness_lib(source_root: Path):
    script = source_root / ".claude" / "scripts" / "witness_lib.py"
    spec = importlib.util.spec_from_file_location("_aegis_cli_witness_lib", script)
    if spec is None or spec.loader is None:
        raise _aegis_installer.AegisError(f"unable to load witness_lib from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def handle_replay(args: argparse.Namespace) -> int:
    import tempfile

    from aegis_foundation import replay

    with _resolve_source_root(args.source_root) as source_root:
        work_dir = args.work_dir or tempfile.mkdtemp(prefix="aegis-replay-")
        report = replay.run_corpus(args.corpus, source_root=source_root, work_dir=work_dir)
        artifact_paths = (str(report.get("report_path") or "aegis-replay-report.json"),)
        if args.json:
            _print_budgeted_json(
                report,
                args,
                command="replay",
                artifact_paths=artifact_paths,
                next_action=f"python3 -m json.tool {artifact_paths[0]}",
            )
        else:
            _print_budgeted_text(
                replay.render_report(report),
                report,
                args,
                command="replay",
                artifact_paths=artifact_paths,
                next_action=f"python3 -m json.tool {artifact_paths[0]}",
            )
        return 0 if report.get("passed") else 1


def handle_witness(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        _refresh_capsule_if_stale(source_root, args.target_dir, reason="pre-delivery")
        witness_lib = _load_witness_lib(source_root)
        report = witness_lib.run_witness(args.target_dir, base=args.base, ci_mode=args.ci)
        if args.ci:
            report["boundary_event"] = {"status": "skipped", "reason": "ci_mode"}
            report["legacy_projection"] = {"status": "skipped", "reason": "ci_mode"}
        else:
            try:
                boundary, projection = _record_witness_boundary(
                    source_root,
                    Path(args.target_dir).resolve(),
                    report,
                    report_path=str(
                        getattr(
                            witness_lib, "WITNESS_REPORT_REL", ".aegis/reports/witness-report.json"
                        )
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - recording cannot change witness verdict.
                boundary = {
                    "status": "warning",
                    "reason": str(exc),
                    "error_type": type(exc).__name__,
                }
                projection = {
                    "status": "skipped",
                    "reason": "boundary event was not recorded",
                }
            report["boundary_event"] = boundary
            report["legacy_projection"] = projection
        artifact_paths = (
            str(getattr(witness_lib, "WITNESS_REPORT_REL", ".aegis/reports/witness-report.json")),
        )
        if args.json:
            _print_budgeted_json(
                report,
                args,
                command="witness",
                artifact_paths=artifact_paths,
                next_action="git status --short",
            )
        else:
            rendered = witness_lib.render_report(report)
            rendered += f"Boundary event: {report['boundary_event']['status']}\n"
            rendered += f"Legacy S:W:H:E projection: {report['legacy_projection']['status']}\n"
            _print_budgeted_text(
                rendered,
                report,
                args,
                command="witness",
                artifact_paths=artifact_paths,
                next_action="git status --short",
            )
        return 0 if report.get("passed") else 1


def handle_delivery(args: argparse.Namespace) -> int:
    if args.delivery_subcommand != "sync":
        raise _aegis_installer.AegisError("unknown delivery subcommand")
    with _resolve_source_root(args.source_root) as source_root:
        snapshot = _aegis_installer.delivery_snapshot(
            args.target_dir,
            pr_number=args.pr_number,
            branch=args.branch,
        )
        if not snapshot.get("available"):
            payload = {
                "status": "failed",
                "snapshot": snapshot,
                "boundary_event": {"status": "skipped"},
                "legacy_projection": {"status": "skipped"},
            }
            if args.json:
                _dump_json(payload)
            else:
                print(f"Aegis delivery sync failed: {snapshot.get('reason')}", file=sys.stderr)
            return 1

        reason = "post-merge" if snapshot.get("action") == "pr_merged" else "pre-delivery"
        _refresh_capsule_if_stale(source_root, args.target_dir, reason=reason)
        if not snapshot.get("recordable"):
            boundary = {"status": "skipped", "reason": "no delivery state to record"}
            projection = {"status": "skipped", "reason": "no delivery state to record"}
        else:
            try:
                boundary, projection = _record_delivery_boundary(
                    source_root,
                    Path(args.target_dir).resolve(),
                    snapshot,
                )
            except Exception as exc:  # noqa: BLE001 - return structured synchronization failure.
                boundary = {
                    "status": "warning",
                    "reason": str(exc),
                    "error_type": type(exc).__name__,
                }
                projection = {
                    "status": "skipped",
                    "reason": "boundary event was not recorded",
                }
        payload = {
            "status": "synced"
            if boundary.get("status") in {"recorded", "unchanged"}
            else "no_change",
            "snapshot": snapshot,
            "boundary_event": boundary,
            "legacy_projection": projection,
        }
        if args.json:
            _dump_json(payload)
        else:
            pr = snapshot.get("pr") if isinstance(snapshot.get("pr"), Mapping) else {}
            pr_suffix = f" for PR #{pr.get('number')}" if pr.get("number") else ""
            print(f"Aegis delivery sync: {snapshot.get('action')}{pr_suffix}")
            print(f"Boundary event: {boundary.get('status')}")
            print(f"Legacy S:W:H:E projection: {projection.get('status')}")
        return 0 if boundary.get("status") in {"recorded", "unchanged", "skipped"} else 1


def handle_brief(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        brief_lib = _load_brief_lib(source_root)
        if args.status:
            status = brief_lib.capsule_status(args.target_dir)
            if args.json:
                _dump_json(status)
            else:
                print(brief_lib.render_status(status), end="")
            return 0 if status.get("fresh") else 1
        if args.check:
            ok, problems = brief_lib.check_capsule(args.target_dir)
            for problem in problems:
                print(problem, file=sys.stderr)
            print("capsule check: " + ("ok" if ok else "FAILED"))
            return 0 if ok else 1
        capsule = brief_lib.compile_capsule(args.target_dir, reason=args.reason)
        markdown = brief_lib.render_markdown(capsule)
        brief_lib.write_capsule(args.target_dir, capsule, markdown)
        if args.json:
            _dump_json(capsule)
        else:
            print(markdown, end="")
        return 0


def handle_coldstart(args: argparse.Namespace) -> int:
    """Forward-capture the current in-progress state as a falsifier-v2 scenario
    (TM 212). Mid-task states get squashed out of history; the corpus is built while
    the work is live."""

    from aegis_foundation import replay_coldstart

    if args.coldstart_subcommand != "capture":
        raise _aegis_installer.AegisError("unknown coldstart subcommand")
    scenario = replay_coldstart.capture_scenario(
        args.target_dir,
        scenario_id=args.id,
        expect_class=args.expect_class,
        fresh_null=args.fresh_null,
        note=args.note or "",
    )
    out = (
        Path(args.out)
        if args.out
        else Path(args.target_dir)
        / ".aegis"
        / "coldstart-scenarios"
        / f"{scenario['scenario_id']}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scenario, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "scenario_id": scenario["scenario_id"],
        "sha": scenario["sha"],
        "branch": scenario["branch"],
        "decision_class": scenario["expected"]["decision_class"],
        "dirty_patch_bytes": len(scenario["dirty_patch"]),
        "untracked_count": scenario["untracked_count"],
        "written": out.as_posix(),
    }
    _dump_json(summary)
    if scenario["dirty_patch_truncated"]:
        print(
            "warning: dirty patch truncated at cap; scenario replay will be incomplete",
            file=sys.stderr,
        )
    return 0


def handle_ab(args: argparse.Namespace) -> int:
    """Per-session A/B stopping-rule counter (spec §7 as amended 2026-06-11, TM 213).

    Counts genuine cold starts per arm from the ledger's session_begin stamps —
    only source == "startup" qualifies (resume/clear/compact are not orientation
    events) — and reports whether each arm has reached the fixed-n stopping rule
    that replaced the 2-week calendar window.
    """

    with _resolve_source_root(args.source_root) as source_root:
        ledger_lib = _load_ledger_lib(source_root)
        try:
            ledger = ledger_lib.open_ledger(cwd=args.target_dir)
        except ledger_lib.LedgerError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        try:
            events = ledger.read(event_type="session_begin")
        finally:
            ledger.close()
        target_root = Path(args.target_dir).resolve()
        arms = {"on": 0, "off": 0}
        excluded_non_startup = 0
        excluded_other_cwd = 0
        for event in events:
            extra = event.get("extra") if isinstance(event.get("extra"), dict) else {}
            if extra.get("source") != "startup":
                excluded_non_startup += 1
                continue
            # Harness/capture sessions (replay worktrees, hook captures) share this
            # ledger via the git common dir but start elsewhere — only sessions begun
            # in the target repo itself are live A/B observations.
            cwd = event.get("cwd")
            if cwd and Path(str(cwd)).resolve() != target_root:
                excluded_other_cwd += 1
                continue
            arms["on" if extra.get("capsule_injected") else "off"] += 1
        remaining = {arm: max(0, args.min_n - count) for arm, count in arms.items()}
        met = not any(remaining.values())
        payload = {
            "cold_starts": arms,
            "excluded_non_startup": excluded_non_startup,
            "excluded_other_cwd": excluded_other_cwd,
            "min_n_per_arm": args.min_n,
            "remaining": remaining,
            "stopping_rule_met": met,
        }
        if args.json:
            _dump_json(payload)
        else:
            print(
                f"Genuine cold starts (source=startup, in-repo): on={arms['on']} off={arms['off']}"
            )
            print(
                f"Excluded: {excluded_non_startup} non-startup, "
                f"{excluded_other_cwd} out-of-repo (harness/capture) stamps"
            )
            if met:
                print(
                    f"Stopping rule MET (>= {args.min_n} per arm) — compute the §7 metric and decide."
                )
            else:
                print(
                    f"Stopping rule not met (need {args.min_n}/arm): "
                    f"{remaining['on']} more on-arm, {remaining['off']} more off-arm."
                )
        return 0


def handle_override(args: argparse.Namespace) -> int:
    """Mint a one-shot, rate-limited break-glass token (recovery contract, TM 201).

    Honored by the gate only for workflow-state (tier-a/b) blocks and consumed on first
    use. Never a generic bypass: tier-c (protected paths, observation boundary,
    adversarial) blocks ignore it entirely.
    """

    import json as _json
    from datetime import datetime, timedelta, timezone

    target = Path(args.target_dir).resolve()
    reason_class = args.reason_class or "any"
    if reason_class not in {"any", "readiness_blocked", "pending_tracking"}:
        print(
            f"override reason-class not eligible for break-glass: {reason_class}", file=sys.stderr
        )
        return 1
    state_dir = target / ".aegis" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    counter_path = state_dir / "override-rate.json"
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    counter: dict[str, Any] = {}
    if counter_path.is_file():
        try:
            loaded = _json.loads(counter_path.read_text(encoding="utf-8"))
            counter = loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError):
            counter = {}
    used_today = int(counter.get(today, 0))
    if used_today >= args.max_per_day:
        print(
            f"break-glass rate limit reached ({used_today}/{args.max_per_day} today); "
            "resolve the block through repair/kickoff or wait.",
            file=sys.stderr,
        )
        return 1
    token = {
        "reason_class": reason_class,
        "note": args.reason,
        "minted_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "minted_by": os.environ.get("USER") or os.environ.get("LOGNAME") or "aegis-cli",
        "expires_at": (now + timedelta(minutes=args.ttl_minutes))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "single_use": True,
    }
    (state_dir / "override-token.json").write_text(_json.dumps(token, indent=2), encoding="utf-8")
    counter[today] = used_today + 1
    counter_path.write_text(_json.dumps(counter), encoding="utf-8")
    _dump_json(
        {
            "status": "minted",
            "token": token,
            "used_today": used_today + 1,
            "max_per_day": args.max_per_day,
            "scope": "workflow-state blocks only (tier a/b); single-use; consumed on next matching mutation",
        }
    )
    return 0


def handle_scope(args: argparse.Namespace) -> int:
    """Record a confirmed scope record for the current branch (capsule PR-1d)."""

    import subprocess

    with _resolve_source_root(args.source_root) as source_root:
        ledger_lib = _load_ledger_lib(source_root)
        target = Path(args.target_dir).resolve()
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        branch = result.stdout.strip()
        if not branch:
            print("aegis scope set requires a git branch in the target repository", file=sys.stderr)
            return 1
        scope_context = _scope_ledger_context(target)
        invoking_agent = _aegis_installer.invoking_agent_from_environment()
        scope_extra: dict[str, Any] = {
            "task_id": str(args.task_id),
            "path_globs": list(args.glob or []),
            "inferred": False,
            "confirmed": True,
        }
        if scope_context["work_id"]:
            scope_extra["work_id"] = scope_context["work_id"]
        ledger = ledger_lib.open_ledger(cwd=target)
        try:
            ledger.append(
                {
                    "branch": branch,
                    "cwd": target.as_posix(),
                    "event_type": "scope",
                    "session_id": scope_context["session_id"],
                    "agent_id": invoking_agent,
                    "agent_type": invoking_agent,
                    "paths": list(args.glob or []),
                    "extra": scope_extra,
                }
            )
        finally:
            ledger.close()
        projection_payload = None
        if args.project_sweh:
            surfaces = legacy_projection.active_surface_paths(target)
            if surfaces:
                projection_payload, _ = _project_legacy_sweh(
                    ledger_lib,
                    target,
                    surfaces,
                    read_limit=args.project_read_limit,
                    limit=args.project_limit,
                )
            else:
                projection_payload = {
                    "status": "skipped",
                    "reason": "no existing active legacy surfaces",
                    "output_paths": [],
                    "event_count": 0,
                    "changed": False,
                }
        print(f"Scope recorded for branch {branch}: task {args.task_id}")
        if projection_payload is not None:
            print(
                "Legacy S:W:H:E projection: "
                f"{projection_payload['status']} "
                f"({len(projection_payload['output_paths'])} surfaces, "
                f"changed={projection_payload['changed']})"
            )
        return 0


def handle_ledger(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        ledger_lib = _load_ledger_lib(source_root)
        if args.ledger_subcommand == "path":
            try:
                print(ledger_lib.store_path(cwd=args.target_dir).as_posix())
            except ledger_lib.LedgerError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            return 0
        if args.ledger_subcommand == "project-sweh":
            output_paths: list[Path] = []
            if args.output:
                output_path = Path(args.output)
                if not output_path.is_absolute():
                    output_path = Path(args.target_dir).resolve() / output_path
                output_paths.append(output_path)
            if args.active:
                output_paths.extend(legacy_projection.active_surface_paths(Path(args.target_dir)))
            if not output_paths:
                print(
                    "ledger project-sweh requires --output or --active with existing legacy surfaces",
                    file=sys.stderr,
                )
                return 1
            try:
                payload, results = _project_legacy_sweh(
                    ledger_lib,
                    args.target_dir,
                    output_paths,
                    dry_run=args.dry_run,
                    read_limit=args.read_limit,
                    limit=args.limit,
                    include_mutations=args.include_mutations,
                    include_gate_decisions=args.include_gate_decisions,
                )
            except ledger_lib.LedgerError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            payload["active"] = args.active
            if args.json:
                _dump_json(payload)
            else:
                print(
                    "Aegis legacy S:W:H:E projection: "
                    f"{payload['status']} ({payload['event_count']} events, "
                    f"{len(results)} surfaces, changed={payload['changed']})"
                )
                for output_path in payload["output_paths"]:
                    print(f"Output: {output_path}")
                if args.dry_run:
                    for result in results:
                        print()
                        print(f"--- {result.output_path.as_posix()} ---")
                        print(result.section, end="")
            return 0
    raise _aegis_installer.AegisError("unknown ledger subcommand")


def handle_next(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        _refresh_capsule_if_stale(source_root, args.target_dir, reason="orientation")
        payload = _aegis_installer.next_action(
            args.target_dir,
            source_root=source_root,
            invoking_agent=_aegis_installer.invoking_agent_from_environment(),
        )
    if args.json:
        _print_budgeted_json(
            payload,
            args,
            command="next",
            artifact_paths=(
                _aegis_installer.AEGIS_CURRENT_WORK_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
                _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
            ),
        )
    else:
        _print_budgeted_text(
            _aegis_installer.format_next_summary(payload),
            payload,
            args,
            command="next",
            artifact_paths=(
                _aegis_installer.AEGIS_CURRENT_WORK_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
                _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
            ),
        )
    return 0


def handle_doctor(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.doctor(
            args.target_dir,
            source_root=source_root,
            invoking_agent=_aegis_installer.invoking_agent_from_environment(),
        )
    if args.json:
        _print_budgeted_json(
            payload,
            args,
            command="doctor",
            artifact_paths=(
                _aegis_installer.AEGIS_MANIFEST_REL,
                _aegis_installer.AEGIS_CURRENT_WORK_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
                _aegis_installer.AEGIS_VERIFY_REPORT_REL,
            ),
            next_action="./.aegis/bin/aegis next --target-dir .",
        )
    else:
        _print_budgeted_text(
            _aegis_installer.format_doctor_summary(payload),
            payload,
            args,
            command="doctor",
            artifact_paths=(
                _aegis_installer.AEGIS_MANIFEST_REL,
                _aegis_installer.AEGIS_CURRENT_WORK_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
                _aegis_installer.AEGIS_VERIFY_REPORT_REL,
            ),
            next_action="./.aegis/bin/aegis next --target-dir .",
        )
    if payload.get("status") == "failed":
        print("Aegis doctor found required failures", file=sys.stderr)
        return 1
    return 0


def handle_enforce(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        if args.mode:
            payload = _aegis_installer.enforce_mode(
                args.target_dir,
                source_root=source_root,
                mode=args.mode,
                reason=args.reason or "",
            )
        else:
            payload = _aegis_installer.enforcement_status(
                args.target_dir,
                source_root=source_root,
            )
    _dump_json(payload)
    return 0


def handle_reconcile(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.reconcile(
            args.target_dir,
            source_root=source_root,
            base_ref=args.base_ref,
            use_github=not args.no_github,
            preview_candidates=args.preview_candidates,
        )
    if args.json:
        _dump_json(payload)
    else:
        print(_aegis_installer.format_reconcile_summary(payload), end="")
    return 0


def handle_repair(args: argparse.Namespace) -> int:
    # TM 221: dedicated batch purge of read-only pending-tracking backlog (no source_root needed).
    if getattr(args, "purge_read_only_pending", False):
        payload = _aegis_installer.purge_read_only_pending(args.target_dir, apply=args.apply)
        if args.json:
            _dump_json(payload)
        else:
            print(
                f"purge-read-only-pending: {payload['status']} — "
                f"{payload['read_only_count']} read-only of {payload['total_pending']} pending "
                f"({'removed' if payload['applied'] else 'preview; rerun with --apply'})"
            )
            for item in payload["purged"]:
                print(f"  - {item['id']} {item['tool']}: {item['evidence']}")
        return 0
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.repair(
            args.target_dir,
            source_root=source_root,
            apply=args.apply,
        )
    if args.json:
        _dump_json(payload)
    else:
        print(_aegis_installer.format_repair_summary(payload), end="")
    if payload.get("status") == "failed":
        print("Aegis repair failed", file=sys.stderr)
        return 1
    return 0


def handle_uninstall(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.uninstall(
            args.target_dir,
            source_root=source_root,
            apply=args.apply,
            remove_hook_scripts=args.remove_hook_scripts,
        )
    if args.json:
        _dump_json(payload)
    else:
        print(_aegis_installer.format_uninstall_summary(payload), end="")
    if payload.get("status") in {"failed", "refused"}:
        print("Aegis uninstall failed or refused unsafe operations", file=sys.stderr)
        return 1
    return 0


def handle_install(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.install(
            args.target_dir,
            source_root=source_root,
            profile=args.profile,
            primary_agent=args.primary_agent,
            agents=_agents_from_args(args),
            apply=args.apply,
        )
    _dump_json(payload)
    if payload.get("status") == "refused":
        print("Aegis install refused unsafe overwrite or manual-review operations", file=sys.stderr)
        return 1
    if payload.get("status") == "failed":
        print("Aegis install failed during apply and attempted cleanup", file=sys.stderr)
        return 1
    return 0


def handle_verify(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.verify(
            args.target_dir,
            source_root=source_root,
            strict=args.strict,
        )
        _refresh_capsule_if_stale(source_root, args.target_dir, reason="verification")
    _print_budgeted_json(
        payload,
        args,
        command="verify",
        artifact_paths=(
            _aegis_installer.AEGIS_VERIFY_REPORT_REL,
            _aegis_installer.AEGIS_PENDING_TRACKING_REL,
        ),
        next_action="./.aegis/bin/aegis next --target-dir .",
    )
    if payload.get("status") == "failed":
        print("Aegis verification failed", file=sys.stderr)
        return 1
    return 0


def handle_closeout(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.closeout(
            args.target_dir,
            source_root=source_root,
            update_handoff=args.update_handoff,
            require_clean_git=args.require_clean_git,
            include_git_guidance=not args.no_git_guidance,
            dry_run=args.dry_run,
        )
    if args.json:
        _print_budgeted_json(
            payload,
            args,
            command="closeout",
            artifact_paths=(
                _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
            ),
        )
    else:
        _print_budgeted_text(
            _aegis_installer.format_closeout_summary(payload),
            payload,
            args,
            command="closeout",
            artifact_paths=(
                _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
                _aegis_installer.AEGIS_PENDING_TRACKING_REL,
            ),
        )
    if payload.get("status") == "failed":
        print("Aegis closeout failed", file=sys.stderr)
        return 1
    return 0


def handle_handoff_repair(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.repair_handoff(
            args.target_dir,
            source_root=source_root,
            dry_run=args.dry_run,
        )
    _dump_json(payload)
    if payload.get("status") == "failed":
        print("Aegis handoff repair failed", file=sys.stderr)
        return 1
    return 0


def handle_certify_release(args: argparse.Namespace) -> int:
    payload = _aegis_installer.certify_release_candidate(
        args.source_dir,
        dist_dir=args.dist_dir,
        report_file=args.report_file,
        build=not args.skip_build,
        run_smoke=not args.skip_smoke,
    )
    _dump_json(payload)
    if payload.get("status") == "failed":
        print("Aegis release certification failed", file=sys.stderr)
        return 1
    return 0


def handle_kickoff(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        if args.local:
            if not args.title:
                print("aegis kickoff --local requires --title", file=sys.stderr)
                return 1
            payload = _aegis_installer.start_local_work(
                args.target_dir,
                title=args.title,
                slug=args.slug,
                goals=list(args.goal or []),
                create_branch=not args.no_create_branch,
                source_root=source_root,
                invoking_agent=_aegis_installer.invoking_agent_from_environment(),
            )
        else:
            missing = [name for name in ("task", "slug", "title") if not getattr(args, name)]
            if missing:
                print(
                    f"aegis kickoff requires: {', '.join('--' + name for name in missing)}",
                    file=sys.stderr,
                )
                return 1
            payload = _aegis_installer.kickoff(
                args.target_dir,
                task_id=args.task,
                slug=args.slug,
                title=args.title,
                goals=list(args.goal or []),
                create_branch=not args.no_create_branch,
                source_root=source_root,
                invoking_agent=_aegis_installer.invoking_agent_from_environment(),
            )
    _dump_json(payload)
    return 0


def handle_start(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.start_local_work(
            args.target_dir,
            title=args.title,
            slug=args.slug,
            goals=list(args.goal or []),
            create_branch=not args.no_create_branch,
            source_root=source_root,
            invoking_agent=_aegis_installer.invoking_agent_from_environment(),
        )
    _dump_json(payload)
    return 0


def handle_observe(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        if args.observe_subcommand == "start":
            payload = _aegis_installer.start_observation(
                args.target_dir,
                title=args.title,
                slug=args.slug or "",
                goals=list(args.goal or []),
                source_root=source_root,
                invoking_agent=_aegis_installer.invoking_agent_from_environment(),
            )
            _dump_json(payload)
            return 0
        if args.observe_subcommand == "stop":
            payload = _aegis_installer.stop_observation(
                args.target_dir,
                summary=args.summary or "",
                allow_dirty=args.allow_dirty,
                collect_artifacts=args.collect_artifacts,
                source_root=source_root,
            )
            _dump_json(payload)
            return 1 if payload.get("status") == "blocked" else 0
    raise _aegis_installer.AegisError("unknown observe subcommand")


def handle_hook(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        phase = str(args.phase)
        if phase == "readiness":
            script = source_root / ".claude" / "scripts" / "readiness.sh"
            os.execv(script.as_posix(), [script.as_posix(), *list(args.hook_args or [])])
        script = source_root / ".claude" / "scripts" / "gate_lib.py"
        os.execv(sys.executable, [sys.executable, script.as_posix(), phase])
    return 1


def handle_runtime(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        if args.runtime_subcommand == "status":
            payload = _aegis_installer.runtime_status(
                args.target_dir,
                source_root=source_root,
            )
            _dump_json(payload)
            return 0
        if args.runtime_subcommand == "update":
            payload = _aegis_installer.runtime_update(
                args.target_dir,
                source_root=source_root,
                apply=args.apply,
            )
            _dump_json(payload)
            if payload.get("status") == "refused":
                print("Aegis runtime update refused", file=sys.stderr)
                return 1
            return 0
    raise _aegis_installer.AegisError("unknown runtime subcommand")


def handle_log(args: argparse.Namespace) -> int:
    payload = _aegis_installer.log_work(
        args.target_dir,
        handler=args.handler,
        evidence=args.evidence,
        note=args.note,
        surfaces=args.surface,
        plan_step=args.plan_step,
        plan_status=args.plan_status,
        event_class=args.event_class,
        pending_event_id=args.pending_id,
    )
    _dump_json(payload)
    return 0


def handle_list_profiles(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.list_profiles(source_root=source_root)
    _dump_json(payload)
    return 0


def handle_explain_profile(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.explain_profile(
            args.profile,
            source_root=source_root,
        )
    _dump_json(payload)
    return 0


def _mcp_registration_request_from_args(
    args: argparse.Namespace,
    *,
    client: mcp_registration.ClientName | None = None,
) -> mcp_registration.RegistrationRequest:
    return mcp_registration.RegistrationRequest(
        client=client or args.client,
        scope=getattr(args, "scope", None),
        source_mode=args.source_mode,
        package_spec=args.package_spec,
        package_version=args.package_version,
        github_url=args.github_url,
        github_ref=args.github_ref,
        artifact=args.artifact,
        target_dir=args.target_dir,
        transport=args.transport,
        uv_cache_dir=args.uv_cache_dir,
        uv_tool_dir=args.uv_tool_dir,
    )


def handle_mcp_generate_registration(args: argparse.Namespace) -> int:
    try:
        payload = mcp_registration.registration_payload(_mcp_registration_request_from_args(args))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _dump_json(payload)
    return 0


def handle_mcp_execute_registration(args: argparse.Namespace) -> int:
    try:
        payload = mcp_registration.execute_registration(
            _mcp_registration_request_from_args(args),
            cwd=args.cwd or args.target_dir,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _dump_json(payload)
    if payload.get("status") in {"missing_client", "failed"}:
        return 1
    return 0


def handle_mcp_verify_registration(args: argparse.Namespace) -> int:
    try:
        payload = mcp_registration.verify_registration(
            _mcp_registration_request_from_args(args),
            cwd=args.cwd or args.target_dir,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _dump_json(payload)
    if payload.get("status") in {"missing_client", "failed"}:
        return 1
    return 0


def handle_mcp_register(args: argparse.Namespace) -> int:
    try:
        payload = mcp_registration.execute_registration(
            _mcp_registration_request_from_args(args),
            cwd=args.cwd or args.target_dir,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _dump_json(payload)
    if payload.get("status") in {"missing_client", "failed"}:
        return 1
    return 0


def _normalize_smoke_clients(
    values: Sequence[str] | None,
) -> tuple[mcp_registration.ClientName, ...]:
    requested = list(values or ["all"])
    if "all" in requested:
        return mcp_registration.SMOKE_CLIENTS
    return tuple(dict.fromkeys(requested))  # type: ignore[return-value]


def handle_mcp_smoke_registration(args: argparse.Namespace) -> int:
    clients = _normalize_smoke_clients(args.client)
    try:
        payload = mcp_registration.smoke_registration(
            _mcp_registration_request_from_args(args, client=clients[0]),
            clients=clients,
            smoke_root=args.smoke_root,
            keep_temp=args.keep_temp,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    mcp_registration.write_smoke_reports(
        payload,
        report_file=args.report_file,
        markdown_report_file=args.markdown_report_file,
    )
    _dump_json(payload)
    if payload.get("status") == "failed":
        return 1
    return 0


def _add_mcp_registration_arguments(
    parser: argparse.ArgumentParser, *, execute: bool = False
) -> None:
    parser.add_argument(
        "--client",
        choices=("claude", "codex"),
        required=True,
        help="Native MCP client to configure.",
    )
    parser.add_argument(
        "--scope",
        choices=("local", "user", "project"),
        help="Claude MCP scope. Defaults to user for Claude and is ignored for Codex.",
    )
    parser.add_argument(
        "--source-mode",
        choices=("package", "pinned", "github", "private-github", "wheel", "source"),
        default="package",
        help="How uvx should resolve the Aegis package that provides aegis-mcp-server.",
    )
    parser.add_argument(
        "--package-spec",
        help="Explicit uvx --from package/artifact spec. Overrides source-mode defaults.",
    )
    parser.add_argument(
        "--package-version",
        help="Version for --source-mode pinned. Defaults to the package version.",
    )
    parser.add_argument(
        "--github-url",
        default=mcp_registration.DEFAULT_GITHUB_URL,
        help="GitHub repository URL for --source-mode github/private-github.",
    )
    parser.add_argument(
        "--github-ref", help="Optional ref for --source-mode github/private-github."
    )
    parser.add_argument(
        "--artifact", help="Wheel path or source checkout path for wheel/source modes."
    )
    parser.add_argument(
        "--target-dir", default=".", help="Default target directory passed to aegis-mcp-server."
    )
    parser.add_argument(
        "--uv-cache-dir",
        default=mcp_registration.DEFAULT_UV_CACHE_DIR,
        help="UV_CACHE_DIR value registered with the native client; use '' to omit.",
    )
    parser.add_argument(
        "--uv-tool-dir",
        default=mcp_registration.DEFAULT_UV_TOOL_DIR,
        help="UV_TOOL_DIR value registered with the native client; use '' to omit.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP server transport to register.",
    )
    if execute:
        parser.add_argument(
            "--cwd",
            help="Working directory for the native client command. Defaults to --target-dir.",
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegis",
        description="Run Aegis Foundation CLI operations.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--source-root",
        help=(
            "Path to the local Aegis source checkout. Defaults to AEGIS_SOURCE_ROOT or "
            "the editable-install source root, then packaged Aegis assets."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect Aegis state and adapter signals in a target repository.",
    )
    inspect_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    inspect_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    inspect_parser.set_defaults(func=handle_inspect)

    plan_install_parser = subparsers.add_parser(
        "plan-install",
        help="Print a dry-run Aegis install plan for a target repository.",
    )
    plan_install_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    plan_install_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    plan_install_parser.add_argument(
        "--primary-agent",
        choices=sorted(_aegis_installer.PRIMARY_AGENT_CHOICES),
        required=True,
        help="Primary agent for the installed runtime.",
    )
    plan_install_parser.add_argument(
        "--agent",
        choices=sorted(_aegis_installer.AGENT_CHOICES),
        action="append",
        required=True,
        help="Enable an agent adapter; repeat for multi-agent installs.",
    )
    plan_install_parser.set_defaults(func=handle_plan_install)

    init_parser = subparsers.add_parser(
        "init",
        help="Install Aegis in the current project with public defaults.",
    )
    init_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    init_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    init_parser.add_argument(
        "--primary-agent",
        choices=sorted(_aegis_installer.PRIMARY_AGENT_CHOICES),
        default="claude",
        help="Primary agent for the installed runtime; defaults to claude.",
    )
    init_parser.add_argument(
        "--agent",
        choices=sorted(_aegis_installer.AGENT_CHOICES),
        action="append",
        help="Enable an agent adapter; defaults to the primary Claude adapter.",
    )
    init_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the standard post-install verification pass.",
    )
    init_parser.set_defaults(func=handle_init)

    setup_parser = subparsers.add_parser(
        "setup",
        help="Compatibility alias for aegis init.",
    )
    setup_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    setup_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    setup_parser.add_argument(
        "--primary-agent",
        choices=sorted(_aegis_installer.PRIMARY_AGENT_CHOICES),
        default="claude",
        help="Primary agent for the installed runtime; defaults to claude.",
    )
    setup_parser.add_argument(
        "--agent",
        choices=sorted(_aegis_installer.AGENT_CHOICES),
        action="append",
        help="Enable an agent adapter; defaults to the primary Claude adapter.",
    )
    setup_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the standard post-install verification pass.",
    )
    setup_parser.set_defaults(func=handle_init)

    status_parser = subparsers.add_parser(
        "status",
        help="Report installed Aegis release state without mutating the target.",
    )
    status_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    _add_output_budget_arguments(
        status_parser,
        add_json=True,
        json_help="Accepted for cross-command consistency; status output is structured JSON.",
    )
    status_parser.set_defaults(func=handle_status)

    update_parser = subparsers.add_parser(
        "update",
        help="Refresh installed runtime pointer, managed assets, verification report, and capsule state.",
    )
    update_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    update_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the safe managed update; omitted means dry-run JSON only.",
    )
    _add_output_budget_arguments(
        update_parser,
        add_json=True,
        json_help="Accepted for cross-command consistency; update output is structured JSON.",
    )
    update_parser.set_defaults(func=handle_update)

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay tool-call corpora through the real gate and report verdict deltas.",
    )
    replay_parser.add_argument(
        "--corpus", action="append", required=True, help="Corpus JSONL path; repeatable."
    )
    replay_parser.add_argument("--work-dir", default=None, help="Scratch dir for state fixtures.")
    _add_output_budget_arguments(
        replay_parser,
        add_json=True,
        json_help="Print the bounded report as JSON.",
    )
    replay_parser.set_defaults(func=handle_replay)

    witness_parser = subparsers.add_parser(
        "witness",
        help="Run the deterministic delivery witness (boundary check; zero LLM).",
    )
    witness_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    witness_parser.add_argument(
        "--base", default=None, help="Base ref for the diff (default: origin/main)."
    )
    _add_output_budget_arguments(
        witness_parser,
        add_json=True,
        json_help="Print the bounded report as JSON.",
    )
    witness_parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: git-derivable checks only; ledger checks reported not_derivable_in_ci.",
    )
    witness_parser.set_defaults(func=handle_witness)

    delivery_parser = subparsers.add_parser(
        "delivery",
        help="Synchronize machine-observed git/GitHub delivery state into the ledger and legacy projections.",
    )
    delivery_sub = delivery_parser.add_subparsers(dest="delivery_subcommand", required=True)
    delivery_sync_parser = delivery_sub.add_parser(
        "sync",
        help="Record the current pushed-branch or PR state without performing a delivery action.",
    )
    delivery_sync_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    delivery_sync_parser.add_argument(
        "--pr",
        dest="pr_number",
        default=None,
        help="Exact pull-request number to inspect, including after branch switching.",
    )
    delivery_sync_parser.add_argument(
        "--branch",
        default=None,
        help="Branch to inspect; defaults to the current git branch.",
    )
    delivery_sync_parser.add_argument(
        "--json", action="store_true", help="Print structured result JSON."
    )
    delivery_sync_parser.set_defaults(func=handle_delivery)

    brief_parser = subparsers.add_parser(
        "brief",
        help="Compile and print the computed Aegis capsule (read-time, never cached).",
    )
    brief_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    brief_parser.add_argument("--json", action="store_true", help="Print the capsule as JSON.")
    brief_parser.add_argument(
        "--status",
        action="store_true",
        help="Report whether .aegis/capsule/current.json is fresh for current repo truth.",
    )
    brief_parser.add_argument(
        "--reason",
        choices=BRIEF_REASON_CHOICES,
        default="manual",
        help="Boundary that triggered this compile (recorded in capsule_meta).",
    )
    brief_parser.add_argument(
        "--check",
        action="store_true",
        help="Offline strict validation: char budget + canary + parse counters (fails over budget).",
    )
    brief_parser.set_defaults(func=handle_brief)

    coldstart_parser = subparsers.add_parser(
        "coldstart",
        help="Falsifier-v2 cold-start tooling (forward-capture replay scenarios).",
    )
    coldstart_sub = coldstart_parser.add_subparsers(dest="coldstart_subcommand", required=True)
    coldstart_capture_parser = coldstart_sub.add_parser(
        "capture",
        help="Capture the current in-progress state as a replayable cold-start scenario.",
    )
    coldstart_capture_parser.add_argument(
        "--target-dir", default=".", help="Target repository root."
    )
    coldstart_capture_parser.add_argument(
        "--id", default=None, help="Scenario id (default: capture-<sha>)."
    )
    coldstart_capture_parser.add_argument(
        "--out", default=None, help="Output path (default: .aegis/coldstart-scenarios/<id>.json)."
    )
    coldstart_capture_parser.add_argument(
        "--expect-class",
        choices=("continue", "do_nothing"),
        default=None,
        help="Override the derived ground truth class.",
    )
    coldstart_capture_parser.add_argument(
        "--fresh-null",
        action="store_true",
        help="Mark as a fresh-null control scenario (clean state; expected ~no capsule edge).",
    )
    coldstart_capture_parser.add_argument(
        "--note", default=None, help="Operator note stored in the scenario."
    )
    coldstart_capture_parser.set_defaults(func=handle_coldstart)

    ab_parser = subparsers.add_parser(
        "ab",
        help="Report per-arm cold-start counts for the §7 capsule A/B and the fixed-n stopping rule.",
    )
    ab_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    ab_parser.add_argument(
        "--min-n",
        type=int,
        default=15,
        help="Genuine cold starts required per arm before deciding (default 15).",
    )
    ab_parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    ab_parser.set_defaults(func=handle_ab)

    override_parser = subparsers.add_parser(
        "override",
        help="Mint a one-shot break-glass token for workflow-state blocks (tier a/b only).",
    )
    override_parser.add_argument(
        "--reason", required=True, help="Why the break-glass is needed (audited)."
    )
    override_parser.add_argument(
        "--reason-class",
        default="any",
        choices=("any", "readiness_blocked", "pending_tracking"),
        help="Restrict the token to one block reason; default any eligible workflow-state block.",
    )
    override_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    override_parser.add_argument(
        "--ttl-minutes", type=int, default=15, help="Token lifetime (default 15)."
    )
    override_parser.add_argument(
        "--max-per-day", type=int, default=3, help="Rate limit per day (default 3)."
    )
    override_parser.set_defaults(func=handle_override)

    scope_parser = subparsers.add_parser(
        "scope",
        help="Record task scope for the current branch (consumed by the delivery witness).",
    )
    scope_sub = scope_parser.add_subparsers(dest="scope_subcommand", required=True)
    scope_set_parser = scope_sub.add_parser(
        "set",
        help="Confirm the task id (and optional path globs) for the current branch.",
    )
    scope_set_parser.add_argument("task_id", help="Task id this branch's work belongs to.")
    scope_set_parser.add_argument("glob", nargs="*", help="Optional in-scope path globs.")
    scope_set_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    scope_set_parser.add_argument(
        "--project-sweh",
        action="store_true",
        help="After recording scope, project the active legacy S:W:H:E surfaces if they exist.",
    )
    scope_set_parser.add_argument(
        "--project-limit",
        type=int,
        default=25,
        help="Maximum projectable events to render when --project-sweh is used.",
    )
    scope_set_parser.add_argument(
        "--project-read-limit",
        type=int,
        default=500,
        help="Maximum recent ledger events to scan when --project-sweh is used.",
    )
    scope_set_parser.set_defaults(func=handle_scope)

    ledger_parser = subparsers.add_parser(
        "ledger",
        help="Inspect the out-of-worktree Aegis ledger store and generated projections.",
    )
    ledger_sub = ledger_parser.add_subparsers(dest="ledger_subcommand", required=True)
    ledger_path_parser = ledger_sub.add_parser(
        "path",
        help="Print the resolved ledger store path for the target repository.",
    )
    ledger_path_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    ledger_path_parser.set_defaults(func=handle_ledger)
    ledger_project_parser = ledger_sub.add_parser(
        "project-sweh",
        help="Project selected ledger events into a generated S:W:H:E block.",
    )
    ledger_project_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    ledger_project_parser.add_argument(
        "--output",
        default=None,
        help="Legacy markdown surface to update, relative to target dir unless absolute.",
    )
    ledger_project_parser.add_argument(
        "--active",
        action="store_true",
        help="Project into existing active session, plan, and work-tracking markdown surfaces.",
    )
    ledger_project_parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum projectable events to render after filtering.",
    )
    ledger_project_parser.add_argument(
        "--read-limit",
        type=int,
        default=500,
        help="Maximum recent ledger events to scan before filtering.",
    )
    ledger_project_parser.add_argument(
        "--include-mutations",
        action="store_true",
        help="Also project low-level mutation events into the legacy surface.",
    )
    ledger_project_parser.add_argument(
        "--include-gate-decisions",
        action="store_true",
        help="Also project advisory gate-decision events into the legacy surface.",
    )
    ledger_project_parser.add_argument(
        "--dry-run", action="store_true", help="Render without writing."
    )
    ledger_project_parser.add_argument(
        "--json", action="store_true", help="Print structured result JSON."
    )
    ledger_project_parser.set_defaults(func=handle_ledger)

    next_parser = subparsers.add_parser(
        "next",
        help="Report the next required Aegis workflow action without mutating the target.",
    )
    next_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    next_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a bounded next-action payload as JSON instead of the concise summary.",
    )
    _add_output_budget_arguments(next_parser)
    next_parser.set_defaults(func=handle_next)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Diagnose installed Aegis workflow state without mutating the target.",
    )
    doctor_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the bounded structured doctor report instead of a concise summary.",
    )
    _add_output_budget_arguments(doctor_parser)
    doctor_parser.set_defaults(func=handle_doctor)

    enforce_parser = subparsers.add_parser(
        "enforce",
        help="Inspect or set Aegis enforcement mode for installed hooks.",
    )
    enforce_parser.add_argument(
        "enforce_subcommand",
        nargs="?",
        choices=("status",),
        help="Use 'status' to inspect enforcement mode. Omitted with --mode sets the mode.",
    )
    enforce_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    enforce_parser.add_argument(
        "--mode",
        choices=sorted(_aegis_installer.AEGIS_ENFORCEMENT_MODES),
        help="Set enforcement mode. File absent remains strict by default.",
    )
    enforce_parser.add_argument(
        "--reason",
        default="",
        help="Reason recorded when setting enforcement mode.",
    )
    enforce_parser.set_defaults(func=handle_enforce)

    reconcile_parser = subparsers.add_parser(
        "reconcile",
        help="Read-only Taskmaster/Aegis/git/PR drift report; never mutates status.",
    )
    reconcile_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    reconcile_parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref that represents merge truth. Defaults to origin/main, falling back to main/master when local.",
    )
    reconcile_parser.add_argument(
        "--no-github",
        action="store_true",
        help="Disable optional gh PR metadata; squash-ambiguous branches remain unknown.",
    )
    reconcile_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured reconcile report instead of a concise summary.",
    )
    reconcile_parser.add_argument(
        "--preview-candidates",
        action="store_true",
        help=(
            "Include inert, report-only mutation candidate preview data for operator review; "
            "never executes or auto-mutates status."
        ),
    )
    reconcile_parser.set_defaults(func=handle_reconcile)

    repair_parser = subparsers.add_parser(
        "repair",
        help="Preview or apply safe Aegis workflow-state repairs.",
    )
    repair_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    repair_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply safe repairs and write .aegis/reports/repair-report.json; omitted means dry-run preview.",
    )
    repair_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured repair report instead of a concise summary.",
    )
    repair_parser.add_argument(
        "--purge-read-only-pending",
        action="store_true",
        help="Instead of repair: drop read-only/inspection events from the pending-tracking "
        "queue (preview unless --apply) so they cannot accrete into required closeout evidence.",
    )
    repair_parser.set_defaults(func=handle_repair)

    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Preview or remove Aegis-managed install and workflow artifacts.",
    )
    uninstall_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    uninstall_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the uninstall plan; omitted means dry-run preview.",
    )
    uninstall_parser.add_argument(
        "--remove-hook-scripts",
        action="store_true",
        help=(
            "Also remove .claude/scripts hook files. Default preserves them so an already-running "
            "Claude session can finish after .claude/settings.json is removed."
        ),
    )
    uninstall_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured uninstall report instead of a concise summary.",
    )
    uninstall_parser.set_defaults(func=handle_uninstall)

    install_parser = subparsers.add_parser(
        "install",
        help="Apply or dry-run an Aegis install plan.",
    )
    install_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    install_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    install_parser.add_argument(
        "--primary-agent",
        choices=sorted(_aegis_installer.PRIMARY_AGENT_CHOICES),
        required=True,
        help="Primary agent for the installed runtime.",
    )
    install_parser.add_argument(
        "--agent",
        choices=sorted(_aegis_installer.AGENT_CHOICES),
        action="append",
        required=True,
        help="Enable an agent adapter; repeat for multi-agent installs.",
    )
    install_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the install plan; omitted means dry-run JSON only.",
    )
    install_parser.set_defaults(func=handle_install)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify an installed Aegis Foundation target repository.",
    )
    verify_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    verify_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require release-certification runtime, workflow, hook, and tracking checks.",
    )
    _add_output_budget_arguments(
        verify_parser,
        add_json=True,
        json_help="Accepted for cross-command consistency; verify output is structured JSON.",
    )
    verify_parser.set_defaults(func=handle_verify)

    closeout_parser = subparsers.add_parser(
        "closeout",
        help="Run the final Aegis task-completion gate and write a closeout report.",
    )
    closeout_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    closeout_parser.add_argument(
        "--update-handoff",
        action="store_true",
        help="Refresh Aegis-owned semantic HANDOFF.md sections before validation.",
    )
    closeout_parser.add_argument(
        "--require-clean-git",
        action="store_true",
        help="Fail closeout when the target git worktree has uncommitted changes.",
    )
    closeout_parser.add_argument(
        "--no-git-guidance",
        action="store_true",
        help="Omit suggested normal git/GitHub commands from the closeout report.",
    )
    closeout_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate closeout gates without writing reports, handoff updates, or current-work state.",
    )
    closeout_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the bounded structured closeout report instead of the concise human summary.",
    )
    _add_output_budget_arguments(closeout_parser)
    closeout_parser.set_defaults(func=handle_closeout)

    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Inspect and repair active Aegis handoff surfaces.",
    )
    handoff_sub = handoff_parser.add_subparsers(dest="handoff_subcommand", required=True)
    handoff_repair_parser = handoff_sub.add_parser(
        "repair",
        help="Repair Aegis-owned semantic HANDOFF.md sections without writing closeout state.",
    )
    handoff_repair_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    handoff_repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the deterministic handoff repair without writing HANDOFF.md.",
    )
    handoff_repair_parser.set_defaults(func=handle_handoff_repair)

    certify_parser = subparsers.add_parser(
        "certify-release",
        help="Build and inspect release-candidate artifacts and write a certification report.",
    )
    certify_parser.add_argument("--source-dir", default=".", help="Source repository root.")
    certify_parser.add_argument(
        "--dist-dir",
        default="dist/aegis-release-candidate",
        help="Directory for built or pre-existing release artifacts.",
    )
    certify_parser.add_argument(
        "--report-file",
        default=_aegis_installer.AEGIS_RELEASE_CERT_REPORT_REL,
        help="Certification report path.",
    )
    certify_parser.add_argument(
        "--skip-build", action="store_true", help="Inspect existing artifacts instead of building."
    )
    certify_parser.add_argument(
        "--skip-smoke", action="store_true", help="Skip clean installed-wheel CLI smoke."
    )
    certify_parser.set_defaults(func=handle_certify_release)

    kickoff_parser = subparsers.add_parser(
        "kickoff",
        help="Create Aegis-native session, plan, and work-tracking state for a task.",
    )
    kickoff_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    kickoff_parser.add_argument("--task", help="Numeric task/work id.")
    kickoff_parser.add_argument("--slug", help="Short lowercase work slug.")
    kickoff_parser.add_argument("--title", help="Human-readable work title.")
    kickoff_parser.add_argument(
        "--local",
        action="store_true",
        help="Allocate a local Aegis task id from --title before creating workflow state.",
    )
    kickoff_parser.add_argument(
        "--goal",
        action="append",
        help="Goal to write into the generated plan/tracker; repeat for multiple goals.",
    )
    kickoff_parser.add_argument(
        "--no-create-branch",
        action="store_true",
        help="Require the current branch to already contain the task id.",
    )
    kickoff_parser.set_defaults(func=handle_kickoff)

    start_parser = subparsers.add_parser(
        "start",
        help="Start local tracked work from a normal task title.",
    )
    start_parser.add_argument("title", help="Normal-language task title.")
    start_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    start_parser.add_argument("--slug", help="Override the generated slug.")
    start_parser.add_argument(
        "--goal", action="append", help="Goal to write into the generated plan/tracker."
    )
    start_parser.add_argument(
        "--no-create-branch",
        action="store_true",
        help="Require the current branch to already contain the allocated task id.",
    )
    start_parser.set_defaults(func=handle_start)

    observe_parser = subparsers.add_parser(
        "observe",
        help="Run a bounded observation/audit window without binding a Taskmaster task.",
    )
    observe_sub = observe_parser.add_subparsers(dest="observe_subcommand", required=True)
    observe_start_parser = observe_sub.add_parser(
        "start",
        help="Start observation mode for app-driving, screenshots, or pre-task audit.",
    )
    observe_start_parser.add_argument("title", help="Human-readable observation title.")
    observe_start_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    observe_start_parser.add_argument("--slug", help="Override the generated observation slug.")
    observe_start_parser.add_argument(
        "--goal", action="append", help="Goal to write into the generated plan/tracker."
    )
    observe_start_parser.set_defaults(func=handle_observe)
    observe_stop_parser = observe_sub.add_parser(
        "stop",
        help="Stop observation mode after checking for unexpected working-tree deltas.",
    )
    observe_stop_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    observe_stop_parser.add_argument("--summary", help="Brief summary of what was observed.")
    observe_stop_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Complete observation even when unexpected deltas are present.",
    )
    observe_stop_parser.add_argument(
        "--collect-artifacts",
        action="store_true",
        help="Move known observation artifacts into the Aegis observation report before closing.",
    )
    observe_stop_parser.set_defaults(func=handle_observe)

    hook_parser = subparsers.add_parser(
        "hook",
        help="Internal dispatcher surface for installed Aegis hook bootstrap scripts.",
    )
    hook_parser.add_argument(
        "phase",
        choices=(
            "pretooluse",
            "posttooluse",
            "stop",
            "path",
            "bash",
            "configchange",
            "readiness",
            "record",
            "posttoolusefailure",
            "sessionstart",
            "sessionend",
        ),
        help="Hook phase to execute from the active runtime source.",
    )
    hook_parser.add_argument("hook_args", nargs=argparse.REMAINDER)
    hook_parser.set_defaults(func=handle_hook)

    runtime_parser = subparsers.add_parser(
        "runtime",
        help="Inspect or update the installed runtime pointer without reinstalling scaffold files.",
    )
    runtime_sub = runtime_parser.add_subparsers(dest="runtime_subcommand", required=True)
    runtime_status_parser = runtime_sub.add_parser(
        "status",
        help="Report which Aegis source root and commit this project runtime uses.",
    )
    runtime_status_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    runtime_status_parser.set_defaults(func=handle_runtime)
    runtime_update_parser = runtime_sub.add_parser(
        "update",
        help="Update .aegis/runtime.env and manifest runtime metadata only.",
    )
    runtime_update_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    runtime_update_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the runtime pointer update; omitted prints a preview.",
    )
    runtime_update_parser.set_defaults(func=handle_runtime)

    log_parser = subparsers.add_parser(
        "log",
        help="Write required S:W:H:E progress entries for the current Aegis task.",
    )
    log_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    log_parser.add_argument(
        "--handler", help="Handler identifier for the S:W:H:E H field. Optional with --pending-id."
    )
    log_parser.add_argument(
        "--evidence",
        help="Evidence path or command for the S:W:H:E E field. Optional with --pending-id.",
    )
    log_parser.add_argument(
        "--note", required=True, help="Past-tense summary to append after the S:W:H:E token."
    )
    log_parser.add_argument(
        "--surface",
        action="append",
        choices=sorted(_aegis_installer.AEGIS_LOG_SURFACES),
        help="Workflow surface to update. Omit for event-aware defaults; repeat to override defaults.",
    )
    log_parser.add_argument(
        "--event-class",
        choices=sorted(_aegis_installer.AEGIS_LOG_EVENT_CLASSES),
        help="Explicit log event class for default surface selection.",
    )
    log_parser.add_argument(
        "--pending-id",
        help=(
            "Consume a pending S:W:H:E event by id; use current/latest only when exactly one event exists. "
            "Preferred after native Edit/Write/Bash/MCP mutations."
        ),
    )
    log_parser.add_argument(
        "--plan-step",
        default="",
        help=(
            "Plan step to update with this evidence. Normal flow uses "
            "plan-step-scope, plan-step-implement, then plan-step-verify. "
            "Use auto only when event class or pending event makes the step deterministic."
        ),
    )
    log_parser.add_argument(
        "--plan-status",
        default="in-progress",
        choices=sorted(_aegis_installer.AEGIS_PLAN_STATUS_CHOICES),
        help="Status to write for --plan-step.",
    )
    log_parser.set_defaults(func=handle_log)

    list_profiles_parser = subparsers.add_parser(
        "list-profiles",
        help="List built-in Aegis profiles.",
    )
    list_profiles_parser.set_defaults(func=handle_list_profiles)

    explain_profile_parser = subparsers.add_parser(
        "explain-profile",
        help="Print the built-in Aegis profile contract.",
    )
    explain_profile_parser.add_argument("--profile", default="generic", help="Aegis profile.")
    explain_profile_parser.set_defaults(func=handle_explain_profile)

    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Generate, execute, and verify native MCP client registration commands.",
    )
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_subcommand", required=True)

    mcp_register = mcp_sub.add_parser(
        "register",
        help="Register Aegis with a native MCP client. Public Claude path: aegis mcp register claude.",
    )
    mcp_register.add_argument(
        "client", choices=("claude", "codex"), help="Native MCP client to configure."
    )
    mcp_register.add_argument(
        "--scope",
        choices=("local", "user", "project"),
        default="user",
        help="Claude MCP scope. Defaults to user for Claude and is ignored for Codex.",
    )
    mcp_register.add_argument(
        "--source-mode",
        choices=("package", "pinned", "github", "private-github", "wheel", "source"),
        default="package",
        help="How uvx should resolve the Aegis package that provides aegis-mcp-server.",
    )
    mcp_register.add_argument("--package-spec", help="Explicit uvx --from package/artifact spec.")
    mcp_register.add_argument(
        "--package-version",
        help="Version for --source-mode pinned. Defaults to the package version.",
    )
    mcp_register.add_argument(
        "--github-url",
        default=mcp_registration.DEFAULT_GITHUB_URL,
        help="GitHub repository URL for --source-mode github/private-github.",
    )
    mcp_register.add_argument(
        "--github-ref", help="Optional ref for --source-mode github/private-github."
    )
    mcp_register.add_argument(
        "--artifact", help="Wheel path or source checkout path for wheel/source modes."
    )
    mcp_register.add_argument(
        "--target-dir", default=".", help="Default target directory passed to aegis-mcp-server."
    )
    mcp_register.add_argument(
        "--uv-cache-dir",
        default=mcp_registration.DEFAULT_UV_CACHE_DIR,
        help="UV_CACHE_DIR value registered with the native client; use '' to omit.",
    )
    mcp_register.add_argument(
        "--uv-tool-dir",
        default=mcp_registration.DEFAULT_UV_TOOL_DIR,
        help="UV_TOOL_DIR value registered with the native client; use '' to omit.",
    )
    mcp_register.add_argument(
        "--transport", choices=("stdio",), default="stdio", help="MCP server transport to register."
    )
    mcp_register.add_argument(
        "--cwd", help="Working directory for the native client command. Defaults to --target-dir."
    )
    mcp_register.set_defaults(func=handle_mcp_register)

    mcp_generate = mcp_sub.add_parser(
        "generate-registration",
        help="Generate the native MCP client command for registering Aegis.",
    )
    _add_mcp_registration_arguments(mcp_generate)
    mcp_generate.set_defaults(func=handle_mcp_generate_registration)

    mcp_execute = mcp_sub.add_parser(
        "execute-registration",
        help="Run the native MCP client command for registering Aegis.",
    )
    _add_mcp_registration_arguments(mcp_execute, execute=True)
    mcp_execute.set_defaults(func=handle_mcp_execute_registration)

    mcp_verify = mcp_sub.add_parser(
        "verify-registration",
        help="Verify the native MCP client's Aegis registration.",
    )
    _add_mcp_registration_arguments(mcp_verify, execute=True)
    mcp_verify.set_defaults(func=handle_mcp_verify_registration)

    mcp_smoke = mcp_sub.add_parser(
        "smoke-registration",
        help="Run native MCP register and verify in isolated temporary client homes.",
    )
    mcp_smoke.add_argument(
        "--client",
        action="append",
        choices=("all", "claude", "codex"),
        help="Native MCP client to smoke test. Repeatable. Defaults to all.",
    )
    mcp_smoke.add_argument(
        "--scope",
        choices=("local", "user", "project"),
        default="user",
        help="Claude MCP scope. Defaults to user and is ignored for Codex.",
    )
    mcp_smoke.add_argument(
        "--source-mode",
        choices=("package", "pinned", "github", "private-github", "wheel", "source"),
        default="package",
        help="How uvx should resolve the Aegis package that provides aegis-mcp-server.",
    )
    mcp_smoke.add_argument("--package-spec", help="Explicit uvx --from package/artifact spec.")
    mcp_smoke.add_argument(
        "--package-version",
        help="Version for --source-mode pinned. Defaults to the package version.",
    )
    mcp_smoke.add_argument(
        "--github-url",
        default=mcp_registration.DEFAULT_GITHUB_URL,
        help="GitHub repository URL for --source-mode github/private-github.",
    )
    mcp_smoke.add_argument(
        "--github-ref", help="Optional ref for --source-mode github/private-github."
    )
    mcp_smoke.add_argument(
        "--artifact", help="Wheel path or source checkout path for wheel/source modes."
    )
    mcp_smoke.add_argument(
        "--target-dir", default=".", help="Default target directory passed to aegis-mcp-server."
    )
    mcp_smoke.add_argument(
        "--uv-cache-dir",
        default=mcp_registration.DEFAULT_UV_CACHE_DIR,
        help="UV_CACHE_DIR value registered with the native client; use '' to omit.",
    )
    mcp_smoke.add_argument(
        "--uv-tool-dir",
        default=mcp_registration.DEFAULT_UV_TOOL_DIR,
        help="UV_TOOL_DIR value registered with the native client; use '' to omit.",
    )
    mcp_smoke.add_argument(
        "--transport", choices=("stdio",), default="stdio", help="MCP server transport to register."
    )
    mcp_smoke.add_argument(
        "--smoke-root",
        help="Directory for isolated client homes. Defaults to a temporary directory.",
    )
    mcp_smoke.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep generated temporary homes after the smoke run.",
    )
    mcp_smoke.add_argument("--report-file", help="Optional JSON report path.")
    mcp_smoke.add_argument("--markdown-report-file", help="Optional Markdown report path.")
    mcp_smoke.set_defaults(func=handle_mcp_smoke_registration)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except _aegis_installer.AegisError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
