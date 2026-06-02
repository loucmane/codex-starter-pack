# Task 148 Verification Summary

## Scope

Task 148 adds an opt-in, inert reconcile mutation-candidate preview contract.
Default reconcile output remains observational. Candidate preview output is
operator-facing, report-only, and non-executable.

## Implementation Evidence

- `scripts/_aegis_installer.py` - `reconcile(..., preview_candidates=True)`
  emits `mutation_candidate_preview` with inert candidate and exclusion records.
- `aegis_foundation/cli.py` - adds read-only `--preview-candidates`.
- `scripts/codex-task` - adds read-only `--preview-candidates`.
- `aegis_mcp/server.py` - adds optional `preview_candidates` MCP argument.
- `docs/aegis/reconcile-mutation-candidate-preview-contract.md` - documents
  the Task 148 contract and enforcement tests.
- `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py`
  - verifies opt-in behavior, inert markers, no action-shaped data, no writer
  consumption, precision-corpus boundaries, and Taskmaster gate backstop.

## Verification Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py \
  tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py \
  tests/meta_workflow_guard/test_aegis_installer.py -k reconcile \
  tests/meta_workflow_guard/test_aegis_mcp_server.py -k reconcile \
  tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py
```

Result: `63 passed, 94 deselected in 25.73s`.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard
```

Result: `665 passed, 4 skipped in 94.60s`.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run black --check \
  scripts/_aegis_installer.py \
  aegis_foundation/cli.py \
  aegis_mcp/server.py \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_aegis_mcp_server.py
```

Result: `6 files would be left unchanged`.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py
```

Result: `All checks passed!`

```bash
cmp -s scripts/_aegis_installer.py \
  aegis_foundation/assets/scripts/_aegis_installer.py
cmp -s scripts/codex-task aegis_foundation/assets/scripts/codex-task
```

Result: both comparisons returned exit code `0`.

## Residual Risk

This task does not add mutation execution. The preview is intentionally inert.
Any future apply path must satisfy the Task 144 promotion contract, Task 145
side-effect oracle, Task 146 precision corpus, Task 147 rollback contract, and
the Task 148 no-consumer/inertness guarantees.
