# Decisions

- 2026-06-03 — Add a shared `aegis_foundation.taskmaster_toolchain` helper rather than hard-coding the Taskmaster version only in workflow YAML. Future apply code can import the same lock/evidence contract.
- 2026-06-03 — Keep `task-master` absence as a valid local/minimal-environment skip path, but make the supported CI job install the pinned CLI so real sacrificial cascade tests execute there.
- 2026-06-03 — Follow observed cascade behavior over the original expectation: pre-existing `.taskmaster/state.json` is rewritten under the pinned Taskmaster toolchain, so the dynamic shadow prediction includes it in both baseline branches.
- 2026-06-03 — Do not add write code, apply flags, MCP apply tools, or persistent multi-run ledgers in Task 152. Those remain Task 153+ concerns.
