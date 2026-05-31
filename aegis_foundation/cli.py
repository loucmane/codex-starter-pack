"""Package-style Aegis CLI entrypoint.

The command surface intentionally delegates to ``scripts._aegis_installer`` so the
repository-local ``scripts/codex-task aegis`` wrapper and package-style ``aegis`` wrapper
share the same deterministic installer behavior.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from aegis_foundation import mcp_registration
from aegis_foundation.resources import packaged_asset_root
from aegis_foundation.version import __version__
from scripts import _aegis_installer


def _dump_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


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
    payload = _aegis_installer.inspect_project(args.target_dir, profile=args.profile)
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
        )
    _dump_json(payload)
    return 0


def handle_next(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.next_action(
            args.target_dir,
            source_root=source_root,
        )
    _dump_json(payload)
    return 0


def handle_doctor(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.doctor(
            args.target_dir,
            source_root=source_root,
        )
    if args.json:
        _dump_json(payload)
    else:
        print(_aegis_installer.format_doctor_summary(payload), end="")
    if payload.get("status") == "failed":
        print("Aegis doctor found required failures", file=sys.stderr)
        return 1
    return 0


def handle_repair(args: argparse.Namespace) -> int:
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
    _dump_json(payload)
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
        _dump_json(payload)
    else:
        print(_aegis_installer.format_closeout_summary(payload), end="")
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
            )
        else:
            missing = [name for name in ("task", "slug", "title") if not getattr(args, name)]
            if missing:
                print(f"aegis kickoff requires: {', '.join('--' + name for name in missing)}", file=sys.stderr)
                return 1
            payload = _aegis_installer.kickoff(
                args.target_dir,
                task_id=args.task,
                slug=args.slug,
                title=args.title,
                goals=list(args.goal or []),
                create_branch=not args.no_create_branch,
                source_root=source_root,
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
        )
    _dump_json(payload)
    return 0


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


def _mcp_registration_request_from_args(args: argparse.Namespace) -> mcp_registration.RegistrationRequest:
    return mcp_registration.RegistrationRequest(
        client=args.client,
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


def _add_mcp_registration_arguments(parser: argparse.ArgumentParser, *, execute: bool = False) -> None:
    parser.add_argument("--client", choices=("claude", "codex"), required=True, help="Native MCP client to configure.")
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
    parser.add_argument("--package-version", help="Version for --source-mode pinned. Defaults to the package version.")
    parser.add_argument(
        "--github-url",
        default=mcp_registration.DEFAULT_GITHUB_URL,
        help="GitHub repository URL for --source-mode github/private-github.",
    )
    parser.add_argument("--github-ref", help="Optional ref for --source-mode github/private-github.")
    parser.add_argument("--artifact", help="Wheel path or source checkout path for wheel/source modes.")
    parser.add_argument("--target-dir", default=".", help="Default target directory passed to aegis-mcp-server.")
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
        parser.add_argument("--cwd", help="Working directory for the native client command. Defaults to --target-dir.")


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
    status_parser.set_defaults(func=handle_status)

    next_parser = subparsers.add_parser(
        "next",
        help="Report the next required Aegis workflow action without mutating the target.",
    )
    next_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    next_parser.set_defaults(func=handle_next)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Diagnose installed Aegis workflow state without mutating the target.",
    )
    doctor_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured doctor report instead of a concise summary.",
    )
    doctor_parser.set_defaults(func=handle_doctor)

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
    repair_parser.set_defaults(func=handle_repair)

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
        help="Print the full structured closeout report instead of the concise human summary.",
    )
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
    certify_parser.add_argument("--skip-build", action="store_true", help="Inspect existing artifacts instead of building.")
    certify_parser.add_argument("--skip-smoke", action="store_true", help="Skip clean installed-wheel CLI smoke.")
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
    start_parser.add_argument("--goal", action="append", help="Goal to write into the generated plan/tracker.")
    start_parser.add_argument(
        "--no-create-branch",
        action="store_true",
        help="Require the current branch to already contain the allocated task id.",
    )
    start_parser.set_defaults(func=handle_start)

    log_parser = subparsers.add_parser(
        "log",
        help="Write required S:W:H:E progress entries for the current Aegis task.",
    )
    log_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    log_parser.add_argument("--handler", help="Handler identifier for the S:W:H:E H field. Optional with --pending-id.")
    log_parser.add_argument("--evidence", help="Evidence path or command for the S:W:H:E E field. Optional with --pending-id.")
    log_parser.add_argument("--note", required=True, help="Past-tense summary to append after the S:W:H:E token.")
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
    mcp_register.add_argument("client", choices=("claude", "codex"), help="Native MCP client to configure.")
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
    mcp_register.add_argument("--package-version", help="Version for --source-mode pinned. Defaults to the package version.")
    mcp_register.add_argument(
        "--github-url",
        default=mcp_registration.DEFAULT_GITHUB_URL,
        help="GitHub repository URL for --source-mode github/private-github.",
    )
    mcp_register.add_argument("--github-ref", help="Optional ref for --source-mode github/private-github.")
    mcp_register.add_argument("--artifact", help="Wheel path or source checkout path for wheel/source modes.")
    mcp_register.add_argument("--target-dir", default=".", help="Default target directory passed to aegis-mcp-server.")
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
    mcp_register.add_argument("--transport", choices=("stdio",), default="stdio", help="MCP server transport to register.")
    mcp_register.add_argument("--cwd", help="Working directory for the native client command. Defaults to --target-dir.")
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
