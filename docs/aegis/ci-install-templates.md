# Aegis CI Install Templates

These templates are copyable starting points for projects that consume Aegis Foundation. Pin public package versions in automation once releases are published.

## GitHub Actions - Pinned Public Package

```yaml
name: Aegis Verify

on:
  pull_request:
  push:
    branches: [main]

jobs:
  aegis-verify:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.11", "3.12"]
        install-method: [pip, uvx, pipx]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Aegis with pip
        if: matrix.install-method == 'pip'
        run: |
          python -m pip install --upgrade pip
          python -m pip install aegis-foundation==0.1.0
          aegis --version
      - name: Verify Aegis with uvx
        if: matrix.install-method == 'uvx'
        run: |
          uvx --from aegis-foundation==0.1.0 aegis --version
          uvx --from aegis-foundation==0.1.0 aegis inspect --target-dir .
          uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
          uvx --from aegis-foundation==0.1.0 aegis plan-install --target-dir . --primary-agent claude --agent claude
          uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
      - name: Verify Aegis with pipx
        if: matrix.install-method == 'pipx'
        run: |
          python -m pip install pipx
          pipx run --spec aegis-foundation==0.1.0 aegis --version
          pipx run --spec aegis-foundation==0.1.0 aegis inspect --target-dir .
          pipx run --spec aegis-foundation==0.1.0 aegis status --target-dir .
          pipx run --spec aegis-foundation==0.1.0 aegis plan-install --target-dir . --primary-agent claude --agent claude
          pipx run --spec aegis-foundation==0.1.0 aegis verify --target-dir .
      - name: Verify Aegis with pip-installed command
        if: matrix.install-method == 'pip'
        run: |
          aegis inspect --target-dir .
          aegis status --target-dir .
          aegis plan-install --target-dir . --primary-agent claude --agent claude
          aegis verify --target-dir .
      - name: Verify MCP startup
        run: |
          uvx --from aegis-foundation==0.1.0 aegis-mcp-server --default-target-dir . --describe-config
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: aegis-reports-${{ matrix.os }}-${{ matrix.python-version }}-${{ matrix.install-method }}
          path: |
            .aegis/reports/install-plan.json
            .aegis/reports/install-report.json
            .aegis/reports/verification-report.json
```

## GitHub Actions - Local Wheel Release Candidate

```yaml
name: Aegis Local Wheel Smoke

on:
  workflow_dispatch:

jobs:
  local-wheel:
    strategy:
      matrix:
        os: [ubuntu-latest]
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Build release candidate
        run: |
          uv build --sdist --wheel --out-dir dist
          aegis certify-release --source-dir . --dist-dir dist --report-file reports/aegis-release-certification/certification-report.json --skip-build --skip-smoke
          python -m pip install dist/aegis_foundation-0.1.0-py3-none-any.whl
          aegis --version
      - name: Exercise local wheel with uvx and pipx
        run: |
          uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .
          uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis status --target-dir .
          uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis verify --target-dir .
          python -m pip install pipx
          pipx run --spec ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .
          pipx run --spec ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis status --target-dir .
          pipx run --spec ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis verify --target-dir .
      - name: Exercise local wheel MCP startup
        run: |
          uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --describe-config
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: aegis-local-wheel-reports-${{ matrix.python-version }}
          path: |
            dist/*.whl
            dist/*.tar.gz
            reports/aegis-release-certification/certification-report.json
            .aegis/reports/install-plan.json
            .aegis/reports/verification-report.json
```

## Editable Development Path

Use this only for development branches of Aegis itself:

```bash
python3 -m venv .venv-aegis
.venv-aegis/bin/python -m pip install -e /path/to/codex
aegis --version
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis verify --target-dir .
aegis-mcp-server --default-target-dir . --describe-config
```

## Required Evidence

CI jobs must preserve:

- `.aegis/reports/install-plan.json`
- `.aegis/reports/install-report.json`
- `.aegis/reports/verification-report.json`
- `reports/aegis-release-certification/certification-report.json`
- package build logs
- checksum/signing/provenance logs for publishing jobs
- MCP `--describe-config` output

Do not treat prompt text or private agent memory as release evidence.
