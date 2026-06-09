# Task ID: 193

**Title:** Reduce CI feedback time without reducing coverage

**Status:** pending

**Dependencies:** 192 ⧖

**Priority:** high

**Description:** Improve GitHub Actions feedback time while preserving the full quality bar for Aegis, Taskmaster, and meta-workflow changes.

**Details:**

Create a tiered CI design: fast PR signal for routine iteration, full matrix coverage for merge confidence, duration measurement before optimization, dependency caching, slow-test sharding, path-aware test selection, duplicate guard cleanup, and documented quality policy. Full coverage must not be removed; any faster lane must either be a preliminary required signal or be backed by full CI before merge.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 193.1. Measure CI duration and slow-test profile

**Status:** pending
**Dependencies:** None

Establish a factual CI timing baseline before changing workflow behavior.

**Details:**

Add or use workflow timing data and pytest duration reporting to separate runner queue/setup time, dependency install/provisioning time, Taskmaster/Aegis proof-step time, pytest execution time, and artifact upload/post time. Capture the slowest pytest cases with duration reporting and use PR #195 or an equivalent run as the initial baseline.

### 193.2. Add fast required PR signal lane

**Status:** pending
**Dependencies:** 193.1

Create a short required CI path that gives useful PR feedback quickly without replacing full coverage.

**Details:**

Introduce a fast PR workflow or job set that runs guard validation, lint/static checks, Taskmaster health, and changed-path focused pytest on one Python version. Target roughly 2-5 minute feedback. Keep full matrix CI available and required before merge or ready-for-review, so this lane is an early signal rather than a coverage reduction.

### 193.3. Deduplicate guard workflow triggers

**Status:** pending
**Dependencies:** 193.1

Remove redundant guard check noise while preserving the meaningful guard coverage.

**Details:**

Audit GitHub Actions triggers and guard workflows to explain why a PR can show multiple guard checks. Collapse duplicate trigger paths or rename/report checks so a PR has one clear guard signal per intended surface. Preserve required protection for guard validation; only remove accidental duplication or confusing duplicate reporting.

### 193.4. Cache Python Node and Taskmaster setup

**Status:** pending
**Dependencies:** 193.1

Reduce CI setup time by caching dependency and provisioning work safely.

**Details:**

Add conservative GitHub Actions caches for Python dependency artifacts, Node package manager data, and pinned Taskmaster CLI provisioning where inputs are stable. Key caches from lock files and relevant config such as uv.lock, pyproject.toml, package manager lock files, and Taskmaster version pins. Do not cache generated workflow state in a way that can hide correctness failures.

### 193.5. Shard slow meta-workflow pytest domains

**Status:** pending
**Dependencies:** 193.1

Lower full-CI wall-clock time by splitting slow pytest domains across parallel jobs.

**Details:**

Use the timing baseline to group slow tests into stable shards, for example installer/assets, readiness/gate, closeout/handoff/repair, reconcile/shadow, and MCP/server. Keep every existing test covered; the change is parallelization and reporting, not deletion. Ensure artifacts remain attributable by shard and failures are easy to inspect.

### 193.6. Add path-aware test selection with full-coverage fallback

**Status:** pending
**Dependencies:** 193.2, 193.5

Run focused checks for low-risk changes while preserving full coverage for risky or merge-bound changes.

**Details:**

Implement changed-path rules that select focused test slices for docs-only, Taskmaster-only, Aegis installer/runtime, guard/readiness, closeout/handoff, reconcile/shadow, and MCP/server changes. Fail closed when a path is unknown or high risk. Full matrix coverage must still run before merge or on ready-for-review for changes that affect shared workflow behavior.

### 193.7. Document CI quality policy and required gates

**Status:** pending
**Dependencies:** 193.2, 193.6

Make the faster CI model explicit so agents and maintainers know which checks are required at each phase.

**Details:**

Document draft-PR, ready-for-review, merge, and release gates. Define which jobs are fast signal, which are full confidence, which are advisory, and which are required. Include rules for when full matrix cannot be skipped, especially Aegis runtime, installer, guard, closeout, reconcile, and MCP changes. Update contributor or workflow docs so natural-language requests like continue or ship do not cause an agent to skip required gates.
