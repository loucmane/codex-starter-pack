# Task ID: 218

**Title:** Robust + recoverable closeout evidence (stable-key matching)

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** Second-order bug from HP-Coach after codex-216 (branch feat/task-80 @ 2be5828; forward-captured at .aegis/coldstart-scenarios/capture-2be5828be2.json). A committed, strict-verify-green task whose implementation pending-tracking event was LOST (drained generically during the pre-216 churn era) has PERMANENTLY unrecoverable closeout.evidence.{session,tracker,implementation,changelog} — while evidence.plan/handoff, handoff.*, strict_verify, and pending_tracking_empty all pass. Root cause = two current-codex behaviors confirmed: (1) _surface_contains_evidence (scripts/_aegis_installer.py:9265) matches the VERBATIM original git-commit command string token; (2) log_work (6776-6782) refuses free-form evidence when a non-matching pending event exists and there is no operator-attested write path; closeout --update-handoff regenerates ONLY handoff, not the other four surfaces; aegis repair is a no-op. The substantive evidence IS present in other forms (CHANGELOG has the commit SHA 14x, IMPLEMENTATION the changed files 4x) — just not the exact command token. This is the brittle-verbatim-matching the #224 adversarial review flagged. Fix options (HP-Coach): (1) extend handoff-style regeneration to the other four surfaces (= the TM 217 populate step, reviewer-constrained); (2) operator-attested 'aegis log --assert --surface S --evidence E' that records WITHOUT a matching pending event, audit-tagged; (3) RECOMMENDED root-cause: make closeout.evidence.* match on a STABLE key (commit SHA / changed-file set / plan-step id) instead of the verbatim multi-line command string — with the #224 reviewer caution (exact SHA, full-path equality / segment membership, NOT substring; compound-command free-text stays advisory). Stable-key matching fixes brittleness AND recoverability (the SHA/files are already in the surfaces) WITHOUT adding an evidence-write bypass. Invariant unchanged: un-evidenced work still fails (strict_verify + pending_tracking_empty independently gate; tokens still originate only from logged plan rows). Acceptance: from a committed task whose implementation pending-event was lost, ONE command re-asserts/recognizes the implementation evidence on the four surfaces and closeout passes — without re-committing, hand-editing markdown, or a matching pending event. Regression test seeded from the HP-Coach drained-event state. Interacts with TM 217 (option 1 IS the 217 populate step); decide whether to subsume or keep separate. Core-gate change: requires the same design + adversarial-review rigor as #224.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
