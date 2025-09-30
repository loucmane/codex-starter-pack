from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = REPO_ROOT / "scripts" / "codex-guard"

_loader = importlib.machinery.SourceFileLoader("codex_guard", str(GUARD_PATH))
_spec = importlib.util.spec_from_loader("codex_guard", _loader)
_codex_guard = importlib.util.module_from_spec(_spec)
sys.modules["codex_guard"] = _codex_guard
_loader.exec_module(_codex_guard)

ValidationIssue = _codex_guard.ValidationIssue
validate_timestamp_policy = _codex_guard.validate_timestamp_policy


class TimestampValidationTests(unittest.TestCase):
    def assert_issue_contains(self, issues, message_fragment):
        rendered = [issue.message for issue in issues]
        self.assertTrue(
            any(message_fragment in message for message in rendered),
            f"Expected fragment '{message_fragment}' in issues {rendered}",
        )

    def test_session_detects_missing_date_command(self):
        session_text = """---\ndate: 2025-09-30\n---\n\n- **[11:00]** — [S:20250930|W:test|H:some/handler|E:note`no date`] entry\n"""
        issues = validate_timestamp_policy(Path("sessions/2025/09/sample.md"), session_text, {"date": "2025-09-30"})
        self.assert_issue_contains(issues, 'Session missing date command entry')

    def test_session_detects_out_of_order_times(self):
        session_text = """---\ndate: 2025-09-30\n---\n\n- **[11:05]** — [S:20250930|W:test|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] logged\n- **[11:00]** — [S:20250930|W:test|H:other|E:note`later entry`] out of order\n"""
        issues = validate_timestamp_policy(Path("sessions/2025/09/sample.md"), session_text, {"date": "2025-09-30"})
        self.assert_issue_contains(issues, 'Session timestamps must be non-decreasing')

    def test_tracker_requires_chronological_order(self):
        tracker_text = """# Tracker\n- **2025-09-30 12:00** — [S:20250930|W:test|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] first\n- **2025-09-30 11:00** — [S:20250930|W:test|H:note|E:note`older`] reversed\n"""
        issues = validate_timestamp_policy(
            Path("docs/ai/work-tracking/active/20250930-test-ACTIVE/TRACKER.md"), tracker_text, {}
        )
        self.assert_issue_contains(issues, 'Tracker progress log must be chronological')

    def test_changelog_requires_reverse_chronological(self):
        changelog_text = """# Changelog\n\n| Date | Change | Evidence |\n|------|--------|----------|\n| 2025-09-29 | older | note |\n| 2025-09-30 | newer | note |\n"""
        issues = validate_timestamp_policy(
            Path("docs/ai/work-tracking/active/20250930-test-ACTIVE/CHANGELOG.md"), changelog_text, {}
        )
        self.assert_issue_contains(issues, 'Changelog entries must be in reverse chronological order')

    def test_tracker_requires_date_command(self):
        tracker_text = """# Tracker\n- **2025-09-30 11:00** — [S:20250930|W:test|H:note|E:note`no command`]\n"""
        issues = validate_timestamp_policy(
            Path("docs/ai/work-tracking/active/20250930-test-ACTIVE/TRACKER.md"), tracker_text, {}
        )
        self.assert_issue_contains(issues, 'Tracker missing recorded `date` command entry')


if __name__ == "__main__":
    unittest.main()
