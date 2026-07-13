# Task 239 Worktree And Subagent Capture Audit

## Verdict

Aegis's existing SQLite store already has the correct repository-level storage
primitive: linked Git worktrees resolve the same Git-common-dir identity and the same
out-of-worktree ledger. Evidence survives normal worktree teardown without loss.

Child capture is nevertheless incomplete:

- Claude hooks can record a real child mutation and child verification when the nested
  client has writable state, but the rows have only flat child identity. They omit
  repository identity, worktree root, HEAD, and parent-agent linkage.
- A failed Read is not recorded, and a successful pytest Bash call is typed as a generic
  mutation rather than verification.
- A nested Claude client with read-only home state loads the project hooks but cannot
  persist child evidence; the shared ledger then contains only parent orchestration.
- Codex completed mutation, failure, and verification actions in a linked worktree, but
  the installed integration has no Codex hook/identity surface, so no nested-session row
  was captured.

The live result is therefore **storage supported, Claude capture degraded, Codex capture
unsupported**. Task 240 must address capture and attribution; it does not need to replace
the Git-common-dir store decision.

## Audit Boundary

- Source HEAD before and after the live scenarios:
  `8bf1f1871ff259987fa1b8d66d875b1adaf8d99e`.
- Runtime behavior, hook registration, ledger schema, witness policy, and installation
  assets were not changed.
- Two local disposable worktrees were created at that HEAD, never pushed, cleaned,
  removed without force, and their local branches deleted normally.
- Raw prompts, transcripts, command payloads, absolute repository paths, credentials,
  and unredacted hook payloads are excluded from checked-in evidence.
- The unrelated tracked configuration drift retained digest
  `sha256:eca031a94a46de3908dbebab0a36c466be1696e27887ef6477ab714a188868f0`
  throughout the audit and was not staged or edited.

## Deterministic Cause Matrix

`tests/fixtures/aegis/worktree-capture-audit.json` contains one replay scenario for every
contract cause code. Replay classification is deterministic and requires no client,
network, or live ledger:

| Status | Count |
| --- | ---: |
| supported | 1 |
| unsupported | 2 |
| degraded | 3 |
| failed | 4 |

The ten covered causes are `pre_install_checkout`, `tracked_assets_missing`,
`client_hooks_unloaded`, `source_root_unresolved`, `ledger_store_mismatch`,
`attribution_missing`, `parent_only_traffic`, `teardown_loss`, `unsupported_surface`,
and `capture_ok`.

## Live Coverage

The normalized machine-readable evidence is
`tests/fixtures/aegis/worktree-subagent-live-coverage.json`.

| Scenario | Actions exercised | Ledger result | Classification |
| --- | --- | --- | --- |
| Two linked worktrees | simultaneous registration, shared reads, deterministic concurrent writers, teardown | same repository identity and ledger path; no event loss | supported |
| Claude with inherited read-only state | child mutation, missing read, pytest | child work completed, but only parent traffic reached the default ledger | failed: `parent_only_traffic` |
| Claude with isolated writable state | child Write, missing Read, child pytest | child Write and pytest rows captured with flat identity | degraded: `attribution_missing` |
| Ephemeral Codex in linked worktree | mutation, expected failure, pytest | actions completed; no nested-session row | unsupported: `unsupported_surface` |

### Shared Store And Teardown

- Initial shared-store event count: 10,111.
- Pre-teardown count: 10,159.
- Post-teardown count: 10,165.
- Every one of the 10,159 pre-teardown event IDs remained queryable afterward.
- Missing pre-teardown events after removal: 0.
- Repository identity and normalized ledger path remained identical.
- The deterministic concurrent-writer regression writes 12 events from each of two
  linked worktrees through independent connections and proves all 24 remain after both
  worktrees are removed.

### Claude Default-State Run

Claude 2.1.207 launched real `Explore` and `general-purpose` children. The general child
created a source artifact, exercised an expected missing read, and ran focused
verification. A hook-event probe proved the hooks loaded, but SessionStart reported that
the nested client's session-state directory was read-only. No event carried the nested
session identity; the five observed rows in that window were parent-only traffic.

This is an environment-sensitive failure, not evidence that Claude hooks never work.
The isolated writable-state run below separates that limitation from Aegis attribution.

### Claude Writable-State Run

A temporary state/config root was used only for the disposable client. Existing
credentials and settings were referenced by symlink; their contents were neither copied
nor included in evidence. Across the bounded attempts, the ledger recorded:

| Event type | Count |
| --- | ---: |
| session begin | 4 |
| gate decision | 15 |
| scope | 1 |
| child tool failure | 1 |
| child mutation | 2 |

The successful child Write and pytest Bash call both have `agent_id`,
`agent_type=general-purpose`, and the worktree branch. They both lack repository identity,
worktree root, HEAD, and `parent_agent_id`. The missing-file Read produced no failure row,
and the pytest call was recorded as `mutation`, not `verification`.

### Codex Linked-Worktree Run

Codex CLI 0.144.0 ran ephemerally with a temporary writable `CODEX_HOME`. It created the
expected artifact, observed the expected missing-file failure, and completed the focused
test (`1 passed, 30 deselected`). The default ledger increased by 13 parent orchestration
decisions, but none matched the nested Codex session and none was attributable to its
worktree actions. The current installed integration therefore has no supported Codex
capture surface for this scenario.

## Asset And Store Evidence

Both live worktrees resolved the repository identity
`sha256:3a62fc637142cc8e57a5235477a737d8552ffd32f6e4b7295b7c63166a191d4e`
and the same normalized ledger path. Their managed-asset SHA-256 digests matched:

| Asset | Digest |
| --- | --- |
| settings | `sha256:76bb3f30de71d905e0451335d49b422688516417a3a89dc39c63225a86e2ccf9` |
| gate library | `sha256:c27b9be81c668ae0906c5b8d38a268dacfae363874bfa6e14530e26533bf2882` |
| ledger library | `sha256:7945eb42a39615250b6c2ac65b2f8da6bb19af195c7fc5a90344dbe263f742f4` |
| recorder | `sha256:acd931fd8490c345c1a6366340a64d5d335f2e02d4b14b4eb5fa365577e03fb9` |

The worktree shim was absent because the worktrees were source checkouts, not installed
targets. Tracked hook, recorder, settings, and ledger assets were present and identical.

## Task 240 Requirements Established By Evidence

This audit deliberately does not choose a runtime mechanism. It establishes the minimum
observable outcomes Task 240 must satisfy:

1. Every child implementation event must carry repository identity, worktree root,
   branch, observed HEAD, child agent identity/type, and parent-agent identity.
2. Claude capture must remain functional when child processes cannot write the ordinary
   user-home state location, without duplicating mutable state into each worktree.
3. Codex needs a supported native event/identity input or an explicit bridge; parent
   orchestration traffic must never be relabeled as child work.
4. Failed Read/command actions and verification runs must be typed and retained, not
   inferred from generic mutation rows.
5. All clients in one Git common directory must continue to resolve one out-of-worktree
   repository store, with concurrent-write and teardown preservation tests retained.
6. Installed targets and advisory behavior must remain backward-compatible.

## Reproduction And Verification

```bash
python3 -m pytest -q tests/claude_adapter/test_worktree_capture_audit.py
python3 -m aegis_foundation.worktree_capture_audit replay \
  --fixture tests/fixtures/aegis/worktree-capture-audit.json
```

The live runs are intentionally not CI prerequisites. CI replays the cause matrix,
validates the sanitized live fixture, exercises linked-worktree identity, performs
concurrent writes, and proves post-teardown persistence without requiring Claude, Codex,
network access, or user credentials.
