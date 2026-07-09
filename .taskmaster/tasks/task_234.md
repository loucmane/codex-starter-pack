# Task ID: 234

**Title:** Project witness and delivery boundaries into legacy S:W:H:E surfaces

**Status:** done

**Dependencies:** 233 ✓

**Priority:** high

**Description:** Extend TM-233 coexistence so witness and GitHub delivery boundaries automatically update existing legacy session, plan, tracker, implementation, changelog, decisions, and handoff projections from machine-grounded ledger events.

**Details:**

Implement two explicit cross-agent boundaries. First, local aegis witness records a deduplicated witness event containing pass/fail, report path, branch, base, head commit, mode, and deterministic check summary, then projects existing active legacy surfaces; CI mode must not append to the persistent ledger or projection surfaces. Second, add aegis delivery sync with optional PR and branch selectors; derive actual PR state through existing gh-backed GitHub truth helpers, record canonical draft/open/ready/merged/closed state only when the fingerprint changes, and project the same existing surfaces. Delivery sync must refuse unverifiable self-reported state. Projection failures are warning metadata and never alter witness pass/fail. Preserve all human-authored content outside generated markers, keep repeated identical boundary calls byte-stable, redact raw commands, support completed archived surfaces through current-work paths, add focused CLI/ledger/projection/installer tests, dogfood witness plus open-PR delivery state in the blog PR, update the coexistence contract and PR-4 parity matrix, and keep TM-210 retirement blocked.

**Test Strategy:**

No test strategy provided.
