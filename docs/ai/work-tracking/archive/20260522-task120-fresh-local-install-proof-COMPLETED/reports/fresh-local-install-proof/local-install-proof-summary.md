# Local Fresh-Project Install Proof Summary

Task 120 proves the local-first path before TestPyPI/PyPI.

## Artifacts

- Wheel: `reports/fresh-local-install-proof/dist/aegis_foundation-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `e0387cd9a26d7be735cee90a24c3d43f13a493ab668a4413118dd81a2f4bc400`
- Sdist SHA-256: `a74dd3a3095ea80b2bb254e66d32286f2dda73817d3532591ed38e67df065f94`
- Certification report: `reports/fresh-local-install-proof/certification-report.json`

## Native Claude MCP Registration

- Live target: `/tmp/aegis-task120-claude-live-shop-dry91w`
- Registration mode: `claude mcp add --scope project`
- Source mode: `wheel`
- Local wheel reference: expected in the live target `.mcp.json` until TestPyPI/PyPI exists
- Registration evidence:
  - `claude-live-target-registration-execute.json`
  - `claude-live-target-registration-verify.json`
- Source-reference scan:
  - `claude-live-target-source-reference-scan.txt`
- Verification status: passed.
- Live Claude test result:
  - `claude-live-test-result.md` -> passed.

The live target is intentionally not fully Aegis-installed by Codex. It contains the project `.mcp.json` registration and a tiny app so a fresh Claude session can prove install, kickoff, edit, logging, verification, and closeout from the local wheel.

## Codex-Side Fresh Target Proof

- Final proof target: `/tmp/aegis-task120-proof-shop-final-cNydTu`
- Install status: `proof-final-install.json` -> `applied`
- Local shim status: `proof-final-local-shim-status.json` -> command succeeded
- Readiness before kickoff: `BLOCKED | blocked=1 | first=branch 'main' does not contain a task ID`
- Kickoff status: `proof-final-kickoff.json` -> `started`
- Readiness after kickoff: `READY | task=1`
- Pending tracking after source edit: `proof-final-pending-after-source-edit.json`
- Second mutation while pending: blocked by pending S:W:H:E tracking
- Stop gate while pending: blocked
- Implementation log: `proof-final-implementation-log.json`
- Protected Aegis path Bash bypass: blocked for `.aegis/foundation-manifest.json`
- Protected Claude entrypoint write: blocked for `CLAUDE.md`
- Strict verify: `proof-final-strict-verify.json` -> `passed`, 27 checks, 0 required failures
- Closeout: `proof-final-closeout.json` -> `passed`, 22 checks, 0 required failures
- Hidden-file leakage scan: `proof-final-source-leakage-scan.txt`
  - No concrete `/home/loucmane/codex` path, PyPI, or TestPyPI reference is present in the installed proof target.
  - The project-local shim contains the literal `AEGIS_SOURCE_ROOT` fallback text by design, but it is inactive unless a user sets that environment variable.

## Findings

The local-first proof found and fixed two portability gaps before publishing:

1. The installed project-local shim used an asset-root fallback as `PYTHONPATH`, which cannot import `aegis_foundation.cli` from a wheel install. The shim now probes the asset root, its parent, and its grandparent so packaged `site-packages/aegis_foundation/assets` resolves to the package import root.
2. Hidden protected directories were not matched because path normalization used `lstrip("./")`, stripping the dot from `.aegis/` and `.claude/`. Normalization now removes only a literal leading `./`, and the protected set now includes `.aegis/**`, `.claude/**`, `CLAUDE.md`, and `AGENTS.md`.

## Publishing Gate

This proof supports continuing toward TestPyPI planning after a separate hardening task records the UX improvements found by the live Claude session. PyPI remains out of scope for Task 120.

## Final Verification

- Final verification evidence: `final-verification.md`
- Focused changed-surface tests: passed, 24 tests
- Broad Aegis slice: passed, 102 tests, 4 explicit opt-in smoke tests skipped
- Plan sync, work-tracking audit, guard validation, Taskmaster health, readiness, and `git diff --check`: passed
