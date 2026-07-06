# Task ID: 223

**Title:** [Codex-led] Sync codex-guard/codex-task assets mirrors

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Discovered during TM 219: aegis_foundation/assets/scripts/codex-guard and codex-task have drifted from the live scripts/codex-guard and scripts/codex-task. These are Codex-owned paths (scripts/codex-*), so Claude must not edit them or their packaged copies — re-syncing is Codex-led per CLAUDE.md. TM 219 added tests/meta_workflow_guard/test_assets_scripts_parity.py which guards the .py mirrors and tracks these two as KNOWN_CODEX_OWNED_DRIFT. When Codex re-syncs (cp scripts/codex-guard aegis_foundation/assets/scripts/codex-guard; same for codex-task), move them from KNOWN_CODEX_OWNED_DRIFT into MIRRORED_* coverage so they are byte-parity-enforced too.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
