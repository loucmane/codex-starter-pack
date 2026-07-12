# Mode-Aware Managed Guidance Contract

## Problem

Installed Aegis entrypoints describe the strict kickoff, per-mutation logging, handoff repair, and
closeout loop even when enforcement is advisory. The Blog consumer reports that child agents spend
tokens reading those instructions and then apologizing for correctly ignoring them. This weakens
the authority of all repository guidance.

The current update materializer also treats `CODEX.md` differently after ownership is recorded:
on first install it merges the managed block into project content, but on a later clean update it
can select the upstream source `CODEX.md` asset instead of merging into the target's current file.
Mode-aware guidance is not safe to ship unless updates preserve target-owned content.

## Static Contract

The managed block is static but mode-aware. Every agent reads the enforcement mode once during
orientation with `aegis enforce status` or the project-local shim, then follows one branch:

- Advisory: work normally; hooks passively record evidence and would-block decisions; use
  `aegis brief` for orientation and `aegis witness` at delivery; do not manually drain advisory
  pending events or run handoff repair/closeout as routine ceremony.
- Strict: `.aegis/contract.md` remains authoritative for readiness, kickoff, logging,
  verification, and closeout; `aegis next` resolves the sanctioned next step.
- Always: native tools perform implementation; Aegis CLI/MCP owns workflow state; direct
  `.aegis/` writes remain forbidden; required client reloads remain explicit; missing hooks or
  unsupported clients are degraded coverage, never successful capture.

The continuation summary remains present and points to the shared contract.

## Size Budget

- Each rendered entrypoint contains at most 25 nonblank lines.
- For an existing file, the marker-delimited managed block including begin/end markers also stays
  within 25 nonblank lines.
- Project-owned content does not count toward the managed-block budget and must remain byte-for-
  byte identical.

## Ownership And Update Semantics

- `CLAUDE.md`, `CODEX.md`, and `AGENTS.md` always merge the current managed block into the target's
  existing bytes when that target exists.
- Existing marker-delimited blocks are replaced in place.
- Files without markers receive one managed prefix plus the existing-content heading.
- Project content outside markers is preserved byte-for-byte on install, idempotent update, and
  stale-managed-block update.
- A malformed or undecodable entrypoint remains fail-closed under existing installer behavior.

## Non-Goals

- No gate, readiness, enforcement-mode, pending-event, witness, closeout, or continuation policy
  behavior changes.
- No rewrite of `.aegis/contract.md`.
- No PR-4 retirement or removal of strict instructions.
- No command-output budgeting beyond these managed entrypoint blocks; Task 238 owns that work.

## Acceptance Matrix

| Case | Claude | Codex | Multi-agent | Expected |
|---|---|---|---|---|
| Fresh install | yes | yes | yes | Compact mode-aware entrypoint |
| Existing project instructions | yes | yes | yes | Managed prefix, exact project bytes preserved |
| Existing stale managed block | yes | yes | yes | Block replaced, project bytes unchanged |
| Idempotent update | yes | yes | yes | No content delta |
| Local project-content change outside block | yes | yes | yes | Change preserved, managed block remains current |
| Source/package parity | yes | yes | yes | Canonical and packaged installer bytes match |

Rollback is a revert of the renderer and preservation change; installed targets can reinstall the
prior managed block without a state migration.
