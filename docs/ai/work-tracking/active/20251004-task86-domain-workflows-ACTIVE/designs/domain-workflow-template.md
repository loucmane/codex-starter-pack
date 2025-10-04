# Domain Workflow Template (Draft)

## Purpose
Provide a reusable structure for domain-specific workflows. Each domain file will:
- Define prerequisites and artifacts.
- List step-by-step actions with guard references.
- Specify evidence requirements and guard integration.
- Link to helper prompts and regression coverage.

## Proposed File Location
`templates/workflows/domain/<domain>.md`

## Sections
1. **Frontmatter**
   ```yaml
   id: <domain>-workflow
   type: workflow-component
   category: domain
   title: <Domain> Workflow
   dependencies:
     - templates/behaviors/<domain>/guard.md (optional)
     - scripts/codex-guard
   related:
     - templates/handlers/orchestrators/<domain>/
   version: 1.0.0
   status: draft
   ```

2. **Purpose & Scope**
   - Describe when to use this workflow.
   - Reference relevant backlog tasks or migrations.

3. **Preconditions**
   - Active plan requirements.
   - Domain-specific artifacts (e.g., test plans, deployment configs).

4. **Steps**
   - Step-by-step actions with guard hooks: `codex-task`, `codex-guard`, domain tools.

5. **Evidence Requirements**
   - Guard logs stored under `reports/domain-workflows/`.
   - Domain-specific regression tests.
   - Session/tracker entries with S:W:H:E.

6. **Failure Modes & Recovery**
   - Common pitfalls for the domain.
   - Links to helper prompts.

7. **Completion Criteria**
   - Guard/tests passing.
   - Documentation updated.
   - Handoff recorded.

## Next Actions
- Instantiate template for each domain with specific steps.
- Create helper prompt files under `templates/helpers/domain/`.
- Update registry/metadata to point to each domain workflow.
