# Task 24 Cost Tracking Scope Reconciliation

**Captured**: 2026-05-10 13:34 CEST  
**Task**: 24 - Implement Cost Tracking System

## Purpose

Task 24 predates the current portable foundation architecture. Its original wording assumes a live API and CI cost-control service with usage telemetry, billing integrations, rate limits, caching, projections, monthly reports, and automatic throttling.

The repository is now a portable workflow foundation with local scripts, static reports, GitHub Actions, Taskmaster state, session/work-tracking evidence, and no always-on application runtime. Task 24 should preserve the useful cost-governance intent without inventing live external telemetry or automatic mutation behavior.

## Evidence Reviewed

- Task 17 implemented static monitoring over local metrics artifacts, not Prometheus, Grafana, StatsD, Elasticsearch, or live alert routing.
- Task 20 implemented GitHub Actions Python CI, but explicitly deferred cost monitoring because GitHub billing/minutes data is external repository/account state.
- Task 16 implemented a static performance harness with repo-local policy and durable report artifacts.
- Task 35 implemented a non-destructive emergency response planner from repo-local policy, not PagerDuty/Slack/webhook automation.
- The current repository has no Anthropic API telemetry ledger, no GitHub billing API credential/configuration, no central runtime cache, and no deployable service where auto-throttling could be applied safely.
- Taskmaster and research-mode commands remain cost-bearing operational surfaces, but their usage is not currently measured inside this repo unless a user supplies a usage ledger.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 24 Decision |
| --- | --- | --- |
| Create `CostTracker` class for API usage monitoring | No live API client wrapper or telemetry source exists in this foundation repo. | Do not add a fake runtime class. Add a static cost policy/report generator instead. |
| Anthropic API usage tracking with rate limits | Taskmaster/AI calls can cost money, but provider billing data is external. | Represent AI usage as a cost category that accepts optional manual usage input; no provider API calls. |
| CI minutes monitoring | GitHub billing/minutes are external account data. Workflows are local repo files. | Report CI as a cost category and document manual/external telemetry status; do not query GitHub billing. |
| Budget alerts at 80% threshold | Useful as static policy classification. | Implement warning/critical thresholds in generated reports. |
| Caching strategy to reduce API calls | No central API call surface exists in this task. | Out of scope; capture guidance in policy notes rather than implementing unused caches. |
| Cost projection based on current usage | Useful only when usage input exists. | Support projection from optional usage JSON; otherwise report categories as not measured. |
| Monthly cost reports | Useful as file artifacts. | Generate Markdown and JSON reports suitable for monthly review. |
| Auto-throttling near limits | Automatic throttling would mutate behavior without a real runtime boundary. | Out of scope. Reports can recommend manual halt/review only. |

## Selected Implementation Scope

Implement Task 24 as a repo-native cost governance report:

```bash
python3 scripts/template-cost-report \
  --usage-file docs/ai/work-tracking/active/<folder>/reports/cost-tracking-system/sample-usage.json \
  --report-dir docs/ai/work-tracking/active/<folder>/reports/cost-tracking-system
```

The report should:

- load cost categories and thresholds from `templates/metadata/template-cost-policy.json`;
- accept optional usage data from a JSON file instead of querying external services;
- classify each category as `pass`, `warn`, `fail`, or `not-measured`;
- apply the policy's default warning threshold at 80% of budget;
- calculate current usage ratio and projected monthly cost when usage input exists;
- write deterministic JSON and Markdown artifacts;
- state explicitly that no provider API call, GitHub billing query, alert delivery, cache mutation, rate-limit change, or throttling action was executed;
- expose report generation through `python3 scripts/codex-task report generate --kind cost|all`;
- keep paths portable through `_repo_structure.load_repo_structure()`;
- bootstrap the policy/report directory into new repositories through `python3 scripts/codex-task bootstrap init`;
- include focused tests for policy loading, usage classification, projection, report writing, codex-task report wiring, repo-structure paths, bootstrap copying, and sync assets.

## Non-Goals

- No Anthropic, OpenAI, GitHub billing, GitHub Actions usage, Stripe, cloud, or other external API calls.
- No secrets, tokens, credentials, or account-level billing configuration.
- No automatic alert delivery to Slack, email, PagerDuty, or GitHub issues.
- No automatic throttling, rate-limit edits, branch blocking, task pausing, or command refusal based on cost report output.
- No runtime API client wrapper that is not used by the current repository.
- No replacement for Task 17 monitoring, Task 16 performance reports, Task 20 CI, Task 35 emergency planning, or future governance/dashboard tasks.

## Proven Gap

The repository can generate metrics, monitoring, Phase 0, performance, rollout, rollback, emergency, and sync reports, but it cannot yet answer:

- Which cost-bearing surfaces does the portable foundation expect every project to review?
- Are supplied AI/CI/runtime usage numbers within configured budgets?
- Which categories are unmeasured because the project has not supplied usage data?
- What manual review or evidence should be captured before claiming cost control?
- Can `report generate --kind all` include cost governance beside the other static foundation reports?

## Implementation Boundary For 24.2

Expected code/data/test surface:

- `templates/metadata/template-cost-policy.json`
- `scripts/template-cost-report`
- `scripts/_repo_structure.py`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_template_cost_report.py`
- targeted updates to `tests/meta_workflow_guard/test_codex_task.py` and `tests/meta_workflow_guard/test_repo_structure_config.py`

Expected behavior:

- policy loads from the configured templates root;
- missing usage data produces `not-measured` category findings without pretending telemetry exists;
- supplied usage data produces `pass`, `warn`, and `fail` classifications based on configured budgets;
- strict mode exits nonzero only when fail-level budget findings exist;
- generated reports include non-goals and recommended review commands;
- `codex-task report generate --kind all` runs cost after performance;
- bootstrap and sync include the cost policy and cost report directory.

## Verification Plan

- Run focused cost-report tests.
- Run focused codex-task and repo-structure tests touched by this task.
- Generate live Task 24 cost report artifacts under the active work-tracking reports folder.
- Capture plan sync, work-tracking audit, Taskmaster health, guard, diff-check, and full pytest evidence before closeout.

## S:W:H:E

- **2026-05-10 13:34 CEST** - [S:20260510|W:task24-cost-tracking-system|H:docs/scope|E:docs/ai/work-tracking/active/20260510-task24-cost-tracking-system-ACTIVE/designs/cost-tracking-scope-reconciliation.md] Reconciled Task 24 from live cost-control wording to a portable static cost governance report grounded in current foundation evidence.
