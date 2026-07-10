# Managed Update Divergence Contract

## Problem

An Aegis manifest currently records ownership by path only. That proves Aegis installed a
file at some point; it does not prove the bytes still equal the last installed version. As a
result, `aegis update` can label a locally hardened governance asset as a safe managed upgrade
and silently replace behavior that the target repository relies on.

HP-Blog Task 56 reproduced this with `scripts/codex-guard`: the update preview was mechanically
safe, but applying it removed completed-archive tracker resolution and failed all five target
regressions.

## Contract

1. New manifests record a SHA-256 checksum for every materialized managed asset.
2. A changed managed file is safe to upgrade only when its current bytes match the recorded
   installed checksum.
3. Legacy manifests without checksums recover the expected prior bytes from the manifest's
   recorded `runtime.source_root` and `runtime.source_commit` for source-backed assets.
4. A current file that differs from both the prior expected bytes and the proposed bytes is a
   local semantic divergence and requires manual review.
5. A source-backed asset whose legacy baseline cannot be established fails closed to manual
   review.
6. Seed-once configuration, generated runtime dispatchers, and marker-merged entrypoints keep
   their existing specialized merge/ownership semantics.
7. Update apply must classify and write against the same pre-update manifest baseline even when
   the runtime pointer is advanced first.

## Guard Parity

The canonical `codex-guard` must resolve work tracking in this order:

1. exactly one active `*-ACTIVE/TRACKER.md`, when present;
2. otherwise, only a `status=completed` path from `.aegis/state/current-work.json` that resolves
   under the configured archive root and ends in `-COMPLETED`.

Both active and archived tracking changes receive the same document validation. Invalid or
ambiguous state fails closed.

## Acceptance Evidence

- Five tracker-resolution regressions cover active preference, absent/empty active roots,
  archive containment, and terminal suffix enforcement.
- Installer tests distinguish pristine stale assets from locally diverged assets.
- A legacy-manifest test proves source-commit baseline recovery.
- An update apply test proves the original baseline survives runtime-pointer advancement.
- A second preview after a successful update contains no managed modifications.
