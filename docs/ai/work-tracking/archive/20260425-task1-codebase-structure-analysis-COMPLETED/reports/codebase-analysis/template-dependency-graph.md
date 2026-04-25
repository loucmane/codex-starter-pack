# Template Dependency Graph Summary

**Generated**: 2026-04-25 13:52 CEST
**Source**: `template-path-refs-live.txt` plus scanner-suite findings

## Graph Shape
- Source files with live template/scanner references: 211
- Distinct referenced template targets: 300
- Dominant dependency pattern: direct markdown/config/script path references.

## Top Reference Sources
| References | Source |
|------------|--------|
| 253 | `templates/metadata/template-overview.md` |
| 104 | `templates/metadata/workflow-guards.json` |
| 99 | `templates/registry/index.json` |
| 52 | `.taskmaster/tasks/tasks.json` |
| 49 | `templates/matrices/mapping/keyword-to-handler.md` |
| 33 | `templates/REGISTRY.md` |
| 30 | `tests/meta_workflow_guard/test_guard_rules.py` |
| 30 | `templates/BEHAVIORS.md` |
| 24 | `CODEX.md` |
| 22 | `templates/metadata/template-metadata-policy.json` |

## Top Reference Targets
| References | Target |
|------------|--------|
| 15 | `templates/TOOLS.md` |
| 15 | `templates/REGISTRY.md` |
| 12 | `templates/workflows/examples/common-workflows.md` |
| 11 | `templates/workflows/domain/README.md` |
| 11 | `templates/shared/patterns/ultrathink-format.md` |
| 11 | `templates/handlers/orchestrators/system-improvement.md` |
| 10 | `templates/handlers/triggers/development/start-new-work.md` |
| 10 | `templates/engine/core/enforcement-check.md` |
| 9 | `templates/engine/execution/swhe-format.md` |
| 9 | `templates/engine/enforcement/meta-workflow-guard-remediation.md` |

## Known Cycles From Scanner Run
- `templates/patterns/selection/handler-selection.md` -> `templates/patterns/routing/intent-detection.md` -> `templates/patterns/selection/handler-selection.md`
- `templates/REGISTRY.md` -> `templates/USER-GUIDE.md` -> `templates/REGISTRY.md`
- `templates/integration/guides/creating-handlers.md` -> `templates/integration/best-practices/handler-design.md` -> `templates/integration/guides/creating-handlers.md`

## Evidence Files
- `template-reference-source-counts.txt`
- `template-reference-target-counts.txt`
- `dependency-risk-notes.txt`
- `reference-patterns.md`
- `scanner-suite-capabilities.md`

## Interpretation
The foundation is reference-dense but has clear hubs. Registry, metadata, and matrix files are the primary source hubs; `templates/TOOLS.md` and `templates/REGISTRY.md` are the most referenced targets. Downstream cleanup should prioritize circular dependencies and noisy runtime/cache references before applying bulk automated fixes.
