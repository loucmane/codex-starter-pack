# Task ID: 111

**Title:** Aegis Cross-Project Install Smoke Harness and Distribution Readiness

**Status:** in-progress

**Dependencies:** 101 ✓, 110 ✓

**Priority:** medium

**Description:** Build a focused cross-project smoke harness that proves the Aegis Foundation installer core and MCP wrapper work safely in isolated target repositories outside this source repo. The task should validate realistic project shapes, both CLI and MCP invocation paths, and durable evidence needed before packaging or broader distribution work begins.

**Details:**

Create a new Task 111 work-tracking/plan/session set and a dedicated pytest harness for Aegis portability. The current codebase already has the source-of-truth installer core in `scripts/_aegis_installer.py`, the CLI wrapper in `scripts/codex-task` under the `aegis` command group, the MCP wrapper/control plane in `aegis_mcp/server.py` plus `scripts/aegis-mcp-server`, schema contracts in `schemas/aegis/*.schema.json`, initial isolated fixture coverage in `tests/meta_workflow_guard/test_aegis_installer.py` and `tests/meta_workflow_guard/test_aegis_installer_fixtures.py`, MCP coverage in `tests/meta_workflow_guard/test_aegis_mcp_server.py`, and reusable cross-project shape helpers in `tests/meta_workflow_guard/cross_project_fixtures.py`. Build on those patterns instead of introducing a parallel installer implementation.

Recommended implementation shape:
- Add a new focused test module such as `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`, plus small local helper functions/classes in that test file unless reusable fixture construction genuinely belongs in `tests/meta_workflow_guard/cross_project_fixtures.py`.
- Create each target repository under `tmp_path` and never point the harness at the source repository as a target. Capture a pre/post source-tree fingerprint for key source paths, or otherwise assert the source repo is not mutated by CLI or MCP smoke flows.
- Cover at least these target shapes: an empty repository; a Python/library repository with `pyproject.toml`, README, and `src/...`; a web/app repository with `package.json`, app/source directories, and existing docs; a docs-heavy repository using the Task 101 style roots from `cross_project_fixtures.py`; and a partial existing Aegis install with `.aegis/foundation-manifest.json`, `.aegis/contract.md`, or adapter files already present.
- For each supported happy-path shape, exercise the CLI sequence with subprocess calls from `REPO_ROOT`: `python3 scripts/codex-task aegis inspect --target-dir <target>`, `plan-install --target-dir <target> --primary-agent ... --agent ...`, `install --target-dir <target> --profile generic --primary-agent ... --agent ... --apply`, and `verify --target-dir <target>`. Parse JSON stdout and assert expected status, schema fields, and filesystem effects.
- For MCP coverage, instantiate `AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=<target>)` and `create_server(...)` for in-process calls where possible. Reuse the `call_tool_payload`/resource-read style from `tests/meta_workflow_guard/test_aegis_mcp_server.py`, or factor a small helper if duplication becomes excessive. Exercise `aegis.inspect`, `aegis.plan_install`, `aegis.install`, and `aegis.verify`; include at least one stdio client smoke path through `scripts/aegis-mcp-server` if practical without making the suite slow or flaky.
- Keep `scripts/_aegis_installer.py` as the only implementation of installer semantics. The MCP path must prove wrapper equivalence by validating that MCP responses preserve core classifications, refusal payloads, cleanup payloads, manifest fields, report paths, and verification results rather than reinterpreting them.
- Validate installed artifacts for each happy-path target: `.aegis/foundation-manifest.json`, `.aegis/contract.md`, `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, `.aegis/reports/verification-report.json`, copied `schemas/aegis/*.schema.json`, managed file records, access policy, interfaces, enabled adapter records, primary agent, and gate records. For Claude-enabled installs, assert expected adapter surfaces such as `CLAUDE.md`, `.claude/settings.json`, `.claude/scripts/readiness.sh`, `.claude/scripts/pretooluse-gate.sh`, `.claude/scripts/bash-command-guard.sh`, and `.claude/scripts/codex-path-guard.sh`; for multi-agent installs, assert Codex/Claude adapter records remain adapter-specific while shared state stays under `.aegis/`.
- Prove safety semantics explicitly: `inspect` and `plan-install`/`aegis.plan_install` do not mutate targets; `install` without `--apply` or MCP `apply: false` refuses or stays dry-run; MCP `aegis.verify` requires `acknowledge_report_write: true`; verification report writes happen only after acknowledgement; existing user files such as README, `CLAUDE.md`, `.claude/settings.json`, docs, or app files are not clobbered; conflicts/manual-review operations return structured refusal reports; and simulated failed applies clean up newly planned files without deleting pre-existing user files.
- Add negative cases for partial installs and conflicts: conflicting `.aegis/foundation-manifest.json`, pre-existing adapter files with different content, missing executable gate files after install, unsupported/invalid agent selection, and malformed target state. Assert predictable JSON or MCP error envelopes and absence of Python tracebacks.
- Document the known-good external install path in Task 111 work-tracking, for example under `docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/designs/` or `reports/aegis-cross-project-smoke/`. Include findings, decisions, implementation notes, handoff, command evidence, and a recommendation for the next distribution or packaging task.
- Preserve the architecture direction selected in Task 48 and implemented through Tasks 109-110: deterministic CLI/library core is the source of truth; MCP is a wrapper/control plane; `.aegis/` is shared readable foundation state; direct `.aegis/` writes remain forbidden; and no wrapper or smoke harness may fork installer semantics.

**Test Strategy:**

Run the new focused pytest suite and existing Aegis regression coverage. At minimum: `python -m pytest tests/meta_workflow_guard/test_aegis_cross_project_smoke.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py`.

Required assertions for the new harness:
- All target shapes are created under temporary directories and the source repository remains unchanged except for intentional tracked work/evidence files.
- CLI `inspect`, `plan-install`, `install --apply`, and `verify` produce parseable JSON and pass for the happy-path target shapes.
- MCP `aegis.inspect`, `aegis.plan_install`, `aegis.install`, and `aegis.verify` produce equivalent structured results or expected structured refusals, including the explicit `apply` and `acknowledge_report_write` gates.
- Dry-run/planning paths create no `.aegis/` state and preserve a target file manifest snapshot.
- Applied installs create the manifest, contract, schemas, adapter files, reports, managed-file records, gates, access policy, and verification metadata expected by the schemas.
- Existing user files are preserved byte-for-byte unless explicitly classified as safe managed skips; conflicts and manual-review cases refuse without partial mutation.
- Failed apply simulation returns cleanup details and removes only newly-created files from that failed attempt.
- Verification failures for missing required gates are structured and deterministic.
- Resource reads such as `aegis://manifest/current`, `aegis://managed-files`, `aegis://install-plan/latest`, and `aegis://verification/latest` return expected post-install content and do not mutate the target.

Final acceptance gates: capture evidence under the Task 111 work-tracking reports directory, then run `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`. The handoff must include the known-good install path, unresolved risks, and a clear recommendation for the next distribution or packaging task.

## Subtasks

### 111.1. Reconcile Task 111 scope and design the Aegis cross-project smoke matrix

**Status:** done  
**Dependencies:** None  

Create the Task 111 planning baseline and convert the requested portability scope into an explicit smoke matrix grounded in the current Aegis implementation.

**Details:**

Review and document the existing source-of-truth boundaries: installer semantics live only in `scripts/_aegis_installer.py`, CLI routing lives in `scripts/codex-task`, MCP wrapping lives in `aegis_mcp/server.py` and `scripts/aegis-mcp-server`, schema contracts live in `schemas/aegis/*.schema.json`, and fixture/test patterns already exist in `tests/meta_workflow_guard/test_aegis_installer.py`, `test_aegis_installer_fixtures.py`, `test_aegis_mcp_server.py`, and `cross_project_fixtures.py`. Create the Task 111 active work-tracking/session/plan artifacts and a design note that defines the target repository shapes, expected CLI/MCP command flows, source-tree fingerprint strategy, artifact assertions, refusal/error expectations, and evidence paths. The matrix must explicitly cover an empty repo, Python/library repo, web/app repo, docs-heavy Task 101-style repo, and partial existing Aegis install without introducing any parallel installer logic.

### 111.2. Implement CLI smoke coverage for isolated target repositories

**Status:** done  
**Dependencies:** 111.1  

Add the focused pytest harness that exercises the Aegis CLI against realistic tmp_path repositories outside the source repo.

**Details:**

Create `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py` with local helper functions for seeding target repositories, invoking `python3 scripts/codex-task aegis ...` from `REPO_ROOT`, parsing JSON stdout, fingerprinting key source paths, and asserting source repo non-mutation. Build target repositories only under `tmp_path`, including empty, Python/library, web/app, docs-heavy using Task 101 `REPO_SHAPES` helpers where useful, and partial existing Aegis install. For each happy-path shape run `inspect`, `plan-install --target-dir <target> --primary-agent ... --agent ...`, `install --target-dir <target> --profile generic --primary-agent ... --agent ... --apply`, and `verify --target-dir <target>`. Assert expected JSON status fields, schema-facing fields, plan summaries, report paths, filesystem effects, idempotent second plans, and preservation of pre-existing README/docs/app files.

### 111.3. Add MCP wrapper equivalence smoke coverage for the same target shapes

**Status:** pending  
**Dependencies:** 111.2  

Exercise the MCP in-process server and a practical stdio smoke path to prove wrapper behavior preserves installer-core results.

**Details:**

Extend the new smoke module with MCP helpers modeled on `call_tool_payload`, `read_resource_payload`, and stdio patterns from `tests/meta_workflow_guard/test_aegis_mcp_server.py`. For representative target shapes instantiate `AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=<target>)` and `create_server(...)`, then call `aegis.inspect`, `aegis.plan_install`, `aegis.install`, and `aegis.verify`. Compare MCP response envelopes to the CLI/core expectations without reinterpreting installer semantics: preserve classifications, refusal payloads, cleanup payloads, manifest fields, report paths, verification summaries, and error status codes. Include one bounded stdio client smoke through `scripts/aegis-mcp-server` if it remains deterministic and fast, reusing the existing list-tools/resources/prompts pattern as the minimum transport proof.

### 111.4. Harden safety and negative-case smoke assertions

**Status:** pending  
**Dependencies:** 111.3  

Add explicit dry-run, conflict, acknowledgement, malformed-state, invalid-agent, and failed-apply cleanup cases to the smoke harness.

**Details:**

Expand `test_aegis_cross_project_smoke.py` with safety-focused cases that prove `inspect` and `plan-install` do not mutate targets, CLI `install` without `--apply` remains dry-run, MCP `aegis.install` with `apply: false` returns `apply_required`, MCP `aegis.verify` refuses without `acknowledge_report_write: true`, verification reports are written only after acknowledgement, and source repo fingerprints remain unchanged. Add negative cases for conflicting `.aegis/foundation-manifest.json`, pre-existing adapter files with different content such as `CLAUDE.md` or `.claude/settings.json`, missing executable gate files after install, unsupported or invalid agent selection, malformed target state, and simulated failed apply cleanup by monkeypatching installer write behavior where appropriate. Assert predictable JSON or MCP error envelopes, no Python tracebacks in stderr, no clobbering of user files, and cleanup removes only newly planned files while preserving pre-existing content.

### 111.5. Record evidence, update Taskmaster state, and recommend the next distribution task

**Status:** pending  
**Dependencies:** 111.4  

Capture durable Task 111 evidence and close out the work with documentation that supports packaging or broader distribution decisions.

**Details:**

Write the known-good external install path and final findings under the Task 111 work-tracking tree, such as `docs/ai/work-tracking/active/20260517-task111-aegis-cross-project-smoke-ACTIVE/designs/` and `reports/aegis-cross-project-smoke/`. Include scope decisions, implementation notes, command evidence, test output paths, safety findings, remaining risks, and a concrete recommendation for the next packaging or distribution task. Refresh Taskmaster-generated artifacts with the narrow `python3 scripts/codex-task taskmaster generate-one --id 111` flow after status or subtask updates, use `python3 scripts/codex-task taskmaster health` for full-graph health, and avoid broad generated-file refreshes unless explicitly needed. Preserve the architecture decision that the deterministic CLI/library core is the source of truth, MCP is a wrapper/control plane, `.aegis/` is shared readable state, direct `.aegis/` writes remain forbidden, and no smoke harness forks installer semantics.
