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
