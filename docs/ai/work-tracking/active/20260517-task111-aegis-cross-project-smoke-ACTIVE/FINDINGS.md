# Findings

- 2026-05-17 — The kickoff wizard generated generic “wizard flow” plan language for Task 111. Corrected the plan before implementation so the work is grounded in the Aegis cross-project smoke harness boundary rather than editing `scripts/codex-task` by default.
- 2026-05-17 — Taskmaster created a strong Task 111 parent scope and five subtasks, but the shell initially interpreted backticks inside the add-task prompt. The failed attempt left no file changes; the successful retry used safe quoting and an approved outside-sandbox Taskmaster provider call.
- 2026-05-17 — The existing Aegis installer and MCP regression suite already covered many safety primitives, so Task 111.2 could stay focused on end-to-end CLI smoke across realistic project shapes instead of duplicating every negative case in the first slice.
- 2026-05-17 — PR CI exposed an archived-workflow lifecycle issue: `tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py` still pointed at the Task 110 ACTIVE folder after Task 110 had been correctly archived. The fix resolves the contract doc from the archived folder first and keeps the ACTIVE path as a fallback for in-progress runs.
