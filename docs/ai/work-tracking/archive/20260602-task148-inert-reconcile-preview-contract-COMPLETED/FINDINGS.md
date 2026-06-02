# Findings

- 2026-06-02 — Reconcile Task 148 is a report-shape safety task, not an
  execution task. The useful next step is an opt-in candidate preview that
  remains inert to agents by construction: no default output change, no
  command-shaped fields, no apply path, and no writer consuming the preview.
- 2026-06-02 — The only auto-candidate class allowed by the current precision
  contract is `merged_but_not_done` with `git_ancestor` proof. Same-class
  findings with weaker proof, including `github_pr_merged`, stay excluded from
  the candidate list because they are not the calibrated auto-eligible class.
- 2026-06-02 — The candidate preview depends on the existing mutation gate as a
  backstop. An agent reading the preview must still be blocked from directly
  applying an out-of-band Taskmaster status flip for a non-active task.
