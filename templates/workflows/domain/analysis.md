---
id: domain-analysis-workflow
type: workflow-component
category: domain
title: Analysis & Evidence Workflow
dependencies:
  - scripts/codex-guard
  - templates/handlers/orchestrators/evidence-check.md
related:
  - templates/handlers/operators/analysis/verify-claim.md
version: 1.0.0
status: draft
---

# Analysis Domain Workflow

## Purpose
Guide analytical tasks (research, evidence gathering, risk analysis) with enforced guard evidence and documentation.

## Preconditions
- Analysis objectives defined in plan/tracker
- Access to required datasets or references

## Steps
1. **Define Claims / Questions**
   - List hypotheses or claims in findings doc
   - Plan evidence sources
2. **Gather Evidence**
   - Use analysis operators (`gather-evidence`, `verify-claim`)
   - Store outputs under `reports/analysis/`
3. **Synthesize Results**
   - Update decisions/findings with results
   - Attach supporting files
4. **Guard Enforcement**
   - Run `python3 scripts/codex-guard validate --include-untracked`
   - Ensure guard hints satisfied (evidence, logging)
5. **Handoff**
   - Summarize conclusions and next steps
   - Provide references in session/tracker

## Evidence Requirements
- Evidence files under `reports/analysis/`
- Guard log referencing analysis activities
- Tracker/session entries describing outcomes

## Failure Modes & Recovery
- **Insufficient evidence** → gather more data, update findings
- **Guard hints** → ensure evidence logged, rerun guard

## Completion Criteria
- Guard passes with evidence attached
- Findings/decisions capture conclusions
