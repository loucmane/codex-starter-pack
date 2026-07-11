# Task 237 - Mode-aware agent guidance

Task 237 replaces contradictory static strict ceremony in managed CLAUDE.md, CODEX.md, and AGENTS.md entrypoints with a compact static mode-aware contract.

Implementation:
- Shared renderer in scripts/_aegis_installer.py.
- Advisory guidance: passive evidence, aegis brief, aegis witness, no routine per-mutation logging, pending drain, handoff repair, or closeout.
- Strict guidance delegates readiness, kickoff, logging, verification, and closeout to .aegis/contract.md.
- Managed blocks are capped at 25 nonblank lines.
- Existing Codex, Claude, and Agents project content remains outside deterministic markers.
- Existing Codex content is always merged on update.
- Fresh Claude and Agents entrypoints get explicit markers.
- Exact manifest-owned markerless legacy CLAUDE.md files migrate to the new block; checksum-diverged files are preserved conservatively.
- Canonical and packaged installer copies remain byte-identical.
- No enforcement, hook, gate, ledger, witness, capsule, or closeout behavior changed.

Verification:
- Final post-scope-cleanup suite: 225 passed, 2 opt-in distribution smokes skipped.
- Ruff, installer mirror cmp, and git diff --check pass.
- Whole-file Black churn was deliberately excluded because the legacy files are not globally Black-normalized; semantic changes were reconstructed onto original formatting and retested.
- Blog live dry-run: 5 safe managed modifications, no conflicts/manual/non-managed paths.
- Isolated Blog advisory apply: Claude/Codex/Agents blocks are 19/19/21 nonblank lines; Codex and Agents project bytes preserved; legacy Claude ceremony removed; second update is 0 modifies/39 skips.
- Evidence: docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/reports/mode-aware-agent-guidance/task-verification.md

Source closeout:
- Taskmaster Task 237 is done and only task_237.md was regenerated.
- Upstream source intentionally has no installed Aegis manifest; installed-target strict verification correctly returned install_aegis_before_verify and was not used.
- Source-native plan sync, work-tracking audit, guard, Taskmaster health/dependency validation, and diff checks pass.
- The completed Task 237 folder remains under active/ as the known compatibility projection until the next kickoff or Task 244 archive fallback.
- Readiness after Taskmaster done reports the known Task 244 done-task/ACTIVE mismatch; do not fabricate installed state or delete the retained tracker.

Residual:
After merge and a clean Blog task boundary, update Blog and capture one real agent orientation canary confirming advisory agents no longer apologize for skipped strict ceremony.