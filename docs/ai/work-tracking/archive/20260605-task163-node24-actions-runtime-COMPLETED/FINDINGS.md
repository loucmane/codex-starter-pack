# Findings

- 2026-06-05 — The Node 20 warning applies to GitHub JavaScript action wrappers (`checkout`, `setup-node`, `setup-python`, `upload-artifact`), not to the Node runtime used by Taskmaster. The lowest-risk transition is therefore a workflow-level Node 24 action-runtime opt-in with action versions unchanged.
- 2026-06-05 — The primary follow-up inspection risk is artifact transport, especially `upload-artifact@v4` handling of `$RUNNER_TEMP/aegis-shadow/` paths. This task preserves `upload-artifact@v4`; the PR run still needs artifact layout inspection before merge.
- 2026-06-05 — PR #163 CI confirms the runtime opt-in is active: GitHub reports the Node 20-targeting actions are being forced to run on Node 24. This validates the June 16 runtime transition but does not remove the annotation entirely; removing it requires a later action-version bump with a separate artifact-layout diff gate.
