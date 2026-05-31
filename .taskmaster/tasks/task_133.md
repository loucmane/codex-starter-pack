# Task ID: 133

**Title:** Run Codex Live Aegis Acceptance Test

**Status:** done

**Dependencies:** 132 ✓

**Priority:** high

**Description:** Prove and harden the Codex client path for Aegis in a safe isolated fixture, comparing behavior with the native repo and Claude MCP acceptance.

**Details:**

Create a /tmp Taskmaster-backed shop-webapp fixture with failing verification and no installed Aegis. Register or expose the local Aegis MCP/CLI path to Codex. Run a real Codex client session from normal language to observe whether it uses Aegis inspect/init/next, respects bootstrap/reload barriers where applicable, starts/kickoffs with the Taskmaster numeric task, logs scope before source edits, uses native source tools, runs project verification, strict Aegis verification, closeout, doctor, and only then marks Taskmaster done. Record exact transcript/evidence, identify parity gaps against Claude and this repo's native Codex workflow, and implement focused hardening if gaps are in Aegis guidance/runtime rather than client limitations. Keep all product testing in /tmp and do not touch real HPFetcher.

**Test Strategy:**

No test strategy provided.
