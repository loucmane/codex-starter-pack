# Bead ga-ur1c.2 Enforce canonical Gas City Operations root and lifecycle parity Tracker

**Started**: 2026-08-31
**Status**: ACTIVE
**Last Updated**: 2026-08-31

## Goals
- [x] Define one machine-readable canonical/retired-root contract.
- [x] Make project-context and both adapter guards consume the same policy.
- [ ] Publish and apply the merge-bound transition without altering preserved historical evidence.

## Progress Log
- **2026-08-31 14:13** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-08-31 14:13 CEST`
- **2026-08-31 14:13** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260831-ga-ur1c.2-canonical-root-lifecycle-parity-ACTIVE/TRACKER.md] Scaffolded the `ga-ur1c.2` ACTIVE work-tracking folder through the bead-native kickoff flow
- **2026-08-31 14:13** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:bd:show|E:bead:ga-ur1c.2] Bound this source-workflow record to primary bead `ga-ur1c.2` without Taskmaster mutation
- **2026-08-31 14:13** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:sessions/current|E:sessions/current] Repointed current session, plan, and session state to `ga-ur1c.2`
- **2026-08-31** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:tests/meta_workflow_guard/test_gas_city_root_policy.py|E:pytest:7-failed] Captured RED coverage for the absent policy/runtime/installer surfaces.
- **2026-08-31** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:plugins/gas-city-workflow/scripts/root_policy.py|E:policy:v1] Implemented Git-common-root classification and shared fail-closed hook/context enforcement.
- **2026-08-31** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:plugins/gas-city-workflow/scripts/install_root_policy.py|E:transactional-user-install] Implemented scoped Codex/Claude configuration, exact backups, hook trust, idempotence, historical non-interference, and rollback.
- **2026-08-31** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:tests/meta_workflow_guard/test_gas_city_root_policy.py|E:pytest:9-passed] Focused root-policy suite passed; Ruff passed on changed Python surfaces.
- **2026-08-31 14:50** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:tests/meta_workflow_guard/test_gas_city_root_policy.py|E:pytest:2395-passed-21-skipped] Full regression passed: 2,395 tests passed and 21 intentionally skipped in 283.74s; changed Python surfaces pass Ruff/Black, the focused root-policy suite passes 9/9, and an isolated real Codex app-server readback proved the exact user-hook trust key can be marked trusted without changing unrelated configuration.
- **2026-08-31 14:58** — [S:20260831|W:ga-ur1c.2-canonical-root-lifecycle-parity|H:tests/meta_workflow_guard/test_gas_city_root_policy.py|E:github:pr-335-py311-fixture-failure] Hosted Python 3.11 exposed a non-hermetic rollback-test fixture that implicitly depended on this host's historical checkout; the production installer was not implicated. Bound both fixture roots explicitly and corrected their Codex/Claude fixture paths; focused suite passes 9/9.

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [ ] plan-step-implement — Update workflow/guard/docs and capture tests (source complete; publication/live apply pending)
- [ ] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
