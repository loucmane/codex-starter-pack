# Task 222 — Repo housekeeping: design scope

Date: 2026-06-14. Two bundled housekeeping streams (low ceremony, both metadata/config).

## A. Secret hygiene (preventive; keys already revoked by owner)
GitHub flagged exposed Firecrawl + ElevenLabs keys after the repo went public; owner
revoked them (exposure neutralized). Durable fix so new real keys can't be re-committed:
- git rm --cached .claude.json (personal Claude Code config that held the real keys;
  local file kept so tools work) + add to .gitignore.
- New .claude/scripts/secret-scan.sh pre-commit guard (wired in .pre-commit-config.yaml)
  blocks staged added lines matching high-confidence key prefixes (fc-/sk-ant-/sk-/sk_/
  AIza/xai-/pplx-, length-anchored to avoid false positives). Tested: blocks a
  real-length fake firecrawl token, allows clean content.
- History scrub skipped (keys dead, strings inert). .mcp.json/.cursor/mcp.json/
  .codex/config.toml left as-is (placeholders only).

## B. Backlog reconciliation (from the read-only reconciliation workflow)
- Commit filed follow-up tasks 219 (assets installer drift), 220 (path-lost populate),
  221 (drain accretion).
- Rescope 189 to residual continuation-brief schema + safe/manual-repair states +
  concise aegis next rendering (core shipped via next_action + PR #197).
- Rescope 191 to residual browser-observation MCP read-only classification (shell/git/
  taskmaster/aegis half shipped by #224).
- No cancellations; 188/190 kept.

## Boundary
.gitignore, .pre-commit-config.yaml, .claude/scripts/secret-scan.sh, .taskmaster/tasks/
tasks.json, work-tracking. No Codex-owned paths; no source-logic changes.
