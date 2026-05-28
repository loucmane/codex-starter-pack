# Task ID: 128

**Title:** Add concise Aegis closeout output mode

**Status:** done

**Dependencies:** 125 ✓

**Priority:** medium

**Description:** Make Aegis closeout and closeout_ready output easier for public users and agents by defaulting to concise actionable summaries while preserving full JSON output for automation.

**Details:**

Add a concise default output mode for aegis closeout_ready and aegis closeout that reports status, failed required gates, warnings, pending tracking, next repair command, and report path without dumping the entire check array. Preserve structured JSON output behind an explicit --json or equivalent flag and keep MCP responses structured. Update docs, packaged docs, CLI tests, MCP tests where relevant, and live-flow acceptance notes so agents can act on closeout failures without parsing oversized terminal output.

**Test Strategy:**

No test strategy provided.
