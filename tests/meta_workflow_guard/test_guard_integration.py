"""Integration tests exercising the codex-guard script end-to-end."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_SCRIPT = REPO_ROOT / "scripts" / "codex-guard"
SESSION_PATH = REPO_ROOT / "sessions" / "9999-guard-integration.md"


def _run_guard(*extra_args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(GUARD_SCRIPT), "validate", "--include-untracked", *extra_args]
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


class GuardIntegrationTests(unittest.TestCase):
    def tearDown(self) -> None:
        SESSION_PATH.unlink(missing_ok=True)

    def test_guard_passes_in_clean_state(self) -> None:
        SESSION_PATH.unlink(missing_ok=True)
        result = _run_guard()
        self.assertEqual(
            result.returncode,
            0,
            f"Expected guard success, got {result.returncode}: {result.stdout}\n{result.stderr}",
        )

    def test_guard_flags_placeholder_handler(self) -> None:
        SESSION_PATH.write_text(
            """
# Integration test session

[S:test|W:guard|H:VOID|E:note`placeholder handler`]
            """.strip()
            + "\n",
            encoding="utf-8",
        )
        result = _run_guard()
        self.assertEqual(result.returncode, 1, "Guard should fail when placeholder handler is present")
        self.assertIn("Handler still in placeholder state", result.stdout)


if __name__ == "__main__":
    unittest.main()
