"""TM 188: the cross-agent continuation contract is installed and conservatively bounded.

A short continuation intent (continue/go/proceed/next/resume) means "advance the Aegis
workflow by exactly one safe step, then re-consult" — it grants no authority to bypass a
gate. These tests lock both that the contract reaches every agent surface (via the shared
.aegis/contract.md plus the AGENTS.md/CLAUDE.md/CODEX.md summaries) and that its autonomy
boundaries stay policy-controlled (manual-review/high-risk work remains attended; explicit
evidence-gated capabilities may authorize routine safe repair, verified closeout, and delivery).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _aegis_installer as inst  # noqa: E402


def contract_md() -> str:
    return inst._render_contract("claude", ["claude"]).decode("utf-8")


def test_contract_md_carries_full_continuation_contract() -> None:
    text = contract_md()
    assert "## Continuation Contract" in text
    assert "advance the current Aegis workflow by exactly ONE safe step" in text
    assert "Run `aegis next`" in text and "next_safe_action" in text
    assert "Taskmaster is the task-selection authority" in text


def test_agents_claude_and_codex_surfaces_carry_the_summary() -> None:
    # Cross-agent reach: AGENTS.md (read by every agent incl. Codex/Gemini), CLAUDE.md,
    # and CODEX.md all carry the summary and point at the authoritative .aegis/contract.md.
    agents = inst._render_agents_doc("claude", ["claude"]).decode("utf-8")
    claude = inst._render_claude_entrypoint().decode("utf-8")
    codex = inst._render_codex_continuation_block().decode("utf-8")
    codex_entrypoint = (REPO_ROOT / "CODEX.md").read_text(encoding="utf-8")
    for surface in (agents, claude, codex, codex_entrypoint):
        assert "Continuation contract:" in surface
        assert ".aegis/contract.md" in surface
    assert codex.strip() in codex_entrypoint
    assert inst.AEGIS_CODEX_BLOCK_BEGIN in codex_entrypoint
    assert inst.AEGIS_CODEX_BLOCK_END in codex_entrypoint


def test_contract_controls_repair_and_closeout_through_active_policy() -> None:
    text = contract_md()
    assert "deterministic safe repairs" in text
    assert "verified closeout" in text
    assert "valid active evidence-gated policy may authorize" in text
    assert "manual-review" in text
    assert "require explicit confirmation" in text


def test_contract_never_authorizes_irreversible_actions() -> None:
    # The autonomy-safety invariant: no continuation intent auto-merges/pushes/rewrites.
    text = contract_md().lower()
    assert "never automatic" in text
    for forbidden in ("merge", "force-push", "reset --hard", "history rewrite"):
        assert forbidden in text, forbidden
    # No copyable command in the contract merges or force-pushes.
    assert "pr merge" not in text
    assert "push --force" not in text and "push -f" not in text


def test_finish_this_still_stops_at_boundaries() -> None:
    text = contract_md()
    assert "Completion-flavored intents" in text
    assert "do NOT authorize skipping closeout" in text


def test_one_step_then_reconsult() -> None:
    text = contract_md()
    assert "re-run `aegis next`" in text
    assert "Do not chain" in text


def test_single_source_constant_reused() -> None:
    # The summary and the full contract derive from the same module constants so doc and
    # (later) the aegis-next brief stay in lockstep.
    assert inst.AEGIS_CONTINUATION_CONTRACT == "\n".join(inst.AEGIS_CONTINUATION_LINES)
    assert "exactly ONE safe step" in inst.AEGIS_CONTINUATION_SUMMARY
    assert inst.AEGIS_CONTINUATION_CONTRACT in contract_md()
