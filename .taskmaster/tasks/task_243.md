# Task ID: 243

**Title:** Refresh The PR-4 Replacement Parity Evidence

**Status:** done

**Dependencies:** 237 ✓, 238 ✓, 239 ✓, 240 ✓, 241 ✓, 242 ✓, 244 ✓, 252 ✓

**Priority:** high

**Description:** Re-evaluate every legacy workflow surface after convergence dogfood and issue explicit keep, shadow, demote, or retire decisions without changing runtime retirement behavior.

**Details:**

Implement roadmap workstream C7 after Tasks 237-242. Refresh the parity matrix with HP-Fetcher post-update capsule, ledger, bounded-status, and residue evidence; Blog merged-state, denial, recovery, dependency, controlled-auto-merge, and semantic-manifest evidence; an ordinary autonomous-delivery canary; worktree capture and attribution results; unique-content comparisons; interrupted-session and teardown recovery; positive and negative witness cases; and an explicit advisory-pending lifecycle. Every row must name current job, replacement owner, proof, dogfood, remaining unique legacy content, rollback, final state, and Task 210 go/no-go. Add guards for missing proof, placeholder dogfood, missing rollback, and unsupported coverage. No runtime surface may be retired in this task.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 243.1. Implement read-only derived Obsidian vault projection

**Status:** done
**Dependencies:** None

Build a deterministic, disposable Obsidian-compatible knowledge view from authoritative Aegis ledger/capsule/task truth and preserved legacy workflow evidence without writeback.

**Details:**

Add a stdlib-only projection module and CLI surface for path, build, and check. Generate YAML-frontmatter Markdown notes, path-qualified wikilinks, Obsidian Bases, and an ownership manifest into an out-of-repo destination. Aggregate low-level traffic, redact sensitive values, preserve source files, reject non-owned/manual output, use atomic replacement, and prove byte-stable rebuilds and bounded output.

### 243.2. Refresh PR-4 coexistence and unique-content parity evidence

**Status:** done
**Dependencies:** 243.1

Audit every legacy S:W:H:E surface against the capsule, ledger, witness, and derived vault using current Blog and HP-Fetcher dogfood.

**Details:**

Add deterministic unique-content inventory and matrix validation. Preserve legacy human narrative. Update each row with replacement owner, proof, dogfood evidence, remaining unique content, rollback, keep/shadow/demote/retire state, and Task 210 go/no-go. No runtime retirement in this task.

### 243.3. Complete read-only cross-repository audit and stopping checkpoint

**Status:** done
**Dependencies:** 243.2

Reconcile source, Blog, and HP-Fetcher evidence into a final hardening checkpoint without mutating downstream repositories.

**Details:**

Verify merged source state, derived-vault behavior, advisory-mode evidence lifecycle, worktree attribution, and coexistence conclusions. Produce explicit remaining risks and a reviewed stopping point before any Taskmaster-to-Gas-Town migration; do not begin that migration.
