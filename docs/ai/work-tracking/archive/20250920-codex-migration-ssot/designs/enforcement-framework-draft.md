# Enforcement Framework (Draft)

## Purpose
Create a unified enforcement strategy ensuring every action consults the correct template workflow before execution. Addresses recurring issues (commit format, plan discipline, timestamp accuracy) by routing all work through template-driven guards and behaviors.

## Core Principles
1. **Registry-first**: Always load the appropriate template handler/behavior before performing work.
2. **Plan-first**: Use plan compliance guard; no work occurs without an approved plan.
3. **Evidence-required**: S:W:H:E must be populated from real commands/files.
4. **Guard-validated**: `codex-guard` acts as gatekeeper—no compliance, no progress.

## Enforcement Layers
- **Behaviors**: session, plan compliance, timestamp, commit guard (to be drafted/updated).
- **Guards**: `codex-guard validate` aggregates checks (plan, timestamps, evidence). Future enhancements may include auto-fix recommendations.
- **Plan & Tracker**: enforce step alignment and documentation.
- **Templates**: workflows/conventions/handlers define execution rules; must be consulted before acting.

## Process Flow
1. Load `templates/registry` entry relevant to task.
2. Invoke necessary behaviors (plan compliance, timestamps, etc.).
3. Execute plan steps; evidence recorded in sessions/work-tracking.
4. Run guard; if compliance passes, proceed. Otherwise fix and rerun.
5. Update documentation/handoff.

## Implementation Tasks (Draft)
- Task: "Build enforcement framework"
  - Subtask 1: Review existing behaviors/guards; map coverage gaps.
  - Subtask 2: Implement plan compliance behavior/guard.
  - Subtask 3: Implement timestamp gate.
  - Subtask 4: Update commit conventions (double-quote rule) within guard behavior.
  - Subtask 5: Ensure meta workflow authoring invokes template checks.
  - Subtask 6: Document enforcement flow (session/tracker/handoff).
  - Subtask 7: Create guard tests to validate enforcement.

## Open Questions
- Additional behaviors needed? (e.g., commit format behavior, guard auto-fix, plan sync helper)
- Handling special cases (informational sessions, plan waivers).

## Next Steps
1. Review draft with loucmane.
2. Integrate enforcement requirements into existing plan/meta/timestamp drafts.
3. Implement behaviors/guards in priority order.
4. Build verification scripts/tests.

## Additional Behaviors/Guards
- Commit Format Behavior: enforce double-quote commit messages (`git log -1 --pretty=format:"%s"`).
- File Scope Guard: compare `git diff --name-only` against plan-declared files; block out-of-scope edits.
- Test Evidence Gate: require test output evidence before plan verification step is marked complete.

## Tooling Enhancements
- Plan Dashboard: visualize active plans, statuses, conflicts (future tooling requirement).
- Guard Report Generator: HTML/JSON report showing violations, trends, suggested fixes.
- Plan Migration Tool: assists in converting legacy work to compliant plans.

## Risk Mitigation & Adoption
- Gradual enforcement: start with opt-in workflows, monitor guard metrics.
- Performance considerations: caching plan hashes, file watchers for guard triggers.
- Degraded mode: document behavior when plan tool temporarily unavailable (manual file-only mode).

## High-Value Enhancements (Proposed)

### Template Drift Detection
- Tool: `scripts/codex-guard drift-check`
- Detects divergence between templates and implementation (AST/diff based).
- Outputs drift percentage, impacted files, reconciliation suggestions.
- Integration: scheduled run + guard hook for high drift.
- Tasks:
  1. Design detection heuristics (AST/diff)
  2. Implement CLI + guard integration
  3. Store drift metrics for dashboard consumption

### Interactive Template Wizard
- Tool: `codex-template wizard --template <name>`
- Guides users through template steps, auto-filling S:W:H:E when possible.
- Enforces plan compliance + guard checks inline.
- Tasks:
  1. Design wizard UX (prompt flow, auto-fill rules)
  2. Implement CLI wrapper calling behaviors/guards
  3. Integrate logging (plan/tracker updates)

### Template Metrics Dashboard
- Aggregates guard logs + plan data (usage/compliance rates, violations).
- Provides trends to guide template improvements.
- Tasks:
  1. Define metrics schema (usage, compliance, violations)
  2. Build data collector (parse guard logs, plan sync logs)
  3. Implement simple dashboard/report (web or markdown)
