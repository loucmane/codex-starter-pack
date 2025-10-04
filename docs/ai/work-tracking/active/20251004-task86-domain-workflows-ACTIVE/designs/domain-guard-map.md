# Domain Guard & Convention Mapping

## Date / Time
- Captured: 2025-10-04 13:15 CEST

## Guard Requirements by Domain
| Domain | Guard Hooks Needed | Existing Behaviors | Notes |
|---|---|---|---|
| analysis | Evidence guard, continuation validation | `validation/evidence-claims.md` | Ensure guard checks analysis artifacts |
| debug | Debug guard behaviors | `handlers/triggers/debug/*` | Need guard reminders for logs/tests |
| development | Plan compliance, continuation | Existing plan guard | Add domain workflow references |
| docs | Documentation guard | `templates/handlers/operators/docs/*` | Guard to ensure documentation updates |
| external | Tool/CI guard | `templates/engine/activation/context-aware.md` | Coordinate with infrastructure workflows |
| file | File conventions guard | `workflow/resolve-handler-void.md` | Validate domain-specific conventions |
| git | Git commit guard | `validation/before-commit` | Already enforced; reference in workflow |
| search | Tool selection | `handlers/operators/search` | Minor guard addition |
| session | Continuation / end session | Task 85 guard | Link to domain workflow |
| test | Testing guard | `templates/testing/` | Combine with new workflow |
| workflow | Meta workflow guard | existing | Already in place |

## Conventions to Reference
- `templates/registry/handlers/operators-registry.md`
- `templates/engine/navigation/template-protocol.md`

## Next Actions
1. Update guard messaging to reference domain workflows.
2. Add guard configuration entries once workflows written.
3. Prepare regression tests per domain guard.
