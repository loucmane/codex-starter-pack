---
id: request-to-handler-matrix
title: Request to Handler Matrix
type: decision-matrix
category: routing
status: stable
usage: Maps user request patterns to appropriate handlers
version: 1.0.0
---

# Request Type → Handler Matrix

Maps common request patterns to their corresponding handlers for quick routing decisions.

## Input
User request pattern or keywords

## Output
Handler name, location, and example usage

## Matrix

| Request Pattern | Handler | Location | Example |
|-----------------|---------|----------|---------|
| "implement X" | standard-dev-workflow | templates/workflows/ | "implement user auth" |
| "fix X" | fix-bug | templates/workflows/ | "fix login bug" |
| "test X" | create-test-checkpoint | templates/workflows/ | "test the auth flow" |
| "find X" | search-code | TOOLS.md | "find user model" |
| "search for X" | search-code | TOOLS.md | "search for login" |
| "debug X" | debug-issue | templates/workflows/ | "debug auth failure" |
| "commit X" | commit-changes | TOOLS.md | "commit my changes" |
| "start session" | session-start | templates/conventions/ | "start new session" |
| "create work folder" | start-new-work | templates/workflows/ | "create work tracking" |
| "analyze X" | evidence-check | templates/patterns/ | "analyze performance" |
| "how does X work" | explain-code | templates/patterns/ | "how does auth work" |
| "refactor X" | refactor-code | templates/workflows/ | "refactor auth module" |
| "review X" | code-review | templates/workflows/ | "review my changes" |
| "document X" | create-docs | templates/conventions/ | "document the API" |
| "optimize X" | optimize-code | templates/workflows/ | "optimize queries" |
| "secure X" | security-check | TOOLS.md | "secure the endpoint" |
| "deploy X" | deployment | templates/workflows/ | "deploy to staging" |
| "rollback X" | rollback | templates/workflows/ | "rollback deployment" |
| "compare X and Y" | compare-code | templates/patterns/ | "compare v1 and v2" |
| "profile X" | performance-profile | TOOLS.md | "profile the API" |
| "monitor X" | monitoring-setup | templates/workflows/ | "monitor errors" |
| "backup X" | backup-data | TOOLS.md | "backup database" |
| "restore X" | restore-backup | TOOLS.md | "restore from backup" |
| "migrate X" | database-migration | templates/workflows/ | "migrate schema" |

## Usage Guidelines

1. **Pattern Matching**: Use the most specific pattern that matches
2. **Fallback**: If no exact match, try broader patterns
3. **Verification**: Always verify handler exists before executing
4. **Context**: Consider surrounding context for ambiguous requests

## Special Cases

- Multiple patterns may apply - choose most specific
- Unknown patterns → check templates/patterns/ for meta-routing
- Ambiguous requests → ask for clarification
- Missing handlers → document gap for future addition

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/routing/request-to-handler.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
