# Task ID: 207

**Title:** Capsule PR-2b: SessionStart injection

**Status:** done

**Dependencies:** 206 ✓

**Priority:** high

**Description:** Spec: AEGIS_CAPSULE_SPEC.md sections 3, 3.3, 3.4. SessionStart hook (matchers startup|resume|clear|compact, main sessions only — no SubagentStart) + aegis brief --inject with the 8k-char budget (10k hook hard cap), the decided degradation order (repo_hygiene first; never drop repo_pose/delivery_state/verification_ledger/task_truth/open_loops/decisions_pending_owner), aegis brief --check as the only over-budget-fails mode, 1500ms total network budget with ~800ms gh timeout rendering STALE-recheck plus cached last-success, falsifier stamping (session_begin + capsule_on/off only; metric computed retrospectively from ledger), injection-safety contract (claim+citation schema, DATA-not-instructions wrapper label, distiller span exclusion). Fallbacks: UserPromptSubmit additionalContext; plain file at .aegis/capsule/current.md referenced from CLAUDE.md/AGENTS.md. First user-visible capsule. Merge gate: acceptance section 8 items 1-4 and 6. Requires install --apply run in target repos.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
