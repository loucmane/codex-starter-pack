# Task ID: 197

**Title:** Aegis observation report size budgets

**Status:** pending

**Dependencies:** 194 ✓

**Priority:** high

**Description:** Prevent observation/runtime reports from ballooning on generated local-runtime artifacts.

**Details:**

Add configurable ignore globs and summarization budgets for observation baselines, allowed_runtime_changes, and aegis next/status payloads. The HP-Coach run produced an ~8MB observation report and ~69MB next output dominated by worker/.wrangler KV blob paths. Replace raw path enumeration with capped samples, counts by path prefix/classification, truncation markers, and explicit artifact links when full detail is needed. Acceptance should prove large runtime directories produce <100KB guidance payloads while preserving enough evidence to audit what changed.

**Test Strategy:**

No test strategy provided.
