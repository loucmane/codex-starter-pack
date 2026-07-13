# Task 241 Quiet Deterministic Witness Contract

## Outcome

`aegis witness` is the canonical local pre-delivery boundary. It evaluates repository
facts without an LLM, emits a one-screen default result through the Task 238 output
budget, and persists complete machine-readable and PR-ready evidence outside stdout.

Task 241 strengthens the existing witness. It does not retire legacy plans, sessions,
trackers, handoffs, closeout, or S:W:H:E narration. Those surfaces remain complementary
human context while the witness supplies deterministic delivery evidence.

## Stable Semantic Classes And Process Exits

Every report carries one top-level `exit_class` and `process_exit_code`:

| Semantic class | Meaning | Process exit |
| --- | --- | ---: |
| `pass` | Every required local check was derivable and passed. | `0` |
| `fail` | At least one deterministically evaluated safety check failed. | `1` |
| `unsupported` | A required local capability or configuration surface was unavailable, so the witness could not make a safe local delivery claim. | `2` |
| `not_derivable_in_ci` | No CI-derivable safety check failed, but the out-of-worktree ledger or local scope configuration intentionally does not travel to CI. Native CI remains authoritative for its own checks. | `0` |

`fail` has precedence over incomplete evidence. A deleted test, unmapped scope, stranded
done flip, or other deterministic failure therefore cannot be hidden by
`not_derivable_in_ci`. `unsupported` is not a pass and is process-failing locally. CI's
expected lack of local ledger evidence is represented by `not_derivable_in_ci`, not by
optimistic `pass` and not by a failing infrastructure error.

The compatibility field `passed` remains true for `pass` and
`not_derivable_in_ci`, because both are process-success states, and false for `fail` and
`unsupported`. Callers must use `exit_class` when they need the semantic distinction.

## Evidence Selection Boundary

The witness computes the current repository identity and canonical worktree root from
Task 240's `repository_context`. Local ledger reads use only rows that match:

1. the current branch;
2. the current repository identity, or a null legacy identity from the same
   repository-owned store; and
3. the current worktree root, or a null legacy worktree root retained for backward
   compatibility.

Rows attributed to a sibling worktree never satisfy scope or verification for the
current worktree, even when both worktrees use the same branch name or one row has a
newer timestamp. Parent/child attribution is preserved in the full report but does not
weaken repository, branch, worktree, or HEAD isolation.

The ledger is opened read-only. Missing or unreadable local ledger state is an explicit
`unsupported` capability result and must not create a new store as a side effect.

## Deterministic Checks

### Scope mapping

The current branch must map to a confirmed or inferred scope record, or to the existing
`task-NN` branch convention. Confirmed scope wins. Scope globs come from the selected
record, then the declared source roots and `witness.always_in_scope` configuration.

A missing task mapping is `fail`. A local witness with no usable path-glob
configuration is `unsupported`, because full diff accounting is not derivable. In CI,
where the ignored brief normally is absent, that same gap contributes
`not_derivable_in_ci` after all git-derivable failures are evaluated.

### Diff accounting and test escalation

The witness reads a NUL-delimited `git diff --name-status --find-renames` inventory.
Every old and new path in a rename is retained and accounted. The complete inventory,
matching glob, and accounting verdict are persisted; no path list is truncated in the
artifact.

Deleted tests always fail. A rename that moves a test out of a recognized test path is
also treated as a test deletion. This remains enforceable in CI even when scope globs
are unavailable.

### Verification at exact HEAD

Every configured verification gate needs a passing ledger event whose recorded `head`
or explicit `extra.commit` resolves to the current full HEAD object. Timestamps alone
never satisfy this check. A stale verification row with a future timestamp therefore
remains stale. An event from a sibling branch or worktree cannot satisfy the check.

No configured gates in a present configuration is a valid empty requirement. A missing
or malformed local gate configuration is `unsupported`; CI reports the local-ledger
portion as `not_derivable_in_ci`.

### Task-flip containment

The witness checks both index and working-tree changes against HEAD for an uncommitted
`done` flip, not only unstaged changes. It also reports committed done flips found in
the base-to-HEAD diff. Any uncommitted done flip is `fail`, preserving the stranded-#73
regression class.

### Native CI delegation

The witness reports native CI as `delegated`; it does not recreate provider checks or
infer remote status. The required GitHub workflow remains the source of truth for CI
greenness.

## Artifacts And Context Budget

Each run atomically replaces two generated artifacts:

- `.aegis/reports/witness-report.json`: complete structured report, including every
  diff path, check, capability, escalation, and semantic class;
- `.aegis/reports/delivery-report.md`: deterministic PR-ready summary with the full diff
  accounting and verification evidence.

Default and verbose stdout continue through Task 238's shared renderer. Default output
must remain at or below 60 lines and 8 KiB; verbose remains bounded; `--all` exposes the
complete payload. The concise text renderer names both artifact paths and never embeds
unbounded path or event lists.

Boundary-event recording and generated S:W:H:E projection remain best-effort post-verdict
operations. Their failure may produce a warning but cannot rewrite a deterministic
witness verdict.

## CI And Backward Compatibility

The existing required workflow may continue invoking `aegis witness --ci`. A clean CI
run with expected local evidence gaps returns process exit 0 and semantic class
`not_derivable_in_ci`; a git-derivable safety failure returns 1. Existing callers that
only inspect `passed` retain process-success compatibility.

The live and packaged `witness_lib.py` copies remain byte-identical. Installed targets
retain the same command name and flags. No policy DSL, hash chain, sandbox, retirement,
or LLM behavior is introduced.

## Acceptance Evidence

Focused regressions must prove:

- local pass and each stable class/exit mapping;
- missing ledger/configuration is explicit rather than optimistic;
- sibling same-branch worktree evidence is excluded;
- stale future-dated verification fails while exact-HEAD verification passes;
- old and new rename paths are fully accounted;
- test deletion and test-to-source rename escalate;
- staged and unstaged done flips fail;
- CI remains honest and still fails every git-derivable safety violation;
- JSON and Markdown artifacts retain all paths while default stdout stays in budget;
- live/package asset parity; and
- the real Task 241 branch can run the command as a dispatch-wave shipping step with
  measured latency, output bytes/lines, and a checked delivery artifact.

## Rollback

Revert the Task 241 runtime, CLI, tests, and documentation commit. The previous witness
command and manual shipping checklist resume unchanged. Generated Task 241 reports may
remain as non-authoritative evidence. No ledger rows, workflow state, legacy scaffolding,
or installed-target data are deleted or repaired.
