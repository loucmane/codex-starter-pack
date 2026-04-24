# Task 101 Cross-Project Fixture Matrix

## Objective

Verify that the portable foundation behaves correctly across multiple repository shapes instead of only the default layout used by this repository.

## Fixture Families

### 1. Product-web repo

Representative traits:
- `apps/web/` or similar product-facing app layout
- templates and docs may live outside the repo root defaults
- work-tracking and reports may remain under an ops-style directory

Validation focus:
- repo-structure overrides resolve correctly
- bootstrap can seed starter assets into a repo with app-centric top-level directories
- guard and metrics tooling honor non-default roots

### 2. Game/tool repo

Representative traits:
- source/assets split
- minimal template surface
- custom docs or workflow directory names

Validation focus:
- bootstrap does not assume a web/docs-heavy layout
- metadata policy and report roots can move without breaking helper logic
- guard behavior still respects configured paths

### 3. Docs-heavy repo

Representative traits:
- docs content is the dominant artifact
- template families may be broader than code-heavy repos
- reports and workflow assets may live under docs-oriented roots

Validation focus:
- portable policy still applies when template scope is docs-heavy
- lifecycle tooling remains path-driven, not codebase-shape-driven
- session/work-tracking roots can coexist with a documentation-first structure

### 4. Utility/library repo

Representative traits:
- very small source tree
- limited template and docs footprint
- lightweight workflow surface

Validation focus:
- bootstrap can seed a minimal repo without requiring unnecessary directories beyond the portable foundation contract
- tests catch accidental assumptions that larger repos always have multiple app/docs roots

## Test Boundary

Task 101 should add fixtures or tests that simulate these repo shapes without creating full product implementations. The tests should validate:

1. repo-structure overrides
2. bootstrap starter-asset generation
3. guard path resolution
4. metrics/drift path resolution where relevant

## Non-Goals

- building real sample applications
- writing migration/adoption guides for humans
- expanding UI or dashboard behavior

Those remain outside Task 101.
