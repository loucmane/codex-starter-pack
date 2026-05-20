# Task 116 Aegis Strict Verification Kickoff

Date: 2026-05-19
Branch: feat/task-116-aegis-strict-verification
Taskmaster: Task 116, Aegis Strict Verification and Release Certification Pipeline

Scope:
- Add a mechanical `aegis verify --strict` gate over installed-project runtime completeness, hook wiring, workflow scaffold integrity, local CLI shim availability, mutation tracking, protected-path behavior, and optional Taskmaster/Serena integration semantics.
- Add release-candidate certification that builds wheel/sdist artifacts, computes checksums/provenance, installs from artifacts into clean target projects, runs strict verification and runtime smokes, and emits machine-readable reports.
- Keep Aegis portable: strict target verification must pass without Taskmaster or Serena, while reporting and using those integrations when present.

Workflow state:
- Active folder: docs/ai/work-tracking/active/20260519-task116-aegis-strict-verification-ACTIVE
- Session: sessions/2026/05/2026-05-19-002-task116-aegis-strict-verification.md
- Plan: plans/2026-05-19-task116-aegis-strict-verification.md

Subtasks:
1. Define strict verification and certification contracts against current Aegis surfaces.
2. Implement strict verifier core plus CLI, codex-task, and MCP surfaces.
3. Create release-candidate certification workflow for artifacts and reports.
4. Add pytest and CI coverage.
5. Document evidence handoff and publish-readiness requirements.
