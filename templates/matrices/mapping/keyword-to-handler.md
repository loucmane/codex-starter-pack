---
id: keyword-to-handler-matrix
title: Keyword to Handler Matrix
type: decision-matrix
category: mapping
status: stable
usage: Maps keywords and phrases to specific handlers for quick lookup
version: 1.0.0
---

# Keyword → Handler Mapping

Quick reference for mapping user keywords to appropriate handlers.

## Input
Keywords or phrases from user request

## Output
Handler name and location

## Primary Keywords

### Development Keywords
| Keyword | Handler | Template |
|---------|---------|----------|
| implement | standard-dev-workflow | templates/workflows/ |
| build | standard-dev-workflow | templates/workflows/ |
| create | start-new-work | templates/workflows/ |
| feature | implement-feature | templates/workflows/ |
| component | create-component | templates/patterns/ |
| module | create-module | templates/patterns/ |
| function | implement-function | templates/workflows/ |
| class | implement-class | templates/workflows/ |
| interface | define-interface | templates/patterns/ |
| api | create-api-endpoint | templates/workflows/ |

### Debugging Keywords
| Keyword | Handler | Template |
|---------|---------|----------|
| fix | fix-bug | templates/workflows/ |
| debug | debug-issue | templates/workflows/ |
| error | investigate-error | templates/patterns/ |
| bug | fix-bug | templates/workflows/ |
| broken | debug-issue | templates/workflows/ |
| failing | test-failure | templates/workflows/ |
| issue | investigate-issue | templates/patterns/ |
| problem | fix-problem | templates/workflows/ |
| crash | debug-crash | templates/patterns/ |
| exception | handle-exception | templates/patterns/ |

### Search Keywords
| Keyword | Handler | Template |
|---------|---------|----------|
| find | search-code | TOOLS.md |
| search | search-code | TOOLS.md |
| locate | find-file | TOOLS.md |
| where | find-location | TOOLS.md |
| grep | grep-pattern | TOOLS.md |
| look | search-code | TOOLS.md |
| discover | find-references | TOOLS.md |
| identify | find-symbol | TOOLS.md |
| trace | trace-execution | templates/patterns/ |
| track | track-usage | templates/patterns/ |

### Git Keywords
| Keyword | Handler | Template |
|---------|---------|----------|
| commit | commit-changes | TOOLS.md |
| push | git-push | TOOLS.md |
| pull | git-pull | TOOLS.md |
| merge | merge-branch | templates/workflows/ |
| branch | create-branch | TOOLS.md |
| checkout | checkout-branch | TOOLS.md |
| rebase | git-rebase | templates/workflows/ |
| stash | git-stash | TOOLS.md |
| diff | show-diff | TOOLS.md |
| log | git-log | TOOLS.md |

### Testing Keywords
| Keyword | Handler | Template |
|---------|---------|----------|
| test | create-test-checkpoint | templates/workflows/ |
| check | validate-implementation | templates/workflows/ |
| verify | verify-behavior | templates/patterns/ |
| validate | validate-data | templates/patterns/ |
| assert | add-assertion | templates/patterns/ |
| mock | create-mock | templates/patterns/ |
| stub | create-stub | templates/patterns/ |
| spy | create-spy | templates/patterns/ |
| coverage | check-coverage | TOOLS.md |
| unit | unit-test | templates/workflows/ |

## Phrase Patterns

### Question Patterns
| Pattern | Handler | Template |
|---------|---------|----------|
| "how does X work" | explain-code | templates/patterns/ |
| "what is X" | explain-concept | templates/patterns/ |
| "why does X" | analyze-behavior | templates/patterns/ |
| "where is X" | find-location | TOOLS.md |
| "when does X" | trace-execution | templates/patterns/ |
| "who uses X" | find-references | TOOLS.md |
| "can you X" | evaluate-request | templates/patterns/ |
| "should I X" | provide-recommendation | templates/patterns/ |
| "what if X" | analyze-scenario | templates/patterns/ |

### Action Patterns
| Pattern | Handler | Template |
|---------|---------|----------|
| "add X to Y" | add-feature | templates/workflows/ |
| "remove X from Y" | remove-feature | templates/workflows/ |
| "update X in Y" | update-implementation | templates/workflows/ |
| "change X to Y" | refactor-code | templates/workflows/ |
| "move X to Y" | relocate-code | templates/workflows/ |
| "copy X to Y" | duplicate-code | templates/patterns/ |
| "rename X to Y" | rename-symbol | TOOLS.md |
| "replace X with Y" | replace-implementation | templates/workflows/ |
| "convert X to Y" | convert-format | templates/patterns/ |

## Composite Keywords

### Multi-word Triggers
- "start new work" → start-new-work
- "create work folder" → create-work-folder
- "save context" → save-context
- "run tests" → run-test-suite
- "code review" → code-review
- "pull request" → create-pr
- "hot fix" → create-hotfix
- "tech debt" → address-tech-debt
- "performance optimization" → optimize-performance
- "security audit" → security-check

## Context Modifiers

### Urgency Modifiers
- "urgent", "asap", "critical" → Prioritize and fast-track
- "when you can", "low priority" → Queue for later
- "blocker", "blocking" → Immediate attention

### Scope Modifiers
- "all", "every", "entire" → Comprehensive approach
- "just", "only", "specific" → Focused approach
- "related", "similar", "like" → Pattern matching

### Certainty Modifiers
- "maybe", "possibly", "might" → Exploratory approach
- "definitely", "must", "required" → Strict execution
- "should", "could", "would" → Recommended approach

## Fallback Strategies

1. **No keyword match**: Check phrase patterns
2. **No phrase match**: Extract verb and noun
3. **Still no match**: Check context modifiers
4. **Final fallback**: Ask for clarification

## Usage Tips

- Keywords are case-insensitive
- Partial matches considered
- Context overrides keywords
- Multiple keywords → most specific wins
- Unknown keywords → document for addition

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/mapping/keyword-to-handler.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
