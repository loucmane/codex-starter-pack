# Findings

- 2026-05-07 16:22 CEST — Task 21 overlaps with completed Task 91 metadata standardization. Existing guard enforcement already requires `title`, `type`, and `status` for policy-governed template files; the remaining current-state gap is schema-backed typed validation of those frontmatter blocks.
- 2026-05-07 16:32 CEST — The Serena MCP `write_memory` call was blocked by stale safety context from an earlier read-only phase in the conversation. The Task 21 memory was preserved as `.serena/memories/2026-05-07_task21_template_frontmatter_schema.md` and logged in tracker/session.
- 2026-05-07 16:43 CEST — PR #41 CI exposed that guard workflows were not installing project dependencies from `pyproject.toml`; local validation passed only because the workstation environment already had `pyyaml` and `jsonschema` installed.
- 2026-05-07 — _Pending_ — document new findings here.
