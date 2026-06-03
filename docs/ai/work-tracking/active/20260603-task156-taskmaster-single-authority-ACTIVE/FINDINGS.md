# Findings

- 2026-06-03 — _Pending_ — document new findings here.
# Findings

- Taskmaster task selection was previously computed by an Aegis JSON heuristic (`_taskmaster_available_task`), which can disagree with `task-master next`.
- The fix is to suppress Aegis task selection whenever `.taskmaster/tasks/tasks.json` exists and is valid, requiring an explicit Taskmaster id for `aegis kickoff`.
- Present-but-invalid Taskmaster state must block local fallback; otherwise invalid authority state degrades into a competing local Aegis authority.
