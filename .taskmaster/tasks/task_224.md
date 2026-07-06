# Task ID: 224

**Title:** [Codex-led] Add continuation-contract managed block to CODEX.md

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** TM 188 installed the cross-agent continuation contract: full text in .aegis/contract.md (authoritative, all agents read it), summary in AGENTS.md + CLAUDE.md (via AEGIS_CONTINUATION_SUMMARY constant). Codex DOES reach the contract via AGENTS.md -> .aegis/contract.md. The design also proposed a dedicated CODEX.md managed block (AEGIS_CODEX_BLOCK markers + _merge_codex_entrypoint mirroring _merge_claude_entrypoint) so Codex's primary entrypoint carries the summary directly — but CODEX.md is Codex-owned (scripts/codex-* / CODEX.md), so Claude must not add it. Codex-led: add the managed block reusing the AEGIS_CONTINUATION_SUMMARY constant (already in _aegis_installer.py) so it stays in lockstep with the other surfaces. GEMINI.md is the same future pattern when Gemini is enabled.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
