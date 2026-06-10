# Task ID: 209

**Title:** Capsule PR-3.5: delivery witness v0

**Status:** done

**Dependencies:** 207 ✓

**Priority:** high

**Description:** Spec: AEGIS_CAPSULE_SPEC.md section 5.1. Deterministic, zero-LLM boundary check computed from ledger + git + section 2.1 scope records, exposed as aegis witness and wired as a REQUIRED GitHub check under branch protection (required-check status is the enforcement — this repo-class auto-merge labels would silently bypass a non-required check). Checks: (1) branch maps to scope record/task; (2) every diff file accounted for by scope path globs, test deletions/weakenings escalate to human review (the G5 diff-accounting gate pulled forward); (3) scope verification gates have pass runs on record at/after head commit; (4) any task flipped done has a containing commit on the branch; (5) CI green via native required checks. Output is the generated delivery report, replacing the old hand-fed closeout entirely — this absorbs Phase-0 task 196's deliver-report scope (durable push/PR/CI/approval/merge evidence). The teeth move here BEFORE anything is retired. Merge gate: runs as a required check on a real PR; zero LLM.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
