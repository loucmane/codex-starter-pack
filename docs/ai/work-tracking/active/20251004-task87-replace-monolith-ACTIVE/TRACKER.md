# Task 87 Replace Legacy Monolithic References Tracker

**Started**: 2025-10-04
**Status**: ACTIVE
**Last Updated**: 2025-10-04

## Goals
- [ ] Enumerate lingering references to WORKFLOWS.md / PATTERNS.md / BUILDING-BETTER.md
- [ ] Map each reference to new modular files (domain workflows, guards, helpers)
- [ ] Implement replacements and ensure guard enforcement blocks legacy paths
- [ ] Document migration and regression coverage

## Progress Log
- **2025-10-04 13:40** — [S:20251004|W:task87-replace-monolith|H:sessions/2025/10/2025-10-04-005-task87-replace-monolith.md|E:files`sessions/2025/10/2025-10-04-005-task87-replace-monolith.md`] Session started for Task 87 legacy replacement.
- **2025-10-04 13:41** — [S:20251004|W:task87-replace-monolith|H:plans/2025-10-04-task87-replace-monolith.md|E:files`plans/2025-10-04-task87-replace-monolith.md`] Task 87 plan created and linked via plans/current.
- **2025-10-04 13:44** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Recorded initial plan/tracker sync for Task 87.
- **2025-10-04 16:51 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md`] Work-tracking folder fully scaffolded with standard files.

- **2025-10-04 17:05 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md`] Catalogued primary legacy reference mappings and pending replacements.

## Plan Compliance Checklist
- [ ] plan-step-scope — Inventory legacy references and targets
- [ ] plan-step-implement — Replace references and update guard/tests
- [ ] plan-step-verify — Evidence bundle captured, guard/tests passing
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Completed Task 86 outputs provide new domain workflows
- Guard: scripts/codex-guard to enforce migration
