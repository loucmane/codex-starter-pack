# Aegis Ledger Schema (v1)

> The documented ledger schema deliverable from `docs/aegis/AEGIS_CAPSULE_SPEC.md` §2 —
> shipped instead of an `aegis ask` query engine (spec §6): agents and humans query the
> store directly with `sqlite3` / `rg`. Owned by `ledger_lib.py`
> (`aegis_foundation/assets/.claude/scripts/ledger_lib.py`, mirrored at
> `.claude/scripts/ledger_lib.py`); stdlib-only, no aegis_foundation imports.

## Store location

```
${XDG_STATE_HOME:-~/.local/state}/aegis/<sha1-of-git-common-dir>/ledger.db
```

- Keyed on `git rev-parse --git-common-dir` so **all worktrees of one repository share
  one store** (a worktree's common dir is its parent repo's `.git`).
- Out-of-worktree by design: governance state must not dirty target repos, and branch
  merges must never merge ledgers.
- Discoverability: `aegis ledger path` prints the resolved path; `aegis status` includes
  a `ledger` block. Out-of-worktree state must never be invisible during debugging.
- SQLite opens with `journal_mode=WAL` and `busy_timeout=5000` (concurrent hook writers).
- **Append-only. No hash chain** (decided, spec §2): append-only rows with timestamps;
  per-row checksums may come later, chaining does not return.
- Rotation: `rotate_if_needed()` rotates the db aside at 64 MB (`ROTATE_BYTES`).
  Enforcement wiring lands with PR-1b.

## Table: `events`

| column | type | nullable | semantics |
|---|---|---|---|
| `seq` | INTEGER PK AUTOINCREMENT | no | insertion order within this store |
| `schema_version` | TEXT | no | `"1"` |
| `event_id` | TEXT UNIQUE | no | uuid4 hex, generated at append when absent |
| `ts` | TEXT | no | UTC ISO-8601 (`...Z`), second precision, set at append when absent |
| `session_id` | TEXT | yes | client session/thread id from the hook payload or `AEGIS_SESSION_ID` bridge |
| `repository_identity` | TEXT | yes | `sha256:` digest of the canonical Git common-directory path; identical for linked worktrees |
| `worktree_root` | TEXT | yes | canonical `git rev-parse --show-toplevel` path at ledger-open time |
| `branch` | TEXT | yes | git branch at ledger-open time |
| `head` | TEXT | yes | full observed `HEAD` object id at ledger-open time |
| `cwd` | TEXT | yes | working directory at ledger-open time |
| `event_type` | TEXT | no | see vocabulary below; `"unknown"` when uninferable |
| `tool_name` | TEXT | yes | e.g. `Bash`, `Edit`, `mcp__playwright__browser_click` |
| `handler` | TEXT | yes | normalized handler, e.g. `bash:rg`, `claude:Edit` |
| `paths` | TEXT (JSON array) | no (`[]`) | normalized target paths |
| `outcome` | TEXT | yes | `pass \| fail \| interrupted \| unknown` |
| `exit_class` | TEXT | yes | same enum; for verification events (see mapping) |
| `duration_ms` | INTEGER | yes | from the hook payload when present |
| `agent_id` | TEXT | yes | subagent attribution when present in the payload |
| `agent_type` | TEXT | yes | subagent type when present |
| `parent_agent_id` | TEXT | yes | client-provided or explicitly bridged parent identifier; never inferred from unrelated traffic |
| `payload_digest` | TEXT | yes | sha256 over the tool payload (advisory-recorder convention) |
| `extra` | TEXT (JSON object) | no (`{}`) | backend-specific detail; **redacted at write time**; unknown top-level keys on input events are preserved here |

Repository/worktree context is computed once per `open_ledger()` call and fills only
absent fields. Explicit event values win. `AEGIS_AGENT_ID`, `AEGIS_AGENT_TYPE`,
`AEGIS_PARENT_AGENT_ID`, and `AEGIS_SESSION_ID` provide an adapter bridge when a client
launcher can propagate identity. Missing fields degrade to NULL — the recorder never
crashes on payload shape (spec §2 payload reality check).

Writable SQLite opens migrate old v1 databases additively with nullable columns and
indexes. Read-only opens select only columns present in an old database and return NULL
for the new fields. JSONL readers apply the same in-memory defaults. Existing rows are
never rewritten, and the schema version remains `"1"` because this is backward-compatible
enrichment rather than a new event meaning.

## `event_type` vocabulary (v1)

Defined here for the whole capsule program; PR-1a ships the vocabulary, later PRs emit
the rows:

| event_type | producer | meaning |
|---|---|---|
| `mutation` | PR-1b PostToolUse | a successful mutating tool call |
| `tool_failure` | PR-1b PostToolUseFailure | a failed tool call (without this, failed mutations silently vanish) |
| `verification` | PR-1d (gate registry match) | a registered gate command run: `{package, gate, exit_class, commit}` in `extra` |
| `delivery` | PR-1b | `git push` / `gh pr create` / merge command events; branch→PR mapping in `extra` |
| `task_truth` | PR-1b | writes to `.taskmaster/tasks/tasks.json` or `task-master` commands; status flips in `extra` |
| `gate_decision` | PR-1c dual-write | one advisory gate decision (verdict, reason, mode, policy commit in `extra`) |
| `checkpoint` | PR-3 Stop hook | deterministic per-turn checkpoint (turn index, mutation count, dirty files) |
| `scope` | PR-1d | inferred/confirmed scope record for a branch (spec §2.1) |
| `session_begin` | PR-2b | falsifier stamp: session start + capsule on/off flag |
| `subagent_begin` | Task 240 Codex `SubagentStart` | child lifecycle start with `agent_id`, `agent_type`, and supported parent attribution |
| `subagent_end` | Task 240 Codex `SubagentStop` | child lifecycle completion; transcript metadata is retained in redacted `extra` |
| `unknown` | any | unclassifiable input; preserved, never dropped |

## Exit-class mapping (decided, spec §2)

`PostToolUseFailure`, an explicit error status, `success/ok=false`, or a recursively
observed nonzero response exit code → `fail` · interruption flags/status →
`interrupted` · successful mutation/delivery/task/verification evidence → `pass` ·
anything else → `unknown`. Codex emits `PostToolUse` after supported Bash calls even
when Bash exits nonzero, so classification cannot assume the hook event name itself
means success. Unknown provider response shapes remain `unknown`; they are not promoted
to `pass` by optimism.

## Redaction (record-time layer)

Applied by `ledger_lib` at append to `paths` and all string values inside `extra`:

- `wrangler secret put <KEY> …` → value scrubbed
- `Authorization: …` headers → value scrubbed
- `Bearer <token>` → token scrubbed
- `sk_…` key shapes → scrubbed
- `eyJ…` JWT shapes → scrubbed

Extensible via the `redact_patterns` argument (PR-1d feeds `redact_extra` from
`.aegis/brief.json`). Render-time is the second layer (spec §2): capsule output renders
normalized verb+paths, never raw command strings.

## Fallback backend (contract defined now, not "if needed")

If SQLite-in-hooks proves fragile: per-session JSONL shards at
`<store-dir>/shards/<session_id>.jsonl`, one JSON event per line, **same schema**, same
append semantics, same reader merge behavior (merged across shards, ordered by
`(ts, event_id)`). Select with `AEGIS_LEDGER_BACKEND=jsonl` or
`open_ledger(backend="jsonl")`. The full test suite runs against both backends.

## Query recipes

```bash
aegis ledger path                          # resolve the store for the current repo
sqlite3 "$(aegis ledger path)" \
  "SELECT ts, event_type, tool_name, paths FROM events ORDER BY ts DESC LIMIT 20"
sqlite3 "$(aegis ledger path)" \
  "SELECT * FROM events WHERE session_id = :sid ORDER BY ts"
sqlite3 "$(aegis ledger path)" \
  "SELECT extra FROM events WHERE event_type = 'verification' ORDER BY ts DESC LIMIT 5"
```

## Reader API (backend-agnostic from PR-1a)

```python
ledger = ledger_lib.open_ledger(cwd=repo_root)          # sqlite by default
ledger.append({...})                                    # normalize + redact + append
ledger.read(session_id=..., event_type=..., since_ts=..., agent_id=..., limit=...)
```

Additional exact-match filters are `repository_identity`, `worktree_root`, `branch`,
`head`, and `parent_agent_id`. `read()` returns events ordered by `(ts, event_id)`;
`limit` keeps the most recent N.

## Worktree and branch isolation

- The delivery witness reads current-repository/current-branch events and requires
  verification evidence at the current full `HEAD`. A newer sibling-branch run cannot
  satisfy the current branch merely because it shares the same database.
- Replay ingestion defaults to the current repository and branch. Corpus work must opt
  into another branch or `all_branches=True` explicitly.
- Legacy rows with NULL repository identity remain readable from the repository-specific
  store for compatibility, but branchless rows do not satisfy branch-scoped verification.
- Removing a linked worktree removes no ledger rows: ownership belongs to the Git common
  directory, while `worktree_root` preserves where each event occurred.

## Codex capture boundary

The Codex adapter installs synchronous, passive handlers for `SessionStart`,
`PostToolUse`, `SubagentStart`, and `SubagentStop` in `.codex/hooks.json`. Installation
merges only exact Aegis handlers and preserves unrelated project hooks. Codex requires
project-hook trust by definition hash; a trusted `SessionStart` proves adapter activation.
Current lifecycle payloads identify a child and the parent session root, but do not expose
an arbitrary nested parent-agent chain. Aegis records the factual session-root parent and
does not fabricate deeper ancestry.
