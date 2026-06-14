# Task 218 — Robust + recoverable closeout evidence: design scope

Date: 2026-06-13. Trigger: HP-Coach second-order report — a committed, strict-verify-green
task whose implementation pending-tracking event was lost has permanently unrecoverable
closeout.evidence.{session,tracker,implementation,changelog} (the required token is the
verbatim git-commit COMMAND string, gone from the surfaces, with no CLI path to re-assert).

## Decision (design + 3-agent adversarial workflow; see DECISIONS.md)
Ship the DEMOTION rule only; defer stable-key matching (redundant) and the populate step (217/220).

- ROOT FIX = demotion: free-text/compound-command tokens (`cmd`...`` / `note`...`` prefix,
  plus a defensive whitespace/shell-metachar-and-not-path fallback) are ADVISORY, not
  required, in _is_closeout_required_evidence. This recovers HP-Coach's canonical case (the
  command token leaves required_evidence; the real artifact paths + strict_verify_rel, which
  ARE on the surfaces, still gate). Verified necessary AND sufficient by the recovery-correctness agent.
- DROPPED stable-key (SHA/path) matching: the adversarial workflow showed it is INERT for
  HP-Coach (required tokens are paths/commands, never bare SHAs) and largely REDUNDANT with
  the existing permissive verbatim-substring match; the path-suffix variant introduced new
  false positives (stale-backup, interior-dir). Not worth the risk for zero marginal recall.
- DEFERRED populate step (TM 220): only the path-lost sub-mode (path absent from
  session/tracker) needs it; HP-Coach isn't hitting that. Artifact-gated, = TM 217 territory.

## Invariant (all 3 attackers: breaks_invariant=False)
Demotion weakens only the DOCUMENTATION-COMPLETENESS gate, never SOURCE-TRUTH:
closeout.strict_verify (recomputes verify against real source) and
mutation.pending_tracking_empty are independent computed gates. Un/under-evidenced work
still fails.

## Boundary
Live scripts/_aegis_installer.py + tests only. The assets/scripts copy is independently
drifted (missing 215, has reverted-in-live observation-globs) — filed as TM 219, NOT synced
here. HP-Coach gets the fix by running the live CLI.
