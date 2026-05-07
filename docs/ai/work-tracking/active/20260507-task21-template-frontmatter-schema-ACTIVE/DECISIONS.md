# Decisions

- 2026-05-07 16:22 CEST — Keep Task 21 inside the existing policy-driven metadata guard path. Add a permanent frontmatter JSON Schema contract and typed validation, but do not create a parallel resolver, broad migration CLI, or template batch rewrite in this task.
- 2026-05-07 16:43 CEST — Fix CI by installing `[project].dependencies` from `pyproject.toml` in guard workflows rather than duplicating dependency names in workflow YAML or removing schema-backed imports from `scripts/codex-guard`.
- 2026-05-07 — _Pending_ — capture decisions with context.
