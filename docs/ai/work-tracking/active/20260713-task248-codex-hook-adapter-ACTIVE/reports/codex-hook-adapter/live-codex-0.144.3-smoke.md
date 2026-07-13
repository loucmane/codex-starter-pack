# Live Codex 0.144.3 Hook Smoke

**Run at:** 2026-07-13 21:38 CEST
**Codex binary:** `codex-cli 0.144.3`
**Adapter source commit:** `f2da51d2615ba198e4cf6825e6f42962c9c3be3d`
**Mode:** advisory
**Result:** PASS

## Purpose

Prove the managed Codex adapter against the real Codex CLI, including exact hook trust,
canonical `apply_patch` input, all-path extraction, PreToolUse evaluation, one atomic
PostToolUse pending event, passive-ledger evidence, and Stop-hook visibility.

## Isolation and trust

- Created a disposable Git repository, disposable `CODEX_HOME`, and disposable
  `XDG_STATE_HOME` under `/tmp`.
- Installed the Task 248 source as a Codex-only Aegis target.
- Marked only the disposable project as trusted in the disposable Codex configuration.
- Opened Codex interactively and used `/hooks` to inspect and trust the exact five managed
  definitions: PreToolUse, two PostToolUse commands, SessionStart, and Stop.
- Did not use `--dangerously-bypass-hook-trust`, change the global Codex configuration, or
  reuse the operator's production hook approvals.
- Started a disposable Aegis local task and logged scope through the supported CLI so the
  PostToolUse mutation could be attributed to an active work envelope.

## Canonical tool invocation

The real CLI was instructed to make exactly one canonical `apply_patch` call and no other
tool calls. Codex emitted one `file_change` item containing two additions:

- `smoke/codex-posttool-a.txt`
- `smoke/codex-posttool-b.txt`

The CLI completed normally and reported one tool item followed by `done`.

## PreToolUse evidence

The gate-decision stream recorded exactly one decision for the patch:

```json
{
  "hook": "pretooluse",
  "mode": "advisory",
  "payload_digest": "665edf3d1673c79dcb15f90a846ce25051427ca0c447e9e7f4c8df71cac942e3",
  "reason": "allow",
  "tool_name": "apply_patch",
  "verdict": "allow"
}
```

This proves Codex's canonical `tool_name: "apply_patch"` reached the first-class Aegis
handler rather than being silently classified as non-hookable.

## Atomic pending evidence

PostToolUse wrote one pending event, not one event per file:

```json
{
  "id": "94fa7135923a",
  "tool": "apply_patch",
  "handler": "codex:apply_patch",
  "evidence": "smoke/codex-posttool-a.txt",
  "affected_paths": [
    "smoke/codex-posttool-a.txt",
    "smoke/codex-posttool-b.txt"
  ],
  "operations": [
    {"operation": "add", "source_path": "smoke/codex-posttool-a.txt"},
    {"operation": "add", "source_path": "smoke/codex-posttool-b.txt"}
  ],
  "patch_digest": "5ec701f2c7213b964d481e80399fac29ff1f3f2051d0096c1e65e942f0bb2366",
  "mode": "advisory"
}
```

The first path is the primary evidence path; both affected paths remain present for policy,
tracking, and replay. The Stop hook subsequently recorded `reason: "pending_tracking"` and
`verdict: "would_block"`, proving the atomic event was visible to the completion boundary.

## Passive-ledger evidence

With `XDG_STATE_HOME` directed to the disposable writable store, the ledger recorded:

1. Gate decision `5e4c04e384f541c7b3f4a9e419c13ce5` for canonical `apply_patch`.
2. Mutation `f6547a8403a4452eb1c74e7041e9b749` with:
   - `event_type: mutation`
   - `tool_name: apply_patch`
   - `handler: codex:apply_patch`
   - both affected paths in order
   - `outcome: pass`
   - the same canonical payload digest as PreToolUse
   - `hook_event_name: PostToolUse`

After adding full operation metadata to the passive row, the managed target was updated from
the Task 248 source and a second real one-tool invocation updated one file and moved/updated a
second file. The latest mutation, `e782e475ef1744af8a6f66b578afd4d7`, proves the final
contract directly:

```json
{
  "event_type": "mutation",
  "tool_name": "apply_patch",
  "handler": "codex:apply_patch",
  "paths": [
    "smoke/codex-posttool-a.txt",
    "smoke/codex-posttool-b.txt",
    "smoke/codex-posttool-b-moved.txt"
  ],
  "outcome": "pass",
  "extra": {
    "primary_evidence_path": "smoke/codex-posttool-a.txt",
    "affected_paths": [
      "smoke/codex-posttool-a.txt",
      "smoke/codex-posttool-b.txt",
      "smoke/codex-posttool-b-moved.txt"
    ],
    "operations": [
      {"operation": "update", "source_path": "smoke/codex-posttool-a.txt"},
      {
        "operation": "move",
        "content_operation": "update",
        "source_path": "smoke/codex-posttool-b.txt",
        "destination_path": "smoke/codex-posttool-b-moved.txt"
      }
    ],
    "patch_digest": "532315e1de2ab78cccd1f292adcc8a5c3f05ab8ac98516695038fc01c18a050d",
    "hook_event_name": "PostToolUse"
  }
}
```

The corresponding pending event `3a25ca557f4c` has the same three paths, operation graph,
primary evidence path, and patch digest. Because the first smoke's pending event was
intentionally still present, advisory PreToolUse correctly recorded `would_block` with
`reason: pending_tracking` while allowing the second real patch; Stop again observed the
pending boundary. The hook definitions did not change, so their previously reviewed exact
hashes remained trusted—no bypass or automatic trust mutation occurred.

## Installed-target strict verification

After logging the two disposable pending events through the supported Aegis workflow,
`aegis verify --strict` passed with 34 checks, zero required failures, one expected advisory
warning, and two unsupported optional surfaces. Every first-class Codex check passed:

- `codex.readiness`
- `codex.pretooluse`
- `codex.posttooluse_tracking`
- `codex.posttooluse_ledger`
- `codex.session_brief`
- `codex.stop_tracking`
- `codex.apply_patch`
- `codex.guard`
- `codex.work_tracking_audit`
- `codex.required_files`
- `codex.hooks_registered`
- `codex.hook_trust_guidance`

`codex.hook_trust` itself remains intentionally `unsupported` as a mechanical verifier: Codex
owns that exact-hash decision outside the repository. The trusted hook invocation cleared the
Codex reload marker through the normal PreToolUse proof path.

## Acceptance conclusion

The live CLI proves the behavior that unit fixtures alone cannot prove: Codex matcher aliases
cause the hook to fire, stdin retains canonical `apply_patch`, the Task 248 runtime parses and
evaluates every source and destination path, and the managed adapter records one atomic
PostToolUse mutation with the complete deterministic operation evidence. Hook trust remains an
explicit user decision and was never bypassed.

Official behavior reference: <https://learn.chatgpt.com/docs/hooks#pretooluse>
