"""Package-style Aegis CLI entrypoint.

The command surface intentionally delegates to ``scripts._aegis_installer`` so the
repository-local ``scripts/codex-task aegis`` wrapper and package-style ``aegis`` wrapper
share the same deterministic installer behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

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


def _resolve_source_root(explicit_source_root: str | None) -> Path:
    for candidate in _candidate_source_roots(explicit_source_root):
        source_root = candidate.expanduser().resolve()
        if _looks_like_source_root(source_root):
            return source_root
    raise _aegis_installer.AegisError(
        "Unable to resolve Aegis source assets. Use --source-root or AEGIS_SOURCE_ROOT "
        "with a local Aegis checkout; bundled wheel assets are deferred to release hardening."
    )


def _agents_from_args(args: argparse.Namespace) -> list[str]:
    return list(getattr(args, "agent", None) or [])


def handle_inspect(args: argparse.Namespace) -> int:
    payload = _aegis_installer.inspect_project(args.target_dir, profile=args.profile)
    _dump_json(payload)
    return 0


def handle_plan_install(args: argparse.Namespace) -> int:
    payload = _aegis_installer.plan_install(
        args.target_dir,
        source_root=_resolve_source_root(args.source_root),
        profile=args.profile,
        primary_agent=args.primary_agent,
        agents=_agents_from_args(args),
    )
    _dump_json(payload)
    return 0


def handle_install(args: argparse.Namespace) -> int:
    payload = _aegis_installer.install(
        args.target_dir,
        source_root=_resolve_source_root(args.source_root),
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
    payload = _aegis_installer.verify(
        args.target_dir,
        source_root=_resolve_source_root(args.source_root),
    )
    _dump_json(payload)
    if payload.get("status") == "failed":
        print("Aegis verification failed", file=sys.stderr)
        return 1
    return 0


def handle_list_profiles(args: argparse.Namespace) -> int:
    payload = _aegis_installer.list_profiles(source_root=_resolve_source_root(args.source_root))
    _dump_json(payload)
    return 0


def handle_explain_profile(args: argparse.Namespace) -> int:
    payload = _aegis_installer.explain_profile(
        args.profile,
        source_root=_resolve_source_root(args.source_root),
    )
    _dump_json(payload)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Aegis Foundation CLI operations.")
    parser.add_argument(
        "--source-root",
        help=(
            "Path to the local Aegis source checkout. Defaults to AEGIS_SOURCE_ROOT or "
            "the editable-install source root."
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
    verify_parser.set_defaults(func=handle_verify)

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
