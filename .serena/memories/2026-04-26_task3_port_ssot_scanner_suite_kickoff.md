# Task 3 Port SSOT Scanner Suite Kickoff - 2026-04-26

Started Task 3 on branch `feat/task-3-port-ssot-scanner-suite` after Task 2 merged and post-merge closeout was committed to `main` as `7709d99 chore(session): archive task 2 closeout`.

Current session: `sessions/2026/04/2026-04-26-001-task3-port-ssot-scanner-suite.md`.
Current plan: `plans/2026-04-26-task3-port-ssot-scanner-suite.md`.
Active tracker: `docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/TRACKER.md`.

Task 3 is broader than the old FPL MCP port wording. FPL MCP is historical context only, not the authority. The current authority is the Codex starter-pack foundation and the scanner behavior required by guards, metadata policy, template drift detection, metrics, repo-structure portability, and cross-project bootstrap/adoption workflows.

Task 3 is scoped as scanner-suite foundation reconciliation: audit current files first, compare against Taskmaster subtasks 3.1-3.8 and current foundation requirements, then implement only proven gaps.

Important decision: do not copy stale FPL source over current Codex scanner files without a diff-backed reason. The current Codex repository is the source of truth until the audit proves a gap.

Audit should include:
- Current scanner commands and whether CLI behavior is safe/predictable.
- Generated output hygiene and whether runtime outputs are ignored.
- Metadata output versioning/schema stability for downstream guard/metrics workflows.
- Repo-structure portability and hardcoded path assumptions.
- Scanner tests for behavior required by foundation workflows.
- Whether FPL MCP modules are still useful as comparison source or superseded.

Next steps:
1. Audit current scanner modules and tests under `scripts/template-ssot-scanner/`.
2. Capture module/capability/foundation-fit report under `docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/reports/ssot-scanner-suite/`.
3. Compare findings against Taskmaster subtasks 3.1-3.8 and broader foundation requirements.
4. Update FINDINGS/DECISIONS/HANDOFF before scanner code changes.
5. Run guard/tests and store evidence.