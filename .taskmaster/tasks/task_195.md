# Task ID: 195

**Title:** Aegis vNext Phase 0 replay harness

**Status:** pending

**Dependencies:** 194 ✓

**Priority:** high

**Description:** Build a replay harness for historical Aegis tool-call and gate-decision traces so policy changes are measured against real HP-Coach friction before rollout.

**Details:**

Implement an additive aegis replay path that can ingest recorded sessions, pending-tracking events, BLOCKED messages, and known outcomes from the HP-Coach 2026-06-08..10 deployment. Seed golden scenarios for the 13 false-positive workflow blocks, the fixture's must-fire set per its labels — one true positive (E01: observation dirty-artifact stop) plus one validated boundary mechanism (E29: trailing unlogged Stop-gate pending, classified ceremony_self_catch, not a second true positive) — and synthetic adversarial cases such as exfil curl, hook writes, test deletion, fabricated artifacts, wrong-branch delivery, and missing verification. Report false-positive and false-negative deltas for any gate/policy change. This is a measurement harness first: record/replay only, no behavior change.

**Test Strategy:**

No test strategy provided.
