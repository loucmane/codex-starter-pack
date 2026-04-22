---
id: pre-ultrathink-protocol
title: Pre-Ultrathink Protocol
type: critical-enforcement
status: stable
critical: true
priority: highest
enforcement-level: mandatory
dependencies:
  - templates/registry/index.md
  - templates/engine/core/enforcement-check.md
exports:
  - pre-ultrathink-sequence
  - handler-comprehension-check
  - violation-detection
---

# 🚨 PRE-ULTRATHINK PROTOCOL (CODEX) 🚨

Guards against fake compliance. Run it immediately after the ULTRATHINK handshake.

## Absolute Rules
- **Never** jump directly from the handshake into implementation.
- **Always** show real evidence that a handler was searched, opened, and understood.

## Required Sequence

1. **Announce the search**
   ```
   Searching templates/registry for a handler that matches <request summary>...
   ```

2. **Run an actual search command**
   - Use `shell` with `rg`, `fd`, or `ls` under `templates/registry/`.
   - Paste the command and at least one real result line, e.g.:
     ```
     $ rg "refactor" templates/registry
     templates/registry/handlers/refactor-feature.md:## Process
     ```
   - If search fails, state that explicitly and branch to remediation (ask the user, expand search, etc.).

3. **Read and summarise the handler**
   - Show `Reading handler: <file>`.
   - Quote 2–3 concrete steps from the handler’s “Process” (or equivalent) section.
   - Generic bullets (“analyze”, “implement”) are violations—cite real language.

4. **Finalise ULTRATHINK context**
   - Emit the second ULTRATHINK line with the resolved handler and evidence:
     ```
     Let me ultrathink about this with Codex... [S:2025-09-20|W:~/codex|H:handlers/refactor-feature|E:steps/"Review plan → Implement changes → Validate"]
     ```
   - `H` should be the registry path (omit `.md`).
   - `E` must reference the key steps or success criteria you quoted.

5. **Only then plan/execute**
   - After the final ULTRATHINK line, you may outline the plan (`update_plan`) and begin the workflow defined by the handler.

## Automatic Failures
- Skipping the real command output (or fabricating results).
- Summaries that do not match the handler’s text.
- Forgetting to issue the second ULTRATHINK line with populated `H` and `E` fields.

## Notes
- If multiple handlers are possible, repeat the search/comprehension cycle until you select the best fit.
- For non-development tasks (documentation answers, greetings), state that the protocol is not applicable and explain why.

This protocol makes ULTRATHINK compliance verifiable. Do not bypass it.

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/pre-ultrathink.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
