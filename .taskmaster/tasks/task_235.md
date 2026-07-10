# Task ID: 235

**Title:** Prevent semantic regression in managed Aegis updates

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Restore completed-archive tracker parity in the canonical Codex guard and make Aegis update detect locally diverged managed governance assets before overwrite.

**Details:**

Promote the HP-Blog Task 56 completed-archive fallback into scripts/codex-guard. Add regression coverage for active tracker preference, completed current-work fallback with absent or empty active root, archive containment and -COMPLETED suffix, and rejection of non-completed state. Extend foundation manifest managed-file records with content checksums. During update planning, compare installed bytes with the recorded checksum; for legacy manifests without checksums, recover the previous expected same-path asset from runtime.source_root/runtime.source_commit when available. Classify a locally diverged managed governance asset as manual-review instead of safe modify. Preserve safe upgrades for pristine stale assets. Add an end-to-end fixture reproducing the blog update from 43e9a66 to current, require a second preview with zero managed changes, and document retry evidence.

**Test Strategy:**

No test strategy provided.
