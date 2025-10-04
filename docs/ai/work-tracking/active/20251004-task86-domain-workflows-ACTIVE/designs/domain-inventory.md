# Domain Inventory – Task 86

## Date / Time
- Captured: 2025-10-04 12:59–13:01 CEST (`date "%Y-%m-%d %H:%M %Z"`)

## Existing Domain Assets

| Domain | Existing Assets | Gaps |
|---|---|---|
| analysis | handlers/operators, handlers/triggers | No dedicated domain workflow modules; guards only partially mapped |
| debug | handlers/operators, handlers/triggers | No dedicated domain workflow modules; guards only partially mapped |
| development | handlers/operators, handlers/triggers | No dedicated domain workflow modules; guards only partially mapped |
| docs | handlers/operators, handlers/triggers | No dedicated domain workflow modules; guards only partially mapped |
| external | handlers/operators, tools | No dedicated domain workflow modules; guards only partially mapped |
| file | handlers/operators | No dedicated domain workflow modules; guards only partially mapped |
| git | handlers/operators | No dedicated domain workflow modules; guards only partially mapped |
| search | handlers/operators | No dedicated domain workflow modules; guards only partially mapped |
| session | handlers/operators, handlers/triggers, workflows/session/* | No dedicated domain workflow modules; guards only partially mapped |
| test | handlers/operators, handlers/triggers, workflows/testing/* | No dedicated domain workflow modules; guards only partially mapped |
| workflow | handlers/operators, handlers/triggers, workflows/processes/* | No dedicated domain workflow modules; guards only partially mapped |

## Notes
- Current handlers cover many domains, but workflows live mostly under generic directories (session/, testing/, processes/).
- Need dedicated domain workflow templates (e.g., templates/workflows/domain/<domain>.md) with guard/evidence requirements.
- Map each domain to required helpers/prompts and guard rules.

## Next Steps
1. Draft domain workflow template structure (Subtask 86.2).
2. Map guard behaviors and conventions per domain (Subtask 86.3).
3. Identify helper prompts and registry entries for each domain (Subtask 86.5).

## Legacy Sections
- BUILDING-BETTER.md:1 — Building Better: System Extension Guide
- WORKFLOWS.md:3 — Universal Development Workflows
- PATTERNS.md:1 — System Patterns Library

## Legacy vs. Modular Mapping
| Legacy Section | Planned Modular Location | Status |
|---|---|---|
| WORKFLOWS.md:1 Continuation Workflow | templates/workflows/domain/session.md | to-create |
| WORKFLOWS.md:120 Testing Workflow | templates/workflows/domain/test.md | missing |
| PATTERNS.md:200 Docs Workflow Patterns | templates/workflows/domain/docs.md | missing |
| BUILDING-BETTER.md:620 Domain Expert Deployment | templates/workflows/domain/analysis.md | missing |
