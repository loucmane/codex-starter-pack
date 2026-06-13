# Task 218 — Robust + recoverable closeout evidence (2026-06-13)

HP-Coach second-order report (after #224): a committed, strict-verify-green task whose
implementation pending-tracking event was lost has permanently unrecoverable
closeout.evidence.{session,tracker,implementation,changelog} — the required token was the
VERBATIM git-commit command string, gone from the surfaces, no CLI path to re-assert
(aegis log refuses free-form; --update-handoff regenerates only handoff; repair no-op).

## What shipped (live scripts/_aegis_installer.py only)
DEMOTION rule in _is_closeout_required_evidence: free-text/compound-command tokens are
ADVISORY, not required — `cmd`...`` / `note`...`` prefix, plus a defensive fallback
(whitespace or shell-metachar AND not path-like, via new _evidence_token_is_path_like).
Real artifact paths and bare SHAs stay required. This recovers HP-Coach's canonical case
(command token leaves required_evidence; the artifact paths + strict_verify_rel already on
the four surfaces still gate).

## Design+adversarial workflow conclusions (3 agents)
- Demotion is necessary AND sufficient for HP-Coach.
- Stable-key matching (SHA/path) was DROPPED: inert for HP-Coach (required tokens are
  paths/commands, not bare SHAs) and largely redundant with the existing permissive
  verbatim-substring match; path-suffix matching added false positives (stale-backup,
  interior-dir). Zero marginal recall, real risk.
- Invariant holds (all attackers breaks_invariant=False): demotion weakens only
  documentation-completeness, never source-truth — closeout.strict_verify (recomputes
  verify against real source) + mutation.pending_tracking_empty are independent computed gates.

## Updated test
test_handoff_repair_converges_with_compound_bash_closeout_evidence pinned the OLD behavior
(cmd tokens required + in evidence_matrix); updated to assert they are now advisory (absent
from matrix) while closeout still converges on the real artifact. New tests:
test_is_closeout_required_evidence_demotes_command_tokens,
test_closeout_recovers_when_command_evidence_absent_from_progress_surfaces.

## Follow-ups filed
- TM 219: assets/scripts/_aegis_installer.py drift (missing 215+218, has reverted-in-live
  observation-globs) — packaging hygiene; NOT synced in 218 (HP-Coach runs live CLI).
- TM 220: path-lost sub-mode populate step (artifact-gated, = TM 217 territory); HP-Coach
  isn't hitting that sub-mode.

See [[task216-closeout-convergence]] and [[task215-schema-skew-diagnosis]].
