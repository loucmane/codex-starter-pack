# Findings

- 2026-06-05 — The Node 20 warning applies to GitHub JavaScript action wrappers (`checkout`, `setup-node`, `setup-python`, `upload-artifact`), not to the Node runtime used by Taskmaster. The lowest-risk transition is therefore a workflow-level Node 24 action-runtime opt-in with action versions unchanged.
- 2026-06-05 — The primary follow-up inspection risk is artifact transport, especially `upload-artifact@v4` handling of `$RUNNER_TEMP/aegis-shadow/` paths. This task preserves `upload-artifact@v4`; the PR run still needs artifact layout inspection before merge.
