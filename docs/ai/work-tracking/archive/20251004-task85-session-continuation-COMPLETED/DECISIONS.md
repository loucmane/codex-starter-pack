# Task 85 Session Continuation & State Workflows – Decisions

## Pending Decisions
- Define guard enforcement surface (plan/tracker/Serena) for continuation before implementation

## Decisions Made
- _None yet_

- 2025-10-02: Implementation will introduce continuation validation behavior with fallback when Serena memories are disabled; guard will treat Serena reference as optional but recommend logging when available.

- 2025-10-03: Guard must block continuation without plan sync + tracker entry + guard log (reports/session-continuation/*).
