---
id: enforcement-check
title: Codex Enforcement Gate
type: critical-enforcement
status: stable
critical: true
priority: highest
enforcement-level: mandatory
dependencies:
  - templates/engine/core/codex-readiness.md
  - templates/engine/core/pre-ultrathink.md
exports:
  - codex-enforcement-gate
  - ultrathink-handshake
---

# 🚨 CODEX ENFORCEMENT GATE 🚨

This is the primary interrupt handler for development work in Codex. Run it before thinking through any solution.

## 1. Confirm Readiness
- Execute the **Codex Readiness Checklist** (`templates/engine/core/codex-readiness.md`).
- If sandbox, approvals, or tools are misaligned, pause and surface the blocker.

## 2. Declare Intent
- If the user’s request is development or workflow related, state the intent explicitly:
  ```
  Acknowledged. Initiating Codex protocol for <request summary>.
  ```
- For casual chat, respond naturally and note that the enforcement sequence is skipped.

## 3. Mandatory ULTRATHINK Handshake
Your first structured output for deep-work tasks must be the Codex ULTRATHINK line:
```
Let me ultrathink about this with Codex... [S:2025-09-20|W:~/codex|H:searching|E:pending]
```
- **S** – Absolute session date in `YYYY-MM-DD` (today).
- **W** – Current workspace root or active focus area.
- **H** – `searching` until a handler is confirmed.
- **E** – Always `pending` until comprehension is complete.

If you already emitted other content, delete/restate it and re-run this gate.

## 4. Enforce the Sequence
- Do **not** proceed to planning, searching, or tooling until the handshake is emitted.
- The handshake immediately hands off to the **Pre-ULTRATHINK Protocol** which verifies real handler discovery.

## 5. Violations
Skipping any step above invalidates the response. Restart from Step 1 and document the correction in your next message.

**This gate runs before every development task. Treat it as code, not documentation.**

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/enforcement-check.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
