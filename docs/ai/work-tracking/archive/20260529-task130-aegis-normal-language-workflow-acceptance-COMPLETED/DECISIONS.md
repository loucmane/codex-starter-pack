# Decisions

- 2026-05-29 — Create Taskmaster Task 130 as "Aegis Normal-Language Workflow Acceptance and First-Pass Closeout Hardening" with dependency on Task 129 and high priority.
- 2026-05-29 — Defer public package release/TestPyPI/PyPI work to a later task. Task 130 will focus on realistic live workflow behavior and only change code/docs where live acceptance exposes friction.
- 2026-05-29 — Measure success by behavior, not prompt compliance: no huge checklist prompt, no synthetic handler names, no direct edits to `IMPLEMENTATION.md` or `CHANGELOG.md`, no hidden Taskmaster/Serena dependency, and first-pass closeout after normal verification wherever feasible.
- 2026-05-30 — Treat `aegis.doctor` as a mandatory read-only post-closeout health check in the normal workflow. It should be suggested after final closeout writes a passing report, but it should not become another mutating gate.
