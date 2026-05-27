# Task 126 Acceptance Fixture Policy

## Decision
Aegis acceptance fixtures must distinguish protocol literals from application behavior evidence.

Protocol literals are intentional when they describe Aegis-owned public contracts:

- S:W:H:E token syntax and parsed fields
- managed runtime blocks and hook/script names
- public command names such as `aegis init`, `aegis start`, `aegis verify`, and `aegis closeout`
- required report paths and schema-backed payload keys

Application behavior should be asserted semantically where practical:

- parsed workflow records instead of whole-line S:W:H:E substring matches
- AST/import/runtime checks for Python and backend fixtures
- DOM/source-intent checks for web fixtures
- negative examples where comments, dead strings, or unattached elements fail

## Current Task Cut
Task 126 hardens the web acceptance slice first because the Task 125 live run exposed the risk there. The helper accepts multiple idiomatic cart-button implementations and rejects comment-only, dead-string, and unattached-button variants. The end-to-end web target now logs `semantic:web-cart-button:src/main.ts` as verification evidence instead of relying on `rg "Add to cart" src/main.ts`.

## Non-Goals
- Redesign Aegis commands, hooks, closeout, or MCP semantics.
- Replace all existing literal checks. Literal checks stay where the public Aegis contract itself is literal.
- Add broad TypeScript parser dependencies before the fixture needs them. The current helper is a deliberately small test-only parser with positive and negative regressions.
