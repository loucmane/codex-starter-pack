"""Smoke test for the codex-guard CLI placeholder detection."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_SCRIPT = REPO_ROOT / "scripts" / "codex-guard"
SESSION_PATH = REPO_ROOT / "sessions" / "9999-guard-integration.md"
IGNORE_PREFIXES = [
    "docs/ai/work-tracking/active/20251020-task88-taskmaster-alignment-ACTIVE",
    "sessions/2025/10/2025-10-20-001-guard-enhancements.md",
]


def _run_guard(*extra_args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CODEX_GUARD_IGNORE_PATHS"] = ":".join(IGNORE_PREFIXES)
    cmd = [sys.executable, str(GUARD_SCRIPT), "validate", *extra_args]
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, env=env)


class GuardIntegrationTests(unittest.TestCase):
    def tearDown(self) -> None:
        SESSION_PATH.unlink(missing_ok=True)

    def test_guard_flags_placeholder_handler(self) -> None:
        SESSION_PATH.write_text(
            """
# Integration test session

[S:test|W:guard|H:VOID|E:note`placeholder handler`]
            """.strip()
            + "\n",
            encoding="utf-8",
        )
        result = _run_guard("--include-untracked")
        self.assertEqual(result.returncode, 1, "Guard should fail when placeholder handler is present")
        self.assertIn("Handler still in placeholder state", result.stdout)


if __name__ == "__main__":
    unittest.main()
