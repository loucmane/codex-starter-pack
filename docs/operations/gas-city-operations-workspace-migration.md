# Gas City Operations repository and workspace migration

Status: prepared, not executed. This document and its auditor authorize no
GitHub rename, clone, consumer rewrite, worktree removal, or workspace cleanup.

## Objective

- Rename `loucmane/codex-starter-pack` to
  `loucmane/gas-city-operations`.
- Establish a fresh canonical clone at `/home/loucmane/gas-city-ops`.
- Keep `/home/loucmane/codex` intact as a compatibility/evidence root until a
  later retirement audit proves it has no active consumers.
- Keep Aegis Foundation, Gas City, Gas City Workflow, and `codex/*` named as
  specified in `repository-and-product-naming.md`.

## Superseded historical prerequisite

The retained design bead `ga-i7z` depended on `ga-2oe` PASS. `ga-2oe` closed
FAIL and must remain an honest historical failure. Its intended safety
precondition is superseded append-forward by the later PASS evidence in:

- `ga-vqm2`: managed-worker recovery, upgrades, reboot, project proof cycles,
  future-project onboarding, live Obsidian projection, and quiescence;
- `ga-yu82`: native Beads and privileged broker capability alignment;
- `ga-0szv`: managed-signing onboarding and broker bundle behavior.

The active implementation bead is `ga-ejrm`. The historical `ga-i7z` record is
not rewritten or reused as a success.

## Preconditions for the attended cutover

1. `ga-ejrm` source changes are merged at an exact signed head and tree.
2. All project rigs are suspended and no worker, shell, MCP server, service, or
   automation is using the old checkout or a nested worktree.
3. The old root and every discovered owning repository have clean, reconciled
   `git worktree list --porcelain` inventories.
4. `scripts/gas-city-operations-migration inventory` has captured exact heads,
   trees, remotes, worktrees, and active/historical legacy consumers.

For the source checkout, use the tracked-only inventory so disposable caches,
untracked build products, and preserved linked worktrees cannot masquerade as
active migration consumers:

```bash
SOURCE_WORKTREE=/home/loucmane/codex/worktrees/<exact-clean-worktree>
scripts/gas-city-operations-migration inventory \
  --repository "$SOURCE_WORKTREE" \
  --scan-root "$SOURCE_WORKTREE" \
  --phase pre-rename \
  --tracked-only
```

Filesystem inventory remains available for an explicitly named external file
or root. It prunes nested Git metadata, virtual environments, package caches,
and generated tool/cache directories at every depth.
5. A single attended authorization names the GitHub rename, exact source head,
   fresh-clone destination, allowed active-consumer updates, and stop rules.

## Cutover procedure

1. Freeze and preserve the pre-rename inventory JSON.
2. Rename the repository using GitHub's supported repository-rename operation;
   record before/after API evidence and the redirect behavior.
3. Fresh-clone the renamed repository into `/home/loucmane/gas-city-ops`.
   Never rename or move `/home/loucmane/codex` in place.
4. Verify exact head, tree, signatures, remote, default branch, submodules, and
   worktree inventory in the new clone.
5. Update active repository URLs and absolute-path consumers one at a time.
   Do not rewrite archived plans, sessions, reports, receipts, Taskmaster
   history, or other retained evidence.
6. Run the auditor in tracked-only `post-rename` mode from the fresh canonical
   clone. It must report no unallowlisted active legacy consumer, the canonical
   origin, the canonical clone, and the intact legacy root. Scan explicitly
   registered external consumers separately in filesystem mode.
7. Verify Aegis package/MCP startup, Gas City Workflow context resolution,
   Beads/readiness/guard/closeout behavior, CI, and Obsidian publication from
   the new clone before declaring it canonical.
8. Record a digest-backed old-to-new mapping. Leave the old checkout intact.

## Rollback and stop rules

Before old-root retirement, rollback is to point active consumers back at the
still-intact old checkout and leave the new clone inert. Stop on head/tree or
signature drift, dirty/unowned worktrees, unknown consumers, failed Aegis or
plugin startup, missing evidence, CI failure, or any need to overwrite/delete
unrelated state. Retiring the old root or any worktree requires a later,
separately reviewed gate.
