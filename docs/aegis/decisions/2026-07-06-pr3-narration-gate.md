# PR-3 Narration Gate Evidence

Date: 2026-07-06

## Decision

Do not implement Capsule PR-3 narration yet.

The dogfood gate for PR-3 asks for real resume/compact evidence that computed capsules are
useful but insufficient to preserve intent across resumes. The current evidence shows a
freshness and computed-field gap, not a narration gap. Computed capsules should first grow
the missing deterministic facts before Aegis adds Stop-hook checkpoints or any LLM distill.

## Evidence

The on-disk capsule was stale during the next-task handoff:

```text
capsule status: STALE
compiled_at: 2026-07-06T15:49:36Z
compile_reason: risk-register-change
stale reasons:
- branch changed: feat/task-228-capsule-boundary-dogfood -> main
- HEAD changed: 5b591d3 -> a84d1f1
- Taskmaster state changed: 0e31049333f61e3d5e98c0ca8262a0eed24fb88b727d2caafa989cfad80a7b4f -> 9be191d867f94c654c36c64035d76ad64cac89a4810d469557ab6738a23998a2
- worktree status changed: c66fdb14d8778f684f228024519535a88715168a5e2ee5f6240163a00dd2ba0f -> e199b4edcab46a2988b2104498ce20975ba892a09ea83746d00aba2c20f91954
- new ledger events recorded: 7 -> 5058
- new gate decisions recorded: <none> -> 3091
```

That is valuable dogfood evidence, but it is evidence that boundary/session compile freshness
needs attention. Narration would not fix a stale computed artifact.

A fresh in-memory computed capsule, compiled with metadata writes disabled for the probe,
corrected the repo pose and task counts:

```text
# Aegis capsule (computed) - compiled 2026-07-06T18:47:37Z

**Branch?** `feat/task-208-capsule-narration-gate` at `a84d1f1` - 2 tracked edits (.codex/deep-work.config.toml, .taskmaster/tasks/tasks.json), 6 untracked; upstream: no upstream or not fetched [as-of 2026-07-06T18:47:37Z, source: git]
**Open PRs?** STALE - recheck (gh timeout or unavailable) [as-of 2026-07-06T18:47:37Z]
**Tests on record?** [source: ledger verification events]
- codex:tests: NO RUN ON RECORD
**Task truth:** counts {'done': 223, 'cancelled': 3, 'in-progress': 1, 'pending': 1}; uncommitted done-flips: False [source: tasks.json + ledger]
**Governance:** mode advisory (set by loucmane); decisions since last capsule: {}
**Known reds (sentinel):** 6 checks attempted, 6 parsed, 1 drift item(s), 2 red(s) listed
- canary fixture drift (planted; proves the sentinel ran)
- hygiene: 30 local branches (threshold)
```

This fresh computed output is useful: it corrects branch, commit, dirty state, Taskmaster
counts, verification absence, governance mode, and sentinel state.

The remaining continuity gap is deterministic: the fresh capsule does not name the current
Taskmaster task (`#208`), active subtask (`208.1`), or next safe action ("collect/record
PR-3 gate evidence; do not implement narration until the gate is met"). Those facts are
available from Taskmaster and current branch naming. They should be computed before adding a
narrated `last_session_story`.

## Consequences

- Keep PR-3 narration deferred.
- Treat #208.1 evidence collection as complete for now: the gate was evaluated and did not
  pass.
- Do not start #208.2 deterministic Stop checkpoints.
- Add a smaller follow-up for the computed capsule: include active task/subtask and next-action
  fields in `task_truth` / rendered injection, sourced from Taskmaster and branch state.
- Revisit PR-3 only after fresh computed capsules still fail to preserve intent after that
  deterministic improvement.

## Non-Decision

This does not reject PR-3 permanently. It only says the current evidence does not justify
building narration before cheaper computed-state fixes.
