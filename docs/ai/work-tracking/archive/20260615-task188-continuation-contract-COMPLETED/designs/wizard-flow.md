# Task 188 — Cross-agent continuation contract: design scope

Date: 2026-06-15. Feature (not a bug fix). Designed via workflow wf_96034856 (map + design +
adversarial autonomy/convention review); owner approved the policy.

## Policy (owner-set)
A short continuation intent (continue/go/proceed/next/keep going/resume) is NOT new authority:
advance the current Aegis workflow by exactly ONE safe step, resolved from `aegis next`'s
next_safe_action (never memory), then re-consult. Owner decisions:
- safe-repair: SURFACE-AND-ASK before `aegis repair --apply` (simplest safe rule; even safe
  repairs rewrite gate-trusted closeout/plan/pointer evidence).
- non-dry-run closeout: REQUIRE explicit close-out intent / confirmation (it records completion
  + arms delivery).
- default clarifications: "finish this"/"wrap up"/"done" still stop at the same boundaries;
  one next_safe_action then re-consult (no implement->log->verify->closeout chaining).
Never automatic on any intent: merge, force-push, reset --hard, branch -D, history rewrite,
direct .aegis/ writes, BLOCKED-readiness bypass, skipping S:W:H:E. (Autonomy review: the
merge/push boundary is correctly constrained; read_only stays hardcoded.)

## Implementation
- AEGIS_CONTINUATION_LINES/_CONTRACT/_SUMMARY constants near AEGIS_ARCHITECTURE_NOTES — single
  source reused by every renderer (and, in TM 189, by the aegis next brief).
- _render_contract: "## Continuation Contract" = full contract in .aegis/contract.md
  (authoritative cross-agent home; every agent is pointed to it).
- _render_agents_doc + _render_claude_entrypoint: "## Continuation" = AEGIS_CONTINUATION_SUMMARY
  + pointer to .aegis/contract.md.
- Assets installer copy mirrored byte-identical (TM 219 parity test enforces).

## Boundary
CODEX.md dedicated managed block is Codex-owned -> Codex-led TM 224. Codex still reaches the
contract via AGENTS.md -> .aegis/contract.md, so cross-agent reach is met. GEMINI.md same future
pattern. TM 189 (the aegis next continuation brief) is the next task, building on these constants.
