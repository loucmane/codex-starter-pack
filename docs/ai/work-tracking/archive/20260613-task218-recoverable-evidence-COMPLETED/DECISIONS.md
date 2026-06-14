# Decisions — Task 218 recoverable closeout evidence

- 2026-06-13 — D1 — Ship the demotion rule; drop stable-key matching (redundant); defer populate step (TM 220). Full record below.

## D1 (2026-06-13): Demotion is the necessary-and-sufficient fix; matching changes dropped.

**Context.** HP-Coach reported a committed, strict-verify-green task (feat/task-80 @ 2be5828)
permanently stuck on closeout.evidence.{session,tracker,implementation,changelog}, each
`missing: [<verbatim git-commit command string>]`. Root cause: closeout required the verbatim
command token in all surfaces; the originating pending event was consumed during the pre-216
churn era, and no CLI path re-asserts evidence (aegis log refuses free-form; --update-handoff
only regenerates handoff; repair is a no-op).

**Design + 3-agent adversarial workflow findings.**
- The DEMOTION rule (command/free-text tokens → advisory) is necessary AND sufficient for
  HP-Coach's canonical case: the command token leaves required_evidence; the real artifact
  paths + strict_verify_rel are already on the four surfaces, so the gates pass.
- Stable-key matching (SHA + path) is INERT for HP-Coach (required tokens are paths/commands,
  not bare SHAs) and largely REDUNDANT with the existing permissive verbatim-substring match;
  the path-suffix variant introduced new false positives. Dropped — zero marginal recall, real risk.
- Full one-shot recovery of the PATH-LOST sub-mode (path absent from session/tracker) needs a
  bounded artifact-gated populate step — deferred to TM 220 (= TM 217 territory). HP-Coach is
  NOT hitting that sub-mode.

**Invariant (all three attackers: breaks_invariant=False).** Demotion weakens only the
documentation-completeness gate, never source-truth: closeout.strict_verify recomputes verify
against real source and mutation.pending_tracking_empty is independent. An un/under-evidenced
source mutation still fails closeout.

**Decision.** Ship demotion (live scripts/_aegis_installer.py) + tests. Drop matching changes.
Defer populate to TM 220. Do not sync the drifted assets/scripts installer copy here — it has
independent drift (missing TM 215, contains reverted-in-live observation-globs); filed as TM 219.

**Follow-ups:** TM 219 (assets installer drift / packaging hygiene), TM 220 (path-lost populate step).
