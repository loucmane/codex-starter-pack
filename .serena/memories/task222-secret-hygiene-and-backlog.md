# Task 222 — Repo housekeeping: secret hygiene + backlog reconciliation (2026-06-14)

## Security incident (resolved)
After the codex repo went PUBLIC (to escape GitHub Actions billing on the private free
plan), GitHub flagged exposed Firecrawl + ElevenLabs API keys. They lived in a TRACKED
`.claude.json` (personal Claude Code config, lines 72/82). Owner REVOKED both keys at the
providers → exposure neutralized (strings now inert). Only those two were real; the nine
LLM-provider keys in .claude.json/.mcp.json/.cursor/mcp.json/.codex/config.toml are short
placeholders (Taskmaster setup defaults), which is why GitHub flagged exactly the two.

## Durable fix (TM 222)
- `git rm --cached .claude.json` + added `.claude.json` to .gitignore (local file kept so
  tools work; new real keys can't be re-committed).
- New `.claude/scripts/secret-scan.sh` pre-commit guard (wired in .pre-commit-config.yaml)
  blocks staged added lines matching high-confidence key prefixes (fc-/sk-ant-/sk-/sk_/
  AIza/xai-/pplx-, length-anchored ≥24-35 to avoid false positives). Excludes itself +
  the pre-commit config from scanning. Tested: blocks real-length fake firecrawl token,
  allows clean content.
- History scrub SKIPPED (keys dead → strings inert; not worth rewriting public history).
- .mcp.json/.cursor/mcp.json/.codex/config.toml left as-is (placeholders only). Real keys
  belong only in the now-gitignored .claude.json.

## Operational note
HP-Coach runs the CLI from /home/loucmane/codex, so it executes whatever branch codex is
checked out on — leave codex on `main` when done so HP-Coach reliably runs merged fixes.
Going public ALSO unlocked required branch-protection checks (witness-as-required-check,
the PR-4 gate the free private plan couldn't do).

## Backlog reconciliation (bundled in TM 222)
Committed filed follow-ups: TM 219 (assets/scripts/_aegis_installer.py drift — packaging
hygiene), TM 220 (path-lost populate sub-mode), TM 221 (drain accretes read-only evidence
— the next HP-Coach fix to BUILD, drain-layer). Rescoped TM 189 (residual continuation-
brief schema + safe/manual-repair states + concise `aegis next` rendering; core shipped
via next_action + PR #197) and TM 191 (residual browser-observation MCP read-only
classification; shell/git/taskmaster/aegis half shipped by #224). No cancellations.

See [[task218-recoverable-closeout-evidence]], [[task216-closeout-convergence]].
