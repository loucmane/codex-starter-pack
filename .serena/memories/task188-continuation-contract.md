# Task 188 — Cross-agent continuation contract (2026-06-15)

FEATURE (not a bug fix), designed via workflow wf_96034856 (map+design+adversarial review);
owner approved the policy. First half of the 188+189 continuation feature; TM 189 (the
`aegis next` continuation brief) builds on these constants.

## Policy (owner-set 2026-06-15)
A short continuation intent (continue/go/proceed/next/keep going/resume) is NOT new authority:
advance the Aegis workflow by exactly ONE safe step, resolved from `aegis next`'s
next_safe_action (never memory/chat), then re-consult. Owner decisions:
- safe-repair → SURFACE-AND-ASK before `aegis repair --apply` (chosen as the simplest safe rule:
  even "safe" repairs rewrite gate-trusted closeout/plan/pointer evidence; no fragile sub-classification).
- non-dry-run closeout → REQUIRE explicit close-out intent/confirmation (records completion + arms delivery).
- "finish this"/"wrap up"/"done" still stop at the same boundaries; ONE next_safe_action then
  re-consult (no implement→log→verify→closeout chaining on one intent).
- Never automatic on any intent: merge, force-push, reset --hard, branch -D, history rewrite,
  direct .aegis/ writes, BLOCKED-readiness bypass, skipping S:W:H:E.

## Implementation (scripts/_aegis_installer.py + assets mirror)
- AEGIS_CONTINUATION_LINES / _CONTRACT / _SUMMARY constants near AEGIS_ARCHITECTURE_NOTES —
  SINGLE SOURCE reused by every renderer (and TM 189's brief next).
- _render_contract: "## Continuation Contract" = full contract in .aegis/contract.md (the
  authoritative cross-agent home; AGENTS.md/CLAUDE.md already point all agents to it).
- _render_agents_doc + _render_claude_entrypoint: "## Continuation" = AEGIS_CONTINUATION_SUMMARY.
- Assets installer copy mirrored byte-identical (TM 219 parity test enforces).

## Boundary
CODEX.md dedicated managed block is Codex-owned → Codex-led TM 224 (Claude must not edit
CODEX.md / scripts/codex-*). Codex still reaches the contract via AGENTS.md → .aegis/contract.md.
GEMINI.md same future pattern.

Tests: tests/meta_workflow_guard/test_continuation_contract.py (7) — install reach +
autonomy-boundary assertions (no auto merge/push, repair/closeout confirmation, finish-this bounded).

See [[session-2026-06-14-hpcoach-fixes]], [[task219-assets-installer-parity]]. NEXT: TM 189.
