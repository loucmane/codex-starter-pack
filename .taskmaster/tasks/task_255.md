# Task ID: 255

**Title:** Implement Host-Scoped Codex Remote Control Trust Management

**Status:** done

**Dependencies:** 254 ✓

**Priority:** high

**Description:** Add an upstream Aegis subsystem that explicitly manages project trust for the separate autonomous Codex Remote Control home without collapsing security contexts or copying hook approvals.

**Details:**

Audit the existing host bridge and wrapper behavior. Add a durable explicit Remote Control project allowlist, canonical path handling, safe trust add/status/remove and bridge status/plan/apply commands, structural TOML generation, atomic replacement, file locking, last-known-good rollback, unrelated-setting preservation, and effective CODEX_HOME diagnostics. Keep normal Codex trust, Remote Control project trust, tracked hook-review guidance, and actual client-local exact-hash hook approval distinct. Never auto-trust repositories, blindly inherit global trust, copy hook hashes, symlink the full config or CODEX_HOME, or claim hooks are trusted. Add comprehensive unit and integration coverage for idempotence, malformed input, duplicates, path aliases, symlinks, concurrency, rollback, separate contexts, changed hook hashes, and generated-config preservation. Deliver through Aegis verification and evidence-governed Git workflow; leave Blog untouched and prepare only the attended post-merge rollout procedure.

**Test Strategy:**

No test strategy provided.
