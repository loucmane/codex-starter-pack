# Template Metrics Dashboard (Draft)

## Objective
Provide visibility into template usage/compliance, guiding future improvements.

## Metrics
- Template usage counts & compliance percentages.
- Most violated rules.
- Drift stats.
- Plan/guard status trends.

## Implementation Plan
- Collect data from guard logs, plan sync logs, wizard usage.
- Store in simple datastore (JSON/SQLite).
- Generate dashboard (static HTML/Markdown).
- Schedule periodic reports.

## Tasks
- Define data schema & collection points.
- Implement log parser/data aggregator.
- Build dashboard/report generator.
- Integrate with enforcement framework & optional alerts.

## Open Questions
- Hosting/visibility (CLI vs. web).
- Data retention policies.
- Performance / privacy considerations.
