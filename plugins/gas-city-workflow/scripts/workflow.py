#!/usr/bin/env python3
"""Run deterministic Gas City workflow lifecycle transitions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from project_context import DEFAULT_REGISTRY, build_context
from workflow_begin import begin, resume
from workflow_common import (
    CommandRunner,
    WorkflowError,
    active_bead_id,
    git_value,
    record_lifecycle_event,
    result_payload,
    run_readiness,
    workflow_runtime_root,
)


def _checkpoint(root: Path, runner: CommandRunner) -> dict[str, Any]:
    context = build_context(root, DEFAULT_REGISTRY)
    root = Path(context["project"]["root"])
    task = root / "scripts" / "codex-task"
    if task.is_file():
        runner.run([sys.executable, str(task), "plan", "sync"], cwd=root)
    run_readiness(runner, root)
    journal = record_lifecycle_event(runner, root, "checkpoint", "ready")
    return result_payload(
        "checkpoint",
        "ready",
        journal=journal.as_posix(),
        context=build_context(root, DEFAULT_REGISTRY),
    )


def _verify(
    root: Path,
    runner: CommandRunner,
    *,
    synchronize: bool = True,
) -> dict[str, Any]:
    context = build_context(root, DEFAULT_REGISTRY)
    root = Path(context["project"]["root"])
    source_task = root / "scripts" / "codex-task"
    checks: list[str] = []
    if synchronize and source_task.is_file():
        runner.run([sys.executable, str(source_task), "plan", "sync"], cwd=root)
        checks.append("plan-sync")
    run_readiness(runner, root)
    guard = root / "scripts" / "codex-guard"
    checks.append("readiness")
    if guard.is_file():
        runner.run([sys.executable, str(guard), "validate", "--include-untracked"], cwd=root)
        checks.append("guard")
    runner.run(["git", "-C", str(root), "diff", "--check"])
    runner.run(["git", "-C", str(root), "diff", "--cached", "--check"])
    checks.append("git-diff-check")
    if source_task.is_file() and not (root / ".aegis" / "foundation-manifest.json").is_file():
        runner.run(
            [sys.executable, str(source_task), "work-tracking", "audit"],
            cwd=root,
        )
        checks.append("source-work-tracking-audit")
    else:
        runtime = workflow_runtime_root()
        runner.run(
            [
                sys.executable,
                str(runtime / "scripts" / "codex-task"),
                "aegis",
                "verify",
                "--target-dir",
                str(root),
                "--strict",
            ],
            cwd=runtime,
        )
        checks.append("aegis-strict")
    journal = record_lifecycle_event(runner, root, "verify", "passed", checks=checks)
    return result_payload("verify", "passed", checks=checks, journal=journal.as_posix())


def _publish(root: Path, runner: CommandRunner) -> dict[str, Any]:
    context = build_context(root, DEFAULT_REGISTRY)
    root = Path(context["project"]["root"])
    _verify(root, runner, synchronize=False)
    status = git_value(runner, root, "status", "--porcelain=v1")
    if status:
        raise WorkflowError("publication preflight requires a clean worktree")
    head = git_value(runner, root, "rev-parse", "HEAD")
    tree = git_value(runner, root, "rev-parse", "HEAD^{tree}")
    branch = git_value(runner, root, "branch", "--show-current")
    runner.run(["git", "-C", str(root), "verify-commit", head])
    journal = record_lifecycle_event(
        runner,
        root,
        "publish",
        "ready",
        head=head,
        tree=tree,
        branch=branch,
    )
    return result_payload(
        "publish",
        "ready",
        head=head,
        tree=tree,
        branch=branch,
        journal=journal.as_posix(),
        next_action=(
            "Push this exact signed head, run hosted CI, and merge only under the "
            "repository's exact-head/base, green-CI, CLEAN/MERGEABLE, zero-thread rules."
        ),
    )


def _finish(root: Path, runner: CommandRunner, *, apply: bool) -> dict[str, Any]:
    context = build_context(root, DEFAULT_REGISTRY)
    root = Path(context["project"]["root"])
    bead_id = active_bead_id(root)
    run_readiness(runner, root)
    source_task = root / "scripts" / "codex-task"
    if source_task.is_file():
        argv = [sys.executable, str(source_task), "work-tracking", "archive"]
        backend = "source-archive"
    else:
        canonical_task = workflow_runtime_root() / "scripts" / "codex-task"
        argv = [
            sys.executable,
            str(canonical_task),
            "aegis",
            "closeout",
            "--target-dir",
            str(root),
            "--update-handoff",
            "--require-clean-git",
            "--json",
        ]
        if not apply:
            argv.append("--dry-run")
        backend = "installed-closeout"
    if not apply and backend == "source-archive":
        journal = record_lifecycle_event(
            runner,
            root,
            "finish",
            "planned",
            bound_bead_id=bead_id,
            backend=backend,
        )
        return result_payload(
            "finish",
            "planned",
            backend=backend,
            journal=journal.as_posix(),
            command=argv,
            next_action="Run finish --apply only after implementation publication evidence is recorded.",
        )
    result = runner.run(argv, cwd=root)
    journal = record_lifecycle_event(
        runner,
        root,
        "finish",
        "applied" if apply else "checked",
        bound_bead_id=bead_id,
        backend=backend,
    )
    return result_payload(
        "finish",
        "applied" if apply else "checked",
        backend=backend,
        journal=journal.as_posix(),
        output=result.stdout.strip(),
        next_action=(
            "Publish any closeout commit, then close the bead and require the terminal "
            "Obsidian projection plus a subsequent no-op reconciliation."
        ),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("begin", "resume", "recover"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", default=".")
        command.add_argument("--registry", default=str(DEFAULT_REGISTRY))
        command.add_argument("--bead", required=name == "begin")
        command.add_argument("--slug")
        command.add_argument("--goal", action="append", default=[])
        if name == "begin":
            command.add_argument("--dry-run", action="store_true")
    for name in ("checkpoint", "verify", "publish"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", default=".")
    finish = subparsers.add_parser("finish")
    finish.add_argument("--root", default=".")
    finish.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runner = CommandRunner()
    root = Path(args.root).expanduser().resolve()
    try:
        if args.command == "begin":
            payload = begin(
                root,
                args.bead,
                slug=args.slug,
                goals=args.goal,
                registry=Path(args.registry),
                dry_run=args.dry_run,
                runner=runner,
            )
        elif args.command in {"resume", "recover"}:
            bead_id = args.bead or active_bead_id(root)
            payload = resume(
                root,
                bead_id,
                slug=args.slug,
                goals=args.goal,
                registry=Path(args.registry),
                runner=runner,
            )
            payload["action"] = args.command
        elif args.command == "checkpoint":
            payload = _checkpoint(root, runner)
        elif args.command == "verify":
            payload = _verify(root, runner)
        elif args.command == "publish":
            payload = _publish(root, runner)
        else:
            payload = _finish(root, runner, apply=args.apply)
    except Exception as exc:  # noqa: BLE001 - stable fail-closed CLI boundary.
        print(f"gas-city-workflow: BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
