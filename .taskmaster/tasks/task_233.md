# Task ID: 233

**Title:** Legacy-shadow S:W:H:E projection from passive ledger

**Status:** done

**Dependencies:** 209 ✓, 229 ✓

**Priority:** medium

**Description:** Define and implement hybrid coexistence where legacy work-tracking, session, and plan surfaces continue receiving S:W:H:E-style updates as generated projections from the passive ledger, while capsule/Taskmaster/git remain current-state authority and legacy checks run as shadow hardening signals.

**Details:**

Implement as a prerequisite to PR-4 retirement, not as deletion. Scope: add a coexistence contract for legacy-shadow projection; define generated-section markers and idempotency rules; preserve human-authored tracker/session/plan content; project selected ledger events into TRACKER.md, sessions, plans, IMPLEMENTATION.md, CHANGELOG.md, DECISIONS.md, and HANDOFF.md at boundaries rather than after every tool call; classify legacy checks as block/warn/record-only/disabled/replaced; treat advisory-era pending events as audit evidence, not strict debt; add HP-Fetcher 2026-07-09 dogfood as acceptance evidence; update the PR-4 parity matrix so old surfaces can become derived/shadow before any retirement. Acceptance: no manual aegis log required for projected entries; projection is deterministic and idempotent; generated sections never overwrite human-authored history; stale current-work/task80 residue becomes a shadow warning; witness remains responsible for stale/missing verification at delivery.

**Test Strategy:**

No test strategy provided.
