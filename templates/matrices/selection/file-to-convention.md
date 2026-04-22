---
id: file-to-convention-matrix
title: File to Convention Matrix
type: decision-matrix
category: selection
status: stable
usage: Maps file types to their required conventions and rules
version: 1.0.0
---

# File Type → Convention Matrix

Specifies conventions and rules that apply to different file types.

## Input
File type or path

## Output
Applicable conventions, handler, and special rules

## Matrix

| File Type | Key Conventions | Handler | Special Rules |
|-----------|----------------|---------|---------------|
| sessions/ | Current Focus required, reverse chronological | session-start | Never append at bottom |
| CLAUDE.md | Execution engine, not documentation | N/A | Do not edit casually |
| *.md in work tracking | 6-file structure, timestamps | work-tracking | Update in real-time |
| memory files | Markdown format, concise | memory-write | Meaningful names |
| test files | Follow existing patterns | test-conventions | Match naming scheme |
| config files | Validate before edit | config-edit | Check dependencies |
| package.json | Version bumps carefully | package-update | Run install after |
| .gitignore | Append only | gitignore-update | Never remove entries |
| TypeScript files | Strict mode, types | ts-conventions | No any types |
| React components | Functional preferred | react-conventions | Use hooks |
| API endpoints | RESTful conventions | api-conventions | Validate inputs |
| Database schemas | Migration required | db-conventions | Never modify directly |
| Environment files | Never commit secrets | env-conventions | Use .env.example |
| Docker files | Multi-stage builds | docker-conventions | Minimize layers |
| CI/CD configs | Test before merge | cicd-conventions | Validate syntax |
| Handler files | YAML frontmatter required | handler-conventions | Follow template |
| Agent files | Role definition clear | agent-conventions | Include constraints |
| Template files | Markdown with anchors | template-conventions | Searchable sections |
| Log files | Append only, timestamps | log-conventions | Rotate when large |
| JSON files | Valid syntax always | json-conventions | Pretty print |

## Special File Rules

### Work Tracking Files
1. **HANDOFF.md**: Current state summary
2. **TRACKER.md**: Progress tracking with timestamps
3. **IMPLEMENTATION.md**: Technical details
4. **MEMORY-REFS.md**: Reference links
5. **TESTS.md**: Test documentation
6. **NOTES.md**: Additional context

### System Files
- **Never modify**: .git/, node_modules/, dist/
- **Careful edit**: package-lock.json, yarn.lock
- **Always backup**: Database files, configs
- **Version control**: All source code

### Documentation Files
- **README.md**: Project overview, setup
- **CHANGELOG.md**: Version history
- **CONTRIBUTING.md**: Contribution guidelines
- **API.md**: API documentation

## Convention Enforcement

### Before Edit
1. Check file type in matrix
2. Load applicable conventions
3. Verify rules compliance
4. Make changes following rules

### After Edit
1. Validate changes meet conventions
2. Check for side effects
3. Update related files if needed
4. Document changes appropriately

## File Categories

### Source Code
- Apply language-specific conventions
- Maintain consistent style
- Include appropriate comments
- Follow project patterns

### Configuration
- Validate syntax before save
- Check for breaking changes
- Document non-obvious settings
- Keep examples updated

### Documentation
- Use consistent formatting
- Include examples
- Keep up-to-date
- Cross-reference related docs

### Tests
- Follow naming conventions
- Include clear descriptions
- Cover edge cases
- Maintain alongside code

## Priority Rules

1. **Safety First**: Never break working code
2. **Consistency**: Match existing patterns
3. **Documentation**: Update docs with code
4. **Validation**: Test changes before commit
5. **Reversibility**: Keep backups when uncertain

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/selection/file-to-convention.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
