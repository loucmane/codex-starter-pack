# Task ID: 181

**Title:** Allow generated dev runtime deltas during Aegis observation stop

**Status:** done

**Dependencies:** 180 ✓

**Priority:** high

**Description:** Observation stop with --collect-artifacts should close after allowed dev-server audits when only generated runtime state changed, such as Wrangler or miniflare caches, while still blocking source, Taskmaster, protected, or unknown persistent changes.

**Details:**

Extend Aegis observation stop classification with a narrow generated-runtime delta category. Runtime deltas should be reported separately from collected screenshot/browser artifacts and should not be moved or deleted. Permit only ignored or generated runtime paths under tightly scoped prefixes such as worker/.wrangler/ and worker/node_modules/.mf/ when produced by observation dev-server tooling. Keep all-or-nothing blocking for source deltas and preserve existing collect-artifacts behavior for screenshots and .playwright-mcp. Mirror packaged installer assets and MCP/CLI behavior if needed. Tests: collect-artifacts succeeds with cleanable screenshots plus allowed ignored runtime deltas, reports allowed runtime changes, leaves runtime caches in place, still blocks tracked/source deltas, and does not treat arbitrary ignored files as allowed runtime state.

**Test Strategy:**

No test strategy provided.
