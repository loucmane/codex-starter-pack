# Task ID: 203

**Title:** Capsule PR-1b: async record hooks

**Status:** in-progress

**Dependencies:** 202 ✓

**Priority:** high

**Description:** Spec: docs/aegis/AEGIS_CAPSULE_SPEC.md sections 1.1, 1.2, 2. Wire PostToolUse AND PostToolUseFailure recording through the installer and rendered assets as a NEW parallel async:true hook entry (existing posttooluse-tracking.sh untouched until PR-4): basic events only (ts, session_id, cwd, branch, tool_name, normalized paths, outcome class, duration_ms, agent_id/agent_type), plus delivery events (git push / gh pr create / merge; branch-to-PR mapping) and task-truth events (tasks.json writes / task-master commands). Prerequisite: capture real hook payload fixtures from a live session under tests/fixtures/hook_payloads/ and test graceful degradation (missing field = null, never crash). Touch all five coordinated points from spec 1.1 (settings renderer, bootstrap script, cli.py hook choices incl. posttoolusefailure/sessionstart/sessionend, gate_lib routing, manifest hashes) using exec-form args. Includes the .gitignore hygiene rider on install/upgrade. Requires aegis plan-install + aegis install --apply in target repos. Together with task 202 this supersedes Phase-0 task 198 (passive ledger spike) and absorbs task 196's delivery-event capture. Merge gate: live HP-Coach events appear, nothing blocks.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
