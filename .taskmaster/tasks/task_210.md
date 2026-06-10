# Task ID: 210

**Title:** Capsule PR-4: retirement (codex + companion target-repo PR)

**Status:** pending

**Dependencies:** 209

**Priority:** medium

**Description:** Spec: AEGIS_CAPSULE_SPEC.md section 5.2. Ships LAST. HARD GATE (do not start before all four hold): (a) witness v0 live as a required PR check, (b) ledger live, (c) capsule in real use, (d) the section 7 falsifier window run (2 weeks of A/B on HP-Coach with the keep/kill decision recorded). Scope, codex side: default enforcement for fresh installs becomes advisory (strict opt-in); PreToolUse readiness/current-work gate class becomes advisory-only permanently (strict mode still hard-blocks only protected-path denylist + settings/hook config integrity); tracking-stop-gate retired and Stop repurposed to checkpoint appends; posttooluse-tracking.sh pending-tracking machinery retired (the PR-1b recorder becomes the only PostToolUse hook); closeout handoff semantic gates removed from required paths (aegis closeout survives as an alias printing the witness delivery report); WORKFLOW_LINK_PREFIXES protections dropped; voluntary kickoff still generates HANDOFF/TRACKER but nothing requires/checks/repairs them; client_reload_required state machine and its ~10 installer message sites removed, gated on doctor min-version check. Doctor: pin minimum CLI version (Stop/SubagentStop additionalContext needs 2.1.163+) via claude --version on PATH (absent = warn, never fail); verify both PostToolUse hooks + injection wiring; shrink sentinel scope per section 3.2 (checks 1 and 4 become vacuous — expected, not rot). Companion PR in each deployed repo retires ceremony scaffolding per that repo's deployment doc. Replace, do not stack.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
