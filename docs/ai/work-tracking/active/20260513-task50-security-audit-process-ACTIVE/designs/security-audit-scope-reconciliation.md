# Task 50 Security Audit Process Scope Reconciliation

## Context

Task 50 was created from older security-program wording that asks for a comprehensive security audit process: audit checklist, SAST, dependency vulnerability checks, penetration-test scenarios, security metrics, compliance validation, report generation, and remediation tracking.

The current repository is a portable workflow foundation, not a deployed application with runtime endpoints, user data processing, hosted infrastructure, or an external vulnerability management service. Security work therefore needs to stay deterministic, repo-local, and evidence-backed unless a future runtime project proves a concrete integration surface.

## Existing Foundation Evidence

- Task 18 implemented `scripts/template-ssot-scanner/security_validator.py`, scanner config rules, allowlist support, scanner-suite integration, and focused tests.
- Task 20 added CI for Python matrix tests and Taskmaster health while keeping broader secret scanning and branch protection outside repo-file scope.
- Task 37 made the static telemetry/report chain explicit with `python3 scripts/codex-task report generate --kind telemetry`.
- Task 47 added `python3 scripts/codex-task recovery plan` for reviewed, non-destructive remediation planning.
- Task 68 final validation already maps `security-validation` to the scanner security validator and Phase 0 validation report.
- `scripts/template-phase0-validation` already evaluates security warning/error counts from `security_validation.json`.
- `scripts/template-ssot-scanner/migration_roadmap.py` already converts security findings into roadmap/remediation items when scanner data exists.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 50 Decision |
| --- | --- | --- |
| Security audit checklist | Work-tracking, final validation, guard, and scanner evidence exist, but there is no single security audit packet. | Add a non-destructive security audit packet/runbook that maps controls, evidence, commands, and remediation follow-up. |
| Automated SAST scanning | Task 18 deliberately implemented scoped template/config security validation instead of broad SAST. | Reuse `security_validator.py`; do not claim broad SAST. |
| Dependency vulnerability checking | No vulnerability database, lockfile scanner, or SBOM service exists in the foundation. | Inventory repo dependencies from `pyproject.toml` and mark CVE lookup as deferred external integration. |
| Penetration-test scenarios | No deployed service, endpoint, auth flow, or attack surface exists. | Provide static scenario prompts only when a future runtime project supplies endpoints; do not implement pentest automation now. |
| Security metrics collection | Static security counts already flow through Phase 0 validation and telemetry/final validation. | Summarize existing scanner/Phase 0 metrics in the audit packet. |
| Compliance validation (GDPR, etc.) | Task 37 rejected runtime GDPR machinery for this non-service repo. | Include compliance scope notes and evidence requirements; no legal/compliance certification claims. |
| Security report generation | Scanner and validation reports exist; no unified security audit report exists. | Implement JSON and Markdown audit outputs under task evidence. |
| Remediation tracking | Migration roadmap can emit security remediation items; Task 47 can create recovery plans. | Reference those helpers and include reviewed remediation commands in the audit packet. |

## Selected Implementation Scope

Implement a non-destructive Task 50 security audit helper:

```bash
python3 scripts/codex-task security audit \
  --summary "Task 50 foundation security audit" \
  --report-file docs/ai/work-tracking/active/<folder>/reports/security-audit-process/security-audit-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/security-audit-process/security-audit-YYYY-MM-DD.md
```

The helper should:

- classify existing security controls and whether evidence is present;
- read existing `security_validation.json` and Phase 0 validation data when available;
- inventory dependencies from `pyproject.toml` without performing CVE lookup;
- include compliance scope notes and explicit non-certification language;
- recommend existing commands for scanner, Phase 0, telemetry/final validation, recovery planning, guard, audit, and diff-check evidence;
- render JSON and Markdown artifacts suitable for work tracking;
- execute no external scanner, no network query, no pentest, no dependency update, no notification, and no remediation.

## Non-Goals

- No broad SAST integration.
- No external dependency vulnerability database lookup.
- No `pip-audit`, `detect-secrets`, Trivy, Semgrep, CodeQL, OWASP ZAP, or hosted scanner integration in this task.
- No penetration-test automation without a deployed application target.
- No GDPR, SOC2, ISO, or legal compliance certification claim.
- No dependency update, remediation mutation, dashboard update, ticket creation, or notification.

## Acceptance

- Parser exposes `python3 scripts/codex-task security audit`.
- JSON audit includes controls, existing evidence paths, dependency inventory, compliance notes, remediation guidance, verification commands, and non-goals.
- Markdown runbook renders the same audit contract in operator-readable form.
- Focused tests cover parser wiring, audit construction, dependency inventory, runbook rendering, and file output.
- Live JSON/Markdown evidence is stored under `reports/security-audit-process/`.
