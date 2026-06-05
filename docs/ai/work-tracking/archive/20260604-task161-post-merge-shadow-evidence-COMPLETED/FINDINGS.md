# Findings

- 2026-06-04 — Run `26959807056` is a valid first operational post-merge shadow entry:
  `push` on `refs/heads/main`, context `post_merge_ci`, `valid_for_shadow: true`,
  artifact stored under `$RUNNER_TEMP`, `executed: false`, `mutated_live_repo: false`,
  `candidate_count: 0`, `would_apply: 0`, `shadow_refused: 0`, and no triage required.
- 2026-06-04 — The same run carries no precision signal. Codex main is structurally
  candidate-free when Taskmaster work is marked done before merge, so empty accumulation
  must not be counted as `0 divergences`, `100% precision`, or enablement evidence.
- 2026-06-04 — The pinned `task-master` CLI version available in this environment is
  `0.43.1`; a first `task-master next` state write over a full Taskmaster fixture creates
  `.taskmaster/state.json` as `{"migrationNoticeShown": true}` with no `tag`,
  `currentTag`, or `branchTagMapping` keys.
