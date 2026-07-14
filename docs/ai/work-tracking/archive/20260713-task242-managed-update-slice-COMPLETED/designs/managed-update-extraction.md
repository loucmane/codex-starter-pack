# Task 242 Managed-Update Extraction

## Objective

Extract the deterministic managed-asset planning, rendering assembly, and update-safety
slice from `scripts/_aegis_installer.py` without changing installed bytes, operation
classification, source-root behavior, packaged behavior, or target-repository state.

## Boundary

`aegis_foundation.managed_update` is the authoritative implementation for:

- the `Asset` value type;
- shared and client-adapter asset-set assembly;
- target-aware entrypoint and Codex hook materialization;
- manifest checksum parsing and prior-byte recovery;
- fail-closed create/modify/skip/conflict/manual-review classification; and
- deterministic operation summaries.

The installer remains the compatibility adapter for:

- profile/path constants and enabled-agent policy;
- concrete Markdown, JSON, shell-dispatcher, and hook renderers;
- project JSON/schema I/O;
- install/update orchestration and report emission; and
- legacy private names used by tests and downstream callers.

The core imports only the Python standard library. It never imports the installer, writes a
target, or owns runtime state. `scripts/_aegis_installer.py` re-exports `Asset` and retains thin
private wrappers so existing source-root, installed-script, MCP, and package callers do not
change invocation shape.

## Measured Surface

| Surface | Before | After | Delta |
|---|---:|---:|---:|
| `scripts/_aegis_installer.py` | 13,651 lines | 13,325 lines | -326 lines |
| authoritative managed-update module | 0 lines | 777 lines | +777 lines |
| installed target migrations | 0 | 0 | 0 |

The packaged installer mirror is copied mechanically from the live installer and must remain
byte-identical. The new Python module is included by ordinary package discovery; installed
repositories do not receive another mutable state copy.

## Golden Consumers

`tests/fixtures/aegis/managed-update-golden-plans.json` stores deterministic operation digests
and summaries for three representative contracts:

- **Codex:** fresh Codex-only install with project-authored `CODEX.md` and hooks; 26 creates,
  two safe structural merges, and no manual review.
- **HP-Fetcher:** Claude-only installed target with one known-prior gate asset; two safe
  modifications, 30 skips, and workflow-state failures treated only as update evidence.
- **Blog:** multi-agent installed target with project-authored entrypoints/hooks and one
  known-prior ledger asset; two safe modifications, 40 skips, and no loss of project hooks.

The tests also require dry-run byte preservation, source/package generated-byte parity,
source/package plan parity, and fail-closed refusal of a locally divergent managed asset.

## Safety Invariants

- A current file matching its recorded checksum may be upgraded.
- A source-backed managed file whose prior bytes cannot be recovered requires manual review.
- A file diverging from its recorded prior bytes requires manual review.
- Project-owned entrypoint text and unrelated Codex hooks are structurally preserved.
- Seed-once configuration remains owner-maintained.
- Apply orchestration and rollback semantics remain in the installer and are unchanged.

## Compatibility Finding

The first extraction bypassed a private legacy-checksum monkeypatch used by an existing
regression. The final adapter passes installer-level baseline and source-path resolvers into the
core, preserving that override seam while leaving the default algorithm authoritative in the
new module.

## Rollback

Revert the Task 242 commit. No installed manifest schema, target file layout, runtime pointer,
ledger schema, or migration has changed, so rollback requires no downstream operation.
