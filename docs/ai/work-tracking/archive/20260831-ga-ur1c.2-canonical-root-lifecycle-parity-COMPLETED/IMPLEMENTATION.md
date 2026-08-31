# Bead ga-ur1c.2 Enforce canonical Gas City Operations root and lifecycle parity – Implementation Notes

## Planned Workstreams

1. Add RED coverage for historical main/worktree blocking, canonical IDLE/ACTIVE acceptance, cross-adapter hook rendering, scoped config transformation, idempotence, and rollback.
2. Add `config/root-policy.json` and `scripts/root_policy.py`; invoke it before project registry/descriptor resolution.
3. Add `scripts/install_root_policy.py` with atomic user-runtime, Codex/Claude hook, Codex trust, Claude MCP source, evidence, non-interference, and rollback handling.
4. Update the migration/naming/workflow contracts and both adapters to name the same boundary.
5. Run focused and full validation, sign/publish/merge the exact candidate, then apply only the merge-bound user-level transition and prove cold-start behavior.

## Current State

- RED captured: 7 missing-surface failures before implementation.
- GREEN focused: evaluator, installer, project-context, and migration tests passing.
- Full regression: 2,395 passed and 21 documented skips; hosted Python 3.11–3.14 and every policy/evidence check passed.
- PR #335 merged exact signed head `5df17ed4…` as merge `0e9c4397…`; merge tree `8fb4b603…` is byte-identical.
- Merge-bound install and idempotent reapply passed with evidence under `~/.local/state/gas-city-workflow/root-policy-installs/`; historical checkout and worktree inventory hashes are unchanged.
