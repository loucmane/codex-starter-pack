---
id: codex-readiness
title: Codex Readiness Checklist
type: critical-enforcement
status: stable
---

# Codex Readiness Checklist

Use this module before deep-work tasks to confirm the Codex runtime matches expectations.

## 1. Session Context
- Run `/status` or review the turn context to confirm:
  - Sandbox mode: `workspace-write` (unless the task explicitly requires read-only).
  - Approval policy: `on-request`.
  - Network access: `true` when the plan depends on HTTP/MCP calls.
- If any setting is off, pause and request alignment before proceeding.

## 2. Tooling Inventory
- Default tools: `shell`, `update_plan`, `view_image`.
- Optional tools in this project:
  - `web_search` (enabled via `.codex/config.toml`).
  - Registered MCP servers listed under `[mcp_servers]` in `.codex/config.toml`.
- Record unavailable tools explicitly in the plan so expectations stay clear.

## 3. Filesystem & Workspace
- Confirm current working directory (expect `/home/loucmane/codex`).
- Verify required folders exist: `templates/`, `.codex/`, `scripts/`, any task-specific directories.
- If you need write access to new paths, note the request in the plan.

## 4. Authentication & Secrets
- Ensure required env vars (e.g., `OPENAI_API_KEY`) are present for the configured model provider.
- For MCP servers, verify credential files referenced in `.codex/config.toml` are available.

## 5. Wrapper Confirmation
- If using `codex-wrapper`, run `codex --dry-run -- resume` (or equivalent) to validate:
  - `CODEX_HOME` points at this project’s `.codex/` directory.
  - `auth.json` linking mode is correct (symlink vs copy).
  - Agent catalog status is understood (warning noted or file supplied).

Document any discrepancies before continuing with ULTRATHINK planning. EOF

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/codex-readiness.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
