# Task 85 Session Continuation & State Workflows – Findings

## Open Questions
- How should guard enforce Serena memory references during continuation when memories are optional?

## Risks & Issues
- Existing workflows reference TodoWrite/TodoRead mapping that no longer fits Codex; risk of inconsistent guidance.
- Lack of dedicated guard checks for continuation could allow context drift across compactions.

## Completed Findings
- 2025-10-01: Inventory confirms continuation/state workflows exist but require Codex-specific guard integration and registry cleanup (see designs/session-continuation-inventory.md).
- 2025-10-02: Implementation plan defines new validation behavior + guard requirements; risks revolve around optional Serena usage and guard strictness (see designs/continuation-workflow-updates.md).
- 2025-10-03: Guard now enforces continuation validation evidence (plan sync, tracker entry, guard log); registry updates pending.
