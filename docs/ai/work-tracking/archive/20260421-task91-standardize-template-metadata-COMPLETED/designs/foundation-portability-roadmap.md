# Foundation Portability Roadmap

## Why This Exists
Task 91 is proving the metadata and enforcement pattern inside this repo, but the long-term goal is broader: make this system the reusable operational foundation for any future project, whether the repo is for a game, a website, or another product entirely.

## Current Proven Foundation
- Canonical metadata baseline: `title`, `type`, `status`
- Generic enforcement engine: `scripts/codex-guard`
- Repo-local policy layer: `templates/metadata/template-metadata-policy.json`
- Repo-local rollout sequencing through policy `enforce` flags

## What Still Needs To Become Portable

### 1. Repo Structure Configuration
Externalize hardcoded assumptions such as:
- template roots
- session roots
- plan roots
- work-tracking roots
- archive naming and folder rules

### 2. Foundation Specification
Write the reusable contract for:
- required metadata keys
- policy-file schema
- enforcement semantics
- session/work-tracking lifecycle expectations
- what belongs in core logic vs repo config

### 3. Bootstrap / Adoption Layer
Make it easy to apply this foundation in a new repo by providing:
- a starter policy file
- starter guard configuration
- setup instructions
- migration guidance for repos that already have content

### 4. Cross-Project Verification
Add tests or fixtures that simulate multiple repo shapes so the same engine works across:
- product-web repos
- game repos
- docs-heavy repos
- lighter utility repos

## Immediate Process Decision
- Finish enough of Task 91 to prove the policy-driven metadata rollout across multiple file families.
- After Task 91 is locally stable, convert the portability roadmap into explicit follow-on Taskmaster work.

## Candidate Follow-On Task Cluster
1. Externalize repo structure assumptions into config.
2. Write the portable foundation specification.
3. Add bootstrap/adoption support for new repos.
4. Add cross-project compatibility fixtures/tests.
5. Document migration/adoption paths.

## Progress Log
- **2026-04-21 17:55** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/foundation-portability-roadmap.md] Captured the post-Task-91 portability roadmap so future work is written down before new Taskmaster items are created
