# Task 123 Artifact Build Evidence

Date: 2026-05-25

## Environment

- Branch: `feat/task-123-aegis-release-candidate-global-mcp-install-proof`
- Python: `Python 3.12.3`
- uv: `uv 0.7.8`
- Package: `aegis-foundation`
- Version: `0.1.0`

## Build Command

```bash
uv build --sdist --wheel --out-dir /tmp/aegis-task123-dist-clean
```

The first build surfaced a release-quality issue: generated `__pycache__` bytecode files under `aegis_foundation/assets/` were included in the wheel/sdist. The fix removed those generated files and added explicit packaging exclusions in `MANIFEST.in` and `pyproject.toml`.

## Clean Artifacts

```text
/tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0.tar.gz
/tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0-py3-none-any.whl
```

## SHA-256

```text
ef201bb691d49a025989541b27d0ac1f33a56762360e60fa772c2fa57cd4e5d6  /tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0.tar.gz
dcfb8ad153d4005cf1ad668e768ccb8fb1b2614fbf1448f0f6f51d5be472db0b  /tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0-py3-none-any.whl
```

## Required Artifact Members

Wheel inspection confirmed these required files:

```text
aegis_foundation/cli.py
aegis_foundation/assets/.claude/scripts/gate_lib.py
aegis_foundation/assets/docs/aegis/live-acceptance-matrix.md
aegis_foundation/assets/docs/aegis/mcp-client-setup.md
aegis_foundation/assets/scripts/_aegis_installer.py
aegis_foundation/assets/scripts/codex-task
aegis_mcp/server.py
```

Sdist inspection confirmed matching required files:

```text
aegis_foundation-0.1.0/aegis_foundation/cli.py
aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/gate_lib.py
aegis_foundation-0.1.0/aegis_foundation/assets/docs/aegis/live-acceptance-matrix.md
aegis_foundation-0.1.0/aegis_foundation/assets/docs/aegis/mcp-client-setup.md
aegis_foundation-0.1.0/aegis_foundation/assets/scripts/_aegis_installer.py
aegis_foundation-0.1.0/aegis_foundation/assets/scripts/codex-task
aegis_foundation-0.1.0/aegis_mcp/server.py
```

## Bytecode Cache Check

Commands inspected both artifacts for `__pycache__` and `.pyc` entries. The clean rebuild produced no such entries.

## Current Limitation

The artifacts are local release-candidate artifacts only. No TestPyPI/PyPI upload was run.

