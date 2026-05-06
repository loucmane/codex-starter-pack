# Mutation Taxonomy

## Purpose
The Claude adapter is only a system if it can name each persistent mutation surface and prove whether it is mechanically gateable. Memories and docs are continuity aids; they are not workflow evidence.

## Labels
- `verified-hookable`: a test proves the repo-configured hook can block it.
- `unverified-hookable`: likely hookable, but Task 103 must prove or demote it.
- `ci-detectable`: not always blockable at tool time, but can be caught by pre-commit, pre-push, or CI.
- `policy-only`: not mechanically enforceable from repo configuration; banned unless explicitly authorized and documented.

## Initial Taxonomy
| Surface | Examples | Initial label | Planned gate |
| --- | --- | --- | --- |
| Claude file writes | `Edit`, `Write`, `MultiEdit`, `NotebookEdit` to repo files | verified-hookable for tested JSON hook payloads | PreToolUse `pretooluse-gate.sh` calls readiness, blocks when `BLOCKED`, then blocks protected paths. Evidence: `tests-2026-05-06-pretooluse.txt`. |
| Claude Bash writes | `>`, `>>`, `sed -i`, `tee`, `cp`, `mv`, `python -c open(...)` | verified-hookable for tested command-string patterns; best-effort for shell grammar outside tests | PreToolUse Bash command guard blocks tested redirects, `sed -i`, and Python write bypasses. Evidence: `tests-2026-05-06-pretooluse.txt`. |
| Git sync inspection | `git status`, `git fetch`, `git pull --ff-only`, clean `git switch main` | policy-allowed bounded setup | Allowed only during explicit sync/setup phases with clean tree checks. |
| Git mutation | `git switch -c`, `git commit`, `git stash`, `git reset`, `git merge`, `git rebase`, `git push` | unverified-hookable / ci-detectable | Bash command guard plus pre-commit/pre-push/CI where applicable. |
| Taskmaster CLI mutation | `add-task`, `add-subtask`, `set-status`, `generate`, `update*`, `expand` | unverified-hookable | Bash command guard; only allowed after proper scaffold or during explicit bootstrap phase. |
| Taskmaster MCP mutation | MCP `add_task`, `set_task_status`, `update_task`, `expand_task` | unverified-hookable | Empirical hookability test required; otherwise policy-only. |
| Workflow state writes | `sessions/**`, `plans/**`, `docs/ai/work-tracking/**`, `.plan_state/**` | verified-hookable when performed through Claude file tools; CI-detectable through guard/pre-commit | PreToolUse readiness gate plus `codex-guard` validation. |
| Serena memory file writes | `.serena/memories/*.md` direct file writes | unverified-hookable | PreToolUse file gate; only after scaffold and S:W:H:E reference. |
| Serena MCP memory writes | `write_memory` through MCP | unverified-hookable | Empirical hookability test required; otherwise policy-only and never evidence by itself. |
| Claude private memory writes | `~/.claude/projects/.../memory/**` | unverified-hookable | Empirical hookability test required; otherwise policy-only and never evidence by itself. |
| GitHub remote operations | `gh pr create`, `gh pr merge`, `git push`, branch deletion | unverified-hookable / ci-detectable | Bash command guard plus GitHub checks; user authorization required for destructive remote cleanup. |

## Cold-Session Acceptance Test
Given no matching Taskmaster task, task branch, `sessions/current`, `plans/current`, or ACTIVE work-tracking folder:
- every `verified-hookable` persistent mutation must be refused by the tool gate;
- every `unverified-hookable` surface must be promoted with a test or demoted with a documented limitation;
- every `policy-only` surface must be listed in `DECISIONS.md` and `HANDOFF.md` as not mechanically enforceable.

## Multimodal Requirement
This taxonomy is intentionally broader than text editing. The adapter must consider shell commands, MCP tools, memory stores, GitHub operations, and future agent/tool surfaces so the workflow foundation can support multiple agents and modalities without relying on a single chat transcript.
