# Task 249 — Pre-adapter Codex Manifest Update Migration

- Date: 2026-07-13
- Branch: `feat/task-249-codex-hook-update-migration`
- Taskmaster: Task 249, in progress, depends on completed Task 248.
- Trigger: a read-only/live-safe Blog rollout rehearsal reproduced `aegis update --apply`
  validating the pre-adapter manifest before the installer could add managed Codex hooks.
- Selected fix: after preview safety succeeds, apply the reviewed managed install before
  strict runtime pointer refresh. Do not weaken direct runtime schema validation.
- Safety: divergent operator-owned `.codex/hooks.json` remains manual review and causes no
  manifest or runtime writes; exact `/hooks` hash trust remains attended.
- Proof: Codex-only and multi-agent legacy migration, current-schema output, idempotence,
  source/package installer parity, strict verification, and a disposable Blog snapshot.
- Local results so far: focused 6 passed; affected 18 passed; broad affected 181 passed
  with three opt-in skips; full suite 1,957 passed with the known `/tmp` location assertion
  reserved for hosted CI.
- Preservation: live Blog Task 40 and the primary Codex checkout's unrelated `.codex`,
  `.agents`, and local `.aegis` drift remain untouched.
