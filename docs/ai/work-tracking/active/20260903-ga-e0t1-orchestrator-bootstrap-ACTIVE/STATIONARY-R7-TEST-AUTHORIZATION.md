# ga-fjoi R7 — disposable test-dependency authorization

Recorded 2026-09-04. The operator replied "i give you permission." to the exact
request permitting the existing tests to download/install their declared
dependencies only inside disposable `/tmp` virtualenvs, with no system/user
package-environment changes or live activation. This resolves only the test
authority HOLD recorded in `reports/ga-fjoi-cache-association-r7-verification-HOLD.json`;
that refusal, partial results and all earlier evidence remain preserved.

Before execution, the current project descriptor/registry, branch, Bead ownership
and all 23 R7 source hashes were reverified. No `PIP_TARGET`, `PIP_PREFIX` or
`PIP_USER` override was present. Supported workflow verification passed at
2026-09-04T16:56:28Z. The existing package test explicitly uses
`tmp_path/aegis-venv/bin/python -m pip`, not the host or user Python environment.

Authorized rerun, with new output path (no failed evidence overwritten):

```sh
PYTHONDONTWRITEBYTECODE=1 PIP_CACHE_DIR=/tmp/ga-fjoi-cache-association-r7-pip-cache python3 -m pytest -p no:cacheprovider tests/claude_adapter tests/meta_workflow_guard -q --maxfail=1 --junitxml=/tmp/ga-fjoi-cache-association-r7-full4.xml
```

This does not authorize system packages, global/user environment installation,
source changes, new clients, rig lifecycle, activation or bypass of any test.
Independent Fable review remains required before runtime activation. No R7
commit, push or merge is part of this test-boundary resolution.
