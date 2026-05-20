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


def handle_status(args: argparse.Namespace) -> int:
    with _resolve_source_root(args.source_root) as source_root:
        payload = _aegis_installer.status(
            args.target_dir,
            source_root=source_root,
        )
    _dump_json(payload)
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


def handle_log(args: argparse.Namespace) -> int:
    payload = _aegis_installer.log_work(
        args.target_dir,
        handler=args.handler,
        evidence=args.evidence,
        note=args.note,
        surfaces=args.surface,
        plan_step=args.plan_step,
        plan_status=args.plan_status,
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

    status_parser = subparsers.add_parser(
        "status",
        help="Report installed Aegis release state without mutating the target.",
    )
    status_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    status_parser.set_defaults(func=handle_status)

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
    kickoff_parser.add_argument("--task", required=True, help="Numeric task/work id.")
    kickoff_parser.add_argument("--slug", required=True, help="Short lowercase work slug.")
    kickoff_parser.add_argument("--title", required=True, help="Human-readable work title.")
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

    log_parser = subparsers.add_parser(
        "log",
        help="Write required S:W:H:E progress entries for the current Aegis task.",
    )
    log_parser.add_argument("--target-dir", default=".", help="Target repository root.")
    log_parser.add_argument("--handler", required=True, help="Handler identifier for the S:W:H:E H field.")
    log_parser.add_argument("--evidence", required=True, help="Evidence path or command for the S:W:H:E E field.")
    log_parser.add_argument("--note", required=True, help="Past-tense summary to append after the S:W:H:E token.")
    log_parser.add_argument(
        "--surface",
        action="append",
        choices=sorted(_aegis_installer.AEGIS_LOG_SURFACES),
        help="Additional workflow surface to update. Defaults to implementation, changelog, and handoff.",
    )
    log_parser.add_argument(
        "--plan-step",
        default="plan-step-implement",
        help="Plan step to update with this evidence. Pass an empty value to skip plan updates.",
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
