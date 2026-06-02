# Decisions

- 2026-06-02 — Keep Task 143 report-first. Do not implement auto-status mutation, Taskmaster mutation, git ref mutation, PR mutation, closeout automation, or Aegis state mutation in this task.
- 2026-06-02 — Treat warning-level ambiguity findings as manual-review-only; do not promote `multi_pr_epic_ambiguity`, stale stubs, local ad hoc stubs, or abandoned in-progress branches to auto-actionable behavior.
- 2026-06-02 — Require high-confidence proof (`git_ancestor` or `github_pr_merged`) and explicit operator confirmation before any later task considers automating `merged_but_not_done`.
