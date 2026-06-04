# Task 157 Harden read-only access and tracking classification – Changelog

- 2026-06-04 11:02 CEST — Initialized active work-tracking folder.
- 2026-06-04 11:20 CEST — Updated Task 157 scope from Claude red-team review and generated only `task_157.md`.
- 2026-06-04 11:20 CEST — Confined Aegis read-only target selection in the live and packaged Claude hooks.
- 2026-06-04 11:20 CEST — Added structured MCP `invalid_target` handling and confined all Aegis MCP target operations to the configured target root.
- 2026-06-04 11:20 CEST — Hardened reconcile `base_ref` validation and removed substring-based implementation inference.
- 2026-06-04 11:20 CEST — Added focused hook, installer, and MCP server regression tests.
- 2026-06-04 11:20 CEST — Verified focused and broader Aegis distribution/reconcile guard suites.
- 2026-06-04 11:20 CEST — Captured Serena memory `2026-06-04_task157_read_only_classification`.
- 2026-06-04 12:03 CEST — Addressed Claude adversarial residual by broadening hook-level MCP `target_dir` confinement to all Aegis target-bearing MCP tools, adding repair/bootstrap regression tests, removing the stale degraded safe-command allowlist, and re-verifying focused gate/Aegis suites.
