# Bead ga-ejrm Transactional workflow foundation and reusable project plugin – Changelog

- 2026-08-29 20:43 CEST — Initialized active work-tracking folder.
- 2026-08-29 — Added transactional source-closeout lifecycle and recovery, packaged-script
  parity, and focused crash/idempotency coverage.
- 2026-08-29 — Added Gas City Workflow `0.1.0`, its tracked marketplace, project registry,
  descriptor schema, shared adapters, and live read-only project checks.
- 2026-08-29 — Added the Gas City Operations naming contract, two-stage migration procedure,
  and read-only legacy-consumer/worktree inventory tool.

## Progress Log
- **2026-08-29 22:54 CEST** - [S:20260829|W:ga-ejrm-workflow-foundation|H:codex:workflow-foundation-recovery|E:scripts/_source_workflow_state.py] Added fail-closed atomic current-work recovery for active uninstalled source checkouts and verified idempotent bead-native logging.
- **2026-08-30 00:20** — [S:20260830|W:ga-ejrm-workflow-foundation|H:cutover-ci-fix|E:test_aegis_release_distribution.py;scripts/codex-task;pytest:23-pass-2-skip] Corrected the canonical repository URL contract and added tested bead-native daily session continuation, then dogfooded it for ga-ejrm.
- **2026-08-30 00:28** — [S:20260830|W:ga-ejrm-workflow-foundation|H:packaged-script-parity|E:scripts/codex-task;aegis_foundation/assets/scripts/codex-task;pytest:369-pass-2-skip] Packaged and in-repository codex-task scripts now share exact SHA-256 47764697f7429251fc5930e0049b912396c68b6d1da8a2cf08c33133e205080c.
- **2026-08-30 00:44 CEST** — [S:20260830|W:ga-ejrm-workflow-foundation|H:canonical-cutover|E:merge:c9a1c17a;plugin:0.1.0;obsidian-runtime:f023e3d4] Completed the canonical repository and consumer cutover with exact rollback evidence and no Gas City or WSL Obsidian epoch change.
- 2026-08-30 00:47 CEST — Archived active work-tracking folder.
