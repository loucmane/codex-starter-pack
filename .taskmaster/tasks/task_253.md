# Task ID: 253

**Title:** Make Codex Hook Trust Verification Reproducible from Tracked State

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Eliminate strict verification's dependency on ignored install reports by deriving the exact no-bypass Codex hook-trust contract from the tracked manifest gate.

**Details:**

Update only the root installer, packaged installer asset, focused installer regression tests, and required task/Aegis evidence. Require strict verification to pass in a clean checkout without .aegis/reports/install-report.json, fail closed when the tracked codex.hook_trust manifest gate is missing, duplicated, or semantically altered, preserve advisory enforcement, and retain root/asset parity.

**Test Strategy:**

No test strategy provided.
