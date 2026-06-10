# Task ID: 200

**Title:** Aegis MCP CLI version handshake

**Status:** in-progress

**Dependencies:** 194 ✓

**Priority:** high

**Description:** Prevent stale MCP server logic after source-root runtime updates or mid-session Aegis upgrades.

**Details:**

Add a version/capability handshake between the Aegis CLI shim, installed hooks, source-root runtime metadata, and the long-running Aegis MCP server. The MCP server should expose its source commit/capabilities, compare against .aegis/foundation-manifest.json and active source root, and return a clear reload_required/degraded state when stale. next_action/doctor should surface stale-MCP guidance instead of letting MCP preview disagree with CLI repair/apply behavior. Acceptance should reproduce the HP-Coach stale MCP case where MCP returned empty repair plans while the CLI had newer repair logic, and prove the mismatch is detected before action decisions.

**Test Strategy:**

No test strategy provided.
