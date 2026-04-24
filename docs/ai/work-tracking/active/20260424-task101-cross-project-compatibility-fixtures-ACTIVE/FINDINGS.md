# Findings

- 2026-04-24 — Task 100 proved the portable foundation can bootstrap another repo, but it did not yet validate multiple repo shapes; Task 101 needs explicit fixture coverage to close that gap.
- 2026-04-24 — The most relevant repo-shape differences for this foundation are path layout, template scope, and workflow-root placement rather than the product code inside those repos.
- 2026-04-24 — A small reusable fixture layer is enough to exercise the portability contract; we do not need full sample repositories to validate repo-structure overrides and helper behavior.
- 2026-04-24 — The highest-value cross-project checks are bootstrap starter-asset generation, template-metadata drift under alternate template roots, and metrics/session/work-tracking resolution under alternate workflow roots.
