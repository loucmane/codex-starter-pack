# Task ID: 180

**Title:** Add safe observation artifact collection to Aegis observe stop

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Implement a sanctioned observation cleanup path so Aegis observe stop can collect known read-only audit artifacts such as screenshots and Playwright MCP output without allowing arbitrary rm during observation. The stop path must remain fail-closed for source, Taskmaster, protected, pre-existing, symlink-escaping, or unknown changes.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
