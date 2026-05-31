# Fresh `/tmp` Private GitHub Smoke

## Source

Private GitHub source:

```text
git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution
```

Resolved commit during smoke:

```text
5afc9752494ee5812fca8169da75a2420d89e27f
```

Target:

```text
/tmp/aegis-task134-private-fresh-project
```

## Commands And Results

1. Generated Codex registration through private source.

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis mcp generate-registration --client codex --source-mode private-github --github-ref feat/task-134-private-github-distribution
```

Result: PASS. Rendered command used `uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution aegis-mcp-server --default-target-dir . --transport stdio`.

2. Described MCP server config through private source.

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis-mcp-server --default-target-dir /tmp/aegis-task134-private-github-smoke --describe-config
```

Result: PASS. `asset_origin` was `package`; `source_root` resolved under `/tmp/uv-cache-task134-private/.../site-packages/aegis_foundation/assets`.

3. Initialized fresh target with Codex adapter.

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis init --target-dir . --primary-agent codex --agent codex
```

Result: PASS. Install applied 23 creates, verification passed, no Claude reload marker required for Codex-only install.

4. Started local tracked work.

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis start --target-dir . "Private GitHub smoke task"
```

Result: PASS. Created branch `feat/task-1-private-github-smoke-task` and active workflow state.

5. Logged scope, created `smoke.md`, logged implementation, ran `test -f smoke.md`, wrote task verification, and logged verification.

Result: PASS. All logs were explicit `codex:*` logs with no pending tracking queue.

6. Ran strict verification.

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis verify --target-dir . --strict
```

Result: PASS. Strict verification passed with 21 checks, 0 required failures, 1 unsupported policy-only check.

7. Ran closeout.

Initial dry-run failed only on placeholder handoff semantic gates. `aegis handoff repair --target-dir .` repaired them, then final closeout passed:

```text
Aegis closeout: PASSED
mode: final
failed_required: 0
warnings: 0
pending_tracking: 0
closeout_report: .aegis/reports/closeout-report.json (written)
```

8. Ran doctor.

```text
Aegis doctor: healthy (completed_closeout)
Checks: 18 total, 0 required failures, 0 warnings
Repair plan: 0 safe, 0 manual-review
```

## Verdict

PASS. A fresh project can install and operate Aegis from the private GitHub branch using `uvx --from git+ssh://...`, without PyPI/TestPyPI and without a local source checkout.
