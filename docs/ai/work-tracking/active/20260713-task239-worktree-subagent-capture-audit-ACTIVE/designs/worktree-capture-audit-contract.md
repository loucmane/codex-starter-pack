# Task 239 Worktree And Subagent Capture Audit Contract

## Purpose

Task 239 measures what Aegis actually captures when work is performed outside the
primary checkout or by a child agent. It is diagnostic-only. It may create disposable
worktrees, invoke supported clients, read ledgers, and write secret-free reports and
fixtures. It must not change hook registration, recorder behavior, ledger schema,
worktree routing, witness filtering, agent identity propagation, or runtime policy.
Those changes belong exclusively to Task 240 after this audit identifies a causal gap.

## Questions The Audit Must Answer

Each scenario must distinguish these causes instead of collapsing them into “no child
events”:

1. `pre_install_checkout`: the worktree commit predates tracked Aegis assets.
2. `tracked_assets_missing`: the selected commit should contain assets but one or more
   required files are absent.
3. `client_hooks_unloaded`: settings/assets exist but the client did not load the hook.
4. `source_root_unresolved`: a loaded hook cannot resolve the intended Aegis source.
5. `ledger_store_mismatch`: parent and child resolve different stores despite the same
   Git common directory.
6. `attribution_missing`: events exist but required branch/worktree/agent fields do not.
7. `parent_only_traffic`: orchestration events exist but no child implementation event
   can be proven.
8. `teardown_loss`: evidence visible before worktree removal is unavailable afterward.
9. `unsupported_surface`: the client exposes no supported hook or identity surface.
10. `capture_ok`: the expected event and attribution evidence is present exactly once.

The harness reports every applicable cause. It must not infer hook execution merely
from asset presence, infer child work from parent traffic, or infer data loss from an
empty filtered query whose filter fields were never recorded.

## Secret-Free Evidence Schema

The checked-in coverage report and replay fixture use this normalized shape:

```json
{
  "schema_version": "1.0.0",
  "run_id": "task239-<stable-fixture-id>",
  "scenario_id": "linked-worktree-success",
  "client": {"name": "claude|codex", "version": "normalized", "mode": "actual|fixture"},
  "parent": {"session_id": "opaque", "agent_id": "opaque", "agent_type": "orchestrator"},
  "child": {"session_id": "opaque|null", "agent_id": "opaque|null", "parent_agent_id": "opaque|null"},
  "repository": {"identity": "sha256:<digest>", "git_common_dir": "<repo-common-dir>"},
  "worktree": {"path": "<worktree-N>", "branch": "fixture/branch", "head": "<sha>"},
  "assets": {"shim": "present|absent", "settings": "present|absent", "recorder": "present|absent", "checksums": {}},
  "hooks": {"session_start": "supported|unsupported|unknown", "post_tool_use": "supported|unsupported|unknown", "post_tool_failure": "supported|unsupported|unknown", "stop": "supported|unsupported|unknown"},
  "ledger": {"backend": "sqlite|jsonl|none", "resolved_path": "<state-root>/<repo-id>/ledger.db", "shared_with_parent": true},
  "event_window": {"before_seq": 0, "after_seq": 0, "event_ids": [], "event_count": 0},
  "attribution": {"branch": "present|missing", "worktree": "present|missing", "head": "present|missing", "agent_id": "present|missing", "agent_type": "present|missing", "parent_agent_id": "present|missing"},
  "result": {"status": "supported|unsupported|degraded|failed", "causes": []},
  "limitations": []
}
```

Live home directories, usernames, raw prompts, raw command payloads, credentials,
transcripts, absolute repository paths, and unredacted hook payloads are prohibited in
checked-in artifacts. Repository identity is a one-way digest of the canonical common
directory. Worktree paths and session/agent identifiers are stable per-run aliases.
Asset evidence uses SHA-256 digests only. Event IDs may be retained because they are
random identifiers, but event payloads must be normalized to the documented fields.

## Scenario Matrix

The audit must cover:

| Scenario | Required action | Expected diagnostic value |
| --- | --- | --- |
| linked worktree A | successful source mutation in a disposable checkout | asset, store, event, and attribution coverage |
| linked worktree B | failed command followed by verification | failure and verification capture coverage |
| pre-install worktree | checkout at a commit before ledger/hook assets | distinguish age from runtime failure |
| actual Claude child | dispatched/headless child in a disposable worktree | real client hook and child identity coverage |
| Codex worktree | current Codex worktree execution or explicit unsupported classification | avoid pretending Codex exposes Claude hooks |
| concurrent readers/writers | two worktrees active against one common directory | detect store mismatch or dropped events without fixing it |
| teardown | remove one disposable worktree after capture | prove whether shared evidence survives removal |

Every mutation is confined to disposable worktrees under `/tmp`; no audit scenario may
modify `main`, the Task 239 feature checkout outside its own report/fixture scope, a
production target, HP-Fetcher, or Blog. Worktree branches are local and never pushed.

## Harness Boundary

`aegis_foundation/worktree_capture_audit.py` owns deterministic collection,
normalization, classification, report rendering, and replay. It may call read-only Git
commands and read the existing ledger through the current ledger library. Scenario
orchestration lives in tests or a task-scoped runner and must make lifecycle operations
explicit. The harness must support fixture replay without Claude, Codex, network, or a
real home-state ledger so CI can validate classification deterministically.

The audit result is evidence, not policy. `supported` means the scenario's required
surface was observed. `unsupported` means the client contract lacks the surface.
`degraded` means work was captured but attribution or lifecycle evidence is incomplete.
`failed` means a supported surface was expected and did not produce usable evidence.

## Acceptance And Stop Conditions

Task 239 is complete only when:

- the deterministic fixture matrix classifies all ten cause codes;
- two linked worktrees prove common-dir and resolved-ledger behavior;
- actual Claude evidence is captured or a concrete client/environment blocker is
  recorded without substitution by a fixture;
- Codex is exercised in a linked worktree or explicitly classified unsupported with
  the missing capability named;
- success, failure, verification, concurrency, and teardown evidence is present;
- checked-in report and fixture pass secret scans and contain no raw prompt/transcript;
- before/after Git and ledger fingerprints prove the audit did not select or implement
  a runtime fix.

If actual child execution is unavailable, deterministic harness work and all other
scenarios continue; the live row remains `unsupported` or `failed` with exact evidence.
Task 239 must never weaken the acceptance criteria or silently relabel fixture evidence
as live evidence.

## Rollback

Remove the diagnostic module, tests, fixture, and report. No migration, repair, ledger
rewrite, hook reinstall, or target rollback is required because Task 239 changes no
runtime behavior.
