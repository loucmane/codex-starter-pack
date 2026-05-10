# Decisions

- 2026-05-10 — Use Task 48 as the backlog/template alignment checkpoint, not as a blind broad template migration. Implementation may proceed only from a proven current-state gap recorded in the Task 48 design artifacts.
- 2026-05-10 — Select CLI-core plus optional MCP/plugin wrappers as the portable foundation distribution model. `scripts/codex-task` should remain the testable source of truth; MCP/plugin layers may wrap it later but must not fork install/adoption semantics.
- 2026-05-10 — Route portable foundation installer/adoption productization to Task 46 rather than creating a duplicate new task. Task 46 should be re-scoped away from ZIP/marketplace/signing-first wording toward manifest, dry-run, doctor, adopt, upgrade, and fixture-tested bootstrap behavior.
- 2026-05-10 — Route permanent multi-agent runtime compatibility to Task 62. Tasks 103-107 are completed evidence for the Claude adapter; Task 62 should define the shared adapter contract and compatibility matrix across Codex, Claude, and future agents.
- 2026-05-10 — Do not hand-edit `.taskmaster/tasks/tasks.json` to force parent rewording after the Taskmaster provider/MCP update issues. Preserve the official status updates that succeeded, document the provider gap, and keep durable scope in work-tracking until a reliable Taskmaster update path is available.
