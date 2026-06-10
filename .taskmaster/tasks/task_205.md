# Task ID: 205

**Title:** Capsule PR-1d: gate registry + verification classification

**Status:** done

**Dependencies:** 204 ✓

**Priority:** high

**Description:** Spec: AEGIS_CAPSULE_SPEC.md sections 2 and 2.1. New installed asset .aegis/brief.json holding {gates, thresholds, redact_extra, archive_keep}; gates map package-to-gate-to-command-patterns matched against normalized Bash commands — matching MUST handle cd-prefix, -C, and --dir invocation variants of the same logical command (pattern VALUES are per-repo config shipped via deployment docs, never hardcoded). Exit-class enum pass|fail|interrupted|unknown mapped exactly as specced (PostToolUse success = pass, PostToolUseFailure = fail, tool_response.interrupted = interrupted, else unknown; Bash tool_response has no documented exit-code field). Also implements section 2.1 scope records: inferred from branch name / in-progress task / PR body, recorded as a ledger event at first mutation on a new branch, with the single non-blocking aegis scope set confirmation nudge. Isolated on purpose: command normalization is the subtle, riskier part. Merge gate: fixture suite incl. cd-prefix/-C/--dir variants.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
