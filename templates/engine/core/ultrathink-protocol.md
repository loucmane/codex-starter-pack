---
id: ultrathink-protocol
title: Ultrathink Protocol
type: engine-component
status: stable
priority: critical
dependencies:
  - templates/engine/core/enforcement-check.md
  - templates/engine/core/pre-ultrathink.md
  - templates/patterns/#execute-ultrathink
exports:
  - ultrathink-format
  - handler-search-protocol
  - evidence-requirements
---

# 🧠 ULTRATHINK (CODEX EDITION)

Codex uses ULTRATHINK as the default reasoning mode for any deep-work request. Follow this end-to-end sequence every time.

## Handshake Format
```
Let me ultrathink about this with Codex... [S:YYYY-MM-DD|W:<workspace>|H:<state>|E:<evidence>]
```
- **S** – Today’s date (ISO-8601). Use `2025-09-20` for the current day.
- **W** – Active workspace focus (`~/codex`, a subfolder, or named initiative).
- **H** – `searching` until a handler is confirmed; afterwards use the relative registry path (no `.md`).
- **E** – `pending` while searching; after comprehension include key steps or success criteria in quotes.

## Required Order
1. Emit the handshake with `H:searching|E:pending` **after** running the Codex Readiness check.
2. Execute the **Pre-ULTRATHINK Protocol** (real search command + comprehension summary).
3. Emit the second handshake populated with the selected handler and evidence.
4. Transition into planning (`update_plan`) and execution using the handler’s process.

## Handler Validation
- Never claim a handler without demonstrating the search output.
- If no handler is found, document the fallback path (ask the user, create new handler) before proceeding.

## Evidence Expectations
- Quote concrete steps (“Review backlog”, “Run tests”) rather than generic verbs.
- Reference command output, file paths, and line numbers when gathering proof during execution.

## Completion Check
At task end, report status referencing the chosen handler:
- `✓ Completed: handlers/refactor-feature (3/3 steps)`
- `⚠️ Interrupted: handlers/refactor-feature (2/3 steps – waiting on review)`
- `❌ Failed: handlers/refactor-feature (error at step 2 – test suite failing)`

ULTRATHINK is executable protocol, not ceremony. Treat each field as verifiable state.

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/ultrathink-protocol.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
