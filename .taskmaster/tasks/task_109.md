# Task ID: 109

**Title:** Build Portable Foundation Installer and MCP Distribution Contract

**Status:** done

**Dependencies:** 100 ✓, 102 ✓, 107 ✓

**Priority:** high

**Description:** Deliver the agreed Option B V1 Aegis Foundation installer slice: keep the deterministic CLI/library core as the source of truth, prove the generic-profile installer path for inspect, plan-install, install, and verify under the `python3 scripts/codex-task aegis ...` namespace, and document MCP as a wrapper contract rather than shipping a production MCP server in this task.

**Details:**

Task 109 V1 remains narrowed to the scope already recorded in `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md` and `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md`: architecture decision, schema contracts, generic-profile CLI prototype, fixture tests, and MCP contract documentation.

Update the terminology and paths to the accepted 2026-05-16 Aegis Foundation naming decision recorded in the active Task 109 work-tracking docs. The portable installed runtime is **Aegis Foundation**. Shared agent-neutral installed state belongs under `.aegis/`, with the V1 manifest path `.aegis/foundation-manifest.json`. Codex and Claude remain adapter-specific surfaces: do not rename `CODEX.md`, `.codex/`, `scripts/codex-*`, `CLAUDE.md`, or `.claude/`. The existing `scripts/_repo_structure.py` loader still reads repo-local structure from `.codex/config.toml`, so Aegis installation should build around that current adapter/config boundary rather than globally moving existing Codex files.

Source of truth: implement installer behavior in a deterministic Python library/core invoked by `scripts/codex-task aegis ...`. MCP is only a documented wrapper contract in this task. Do not build a separate MCP-only implementation path.

V1 deliverables:
- Preserve and build on the completed architecture decision in `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md`, which now documents Aegis Foundation, `.aegis/`, and `aegis` CLI/MCP naming.
- Define Draft 2020-12 jsonschema contracts for the Aegis manifest, Aegis project profiles, and Aegis install plans, likely under a new `schemas/aegis/` directory because the repository currently has schema examples but no top-level `schemas/` tree. Follow existing schema conventions from `templates/metadata/template-frontmatter.schema.json` and `scripts/template-ssot-scanner/config/scanner_config.schema.json`: stable `$id` values such as the existing `https://codex.local/schemas/...` pattern, explicit `schema_version` fields where the document is versioned, typed `$defs`, and strict `additionalProperties` discipline for installer-owned contracts.
- Target the installed Aegis manifest path `.aegis/foundation-manifest.json` unless the schema design explicitly reserves a future override.
- Implement only the generic profile in V1 while allowing the Aegis profile schema to describe future profiles.
- Add an `aegis` command group under `scripts/codex-task` for the V1 prototype commands: `inspect`, `plan-install`, `install`, and `verify`. It may also expose `list-profiles` and `explain-profile` if they are needed to make the generic profile discoverable, but `status`, `plan-update`, `update`, `rollback`, and production MCP command paths are deferred.
- Reuse or adapt existing bootstrap/repo-structure patterns instead of creating a disconnected installer path. Relevant current code includes `scripts/codex-task` functions `handle_bootstrap_init`, `_bootstrap_values_from_args`, `_render_bootstrap_config`, `_write_bootstrap_file`, `_ensure_directory`, the existing `bootstrap` parser group in `build_parser`, and `scripts/_repo_structure.py` functions/classes `load_repo_structure` and `RepoStructure`.
- Produce structured JSON output for inspect, plan-install, install report, and verification report, with Markdown evidence where useful for work-tracking. Aegis runtime reports should be able to live under `.aegis/reports/` or another schema-declared report location while preserving existing repo reports roots where the generic profile needs them.
- Implement fixture tests for generic-profile install, verify, and install-twice idempotence. Initial fixture coverage should include empty-repo and a basic Python/tooling repo shape; existing `tests/meta_workflow_guard/cross_project_fixtures.py` can inform repository-shape fixtures but does not need to become full multi-profile coverage.
- Document MCP tools, resources, prompts, input/output schemas, read-only versus mutating behavior, explicit apply gates, and how each MCP surface delegates to the CLI/library core. Rename future MCP examples from `foundation.*` and `foundation://...` to `aegis.*` and `aegis://...`.

Deferred to follow-up tasks: full production MCP server implementation, multi-profile support beyond schema plus generic implementation, complex cross-version update migrations, package publishing, automatic CI installation into target projects, hosted or long-running service infrastructure, full cross-agent automation, and hardened update/rollback across multiple installed Aegis Foundation versions.

Acceptance for this task: Task 109 session/plan/work-tracking remain current; the architecture decision and Option B scope are documented with Aegis terminology; schema and CLI prototype work are aligned with the existing Python 3.11/argparse/jsonschema/pytest project style in `pyproject.toml`; generic install/verify/idempotence fixture tests pass; MCP contract documentation is complete enough for a later server task and uses `aegis.*` / `aegis://...`; no implementation renames Codex or Claude adapter surfaces; and final workflow gates pass: `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`.

**Test Strategy:**

Validate the V1 installer as a deterministic local Python tool, not as a production MCP service. Add focused pytest coverage for Aegis schema validity, core planning behavior, CLI parsing/dispatch, fixture installs, verification, and idempotence.

Required checks:
- Use `jsonschema.Draft202012Validator.check_schema` and positive/negative sample payload tests for the Aegis manifest, Aegis project profile, and Aegis install-plan schemas under `schemas/aegis/` or the final schema location.
- Add parser tests near `tests/meta_workflow_guard/test_codex_task.py` for `python3 scripts/codex-task aegis inspect`, `plan-install`, `install`, `verify`, and any V1 profile-discovery commands that are implemented.
- Add temporary-repository fixture tests for `inspect -> plan-install -> install --apply -> verify` using the generic profile.
- Add golden install-plan assertions for create/skip/conflict/manual-review classifications and dry-run versus apply semantics.
- Add install-twice idempotence tests proving the second plan reports no unsafe changes and verify still passes.
- Add manifest assertions for `.aegis/foundation-manifest.json`: `schema_version`, `foundation_name` or equivalent Aegis identity, `foundation_version`, `installer_version`, `profile`, adapter-specific surfaces such as Codex/Claude entries where present, managed files, customized files or equivalent tracking, `last_verified_at` behavior, and report references.
- Add assertions that V1 writes no `.codex/foundation-manifest.json` and does not globally rename `CODEX.md`, `.codex/`, `scripts/codex-*`, `CLAUDE.md`, or `.claude/`.
- Add conflict/refusal tests showing existing files are not overwritten unless the plan and explicit apply semantics allow it.
- Add documentation/schema checks for the MCP contract only, including `aegis.*` tool names and `aegis://...` resource URIs. Full MCP protocol/runtime tests are deferred with the production MCP server follow-up.

Suggested command coverage after implementation: `python -m pytest tests/meta_workflow_guard/test_codex_task.py` plus any new installer-focused test file such as `tests/meta_workflow_guard/test_aegis_installer.py` or `tests/meta_workflow_guard/test_foundation_installer.py`. Final handoff must also run `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task plan sync`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`.

## Subtasks

### 109.2. Define Aegis manifest, profiles, and install-plan schema

**Status:** done
**Dependencies:** None

Define the V1 schema contracts for `.aegis/foundation-manifest.json`, Aegis project profiles, and Aegis generic-profile install plans, including dry-run/apply semantics, conflict classes, adapter tracking, and managed/customized file tracking.

**Details:**

Keep this as schema-contract work that unblocks the generic-profile Aegis CLI prototype in 109.3. The schema artifacts should likely live under `schemas/aegis/`, for example `schemas/aegis/foundation-manifest.schema.json`, `schemas/aegis/profile.schema.json`, and `schemas/aegis/install-plan.schema.json`, because current schema examples live in `templates/metadata/template-frontmatter.schema.json` and `scripts/template-ssot-scanner/config/scanner_config.schema.json` but there is not yet a top-level schema directory.

The schemas must be consistent with existing repository conventions: Draft 2020-12 jsonschema, stable `$id` values following the current `https://codex.local/schemas/...` style with an Aegis path segment, explicit `schema_version` fields for versioned documents, clear `$defs`, and strict `additionalProperties` discipline in installer-owned sections as demonstrated by the scanner config schema.

The Aegis manifest must target `.aegis/foundation-manifest.json` and include enough fields to support V1 install/verify and future update planning: schema_version, foundation_name or equivalent identity set to Aegis Foundation, foundation_version, installer_version, installed_at, profile, selected capabilities or feature flags, adapter-specific surfaces for Codex/Claude where applicable, managed_files, customized_files or equivalent customization tracking, verification metadata, and report/checkpoint references where needed.

The Aegis project profile schema should describe future profile shape but only the generic profile must be implemented in V1. Keep multi-profile selection behavior minimal and deterministic.

The Aegis install-plan schema should support inspect/plan-install/install/verify outputs for the generic profile: target root, selected profile, dry-run/apply mode, proposed operations, path classification such as create/modify/skip/conflict/manual-review, refusal reasons, expected manifest changes under `.aegis/`, verification requirements, adapter-specific file handling, and report paths.

Out of scope for this subtask: production MCP runtime behavior, complex cross-version update migrations, package publishing metadata, automatic CI installation, and full multi-profile behavior beyond defining the contract shape.
<info added on 2026-05-16T09:51:17.853Z>
Update the Aegis schema contract to carry the 2026-05-16 agent-selection and gate decisions from docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md and DECISIONS.md. The generic profile schema should set default_primary_agent to claude and agent_selection_required to true, but the install-plan contract must still model the installer prompt/answer for primary_agent and additional enabled agents; non-interactive plans should require explicit primary-agent and agent flags instead of silently choosing Claude. The manifest schema for .aegis/foundation-manifest.json must add primary_agent, enabled adapter records, entrypoints, interfaces, access_policy, and gates as first-class required installer-owned sections. Model primary_agent as a constrained value such as claude, codex, gemini, multi, or none; model enabled adapters as strict per-agent records that include enabled, available, entrypoint, managed files, and contributed gate ids. access_policy must explicitly permit direct agent reads of .aegis while forbidding direct .aegis writes, with write_interface limited to the Aegis CLI and future MCP wrapper. Gate records must include id, required, enforcement, adapter or shared scope, command or path/configuration evidence, and verification semantics; enforcement must be limited to mechanical, verification, or policy. Required gates that are missing, non-executable where executable, not configured, or reporting failure must make aegis verify fail, so the schema and sample payloads should distinguish required hard failures from unsupported optional checks. For Claude-enabled installs, the manifest/profile/install-plan schemas must require and verify the Claude hook runtime surfaces already present in this repo: CLAUDE.md, .claude/settings.json, .claude/scripts/readiness.sh, .claude/scripts/pretooluse-gate.sh, .claude/scripts/bash-command-guard.sh, and .claude/scripts/codex-path-guard.sh, plus hook registration in .claude/settings.json matching the existing PreToolUse dispatcher pattern from tests/claude_adapter/test_adapter_contract_files.py and .claude/scripts/gate_lib.py.
</info added on 2026-05-16T09:51:17.853Z>

### 109.3. Build generic-profile Aegis CLI installer lifecycle and verification commands

**Status:** done
**Dependencies:** None

Implement the V1 deterministic library/CLI prototype for the generic profile under `python3 scripts/codex-task aegis ...`: inspect, plan-install, install, and verify, with explicit dry-run/apply behavior and structured reports.

**Details:**

Add an `aegis` command group under `scripts/codex-task` that calls a reusable Python core rather than embedding all behavior directly in argparse handlers. Align with the existing `scripts/codex-task` style and the repo's Python 3.11 dependencies in `pyproject.toml`; a helper module analogous to `scripts/_repo_structure.py` is appropriate if it keeps planning, manifest handling, rendering, and verification testable outside argparse.

Build on existing repo-structure/bootstrap patterns instead of creating a disconnected copy mechanism. Current relevant code includes `scripts/codex-task` functions `handle_bootstrap_init`, `_bootstrap_values_from_args`, `_render_bootstrap_config`, `_write_bootstrap_file`, `_ensure_directory`, `_repo_structure_from_values`, and `build_parser`, plus `scripts/_repo_structure.py` `load_repo_structure`/`RepoStructure`. The new installer should improve on bootstrap by producing inspect output, an install plan, managed-file manifest state at `.aegis/foundation-manifest.json`, verification output, and idempotence behavior.

V1 commands:
- `python3 scripts/codex-task aegis inspect --target-dir <repo>`
- `python3 scripts/codex-task aegis plan-install --target-dir <repo> [--profile generic]`
- `python3 scripts/codex-task aegis install --target-dir <repo> [--profile generic] --apply`
- `python3 scripts/codex-task aegis verify --target-dir <repo>`

Optional V1 commands if needed for discoverability: `list-profiles` and `explain-profile`.

Command behavior:
- `inspect`, `plan-install`, `list-profiles`, and `explain-profile` are read-only.
- `install` defaults to non-mutating behavior unless explicit apply semantics are supplied.
- `install` refuses unsafe overwrites and reports conflicts/manual-review items instead of silently replacing files.
- `verify` reads the Aegis manifest and repo structure, checks installed files/reports relevant to the generic profile, and emits structured JSON with pass/fail/warn details.
- Write JSON reports and, where useful, Markdown evidence under `.aegis/reports/` or the schema-declared report path. Preserve existing Codex/Claude adapter file names where they are installed or referenced; do not rename `CODEX.md`, `.codex/`, `scripts/codex-*`, `CLAUDE.md`, or `.claude/`.

Deferred from implementation in this task: `status`, `plan-update`, `update`, `rollback`, production MCP server command handlers, package publishing, and automatic CI installation. The Aegis manifest/schema should still leave room for later update/rollback tasks.

### 109.4. Implement generic Aegis fixture, verification, and idempotence tests

**Status:** done
**Dependencies:** None

Create V1 fixture tests proving the generic-profile Aegis installer can install, verify, and run idempotently across minimal target repositories.

**Details:**

Narrow this subtask to V1 proof for the generic profile. Required fixture matrix: empty-repo and basic-python-tool. The existing `tests/meta_workflow_guard/cross_project_fixtures.py` repository-shape helpers can inform the approach, but V1 does not need full web-app/docs-site/game-tool/profile coverage.

Required coverage:
- golden inspect and plan-install outputs for generic Aegis fixtures;
- `install --apply` creates expected starter assets, reports, and `.aegis/foundation-manifest.json`;
- verify passes after install and reports unsupported optional checks clearly;
- running plan-install/install a second time is idempotent and does not create unsafe changes;
- existing file conflicts are classified as conflict or manual-review and are not overwritten by default;
- Codex/Claude adapter surfaces remain adapter-specific if present, while shared Aegis runtime state is written under `.aegis/`;
- V1 failure cleanup behavior is tested only as needed for safe local install attempts.

Full rollback lifecycle tests, cross-version update migration tests, automatic CI installation tests, and automated Codex/Claude cross-agent smoke tests are deferred. Keep cross-agent expectations as documented verification notes unless a small static/schema check is needed for the MCP/adapter contract.

### 109.5. Define Aegis MCP wrapper contract and evidence handoff

**Status:** done
**Dependencies:** None

Document the MCP wrapper contract over the CLI/library core, including Aegis tools, resources, prompts, schemas, apply gates, evidence outputs, and deferred production-server follow-up tasks.

**Details:**

Keep MCP as documentation/contract work for Task 109 V1. Do not implement a production MCP server here.

The contract should document how MCP clients would call the same deterministic Aegis installer library used by `scripts/codex-task aegis ...`. It should cover:
- tools such as `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.status`, `aegis.plan_update`, `aegis.update`, `aegis.rollback`, `aegis.list_profiles`, and `aegis.explain_profile`, clearly marking which are V1-backed by the CLI prototype and which are future/deferred;
- resources such as `aegis://contract/current`, `aegis://profiles`, `aegis://profiles/{name}`, `aegis://install-plan/latest`, `aegis://verification/latest`, `aegis://limitations`, `aegis://managed-files`, and `aegis://project/status`;
- prompts such as `aegis.bootstrap_new_project`, `aegis.migrate_existing_project`, `aegis.verify_runtime`, `aegis.prepare_agent_session`, `aegis.close_agent_session`, `aegis.install_claude_adapter`, and `aegis.install_codex_adapter`;
- input/output schemas aligned with the Aegis manifest/profile/install-plan schemas from 109.2;
- read-only versus mutating behavior, explicit apply gates for mutating operations, report paths, changed/skipped/conflict path reporting, refusal semantics, and the boundary between shared `.aegis/` runtime state and adapter-specific Codex/Claude files.

Handoff must identify follow-up tasks for the production MCP server, expanded profiles, update/rollback hardening, packaging/distribution, optional CI installation templates, and hosted/service infrastructure if those remain desired after V1.

### 109.1. Document installer architecture and distribution decision

**Status:** done
**Dependencies:** None

Capture the CLI/library core plus optional MCP wrapper architecture, alternatives considered, chosen decision, risks, and acceptance gates in tracked design documentation.
