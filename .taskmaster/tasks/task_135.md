# Task ID: 135

**Title:** Add Isolated Native MCP Registration Smoke Command for Aegis

**Status:** done

**Dependencies:** 118 ✓

**Priority:** high

**Description:** Add an Aegis smoke-test command that exercises native Claude and Codex MCP registration in temporary client homes/config directories, verifies the resulting registration, and emits structured evidence without mutating real user configuration.

**Details:**

Implement this as an additive smoke surface on top of the existing native MCP registration helpers in `aegis_foundation/mcp_registration.py`, package CLI wiring in `aegis_foundation/cli.py`, and the repo wrapper in `scripts/codex-task`. Add a command such as `aegis mcp smoke-registration` and mirror it under `python3 scripts/codex-task aegis mcp smoke-registration`.

Core behavior:
- Accept `--client` as repeatable or `all` with supported clients `claude` and `codex`; accept the same source-selection inputs already used by `RegistrationRequest`: `--source-mode`, `--package-spec`, `--package-version`, `--github-url`, `--github-ref`, `--artifact`, `--target-dir`, `--transport`, `--uv-cache-dir`, and `--uv-tool-dir`.
- Create a temporary smoke root with isolated homes/config dirs per client. For Claude, isolate `HOME`, `XDG_CONFIG_HOME`, and any Claude-specific config path the native CLI honors. For Codex, pre-create `CODEX_HOME` inside the smoke root before invoking `codex mcp add`, and ensure `HOME`/`XDG_CONFIG_HOME` also point at temporary locations.
- Do not write `.mcp.json`, Codex config files, `~/.claude`, `~/.codex`, or the caller's real `CODEX_HOME`. The command must fail tests if native clients observe real user home/config paths.
- Reuse `mcp_registration.client_argv()`, `execute_registration()`, `inspect_argv()`, and `verify_registration()` where practical, but extend the execution path to accept an environment override so smoke runs can supply isolated `env` to `subprocess.run` without shell execution.
- Run registration followed by verification for each requested client against the supplied source mode/ref. Verification should assert the same required fields as `verify_registration_output()`: server name `aegis`, `uvx`, expected `source_spec`, `aegis-mcp-server`, `--default-target-dir`, `--transport`, and registered UV env values.
- Treat missing native clients as a clean `skipped`/`missing_client` result for that client, not an unhandled exception. Include the attempted argv, rendered command, isolated paths, and reason in the JSON payload.
- Emit one structured JSON document to stdout with aggregate status (`passed`, `failed`, `skipped`, or `partial`), per-client results, source metadata, temp path metadata, and safety notes such as `isolated-client-home`, `real-user-config-not-touched`, and `codex-home-precreated` for Codex.
- Add optional `--report-file` for JSON evidence and optional `--runbook-file` or `--markdown-report-file` for a concise Markdown report, following existing `scripts/codex-task` report-file patterns. Ensure `--dry-run` or `--keep-temp` semantics are explicit if added; by default temp dirs should be cleaned after the run while still reporting their logical layout.
- Update `docs/aegis/mcp-client-setup.md` and the release verification matrix to document the smoke command as the isolated way to prove native registration without touching user config.

Implementation should preserve current native registration commands (`register`, `generate-registration`, `execute-registration`, `verify-registration`) and add the smoke workflow without changing their existing output contracts.

**Test Strategy:**

Add focused pytest coverage in `tests/meta_workflow_guard/test_aegis_native_mcp_registration.py` and release/documentation assertions where appropriate.

Required tests:
- Unit-test the smoke helper with fake `claude` and `codex` executables on `PATH`, similar to `_write_fake_native_client()`, proving registration and verification are invoked with exact argv and no shell.
- For Codex, assert the command pre-creates temporary `CODEX_HOME`, passes it to the subprocess environment, and never uses an existing real `CODEX_HOME` from the parent environment.
- For Claude, assert `HOME` and config-related env values point under the smoke temp root and that no repo or user config path is written.
- Test package, pinned, private-github with `--github-ref`, and source checkout modes by validating the expected `uvx --from` source spec appears in verification results.
- Test missing clients by monkeypatching `shutil.which`/`PATH` so one or both clients are absent; the command should return structured skipped/missing-client evidence cleanly and should not attempt fallback config-file writes.
- Test JSON stdout is parseable and stable, `--report-file` writes the same structured payload, and optional Markdown output summarizes aggregate and per-client outcomes.
- Add CLI tests for both `aegis mcp smoke-registration` and `python3 scripts/codex-task aegis mcp smoke-registration` to ensure package CLI and repo wrapper stay aligned.
- Run targeted tests: `python3 -m pytest tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_release_distribution.py`.
