# Task 240 Worktree And Child-Agent Evidence Report

## Verdict

Task 240 closes the causal capture gap selected by Task 239 without replacing the
already-correct Git-common-dir store. Installed Codex targets now receive passive,
structurally merged project hooks for `SessionStart`, `PostToolUse`, `SubagentStart`,
and `SubagentStop`. Events from the main checkout and linked worktrees resolve one
repository ledger while retaining the worktree, branch, observed HEAD, agent, and
supported parent relationship that existed at capture time.

The deterministic installed-target scenario records two child worktrees concurrently:
one successful `apply_patch` mutation and one failed Bash command. It then records a
child lifecycle start and stop, removes both worktrees normally, and proves every row
remains in the shared store. Branch-scoped witness and replay reads reject unrelated
sibling traffic.

The result is **supported for installed Codex project hooks and additive Claude hook
enrichment**, with explicit degradation for clients that do not expose hooks, for
untrusted Codex project hooks, and for ancestry deeper than the parent identity supplied
by the client or adapter environment bridge.

## Audit Boundary

- Implementation branch: `feat/task-240-worktree-child-evidence`.
- Baseline commit: `c9c496487215df100f532c822b12480185d36949`.
- Enforcement remains advisory.
- Ledger schema remains version `1`; no historical row is rewritten.
- The repository's local untracked `.codex/hooks.json` and unrelated `.codex`,
  `.agents`, and `.aegis` drift are not read as authoritative assets, modified, staged,
  or adopted by this task.
- Tests install Aegis into disposable repositories and use isolated XDG state roots.
  No user credentials, transcripts, or raw production payloads enter checked-in
  evidence.

## Measured Before And After

The before measurements come from Task 239's normalized live fixture and coverage
report. The after measurements come from the deterministic installed-target acceptance
test and focused query/migration regressions.

| Capability | Task 239 before | Task 240 after |
| --- | --- | --- |
| Installed Codex project-hook events | 0 attributable nested-session rows | 6 retained rows: 5 native hook-derived rows plus 1 inferred scope row |
| Codex child mutation capture | 0 | 1 successful `apply_patch` mutation with path, branch, HEAD, child, and parent attribution |
| Codex child failure capture | 0 | 1 `tool_failure` row for nonzero Bash, attributed to the second child worktree |
| Codex child lifecycle | 0 | 1 `subagent_begin` and 1 `subagent_end` row |
| Repository/worktree/HEAD attribution | absent from child rows | present on 6/6 installed-scenario rows |
| Agent identity/type | no Codex child rows | present on 6/6 installed-scenario rows |
| Parent identity | absent | present on every child-derived row; intentionally null on the root-session row |
| Shared mutable stores | 1 repository store | 1 repository store; 0 per-worktree `.aegis/state` directories |
| Child worktrees exercised together | no attributable Codex rows | 2 concurrent child hook writers on distinct branches/worktree roots |
| Teardown retention | 10,159/10,159 Task 239 rows retained | 6/6 Task 240 scenario rows retained after normal removal of both child worktrees |
| Branch-safe replay | unscoped ledger ingestion | current branch by default; explicit branch and all-branches escape hatches |
| Branch-safe witness | sibling traffic could be selected by recency | sibling verification cannot satisfy current-branch verification-at-HEAD |

The extra sixth row in the installed scenario is expected: the first child mutation
derives the zero-ceremony scope record for `feat/task-2-child`. Task 240 propagates the
triggering child and parent attribution into that generated row, rather than allowing a
derived record to lose provenance.

## Installed Codex Scenario

`test_installed_codex_hooks_capture_linked_worktree_and_child_lifecycle` proves the
installed rather than source-only path:

1. Install a Codex-only target and commit the shim, runtime pointer, and merged
   `.codex/hooks.json`.
2. Create two linked child worktrees on distinct task branches.
3. Record a root PostToolUse event.
4. Invoke the two child PostToolUse hooks concurrently: a successful `apply_patch` and a
   failed Bash command.
5. Record `SubagentStart` and `SubagentStop` for the first child.
6. Assert one ledger file, one repository identity, three worktree roots, three
   branches, complete observed HEAD values, and complete agent identity/type values.
7. Assert all child-derived events link to `session:parent-session`; the root event has
   no fabricated parent.
8. Assert SubagentStop emits valid `{}` JSON as required by the Codex hook protocol.
9. Remove both worktrees without force and prove the ledger still contains all six
   rows.

## Concurrency, Migration, And Query Isolation

- Four independent SQLite processes append 25 rows each; all 100 rows remain and retain
  their writer sessions.
- A deliberate `BEGIN IMMEDIATE` lock is released after 150 ms; the blocked append
  retries successfully and both the pre-lock and post-lock rows remain.
- SQLite and JSONL backends resolve the same repository identity for linked worktrees,
  retain distinct worktree/branch context, and preserve rows after teardown.
- A legacy pre-Task-240 SQLite table remains readable in read-only mode with null new
  fields. The first writable open adds nullable columns/indexes and preserves the old
  row before appending an enriched row.
- Ledger reads filter by repository identity, worktree root, branch, HEAD, and parent
  agent in addition to the existing dimensions.
- Replay ingestion defaults to the current branch. `branch=` selects an explicit branch
  and `all_branches=True` is the deliberate corpus-analysis escape hatch.
- The delivery witness requires current-branch evidence. A newer sibling-worktree
  verification cannot satisfy the current branch; current-branch verification then
  passes normally.

## Installer And Activation Safety

- The installer structurally merges Aegis-owned synchronous handlers into existing
  `.codex/hooks.json` while preserving unrelated top-level metadata, event groups, and
  commands.
- Invalid or structurally incompatible project hook JSON is classified for manual
  review and install refuses to overwrite it.
- Reinstall is idempotent.
- Uninstall removes only exact Aegis-owned commands and preserves project hooks.
- Codex and Claude reload markers clear independently. Codex clears only its marker
  after a trusted `SessionStart` hook reaches the runtime; remaining clients stay
  pending.
- Installed guidance tells Codex users to restart, trust the exact project hooks through
  `/hooks`, and use `/clear` when needed. A marker is not cleared merely because install
  wrote the file.
- Source and packaged copies of the installer, gate, ledger, witness, adapter contract,
  and release-verification matrix remain byte-identical.

## Verification Evidence

| Verification | Result |
| --- | --- |
| Changed Claude-adapter core suites | 92 passed |
| Full installer suite | 139 passed, 1 opt-in certification smoke skipped |
| Schema, asset-parity, replay-coldstart, and PR-4 parity suites | 43 passed |
| Ledger plus witness focused rerun | 52 passed |
| Tightened installed Codex two-worktree scenario | 1 passed |
| Codex reload/continuation/repair/release-contract regressions | 21 passed |
| Repository suite in the temp worktree | 1,908 passed, 4 opt-in smokes skipped; one unchanged temp-location premise deferred to hosted CI |
| Black | 17 changed Python files clean |
| Ruff | changed Python files clean |
| Runtime/package `cmp` checks | 6 mirror pairs byte-identical |
| Taskmaster graph health | 245 tasks, 383 subtasks, 430 valid dependency references, 0 invalid |
| Plan/tracker sync | passed |
| Source meta-workflow pipeline | timestamp, guard, zero drift, six scanners, reference-fix, monitoring, performance, cost, and migration commands passed |
| `git diff --check` | passed at the completed implementation/evidence head |

The installer suite's single skip is the existing opt-in full release certification
smoke (`AEGIS_RUN_CERTIFICATION_SMOKE=1`); it is not a Task 240 behavioral omission.
The repository-wide run has four existing opt-in distribution/MCP skips. Its only local
deselection is an unchanged safety test whose governed-repository path must be outside
the system temp directory; hosted CI supplies that environment and remains mandatory.

## Explicit Capability Boundaries

- Codex project hooks must be trusted by exact hash. If they are untrusted or the client
  has not restarted after install, Aegis reports reload-required rather than claiming
  capture.
- Codex currently runs command hooks synchronously; asynchronous command handlers are
  parsed but skipped by the client, so Aegis intentionally installs synchronous,
  failure-proof recorder commands.
- Current Codex payloads supply a session-root relationship but do not guarantee an
  arbitrary nested parent chain on every tool event. Deeper ancestry is recorded only
  when the client supplies it or the launcher exports `AEGIS_PARENT_AGENT_ID`; Aegis
  never guesses it from parent traffic.
- A client with no supported hook surface remains explicitly unsupported. Parent
  orchestration rows are never relabeled as child implementation.
- Claude hook events inherit repository/worktree context and accept child/parent fields
  when supplied. A nested Claude process that cannot execute its loaded hooks because
  its own client state is read-only remains a client-runtime degradation, not evidence
  of a successful child capture.
- Legacy branchless rows remain readable but cannot satisfy branch-scoped verification.

## Parent-Only Rollback

Rollback is additive and non-destructive:

1. Remove the four Aegis-owned Codex hook registrations through the normal installer or
   uninstall path; preserve every unrelated project hook.
2. Stop providing adapter identity defaults for new rows.
3. Keep the shared repository ledger, additive SQLite columns, historical enriched
   rows, and legacy rows intact.
4. Continue parent-only recording with an explicit degraded capability result.
5. Do not rewrite, delete, migrate, or repair ledger history and do not create
   per-worktree state.

This rollback returns capture to the Task 239 parent-only boundary without corrupting
or hiding evidence gathered while Task 240 was active.
