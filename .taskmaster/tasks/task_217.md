# Task ID: 217

**Title:** One-shot closeout convergence for non-canonical usage (populate step)

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** Follow-up to TM 216. The churn-engine fix made canonical logged work (kickoff -> log scope/implement/verify -> verify --strict -> closeout --update-handoff) converge one-shot, proven empirically; the invariant holds (un-evidenced work fails). Residual: non-canonical usage (no --update-handoff flag, or non-default --surface selection) needs a fail->repair->pass step. OPTIONAL enhancement: a generate-don't-assert populate step so even non-canonical usage one-shots. GATED on adversarial-review constraints (do not ship without all five): (a) populate sources tokens ONLY from logged plan-step-implement/plan-step-verify rows, never from changed files; (b) NEVER synthesize strict_verify_rel SWHE lines unless a green .aegis/reports/verification-report.json exists on disk; (c) surgical per-section handoff repair preserving operator-authored prose, NOT _render_closeout_handoff wholesale regeneration (default-on full re-render clobbers operator edits); (d) pending-drain must compare on the pre-escape _normalize_evidence form with a log_work-style no-silent-miss guard (plan-cell tokens and payload_evidence use different normalizers); (e) dry_run stays strictly read-only. Negative test must assert failure on closeout.pending_tracking/closeout.strict_verify (handoff evidence gates pass vacuously over empty token lists). Central tests test_closeout_requires_semantic_handoff_and_passes_with_update and test_closeout_reports_missing_evidence_repair_guidance need rewrites; preserve repair_guidance coverage. Full design + 3 adversarial reviews captured in the TM 216 work-tracking DECISIONS.md and the analysis workflow output.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
