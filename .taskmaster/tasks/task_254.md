# Task ID: 254

**Title:** Complete strict Codex hook-trust portability contract

**Status:** done

**Dependencies:** 253 ✓

**Priority:** high

**Description:** Persist explicit schema-validated Codex hook-trust guidance so strict verification and closeout are reproducible in clean clones and Git worktrees without generated install reports.

**Details:**

Extend Task 253 by storing settings_path=.codex/hooks.json, review_command=/hooks, hash_scope=exact_hook_definition, and bypass_allowed=false in the tracked codex.hook_trust manifest gate; validate the exact contract in root and packaged schemas and strict verification; keep client trust external, session-local, and hash-bound; treat install-report evidence as supplemental only; fail closed for missing, malformed, bypass-permitting, wrong-path, wrong-command, or weak-hash guidance; add clean clone/worktree, report-present, stale-report, changed-hook-hash renewal, full strict verification, and closeout dry-run regressions; prove /tmp/blog-task42 passes without an install report while preserving all Task 42 product and evidence files.

**Test Strategy:**

No test strategy provided.
