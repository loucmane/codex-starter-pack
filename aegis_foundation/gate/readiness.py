"""Canonical adapter-neutral Aegis workflow-readiness façade."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import BLOCKED, Check
from .render import print_full, print_quick, summarize_state
from .state import discover_root
from .workflow import build_checks


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether Aegis workflow state is ready for persistent mutations."
    )
    parser.add_argument(
        "--quick", action="store_true", help="Emit one machine-friendly status line."
    )
    parser.add_argument(
        "--root",
        "--target-dir",
        dest="root",
        help="Repository root; --root remains the compatibility alias.",
    )
    parser.add_argument(
        "--adapter",
        choices=("aegis", "claude", "codex"),
        default="aegis",
        help="Select only the human-readable heading; policy is adapter-neutral.",
    )
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument(
        "--verbose",
        action="store_true",
        help="Emit a larger but bounded readiness sample (120 lines / 32 KiB).",
    )
    detail.add_argument(
        "--all",
        dest="all_output",
        action="store_true",
        help="Emit every readiness check without a renderer cap.",
    )
    return parser.parse_args(argv)


def evaluate(root: Path) -> tuple[str | None, list[Check], str]:
    """Return the authoritative read-only readiness result for ``root``."""

    task_id, checks = build_checks(root)
    return task_id, checks, summarize_state(checks)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = discover_root(args.root)
    task_id, checks, state = evaluate(root)
    if args.quick:
        print_quick(state, task_id, checks)
    else:
        print_full(
            root,
            state,
            task_id,
            checks,
            adapter=args.adapter,
            verbose=args.verbose,
            all_output=args.all_output,
        )
    return 2 if state == BLOCKED else 0


if __name__ == "__main__":
    sys.exit(main())
