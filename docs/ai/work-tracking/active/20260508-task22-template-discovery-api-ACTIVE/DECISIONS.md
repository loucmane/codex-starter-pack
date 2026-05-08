# Decisions

- 2026-05-08 — Implement Task 22 as an in-process `TemplateDiscoveryAPI` facade in `scripts/template_registry.py`. Do not add a REST server, Redis dependency, or GraphQL runtime in this task because those would conflict with the current portable foundation's core-script plus repo-adapter architecture.
- 2026-05-08 — Do not reopen completed Taskmaster Task 22 only to rewrite historical parent details. Taskmaster locked the completed task against update, and the implemented scope is already captured in the mandatory scope gate, tracker, handoff, session, and evidence files.
