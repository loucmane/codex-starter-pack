# Task 216 — Closeout convergence: kill the evidence/pending-tracking loop (2026-06-13)

## What shipped
The CHURN-ENGINE fix in .claude/scripts/gate_lib.py (+ assets mirror):
- Read-only inspectors no longer misclassify as mutations: added jq, column, comm, cmp,
  cut, diff, dirname, basename, file, fmt, fold, nl, od, paste, printf, realpath, sort,
  tr, uniq, xxd, yq to READ_ONLY_SIMPLE_COMMANDS, with READ_ONLY_WRITE_FLAG_GUARDS for
  in-place writers (sed -i, yq -i/--inplace, sort -o) — those stay mutations. Redirect
  to file still caught by is_persistent_redirect_target.
- codex-task logging/workflow commands no longer arm pending-tracking against themselves:
  new payload_is_codex_task_logging (work-tracking update, work-tracking audit, sessions
  update, plan sync, scanner run) added to record_pending_tracking_event exclusions —
  the codex-task analog of payload_is_aegis_log (which already excluded both `aegis log`
  and `python3 -m aegis_foundation.cli log`).
- Tests: tests/claude_adapter/test_pending_tracking_churn.py (54) + corrected one
  existing gate test that pinned the OLD buggy "block read-only jq when BLOCKED" behavior
  (read-only inspection is allowed even when BLOCKED) + added positive test for that.

## Adversarial diff-review caught 5 gate-bypass escapes pre-merge (hardening that shipped)
A 5-agent review workflow on the actual diff found real escapes; all fixed before merge with tests:
- Bundled short clusters (sed -ni, sort -uo, yq -Pi) — first guard used token.startswith,
  missed non-leading write letters. Fixed with cluster-aware command_has_write_flag.
- GNU long forms sed --in-place / sort --output[=FILE] — guard set only had short forms.
  Added long forms; matcher handles --flag and --flag=value.
- Positional-output writers uniq IN OUT, xxd -r IN OUT — a flag guard CANNOT model positional
  output arity, so removed from READ_ONLY_SIMPLE_COMMANDS entirely (now mutations = safe
  over-enqueue). LESSON: only stdout-only commands belong in the read-only set.
- MOST SERIOUS — compound bypass: bash_is_codex_task_logging / bash_has_trusted_aegis_subcommand
  / _nested returned True if ANY segment matched, so `codex-task plan sync; rm -rf src` (and
  pre-existing `aegis log && rm -rf src`, `aegis kickoff && rm`) excluded the WHOLE payload —
  core-invariant break. Fixed to whole-payload-AND: a sanctioned segment excludes only when
  EVERY other segment is read-only (redirect-aware bash_is_read_only per segment, so
  `...; echo x > src/f` is caught). Legit logging+read-only chains still excluded.

## The decisive finding (9-agent read-only workflow: reproduce + map + design + review)
Post-churn-fix, the canonical flow ALREADY converges one-shot (empirically reproduced via
real CLI: kickoff -> log scope/implement/verify -> verify --strict -> closeout
--update-handoff = status passed, 23/23, idempotent). The original HP-Coach loop WAS the
adapter hooks (gate_lib.py) arming pending-tracking on inspection/self-writes — exactly
what the churn fix removes. `aegis log` clears pending-tracking, never arms it; the
_aegis_installer.py closeout machinery has no self-re-arming loop. Invariant holds:
un-evidenced source mutation fails closeout (11 gates); --update-handoff can't fabricate
evidence.

## Why the generate-don't-assert populate rework was NOT done (deferred to TM 217)
3 adversarial reviewers returned sound-with-changes with serious concerns: strict_verify_rel
synthesis soft spot; default-on handoff render CLOBBERS operator prose; drain normalizer
mismatch reintroduces non-convergence; central test rewrites needed; design's own negative
test reasoning was wrong (handoff evidence gates pass vacuously over empty token lists; real
blockers are closeout.pending_tracking + closeout.strict_verify). Residual non-convergence is
bounded (non-default --surface = fail -> 1 repair -> pass, with exact repair commands emitted),
not an infinite loop. Full design + reviews in the TM 216 DECISIONS.md.

See [[task215-schema-skew-diagnosis]] (companion HP-Coach report fix) and
[[capsule-program-state]].
