# Aegis Cross-Project Smoke Matrix

## Purpose

Task 111 proves that Aegis works as a portable foundation in isolated target repositories before broader packaging or distribution work begins.

The test target is not this repository. The harness must create temporary target repositories, invoke the existing Aegis CLI and MCP surfaces, and verify that target state changes match the installer contract while the source repository remains untouched except for intentional Task 111 files and evidence.

## Source-of-Truth Boundary

- `scripts/_aegis_installer.py` remains the only implementation of installer semantics.
- `scripts/codex-task aegis ...` is the CLI wrapper over that core.
- `aegis_mcp/server.py` is the MCP control-plane wrapper over that same core.
- Tests may add harness helpers, but must not duplicate install/verify rules.
- MCP assertions must check wrapper equivalence: same classifications, safety gates, refusal shapes, report paths, manifest fields, and verification outcomes as the core installer.

## Inputs From Prior Tasks

| Prior task | Relevant outcome for Task 111 |
| --- | --- |
| Task 48 | Selected hybrid architecture: CLI/library core is primary, MCP/plugin wrappers are adapters over the core. |
| Task 101 | Added cross-project fixture thinking for product-web, game/tool, docs-heavy, and utility/library shapes. |
| Task 109 | Added Aegis schemas, installer core, CLI command group, fixture/idempotence tests, and MCP wrapper contract. |
| Task 110 | Added production `aegis.*` MCP tools, read-only `aegis://` resources, prompts, `.mcp.json`, and stdio smoke coverage. |

## Target Repository Matrix

| Shape | Fixture contents | Required flow |
| --- | --- | --- |
| Empty repo | Empty directory plus optional `.gitkeep`/README if needed for assertions. | CLI inspect, plan-install, install apply, verify. |
| Python/library repo | `pyproject.toml`, README, `src/<package>/__init__.py`, tests directory. | CLI happy path and source-preservation assertions. |
| Web/app repo | `package.json`, app/source directory, docs or public assets. | CLI happy path and no-clobber assertions for app files. |
| Docs-heavy repo | `docs/`, README, documentation config or placeholder structure. | CLI happy path and docs-preservation assertions. |
| Partial Aegis install | Existing `.aegis/` or adapter files in controlled variants. | Conflict/refusal and repair/verify negative cases. |

## Invocation Matrix

| Surface | Commands/tools | Required assertions |
| --- | --- | --- |
| CLI inspect | `python3 scripts/codex-task aegis inspect --target-dir <target>` | Parseable JSON, no mutation, detected agents/state is stable. |
| CLI plan | `python3 scripts/codex-task aegis plan-install --target-dir <target> ...` | Parseable JSON, no mutation, plan/report path intent is clear. |
| CLI install | `python3 scripts/codex-task aegis install --target-dir <target> --apply ...` | Manifest, contract, schemas, reports, managed-file records, adapter files, gates. |
| CLI verify | `python3 scripts/codex-task aegis verify --target-dir <target> --acknowledge-report-write` | Verification report written only with acknowledgement; failures are structured. |
| MCP tools | `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify` | Same core classifications and safety semantics as CLI/core. |
| MCP resources | `aegis://manifest/current`, `aegis://managed-files`, `aegis://install-plan/latest`, `aegis://verification/latest` | Read-only resource views after install/verify; no mutation. |

## Safety Matrix

Task 111 must prove these behaviors:

- Planning and inspect flows do not create `.aegis/` or alter target user files.
- Install refuses or remains dry-run unless explicit apply is provided.
- Verify report writes require explicit acknowledgement.
- Existing README, app/docs/source files, and user-owned adapter files are preserved byte-for-byte unless explicitly managed by the installer.
- Conflicting manifests or adapter files produce structured refusal reports, not tracebacks.
- Failed apply cleanup removes only newly-created files from that failed attempt.
- Missing required gates after install produce deterministic verification failures.
- The source repository does not gain or lose files during target smoke runs except tracked Task 111 work/evidence.

## Subtask Mapping

| Subtask | Scope |
| --- | --- |
| 111.1 | This scope matrix and implementation boundary. |
| 111.2 | CLI smoke coverage for isolated target repositories. |
| 111.3 | MCP wrapper equivalence coverage for the same contract. |
| 111.4 | Safety/negative-case hardening. |
| 111.5 | Evidence, closeout, and recommendation for distribution/packaging. |

## Non-Goals

- Do not build the packaging/distribution mechanism in this task.
- Do not add a second installer engine.
- Do not make MCP the primary source of install semantics.
- Do not mutate the source repository as an Aegis target.
- Do not rely on private agent memory as evidence.

## Open Questions

- Whether the first implementation slice should keep all smoke helpers local to `test_aegis_cross_project_smoke.py` or promote reusable fixture builders into `cross_project_fixtures.py`.
- Whether direct stdio MCP smoke should stay in the existing MCP server test module or move into the new cross-project smoke module.
- How broad the first MCP resource assertions should be without making the suite slow or brittle.
