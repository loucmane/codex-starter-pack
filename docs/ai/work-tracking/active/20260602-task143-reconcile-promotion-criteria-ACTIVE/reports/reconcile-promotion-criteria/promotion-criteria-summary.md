# Task 143 Reconcile Promotion Criteria Summary

## Scope

Task 143 dogfooded the read-only `aegis reconcile` report against three additional safe fixture histories beyond the Task 142 current-repo and hpfetcher samples.

Fixture root:

```text
/tmp/aegis-task143-reconcile-promotion-fixtures-1780398438
```

Targets:

- `squash-offline`: disposable fixture repo with a squash-merge-shaped branch where git ancestry cannot prove merge in no-GitHub mode.
- `drift-mixed`: disposable fixture repo with one true `merged_but_not_done` case and one `done_but_not_merged` case exposed only when GitHub-style PR metadata is available.
- `ambiguity-stubs`: disposable fixture repo with abandoned in-progress branch, stale task branch, local Aegis ad hoc task, and multi-PR ambiguity.

No status automation, Taskmaster status mutation, git ref mutation, PR mutation, closeout automation, or Aegis state mutation was added or invoked by reconcile. All target repositories are disposable `/tmp` fixtures.

## Evidence Index

Per-target evidence includes before/after `git status --short`, branch, Taskmaster snapshot, Aegis state snapshot where present, raw command output, command-wrapped JSON output, and pure JSON payload output.

- `squash-offline-no-github.txt`
- `squash-offline-no-github.json`
- `squash-offline-no-github.payload.json`
- `drift-mixed-no-github.txt`
- `drift-mixed-no-github.json`
- `drift-mixed-no-github.payload.json`
- `drift-mixed-github.txt`
- `drift-mixed-github.json`
- `drift-mixed-github.payload.json`
- `ambiguity-stubs-no-github.txt`
- `ambiguity-stubs-no-github.json`
- `ambiguity-stubs-no-github.payload.json`
- `ambiguity-stubs-github.txt`
- `ambiguity-stubs-github.json`
- `ambiguity-stubs-github.payload.json`

Before/after status files:

- `current-repo-before-status.txt`
- `current-repo-after-status.txt`
- `squash-offline-before-status.txt`
- `squash-offline-after-status.txt`
- `drift-mixed-before-status.txt`
- `drift-mixed-after-status.txt`
- `ambiguity-stubs-before-status.txt`
- `ambiguity-stubs-after-status.txt`

All fixture before/after status diffs were empty.

## Target Results

### squash-offline

Command:

```bash
python3 scripts/codex-task aegis reconcile --target-dir /tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/squash-offline --base-ref main --no-github
```

Result:

- Status: `clean`
- Tasks checked: 1
- Findings: 0
- Errors: 0
- Warnings: 0
- GitHub: disabled

Interpretation:

- This is the desired behavior for squash-merge-shaped offline history.
- Task 201 remains `pending`, but its branch tip is not an ancestor of `main`; without GitHub metadata, reconcile records merge truth as `unknown` with proof `git_only_non_ancestor_or_missing_base`.
- No actionable finding is emitted, preventing a false `not merged` or `merged` claim.

Signal quality:

- False positives: 0.
- False negatives: no actionable false negative for the report-first contract; this is intentionally unknown without PR metadata.
- Operator action: no automatic action. If a human needs certainty, rerun with trustworthy PR metadata.

### drift-mixed

No-GitHub command:

```bash
python3 scripts/codex-task aegis reconcile --target-dir /tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/drift-mixed --base-ref main --no-github
```

No-GitHub result:

- Status: `drift`
- Tasks checked: 2
- Findings: 1
- Errors: 1
- Warnings: 0
- Finding: `merged_but_not_done` for Task 202 with proof `git_ancestor`

GitHub-enabled command using fixture `gh` metadata:

```bash
PATH=/tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/fake-gh/bin:$PATH python3 scripts/codex-task aegis reconcile --target-dir /tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/drift-mixed --base-ref main
```

GitHub-enabled result:

- Status: `drift`
- Tasks checked: 2
- Findings: 2
- Errors: 2
- Warnings: 0
- Findings:
  - `merged_but_not_done` for Task 202 with proof `git_ancestor`
  - `done_but_not_merged` for Task 205 with proof `github_pr_open`

Interpretation:

- Task 202 is true drift: the task is `pending`, but the task branch is provably merged by git ancestry.
- Task 205 is true drift only when PR metadata is available: the task is `done`, but fixture PR metadata says its PR is still open.
- The no-GitHub run correctly does not invent `done_but_not_merged` from non-ancestor git state alone.

Signal quality:

- False positives: 0 of 1 no-GitHub findings; 0 of 2 GitHub-enabled findings.
- False negatives: expected metadata-limited blind spot in no-GitHub mode for `done_but_not_merged` where only PR state can prove the open-PR condition.
- Operator action: treat `merged_but_not_done` with `git_ancestor` as high-confidence status drift; treat `done_but_not_merged` as high-confidence only when backed by current PR metadata.

### ambiguity-stubs

No-GitHub command:

```bash
python3 scripts/codex-task aegis reconcile --target-dir /tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/ambiguity-stubs --base-ref main --no-github
```

No-GitHub result:

- Status: `needs_review`
- Tasks checked: 4
- Findings: 3
- Errors: 0
- Warnings: 3
- Findings:
  - `abandoned_in_progress_branch` for Task 203
  - `stale_local_stub` for Task 999
  - `local_ad_hoc_stub` for Task 1000

GitHub-enabled command using fixture `gh` metadata:

```bash
PATH=/tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/fake-gh/bin:$PATH python3 scripts/codex-task aegis reconcile --target-dir /tmp/aegis-task143-reconcile-promotion-fixtures-1780398438/ambiguity-stubs --base-ref main
```

GitHub-enabled result:

- Status: `needs_review`
- Tasks checked: 4
- Findings: 4
- Errors: 0
- Warnings: 4
- Findings:
  - `abandoned_in_progress_branch` for Task 203
  - `multi_pr_epic_ambiguity` for Task 204
  - `stale_local_stub` for Task 999
  - `local_ad_hoc_stub` for Task 1000

Interpretation:

- All findings are expected review-only warnings.
- GitHub metadata adds useful operator signal for Task 204 but does not make the case auto-actionable.
- The warning set is correctly separated from drift errors.

Signal quality:

- False positives: 0 of 3 no-GitHub warnings; 0 of 4 GitHub-enabled warnings.
- False negatives: no known false negatives for the fixture shape; multi-PR ambiguity is necessarily unavailable in no-GitHub mode.
- Operator action: manual review only. Do not auto-close, auto-delete branches, or auto-mutate Taskmaster based on these warnings.

## Cross-Target Findings

- Reconcile remained read-only. All target before/after `git status --short` files were identical.
- Git ancestry is high-confidence for true merges and fast-forwards.
- Git non-ancestor is not sufficient evidence of not-merged because squash merges are possible.
- GitHub PR metadata is a useful accelerator, but when unavailable the report must keep squash-shaped cases unknown instead of producing false certainty.
- Warning-level ambiguity is useful as operator signal and should remain manual-only.

## Promotion Criteria For Future Auto-Mutation

Do not implement auto-mutation yet. A later task may consider it only if all criteria below are satisfied.

### Required sample coverage

- At least 5 safe target histories must be dogfooded, including:
  - the current Aegis repo,
  - at least one external real-project clone,
  - at least one squash-merge-shaped history,
  - at least one GitHub-metadata-backed history,
  - at least one ambiguity/stub-heavy history.
- Each sample must include before/after status proof showing reconcile itself did not mutate the target.

### Required signal quality

- Error-severity findings eligible for automation must have 0 unexplained false positives across the sample set.
- Any false positive in an error-severity finding blocks automation until the classifier or confidence model is corrected and redogfooded.
- Warning-severity findings remain manual review and are not auto-actionable.
- No-GitHub mode must preserve unknown state for squash-shaped non-ancestor branches.

### Auto-action eligibility

Potentially automatable in a later task, with explicit operator confirmation:

- `merged_but_not_done` only when merge proof is `git_ancestor` or `github_pr_merged` and the target worktree is clean.

Manual-only unless a later design proves otherwise:

- `done_but_not_merged`
- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- any `unknown` merge truth
- any case where GitHub metadata is unavailable or stale

### Required control-plane behavior

- Auto-mutation, if ever added, must be a separate explicit subcommand or mode, not part of default `aegis reconcile`.
- Default `aegis reconcile` must remain read-only.
- Any mutation must require an audit breadcrumb with before/after state, finding id, proof, operator confirmation, rollback notes, and exact command.
- Closeout/doctor must be able to report auto-mutation evidence and block if mutation evidence is missing or degraded.
- Rollback must be CLI-first and not depend on MCP availability.

## Recommendation

Keep `aegis reconcile` report-first. The current report is producing useful, low-noise operator signal across the tested fixture histories, but Task 143 intentionally stops at criteria and evidence. The next implementation task should not auto-flip status yet unless it starts by encoding the promotion criteria above as tests and an explicit design gate.
