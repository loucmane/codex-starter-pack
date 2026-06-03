# Findings

- 2026-06-02 — Shadow mode should not rewrite the Task 147 rollback fixture contract. The fixture starts with `.taskmaster/state.json`, so the registered Taskmaster done cascade remains `tasks.json` plus generated task markdown.
- 2026-06-02 — Real target baselines may lack `.taskmaster/state.json`; Taskmaster creates it during status mutation. Task 151 therefore records target-specific dynamic shadow prediction and validation rather than treating the preview path list as exhaustive.
- 2026-06-02 — CI evidence should be artifact-backed rather than repo-state-backed. The workflow now captures GitHub Actions context proof into the existing CI artifact path without adding an apply surface.
- 2026-06-03 — GitHub Actions Python jobs do not guarantee a global `task-master` CLI. The real sacrificial cascade tests should remain local/optional when the CLI is unavailable, matching the existing Task 147 rollback contract tests.
