# Meta Workflow Guard Remediation Guidance

## Preventative Requirements
- Plans modifying `templates/workflows/**` **must** include
  - `templates/workflows/processes/meta-workflow-authoring.md`
  - `templates/handlers/orchestrators/meta-workflow-authoring.md`
  - `templates/patterns/integration/workflow-gap-detection.md`
- Branch must follow the plan’s Branch Policy (e.g. `feat/task82-...`, `main-only` only when plan explicitly says so).
- `.plan_state/sync.log` entry must be up to date.

## Failure Modes & Fixes
### Guard failure `workflow authoring guard required`
1. Add the meta workflow files to plan scope (`## Scope` + evidence columns).
2. Update tracker checklist to mirror plan-step status.
3. Run `python3 scripts/codex-task plan sync`.
4. Re-run `python3 scripts/codex-guard validate --include-untracked`.

### Branch-policy failure
1. Switch to feature branch `feat/task<id>-description`.
2. If work must be on `main`, set plan `Branch Policy: main-only` and document rationale in tracker/handoff.
3. Record guard output in `reports/meta-workflow-guard/` and re-run guard.

### Missing evidence
- Create report file under `reports/meta-workflow-guard/` (e.g., guard logs, plan sync outputs) using `codex-task` helper logging.
- Update plan evidence column with concrete files/commands.

## Remediation Checklist
- [ ] Meta workflow files included in plan scope.
- [ ] Plan ↔ tracker sync current (`.plan_state/sync.log`).
- [ ] Guard run stored in `reports/meta-workflow-guard/` with timestamp.
- [ ] Session & tracker updated via `codex-task` logging.
- [ ] Branch name satisfies plan policy or waiver documented.
- [ ] Serena memory created if guard failure persisted across sessions.

