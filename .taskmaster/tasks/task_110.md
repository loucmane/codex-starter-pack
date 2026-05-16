# Task ID: 110

**Title:** Build Aegis MCP Installer Server

**Status:** in-progress

**Dependencies:** 62 ✓, 109 ✓

**Priority:** medium

**Description:** Create the production Aegis MCP server that wraps the deterministic Task 109 Aegis installer core and exposes install, verify, profile, resource, and prompt surfaces to agents through the `aegis` namespace. The server must reuse `scripts/_aegis_installer.py`, preserve the `.aegis/` safety contract, and provide a local MCP smoke path that does not shell through `scripts/codex-task`.

**Details:**

Implement this as the follow-up production server explicitly deferred by Task 109. Use the Task 109 artifacts as the source of truth: `scripts/_aegis_installer.py`, `schemas/aegis/foundation-manifest.schema.json`, `schemas/aegis/profile.schema.json`, `schemas/aegis/install-plan.schema.json`, and `docs/ai/work-tracking/archive/20260515-task109-foundation-installer-mcp-COMPLETED/designs/aegis-mcp-wrapper-contract.md`. Also consume the Task 62 agent compatibility matrix at `templates/registry/agent-compatibility-matrix.json` where prompts or guidance need to explain supported agents, fallback behavior, or compatibility limits.

Recommended implementation shape:
- Add an importable MCP module such as `aegis_mcp/server.py` plus a thin executable entrypoint such as `scripts/aegis-mcp-server`. Keep protocol registration, resource handling, prompt templates, and structured error mapping in the MCP module; keep deterministic install behavior in `scripts/_aegis_installer.py`.
- Use a stdio MCP server transport suitable for project-local `.mcp.json` configuration. If the Python MCP SDK is introduced, add it deliberately to `pyproject.toml` with the narrowest dependency needed and keep the server factory testable without launching a long-running process.
- Provide startup configuration for `source_root` and a default `target_dir`, both defaulting to the current repository when omitted. Tools must still require explicit `target_dir` for install/apply flows so agents cannot mutate an implicit repository by accident.
- Add or document a project-local `.mcp.json` entry for `aegis` that runs the new entrypoint, while preserving existing `task-master-ai` and `serena` entries.

Register these V1-backed MCP tools and map each directly to the core functions already present in `scripts/_aegis_installer.py`:
- `aegis.inspect` -> `inspect_project(target_dir, profile=...)`; read-only; returns the inspect payload without writing `.aegis/`.
- `aegis.plan_install` -> `plan_install(target_dir, source_root=..., profile=..., primary_agent=..., agents=...)`; read-only; validates output against `schemas/aegis/install-plan.schema.json`; must require explicit `primary_agent` and `agents` and must not silently choose the default.
- `aegis.install` -> `install(target_dir, source_root=..., profile=..., primary_agent=..., agents=..., apply=...)`; mutating only when `apply` is true; reject missing or false `apply` as a structured dry-run/refusal response rather than silently applying; preserve core refusal behavior for `manual-review` and `conflict` operations.
- `aegis.verify` -> `verify(target_dir, source_root=...)`; treat as mutating because V1 writes `.aegis/reports/verification-report.json` and updates manifest verification state; require an explicit target and an acknowledgement field such as `acknowledge_report_write: true`.
- `aegis.list_profiles` -> `list_profiles(source_root=...)`; read-only; must expose `generic` in V1.
- `aegis.explain_profile` -> `explain_profile(profile, source_root=...)`; read-only; validates output against `schemas/aegis/profile.schema.json`.

Do not implement `aegis.status`, `aegis.plan_update`, `aegis.update`, or `aegis.rollback` as production tools unless deterministic core support is added first. If they remain visible in docs, mark them as future/deferred and do not register mutating stubs that can be mistaken for working operations.

Define formal MCP input schemas that mirror the Aegis core constraints from `scripts/_aegis_installer.py`: `profile` defaults only to `generic`; `primary_agent` is constrained to `claude`, `codex`, `gemini`, `multi`, or `none`; `agents` is a unique list of `claude`, `codex`, and `gemini`; `install` requires `target_dir`, `profile`, `primary_agent`, `agents`, and `apply`; `verify` requires `target_dir` and the explicit report-write acknowledgement. Output payloads should be the core JSON reports plus MCP wrapper metadata, not a second schema invented by the server.

Expose read-only `aegis://` resources backed by target `.aegis/` state, current schemas, and the server session cache:
- `aegis://manifest/current` backed by `.aegis/foundation-manifest.json`.
- `aegis://contract/current` backed by `.aegis/contract.md`.
- `aegis://schemas/foundation-manifest`, `aegis://schemas/profile`, and `aegis://schemas/install-plan` backed by `schemas/aegis/*.schema.json`.
- `aegis://profiles` backed by `list_profiles`.
- `aegis://profiles/{name}` backed by `explain_profile`.
- `aegis://install-plan/latest` backed by `.aegis/reports/install-plan.json` when present or the most recent in-process plan generated by `aegis.plan_install`.
- `aegis://verification/latest` backed by `.aegis/reports/verification-report.json`.
- `aegis://limitations` backed by manifest gates with `unsupported` or `policy` enforcement plus deferred-tool notes from the Task 109 contract.
- `aegis://managed-files` backed by manifest `managed_files`.
Missing target files must return structured `not_installed` or `not_available` payloads, not stack traces, and resources must never create or update `.aegis/` files.

Expose prompts that guide agents without acting as gates or evidence. At minimum implement `aegis.bootstrap_new_project`, `aegis.migrate_existing_project`, `aegis.verify_runtime`, `aegis.prepare_agent_session`, and `aegis.close_agent_session`. The prompt text should steer agents through `inspect -> plan_install -> user approval -> install -> verify`, explain explicit primary/additional agent selection, call out required gates from the manifest/profile, distinguish mechanical gates from policy-only limitations, and instruct agents to read resources such as `aegis://contract/current`, `aegis://limitations`, and `aegis://verification/latest`. Prompts must not claim success without tool evidence and must not tell agents to write `.aegis/` directly.

Map errors consistently. Wrap `AegisError`, schema validation failures, missing resources, refused installs, failed applies, and failed verifies into structured MCP responses such as `{ok: false, error: {code, message, status, details}}`, preserving the core report payload under `details` whenever possible. Do not expose Python tracebacks to MCP clients for predictable invalid input or unsafe-install cases. Preserve Task 109 cleanup semantics: failed apply attempts should surface the `cleanup` object returned by `install`.

Update documentation from the Task 109 wrapper design into implementation-facing docs for Task 110. Create active work-tracking/session/plan artifacts for Task 110, update the MCP contract documentation to describe the actual server entrypoint and test path, and fix any stale doc tests such as `tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py` so they reference the archived Task 109 contract or the new Task 110 implementation docs rather than the removed active Task 109 directory. Capture Taskmaster status changes and final evidence with the existing workflow commands, including a targeted generated task refresh rather than a broad `task-master generate` unless explicitly needed.

**Test Strategy:**

Add focused pytest coverage for both the in-process server registration layer and a local stdio MCP smoke path.

Required test coverage:
- Tool discovery lists exactly the V1-backed tools `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.list_profiles`, and `aegis.explain_profile`, and does not expose future mutating tools as active production tools.
- Resource discovery lists the required `aegis://` resources and resource templates, including manifest, contract, schemas, profiles, latest install plan, latest verification report, limitations, and managed files.
- Prompt discovery returns the safe workflow prompts and their content includes the required inspect/plan/approval/install/verify flow, explicit agent-selection guidance, gate/limitation language, and no direct `.aegis/` write instructions.
- `aegis.inspect` on an isolated temp repo reports `installed: false` and performs no writes.
- `aegis.plan_install` returns a schema-valid install plan, requires explicit `primary_agent` and `agents`, classifies create/skip/conflict/manual-review operations correctly, and leaves the target unchanged.
- `aegis.install` refuses missing or false `apply`, applies successfully when `apply: true` and inputs are explicit, writes `.aegis/foundation-manifest.json`, `.aegis/contract.md`, `.aegis/reports/install-plan.json`, and `.aegis/reports/install-report.json`, and does not write `.codex/foundation-manifest.json`.
- `aegis.verify` requires explicit acknowledgement of report writes, returns a structured verification report, writes `.aegis/reports/verification-report.json`, and fails structurally when required gate files are missing or non-executable.
- `aegis.list_profiles` and `aegis.explain_profile` expose and validate the V1 `generic` profile against `schemas/aegis/profile.schema.json`.
- Invalid profile names, unsupported agents, inconsistent `primary_agent`/`agents` combinations, missing target dirs where forbidden, and malformed inputs return structured MCP errors without Python tracebacks.
- Existing-file conflicts and conflicting `.aegis/foundation-manifest.json` are refused without overwriting user files, matching existing tests in `tests/meta_workflow_guard/test_aegis_installer.py` and `tests/meta_workflow_guard/test_aegis_installer_fixtures.py`.
- Install/apply idempotence is preserved: install, verify, second plan, second install, second verify should produce skip-only/no-unsafe behavior for empty-repo and basic-python-tool fixtures.
- Failed-apply cleanup is surfaced through the MCP layer by monkeypatching the core write path or equivalent injection and asserting created files/reports are removed as in the Task 109 fixture test.
- Resource reads before install return `not_installed` or `not_available`; after plan/install/verify they return the expected schema/report content and never mutate the target.
- A local smoke test starts the MCP server entrypoint over stdio, uses an MCP client to `list_tools`, call `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, and read at least one `aegis://` resource, proving an agent can use the contract without shelling directly into `scripts/codex-task`.

Suggested command coverage: run the new MCP server tests plus the existing Aegis tests, for example `python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py tests/meta_workflow_guard/test_aegis_mcp_server.py`. Final evidence should also include `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`, with evidence stored under the Task 110 work-tracking reports directory.

## Subtasks

### 110.1. Scaffold the Aegis MCP package, server factory, and stdio entrypoint

**Status:** done
**Dependencies:** None

Create the importable MCP server module and executable path that Task 110 will build on.

**Details:**

Add an `aegis_mcp/` package, likely `aegis_mcp/server.py`, with a testable server factory and a thin `scripts/aegis-mcp-server` stdio entrypoint. Reuse `scripts/_aegis_installer.py` as the deterministic core boundary, load `source_root` and `default_target_dir` startup configuration with repository defaults, and add the narrowest Python MCP SDK dependency to `pyproject.toml` because the current project dependencies only include click, jsonschema, pyyaml, and rich. Keep long-running stdio startup separate from in-process registration so pytest can inspect the server without launching a daemon.

### 110.2. Register V1-backed Aegis tools with formal input schemas

**Status:** pending
**Dependencies:** 110.1

Expose only the production-supported `aegis.*` tools and validate their inputs before calling the core.

**Details:**

Register exactly `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.list_profiles`, and `aegis.explain_profile`. Mirror core constraints discovered in `scripts/_aegis_installer.py`: profile defaults only to `generic`, `primary_agent` is one of `claude`, `codex`, `gemini`, `multi`, or `none`, and `agents` is a unique list drawn from `claude`, `codex`, and `gemini`. Require explicit `primary_agent` and `agents` for planning, require `target_dir`, `profile`, `primary_agent`, `agents`, and `apply` for install, and require `target_dir` plus `acknowledge_report_write: true` for verify. Do not register production `aegis.status`, `aegis.plan_update`, `aegis.update`, or `aegis.rollback` because the core has no deterministic support for them yet.

### 110.3. Wire tool handlers to installer core with schema checks and structured errors

**Status:** pending
**Dependencies:** 110.2

Map each MCP tool directly to the existing installer functions while preserving `.aegis/` safety behavior.

**Details:**

Call `inspect_project`, `plan_install`, `install`, `verify`, `list_profiles`, and `explain_profile` from `scripts/_aegis_installer.py` rather than reimplementing planning or writes. Validate `aegis.plan_install` output against `schemas/aegis/install-plan.schema.json` and `aegis.explain_profile` output against `schemas/aegis/profile.schema.json`. Treat `inspect`, `plan_install`, `list_profiles`, and `explain_profile` as read-only. Treat `install` as mutating only when `apply` is true, returning a structured dry-run/refusal response for missing or false `apply` instead of silently applying. Treat `verify` as mutating because the core writes `.aegis/reports/verification-report.json` and may update manifest verification state. Wrap `AegisError`, jsonschema failures, refused installs, failed applies, and failed verifies as `{ok: false, error: {code, message, status, details}}`, preserving report and cleanup payloads where the core returns them and avoiding Python tracebacks for predictable user errors.

### 110.4. Expose read-only Aegis resources and workflow prompts

**Status:** pending
**Dependencies:** 110.3

Implement the `aegis://` resource layer and agent prompts backed by target state, schemas, profiles, cache, and compatibility guidance.

**Details:**

Add resources for `aegis://manifest/current`, `aegis://contract/current`, `aegis://schemas/foundation-manifest`, `aegis://schemas/profile`, `aegis://schemas/install-plan`, `aegis://profiles`, `aegis://profiles/{name}`, `aegis://install-plan/latest`, `aegis://verification/latest`, `aegis://limitations`, and `aegis://managed-files`. Back them with `.aegis/foundation-manifest.json`, `.aegis/contract.md`, `schemas/aegis/*.schema.json`, `list_profiles`, `explain_profile`, report files, and the latest in-process plan cache. Missing files must return structured `not_installed` or `not_available` payloads and resources must never create or update `.aegis/`. Implement prompts `aegis.bootstrap_new_project`, `aegis.migrate_existing_project`, `aegis.verify_runtime`, `aegis.prepare_agent_session`, and `aegis.close_agent_session` that guide `inspect -> plan_install -> user approval -> install -> verify`, cite resources such as `aegis://contract/current`, `aegis://limitations`, and `aegis://verification/latest`, use `templates/registry/agent-compatibility-matrix.json` for supported-agent and fallback guidance, distinguish mechanical gates from policy-only limitations, and avoid claims of success without tool evidence.

### 110.5. Update Task 110 docs, MCP config guidance, and smoke coverage

**Status:** pending
**Dependencies:** 110.4

Document the implemented server path and add focused tests, local stdio smoke coverage, and workflow evidence.

**Details:**

Promote the archived Task 109 wrapper contract at `docs/ai/work-tracking/archive/20260515-task109-foundation-installer-mcp-COMPLETED/designs/aegis-mcp-wrapper-contract.md` into active Task 110 implementation-facing documentation that names the actual `scripts/aegis-mcp-server` entrypoint, local stdio test path, supported tools, deferred tools, resources, prompts, structured error format, and `.aegis/` safety contract. Add or document a project-local `.mcp.json` `aegis` entry while preserving the existing `task-master-ai` and `serena` entries. Fix stale doc tests such as `tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py`, which currently points at the removed active Task 109 directory and still expects deferred resources/prompts like `aegis://project/status` and adapter-install prompts. Capture Taskmaster progress and final evidence in the active Task 110 work-tracking folder and refresh only the targeted generated task file with the existing `generate-one` workflow.
