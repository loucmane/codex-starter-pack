# Decisions

- 2026-06-02 — Keep Task 142 as a dogfood/evidence task only. Do not add status automation, Taskmaster mutation, git ref mutation, PR mutation, closeout, or Aegis state mutation to `aegis reconcile`.
- 2026-06-02 — Keep `done_merge_unknown` as task-level JSON detail rather than an actionable finding; the current-repo no-GitHub pass confirmed this keeps offline mode quiet.
- 2026-06-02 — Keep GitHub-enabled multi-PR ambiguity as a warning. It is useful operator signal and low-volume on current repo history.
