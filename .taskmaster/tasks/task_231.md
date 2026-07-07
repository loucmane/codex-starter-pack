# Task ID: 231

**Title:** Unified Aegis project update command

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Add a first-slice 'aegis update --target-dir . [--apply]' command for installed target repositories so operators can refresh runtime pointers, managed assets, verification, and computed capsule state through one safe workflow.

**Details:**

Scope: implement single-repo update only, not fleet registry, update PR mode, PR-4 retirement, product cleanup, or broad MCP rewrite. Dry-run must report runtime pointer status, managed asset install-plan changes, verify status, capsule freshness/compile result, enforcement mode, and product-file safety. Apply must preserve advisory/strict mode, refuse unsafe/manual-review install plan items, touch only installer-managed Aegis assets and installer-owned reports/state, then compile the capsule. Include focused temp-target tests reproducing the HP-Fetcher stale installed brief_lib asset case after upstream #252: runtime source current but installed managed asset stale.

**Test Strategy:**

No test strategy provided.
