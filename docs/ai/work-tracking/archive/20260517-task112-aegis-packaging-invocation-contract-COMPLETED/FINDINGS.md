# Findings

- 2026-05-17 — Task 111 proved cross-project install behavior, but its CLI helper still used `cwd=REPO_ROOT`. Task 112 must explicitly test commands launched from an external project `cwd` to prove the adoption contract.
- 2026-05-17 — `pyproject.toml` has `[tool.uv] package = false` and no console scripts. A package-style Aegis command is therefore not defined yet, even though dependencies and importable MCP code already exist.
- 2026-05-17 — MCP configuration already has the right external hooks through `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR`; Task 112 should document and test those instead of replacing them.
- 2026-05-17 — The install-plan schema intentionally models `target_root` as a repository-relative path and existing schema coverage expects `"."`. The external-cwd test therefore proves target resolution through absolute `inspect`/`install`/`verify` payloads and created target files, while preserving the install-plan schema contract.
