# Task ID: 216

**Title:** Closeout convergence: kill the evidence/pending-tracking loop

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** From HP-Coach closeout report 2026-06-12: closeout.evidence.*/closeout.handoff.* gates demand verbatim mutation-evidence strings present in all five surfaces, but every edit that populates a surface enqueues a new pending-tracking event, which fails closeout.pending_tracking — fix-creates-failure loop; closeout effectively unreachable without edit/log ping-pong. Also: read-only Bash (git status, jq, ls, cat — recorded as bash:cd/bash:jq) wrongly spawns pending events. Fixes per report: (1) generate-dont-assert — aegis log / closeout --update-handoff populate implementation/changelog/handoff surfaces + HANDOFF semantic sections from logged events; (2) mutations whose sole targets are work-tracking surfaces (or performed by aegis log/closeout itself) must not re-arm pending tracking; (3) read-only Bash must not enqueue; (4) evidence matching on stable keys (commit SHA, path, event id) not verbatim multi-line command text; (5) idempotent one-shot aegis closeout --update-handoff --apply that populates then drains atomically. Acceptance: from a committed test-green task, one closeout invocation converges with empty queue; regression test for one-shot convergence.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
