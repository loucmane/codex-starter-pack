# Task 249 Design — Pre-adapter Codex Update Migration Order

## Reproduced failure

Blog was installed before Task 248 promoted Codex hooks to a managed adapter. Its
manifest legitimately enables Codex but does not yet list `.codex/hooks.json` or the
new Codex hook gate IDs. `aegis update` correctly previews the migration. On apply,
however, `project_update` calls `runtime_update(..., apply=True)` before `install`.
`runtime_update` validates the old manifest with the new source schema and fails before
the reviewed installer migration can produce a current manifest.

## Invariants

1. A divergent operator-owned `.codex/hooks.json` remains a manual-review refusal and
   causes zero update writes.
2. Direct `aegis runtime update` remains strict; Task 249 does not add a permissive schema
   fallback or trust a target-controlled schema mirror.
3. A safe project update installs only the already-reviewed managed plan, producing a
   current-schema manifest, before refreshing runtime metadata.
4. If managed install refuses or fails, the runtime pointer and manifest runtime metadata
   do not advance.
5. Final strict verification, capsule compilation, idempotence, and source/package parity
   remain mandatory.

## Selected change

Within `project_update(..., apply=True)`, call `install(..., apply=True)` before
`runtime_update(..., apply=True)`. The preview and unsafe-operation checks remain ahead
of both calls. The installer already renders the complete current manifest from the
reviewed baseline while preserving existing runtime and verification records. Once that
manifest validates and is written, the existing strict `runtime_update` can safely update
the pointer and source metadata.

This is narrower and safer than teaching `runtime_update` to accept manifests that fail
the current schema. It also improves failure atomicity: a managed install refusal can no
longer leave the project pointed at a newer runtime.

## Regression matrix

- Codex-only and multi-agent pre-adapter manifests with no hook file migrate successfully.
- The final manifest contains the managed hook, all Codex hook gate IDs, and validates
  against the current schema.
- A second update preview is idempotent.
- A divergent unowned hook remains byte-identical and causes refusal before runtime or
  manifest changes.
- Source and packaged installer copies remain byte-identical.
