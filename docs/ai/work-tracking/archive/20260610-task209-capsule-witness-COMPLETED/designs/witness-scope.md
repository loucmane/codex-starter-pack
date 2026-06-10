# PR-3.5 scope — delivery witness v0

Binding contract: AEGIS_CAPSULE_SPEC.md sections 1.2 (row 3.5), 5.1. Pulled ahead of
PR-3 (narration) deliberately: PR-3's merge gate ("only after the computed capsule
proves useful") needs falsifier-window evidence, while the witness is buildable now and
the program principle is BOUNDARY CHECKS EXIST BEFORE THE OLD SAFETY CLAIM IS RETIRED.
Taskmaster deps rewired accordingly (209 now depends on 207, not 208).

## Deliverables

1. **witness_lib.py** (assets + live mirror, stdlib-only): deterministic, zero-LLM
   boundary check computed from ledger + git + section 2.1 scope records. Checks:
   1. branch maps to a scope record (confirmed beats inferred) or the task-NN branch
      convention;
   2. every file in the base...HEAD diff is accounted for by the scope's path globs
      plus brief.json `witness.always_in_scope` (per-repo config — workflow surfaces
      etc.); DELETED test files escalate to human review (content weakening detection
      is the Q2 LLM upgrade, not v0);
   3. the scope's verification gates have `pass` runs on record AT the head commit
      (ledger);
   4. any done-flip recorded for this branch has a containing commit (uncommitted
      tasks.json done-flips fail);
   5. CI green is NOT re-implemented — native required checks own it; the report says
      so explicitly.
   Output = the generated delivery report (.aegis/reports/witness-report.json +
   rendered summary) — the replacement for the old hand-fed closeout.
2. **`aegis witness` CLI** (--base, --json, --ci), exit 0/1, read-only gate
   classification.
3. **CI mode finding (spec-revision note):** the out-of-worktree ledger does NOT
   travel to CI, so a required GitHub check cannot evaluate ledger-dependent check 3.
   v0 splits honestly: `--ci` runs the git+config-derivable checks (1 via branch
   convention + committed brief.json, 2, 4) and reports check 3 as
   `not_derivable_in_ci` (non-failing) with the local witness report as the
   authoritative artifact. Full resolution (witness report as PR artifact /
   attestation) feeds the spec's next revision.
4. **.github/workflows/aegis-witness.yml** running `aegis witness --ci` on PRs in this
   repo (dogfood). Flipping it to a REQUIRED check under branch protection is an
   owner/GitHub-settings action — flagged in the report, not performed by the agent.

## Merge gate (spec 1.2 row 3.5)
Runs as a check on a real PR (this one); zero LLM. Required-check designation is the
owner's branch-protection flip.
