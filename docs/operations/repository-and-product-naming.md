# Repository and product naming contract

This repository has four related identities. They are deliberately distinct:

| Surface | Canonical name | Stable machine identity |
| --- | --- | --- |
| Operations repository and operator workspace | **Gas City Operations** | `loucmane/gas-city-operations`, `/home/loucmane/gas-city-ops` |
| Portable workflow package and evidence gates | **Aegis Foundation** | `aegis-foundation`, `aegis_foundation`, `aegis`, `aegis-mcp-server` |
| Multi-project agent runtime | **Gas City** | `gc`, Gas City rigs, Gas City beads |
| Codex/Fable project-context plugin | **Gas City Workflow** | `gas-city-workflow` |

`codex-starter-pack` was the repository's bootstrap name. It is a legacy
repository alias, not the product name. `/home/loucmane/codex` is the legacy
canonical checkout and remains an evidence/worktree compatibility root until a
separate retirement audit reports no remaining consumers.

## Compatibility decisions

- Keep the `codex/*` branch namespace. It is a delivery/signing policy, not a
  repository-brand name.
- Keep the Aegis distribution, import packages, CLI, MCP server, schemas, and
  evidence vocabulary. Renaming those would break a portable product that is
  already correctly scoped.
- Keep Gas City as the runtime and Beads as the authoritative work ledger.
- Preserve historical plans, sessions, Taskmaster records, reports, receipts,
  and evidence byte-for-byte. A historical `codex-starter-pack` or
  `/home/loucmane/codex` citation is evidence, not an active consumer.
- New project onboarding uses the versioned `gas-city-workflow` plugin and its
  descriptor/registry contract; it does not copy this operations repository's
  old name into each project.

## Migration sequencing

The migration has a hard two-stage boundary:

1. **Prepare:** merge this terminology contract and the read-only inventory
   tool while the old GitHub name and checkout are still authoritative. Active
   defaults continue to use the old URL during this stage so installs do not
   point at a repository that does not exist.
2. **Cut over:** under one attended authorization, rename the GitHub repository,
   fresh-clone the exact approved head into `/home/loucmane/gas-city-ops`, then
   update active URLs and absolute-path consumers. Verify each consumer from
   the new clone before designating it canonical.

The old checkout is not moved or deleted. Its eventual retirement is a separate
gate because linked worktrees contain absolute administrative paths.

The machine-readable source of this contract is
`config/gas-city-operations-migration.json`. The auditor
`scripts/gas-city-operations-migration` classifies active consumers separately
from historical evidence and refuses a post-rename PASS while an unallowlisted
active legacy reference remains.
