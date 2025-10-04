---
id: domain-test-workflow
type: workflow-component
category: domain
title: Testing Domain Workflow
dependencies:
  - scripts/codex-guard
  - templates/handlers/triggers/test/validate-changes.md
related:
  - templates/workflows/testing/regression.md
version: 1.0.0
status: draft
---

# Testing Domain Workflow

## Purpose
Standardize testing activities (unit, integration, regression) and ensure guard evidence is captured before marking work complete.

## Preconditions
- Tests defined for the scoped change
- Plan/tracker synced
- Dependencies installed (pytest, automation tools)

## Steps
1. **Review Requirements**
   - Identify test coverage expectations from plan
   - Ensure fixtures and data are available
2. **Execute Tests**
   - Run domain-specific commands (e.g., `python3 -m pytest`, `npm test`)
   - Capture outputs under `reports/testing/`
3. **Analyze Results**
   - Investigate failures, create issues/findings as needed
   - Update tracker findings/decisions
4. **Update Documentation**
   - Record test commands/results in session log
   - Store guard log under `reports/testing/guard-<timestamp>.txt`
5. **Gate Enforcement**
   - Run `python3 scripts/codex-guard validate --include-untracked`
   - Ensure guard hints show no missing evidence

## Evidence Requirements
- Test output files (`reports/testing/tests-<timestamp>.txt`)
- Guard log referencing test commands
- Tracker entries showing test status

## Failure Modes & Recovery
- **Test failures** → capture issue in findings, resolve, re-run tests
- **Missing coverage** → update plan or add new tests
- **Guard failure** → store missing artifacts, re-run guard

## Completion Criteria
- All planned tests executed and passing
- Evidence stored under `reports/testing/`
- Guard validation passes
