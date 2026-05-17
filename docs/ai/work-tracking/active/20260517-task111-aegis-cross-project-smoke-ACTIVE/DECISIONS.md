# Decisions

- 2026-05-17 — Task 111 will be implemented as a pytest-driven smoke harness over isolated temporary target repositories. It will not create a second installer, and it will not treat the source repository as an Aegis install target.
- 2026-05-17 — Preserve the Task 48/109/110 architecture boundary: `scripts/_aegis_installer.py` is the source of truth, `scripts/codex-task aegis ...` is the CLI wrapper, and `aegis_mcp/server.py` is a control-plane wrapper that must prove equivalence rather than fork semantics.
- 2026-05-17 — Keep the initial Task 111 shape builders local to `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`. Promotion into `cross_project_fixtures.py` should wait until another test module needs the same Aegis-specific target repository builders.
- 2026-05-17 — Task 111 recommends Task 112 as an Aegis packaging and invocation contract rather than expanding this task into distribution. The smoke harness proves install correctness; the remaining gap is how external projects invoke Aegis without relying on this source repo layout.
