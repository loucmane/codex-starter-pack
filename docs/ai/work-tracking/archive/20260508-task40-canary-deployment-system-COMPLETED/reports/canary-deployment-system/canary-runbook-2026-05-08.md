# Foundation Canary Rollout Runbook

- Label: task40-foundation-canary
- Created at: 2026-05-08T18:57:00+02:00
- Mode: non-destructive-foundation-canary-rollout-plan
- Executes mutations: False
- Current branch: feat/task-40-canary-deployment-system
- Current HEAD: d9cb3d01394139dc80caa1396cbe9b0fb91a1932
- Current dirty status entries: 10

## Promotion Model

- Automatic promotion: False
- Reviewed evidence required: True
- Minimum total observation hours: 144

## Rollback Policy

- Automatic rollback: False
- Checkpoint required: True

## Stages

### Codex baseline canary

- Stage ID: codex
- Minimum observation: 24 hours
- Scope: Codex runtime, direct git execution, guard/task helpers, and local verification workflow

Entry criteria:
- Task scope is reconciled against the portable foundation.
- Codex guard passes locally and in CI.
- Full pytest suite passes locally and in CI.
- Taskmaster health reports zero invalid dependency references.
- Work-tracking audit has no active-session issues.

Health checks:
- `python3 scripts/codex-guard validate --include-untracked`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-task work-tracking audit`
- `git diff --check`

Promotion criteria:
- Observation window completes with no guard, CI, or workflow-state regression.
- Rollback checkpoint or recovery path is documented for the rollout slice.
- Findings and decisions are updated for any anomaly.

Rollback triggers:
- Guard, CI, or pytest regression caused by the rollout slice.
- Workflow state cannot be restored to a clean between-session state.
- Taskmaster dependency health reports invalid references.

### Claude runtime canary

- Stage ID: claude
- Minimum observation: 48 hours
- Scope: Claude runtime adapter, readiness gate, pretooluse gate, slash commands, and Claude-owned workflow surfaces

Entry criteria:
- Codex baseline canary promotion criteria are satisfied.
- Claude readiness exits READY in a properly scaffolded session.
- Cold-session mutation gate evidence remains current.
- Claude-owned changes stay out of Codex-owned paths unless explicitly authorized.

Health checks:
- `bash .claude/scripts/readiness.sh --quick`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/claude_adapter`
- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task work-tracking audit`

Promotion criteria:
- Claude can perform allowed mutations only after readiness is READY.
- Claude cannot mutate protected Codex-owned paths through file tools or Bash bypasses.
- Evidence is captured in session/work-tracking artifacts, not private memory alone.

Rollback triggers:
- Claude can mutate a hookable persistent surface while readiness is BLOCKED.
- Claude can bypass protected-path ownership through Bash or another configured tool surface.
- Adapter work proceeds without Taskmaster/session/plan/work-tracking alignment.

### Other agent/profile canary

- Stage ID: other-agents
- Minimum observation: 72 hours
- Scope: Additional agents, profiles, or project adapters consuming the portable foundation

Entry criteria:
- Codex and Claude canary promotion criteria are satisfied.
- The target agent/profile has an explicit entrypoint contract.
- Repo-local adapter configuration is reviewed before rollout.
- Policy-only surfaces and unhookable mutations are documented.

Health checks:
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task sync plan --target-dir <target-repo>`

Promotion criteria:
- The agent/profile follows the same session/plan/work-tracking lifecycle.
- All hookable mutation surfaces are gated or explicitly deferred.
- Adoption evidence is recorded in repo-local work tracking.

Rollback triggers:
- The target agent/profile bypasses session, plan, or work-tracking gates.
- Repo-local adapter config breaks core guard or bootstrap behavior.
- Required evidence cannot be reproduced from tracked files.

## Recommended Verification Commands

- `python3 scripts/codex-task rollout canary-plan --report-file <plan.json> --runbook-file <runbook.md>`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`
- `git diff --check`

## Non-Goals

- No deployment is executed.
- No traffic is split.
- No automatic promotion is performed.
- No rollback command is executed.
- No dashboard is generated.
- No notification is sent.
- No external feature flag service is configured.

No deployment, promotion, rollback, traffic split, dashboard update, or notification was executed by this plan.
