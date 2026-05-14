# Stakeholder Reporting

Generate a static stakeholder-facing reporting packet with:

```bash
python3 scripts/codex-task stakeholder report \
  --report-file reports/stakeholder-reporting/latest.json \
  --runbook-file reports/stakeholder-reporting/latest.md
```

The packet composes existing Taskmaster, workflow, success metrics, knowledge transfer, deprecation governance, risk/compliance, and communication-template evidence. It is intentionally file-backed and non-destructive.

Non-goals:

- no hosted executive dashboard or BI workspace
- no report scheduler, daemon, cron job, or background worker
- no email, Slack, webhook, ticket, or notification delivery
- no database, warehouse, analytics backend, ROI engine, or external integration
- no mutation outside the requested JSON/Markdown report artifacts
