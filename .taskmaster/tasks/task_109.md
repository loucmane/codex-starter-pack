# Task ID: 109

**Title:** Build Portable Foundation Installer and MCP Distribution Contract

**Status:** in-progress

**Dependencies:** 100 ✓, 102 ✓, 107 ✓

**Priority:** high

**Description:** Deliver the agreed Option B V1 foundation-installer slice: keep the deterministic CLI/library core as the source of truth, prove the generic-profile installer path for inspect, plan-install, install, and verify, and document MCP as a wrapper contract rather than shipping a production MCP server in this task.

**Details:**

Task 109 V1 is narrowed to the scope already recorded in docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md and docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md: architecture decision, schema contracts, generic-profile CLI prototype, fixture tests, and MCP contract documentation.

Source of truth: implement installer behavior in a deterministic Python library/core invoked by scripts/codex-task. MCP is only a documented wrapper contract in this task. Do not build a separate MCP-only implementation path.

V1 deliverables:
- Preserve and build on the completed architecture decision in docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md.
- Define Draft 2020-12 jsonschema contracts for the installed foundation manifest, project profiles, and install plans. Follow existing schema conventions from templates/metadata/template-frontmatter.schema.json and scripts/template-ssot-scanner/config/scanner_config.schema.json: explicit schema_version fields where the document is versioned, stable $id values, typed $defs, and strict additionalProperties discipline for installer-owned contracts.
- Target the installed manifest path .codex/foundation-manifest.json unless the schema design explicitly reserves a future override.
- Implement only the generic profile in V1 while allowing the profile schema to describe future profiles.
- Add a foundation command group under scripts/codex-task for the V1 prototype commands: inspect, plan-install, install, and verify. It may also expose list-profiles and explain-profile if they are needed to make the generic profile discoverable, but status, plan-update, update, rollback, and production MCP command paths are deferred.
- Reuse or adapt existing bootstrap/repo-structure patterns instead of creating a disconnected installer path. Relevant current code includes scripts/codex-task handle_bootstrap_init, _bootstrap_values_from_args, _render_bootstrap_config, _write_bootstrap_file, and scripts/_repo_structure.py load_repo_structure/RepoStructure.
- Produce structured JSON output for inspect, install-plan, install report, and verification report, with Markdown evidence where useful for work-tracking.
- Implement fixture tests for generic-profile install, verify, and install-twice idempotence. Initial fixture coverage should include empty-repo and a basic Python/tooling repo shape; existing tests/meta_workflow_guard/cross_project_fixtures.py can inform but does not need to become full multi-profile coverage.
- Document MCP tools, resources, prompts, input/output schemas, read-only versus mutating behavior, explicit apply gates, and how each MCP surface delegates to the CLI/library core.

Deferred to follow-up tasks: full production MCP server implementation, multi-profile support beyond schema plus generic implementation, complex cross-version update migrations, package publishing, automatic CI installation into target projects, hosted or long-running service infrastructure, full cross-agent automation, and hardened update/rollback across multiple installed foundation versions.

Acceptance for this task: Task 109 session/plan/work-tracking remain current; the architecture decision and Option B scope are documented; schema and CLI prototype work are aligned with the existing Python 3.11/argparse/jsonschema/pytest project style in pyproject.toml; generic install/verify/idempotence fixture tests pass; MCP contract documentation is complete enough for a later server task; and final workflow gates pass: python3 scripts/codex-task plan sync, python3 scripts/codex-task work-tracking audit, python3 scripts/codex-task taskmaster health, python3 scripts/codex-guard validate --include-untracked, and git diff --check.

**Test Strategy:**

Validate the V1 installer as a deterministic local Python tool, not as a production MCP service. Add focused pytest coverage for schema validity, core planning behavior, CLI parsing/dispatch, fixture installs, verification, and idempotence.

Required checks:
- Use jsonschema Draft202012Validator.check_schema and positive/negative sample payload tests for the foundation manifest, project profile, and install-plan schemas.
- Add parser tests near tests/meta_workflow_guard/test_codex_task.py for python3 scripts/codex-task foundation inspect, plan-install, install, verify, and any V1 profile-discovery commands that are implemented.
- Add temporary-repository fixture tests for inspect -> plan-install -> install --apply -> verify using the generic profile.
- Add golden install-plan assertions for create/skip/conflict/manual-review classifications and dry-run versus apply semantics.
- Add install-twice idempotence tests proving the second plan reports no unsafe changes and verify still passes.
- Add manifest assertions for .codex/foundation-manifest.json: schema_version/foundation_version/installer_version/profile, managed_files, customized_files or equivalent tracking, last_verified_at behavior, and report references.
- Add conflict/refusal tests showing existing files are not overwritten unless the plan and explicit apply semantics allow it.
- Add documentation/schema checks for the MCP contract only; full MCP protocol/runtime tests are deferred with the production MCP server follow-up.

Suggested command coverage after implementation: python -m pytest tests/meta_workflow_guard/test_codex_task.py plus any new installer-focused test file such as tests/meta_workflow_guard/test_foundation_installer.py. Final handoff must also run python3 scripts/codex-task work-tracking audit, python3 scripts/codex-task taskmaster health, python3 scripts/codex-task plan sync, python3 scripts/codex-guard validate --include-untracked, and git diff --check.

## Subtasks

### 109.2. Define foundation manifest, profiles, and install-plan schema

**Status:** pending  
**Dependencies:** None  

Define the V1 schema contracts for .codex/foundation-manifest.json, project profiles, and generic-profile install plans, including dry-run/apply semantics, conflict classes, and managed/customized file tracking.

**Details:**

Keep this as schema-contract work that unblocks the generic-profile CLI prototype in 109.3. The schema artifacts must be consistent with existing repository conventions: Draft 2020-12 jsonschema, explicit schema_version fields for versioned documents, stable $id values, clear $defs, and strict additionalProperties discipline as demonstrated by templates/metadata/template-frontmatter.schema.json and scripts/template-ssot-scanner/config/scanner_config.schema.json.

The foundation manifest should target .codex/foundation-manifest.json and include enough fields to support V1 install/verify and future update planning: schema_version, foundation_version, installer_version, installed_at, profile, feature flags or selected capabilities, managed_files, customized_files or equivalent customization tracking, verification metadata, and report/checkpoint references where needed.

The project profile schema should describe future profile shape but only the generic profile must be implemented in V1. Keep multi-profile selection behavior minimal and deterministic.

The install-plan schema should support inspect/plan-install/install/verify outputs for the generic profile: target root, selected profile, dry-run/apply mode, proposed operations, path classification such as create/modify/skip/conflict/manual-review, refusal reasons, expected manifest changes, verification requirements, and report paths.

Out of scope for this subtask: production MCP runtime behavior, complex cross-version update migrations, package publishing metadata, automatic CI installation, and full multi-profile behavior beyond defining the contract shape.

### 109.3. Build generic-profile CLI installer lifecycle and verification commands

**Status:** pending  
**Dependencies:** None  

Implement the V1 deterministic library/CLI prototype for the generic profile: inspect, plan-install, install, and verify, with explicit dry-run/apply behavior and structured reports.

**Details:**

Add a foundation command group under scripts/codex-task that calls a reusable Python core rather than embedding all behavior directly in argparse handlers. Align with the existing scripts/codex-task style and the repo's Python 3.11 dependencies in pyproject.toml.

Build on existing repo-structure/bootstrap patterns instead of creating a disconnected copy mechanism. Current relevant code includes scripts/codex-task handle_bootstrap_init, _bootstrap_values_from_args, _render_bootstrap_config, _write_bootstrap_file, _ensure_directory, and scripts/_repo_structure.py. The new installer should improve on bootstrap by producing inspect output, an install plan, managed-file manifest state, verification output, and idempotence behavior.

V1 commands:
- python3 scripts/codex-task foundation inspect --target-dir <repo>
- python3 scripts/codex-task foundation plan-install --target-dir <repo> [--profile generic]
- python3 scripts/codex-task foundation install --target-dir <repo> [--profile generic] --apply
- python3 scripts/codex-task foundation verify --target-dir <repo>

Optional V1 commands if needed for discoverability: list-profiles and explain-profile.

Command behavior:
- inspect and plan-install are read-only.
- install defaults to non-mutating behavior unless explicit apply semantics are supplied.
- install refuses unsafe overwrites and reports conflicts/manual-review items instead of silently replacing files.
- verify reads the manifest and repo structure, checks installed files/reports relevant to the generic profile, and emits structured JSON with pass/fail/warn details.
- write JSON reports and, where useful, Markdown evidence under the target repo's configured reports root.

Deferred from implementation in this task: status, plan-update, update, rollback, production MCP server command handlers, package publishing, and automatic CI installation. The manifest/schema should still leave room for later update/rollback tasks.

### 109.4. Implement generic fixture, verification, and idempotence tests

**Status:** pending  
**Dependencies:** None  

Create V1 fixture tests proving the generic-profile installer can install, verify, and run idempotently across minimal target repositories.

**Details:**

Narrow this subtask to V1 proof for the generic profile. Required fixture matrix: empty-repo and basic-python-tool. The existing tests/meta_workflow_guard/cross_project_fixtures.py shapes can inform the approach, but V1 does not need full web-app/docs-site/game-tool/profile coverage.

Required coverage:
- golden inspect and plan-install outputs for generic fixtures;
- install --apply creates expected starter assets, reports, and .codex/foundation-manifest.json;
- verify passes after install and reports unsupported optional checks clearly;
- running plan-install/install a second time is idempotent and does not create unsafe changes;
- existing file conflicts are classified as conflict or manual-review and are not overwritten by default;
- V1 failure cleanup behavior is tested only as needed for safe local install attempts.

Full rollback lifecycle tests, cross-version update migration tests, automatic CI installation tests, and automated Codex/Claude cross-agent smoke tests are deferred. Keep cross-agent expectations as documented verification notes unless a small static/schema check is needed for the MCP/adapter contract.

### 109.5. Define MCP wrapper contract and evidence handoff

**Status:** pending  
**Dependencies:** None  

Document the MCP wrapper contract over the CLI/library core, including tools, resources, prompts, schemas, apply gates, evidence outputs, and deferred production-server follow-up tasks.

**Details:**

Keep MCP as documentation/contract work for Task 109 V1. Do not implement a production MCP server here.

The contract should document how MCP clients would call the same deterministic installer library used by scripts/codex-task. It should cover:
- tools such as foundation.inspect, foundation.plan_install, foundation.install, foundation.verify, foundation.status, foundation.plan_update, foundation.update, foundation.rollback, foundation.list_profiles, and foundation.explain_profile, clearly marking which are V1-backed by the CLI prototype and which are future/deferred;
- resources such as foundation://contract/current, foundation://profiles, foundation://profiles/{name}, foundation://install-plan/latest, foundation://verification/latest, foundation://limitations, foundation://managed-files, and foundation://project/status;
- prompts such as foundation.bootstrap_new_project, foundation.migrate_existing_project, foundation.verify_runtime, foundation.prepare_agent_session, foundation.close_agent_session, foundation.install_claude_adapter, and foundation.install_codex_adapter;
- input/output schemas aligned with the manifest/profile/install-plan schemas from 109.2;
- read-only versus mutating behavior, explicit apply gates for mutating operations, report paths, changed/skipped/conflict path reporting, and refusal semantics.

Handoff must identify follow-up tasks for the production MCP server, expanded profiles, update/rollback hardening, packaging/distribution, optional CI installation templates, and hosted/service infrastructure if those remain desired after V1.

### 109.1. Document installer architecture and distribution decision

**Status:** done
**Dependencies:** None

Capture the CLI/library core plus optional MCP wrapper architecture, alternatives considered, chosen decision, risks, and acceptance gates in tracked design documentation.
