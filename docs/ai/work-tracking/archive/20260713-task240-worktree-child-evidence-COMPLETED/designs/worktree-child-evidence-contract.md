# Task 240 Worktree And Child-Agent Evidence Contract

## Outcome

Aegis keeps the existing out-of-worktree store keyed by Git common directory. Task 240
does not introduce per-worktree databases or duplicate mutable Aegis state. Instead, it
adds enough immutable capture context to each event to identify the repository,
worktree, branch, observed commit, agent, and parent relationship at record time.

## Additive Event Contract

The v1 event schema gains four nullable top-level fields:

- `repository_identity`: `sha256:` digest of the canonical Git common-directory path;
- `worktree_root`: canonical `git rev-parse --show-toplevel` path;
- `head`: full observed `HEAD` object id;
- `parent_agent_id`: client-provided or explicitly bridged parent identifier.

Existing `branch`, `agent_id`, and `agent_type` remain top-level fields. Repository
context is computed once when a ledger is opened and fills only absent event values.
Explicit payload fields win. `AEGIS_AGENT_ID`, `AEGIS_AGENT_TYPE`, and
`AEGIS_PARENT_AGENT_ID` are supported adapter-bridge inputs; they are never guessed from
unrelated parent traffic.

This is an additive v1 change. Writable SQLite opens migrate existing tables with
nullable columns and indexes. Read-only opens tolerate pre-migration databases by
selecting their available columns and filling the new fields with null. JSONL readers
do the same in memory. No existing row is rewritten.

## Client Capability Boundary

Claude's installed PostToolUse/PostToolUseFailure payload is recorded as before and now
inherits repository/worktree context. Child identity fields are accepted when Claude
provides them, and the explicit environment bridge supplies parent identity when the
launcher can propagate it.

Codex 0.144 exposes stable project hooks for `SessionStart`, `PostToolUse`,
`SubagentStart`, and `SubagentStop`. The installer merges passive Aegis handlers into
`.codex/hooks.json` without deleting unrelated hooks. Commands run through the installed
shim and therefore do not require copied ledger state in each worktree. Codex reports
failed Bash operations through PostToolUse, so response classification records those as
failures. Subagent lifecycle payloads supply `agent_id` and `agent_type`; current Codex
tool-event payloads do not promise a child id, so tool-level child identity remains
explicitly unsupported when absent. Worktree/branch/HEAD ownership remains factual.

The source checkout's existing untracked `.codex/hooks.json` is user drift and is not
modified, staged, or adopted as an authoritative asset by this task. Installer behavior
is proven in disposable targets.

## Query Isolation

Ledger reads accept repository identity, worktree root, branch, HEAD, and parent-agent
filters in addition to the existing session/type/agent/time filters. The delivery
witness reads only current-repository/current-branch rows. Replay ingestion defaults to
the current repository and branch, with an explicit all-branches mode for corpus work.
No verification run from sibling worktree B may satisfy branch A's verification-at-HEAD
check merely because its timestamp is newer.

Legacy rows remain readable. Because stores were already repository-specific, a legacy
row with a matching branch may be consumed for compatibility; branchless rows are not
used as branch-scoped verification evidence.

## Concurrency And Lifecycle

SQLite remains WAL-backed with the existing busy timeout and journal-mode retry. Tests
exercise two concurrent writers from separate worktrees, deliberate lock contention,
distinct parent/child attribution, successful mutations, failed commands, and
verification events. Removing either worktree must not remove any event because the
store remains owned by the Git common directory's repository identity.

## Rollback

Remove the Codex passive hook additions and stop enriching newly appended rows. Existing
nullable columns and enriched rows remain harmless and readable. Parent-only recording
continues with an explicit degraded capability result; no ledger rewrite, repair,
worktree migration, or event deletion is permitted.
