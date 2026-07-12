# Task 244: Derivable source-checkout closeout

## Outcome
Task 244 is implemented, marked done, and archived. The uninstalled Aegis source checkout now derives terminal workflow state from fail-closed repository evidence without fabricating installed Aegis state.

## Source-only authority contract
- `scripts/_source_workflow_state.py` is stdlib-only.
- Derivation requires Aegis source markers, no installed foundation manifest, no current-work state, a task-bearing branch, a Taskmaster task with status `done`, no ACTIVE folder, exactly one direct matching `archive/*-COMPLETED` directory, and a regular COMPLETED tracker with matching task identity.
- Non-done tasks, ambiguous/missing archives, symlinked archives, missing/mismatched trackers, installed manifests, and current-work state fail closed.
- ACTIVE envelopes and installed current-work retain precedence.

## Consumers and lifecycle
- `.claude/scripts/readiness.sh` validates completed source session, plan, tracker, and checklist parity.
- `scripts/codex-guard` resolves the same completed tracker.
- The supported archive helper now relocates exact ACTIVE-root references in the moved Markdown bundle, current plan, and current session, then records fresh plan/tracker hashes.
- Canonical and packaged readiness, guard, and `codex-task` assets remain byte-identical.
- Installed-target behavior is unchanged.
- Plans, sessions, trackers, handoffs, and S:W:H:E evidence remain preserved; this is not legacy-system retirement.

## Live dogfood
Task 244 was set to done and archived through the supported helper. The first guard run found stale plan evidence paths after the move. The archive transition was corrected and replayed. Final source readiness reported READY, the scoped guard passed, and `.aegis/state/current-work.json` remained absent.

## Verification
- Source-closeout tests: 13 passed.
- Post-dogfood workflow regression set: 307 passed.
- Installer suite: 121 passed, 1 opt-in skip.
- Final coverage: 1,771 tests passed under xdist plus the bounded stdio smoke passed in isolation;
  4 existing opt-in smoke skips. The recurring xdist-only timeout is a text-buffer/select race in
  the smoke harness and remains separate follow-up work; no MCP production code changed.
- Taskmaster graph: 0 invalid dependencies.
- Plan sync, mirror parity, work-tracking audit before terminal transition, and diff checks passed.

## Publication and follow-up
Publish Task 244 through its reviewed branch and hosted CI. Separately plan an Obsidian-compatible knowledge-vault projection over authoritative Aegis/Taskmaster evidence; the vault complements rather than replaces the ledger or human workflow surfaces.
