# Task ID: 198

**Title:** Aegis passive ledger spike

**Status:** cancelled

**Dependencies:** 195

**Priority:** high

**Description:** Prototype auto-captured PostToolUse event ranges with boundary annotations instead of log-after-every-mutation blocking.

**Details:**

Add an experimental passive-ledger path: PostToolUse records the WHAT automatically (tool, normalized command/action, args digest, diff hash, output hash or artifact pointer, timestamp, cwd, agent identity) without blocking the next mutation. Replace per-mutation aegis log ceremony with aegis annotate --range for WHY narration at phase boundaries. Boundary gates should fail only when a phase has unannotated substantive event ranges, preserving the Stop-gate true positive without taxing every edit/browser action. Run the replay harness to show historical per-mutation false positives disappear while true positives and adversarial cases still fire.

**Test Strategy:**

No test strategy provided.
