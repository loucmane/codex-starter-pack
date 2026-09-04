# Claude orchestrator command permissions

A successful Aegis PreToolUse check is normally a silent exit zero. Claude then
applies its native permissions; in `dontAsk` mode an unapproved command is refused.
The ga-e0t1 live probe established this exact split: both hooks passed, then Claude
refused `project_context.py --check` before the shell executed it.

## Opt-in profile, not a wildcard Bash grant

`.claude/orchestrator-command-profile.json` is a project-local, protected opt-in.
Operations enables three command classes, using the existing closed grammar:

- `project-context`: the unchanged canonical `project_context.py`, current root,
  and `--check` only.
- `beads-read`: the managed absolute `gc`, exact city and descriptor-matching rig,
  followed by `bd show`, `list`, or `ready` and their closed read-only flags.
- `workflow-begin`: the unchanged canonical `workflow.py begin`, targeting the
  canonical checkout, with its existing Bead/slug/goal/dry-run grammar. Internal
  project, Bead, worktree, ownership, journal and readiness checks remain in force.

Only after the applicable strict gate checks succeed, the bridge records a
payload-digest decision and emits Claude's `hookSpecificOutput.permissionDecision`
as `allow`. It does **not** return early from the existing gate. Observation,
pending tracking, protected paths, hard policy and native-delegation restrictions
retain precedence. Advisory success and degraded fallbacks never issue this approval.
Unknown or missing permission modes never receive a bootstrap mutation approval.
Explicit native deny/ask rules and other hooks' denials are not overridden.

Plan mode has a separate hard boundary: hookable mutations and provider-native
delegation are explicitly refused before bootstrap, readiness, or delegation
exceptions can return success. The same refusal runs before the degraded advisory
fallback. Read-only inspection keeps the existing classifier and permission
checks. Plan-file writes, real kickoff, tracking logs, and repair/apply commands
have no exemption. Unclassifiable plan-mode hookable requests fail closed; an
unavailable audit sink cannot convert denial into permission. This does not grant
new rights to normal, missing, or unknown modes.

The R4 real-client test demonstrated why this is necessary: withholding an
`allow` message still let Claude execute `workflow.py begin` in plan mode. A
negative acceptance must prove exit/refusal plus zero requested mutation, not
merely the absence of approval JSON. Gate-owned denial audit records are expected;
they do not permit the requested command to run.

The profile is permission policy, not operator task authorization. A supported
command remains subject to the operator's stated scope. It grants no signing,
push/merge, Bead mutation CLI, dispatch, lifecycle, file-write or privileged access.
It does not prove Claude implementation-worker capabilities.

## Identity and preservation

The profile must be a regular, unaliased, size-bounded JSON object with unique
keys, exact schema and a nonempty subset of the three known command classes.
Both task and canonical copies must equal their tracked HEAD bytes **and each
other**. A task branch cannot opt itself in or expand the canonical grant. The
managed descriptor, Git remote/common-directory identity, current hook cwd, city,
rig and direct-child worktree placement must agree. Exceptional worktree layouts
are not supported by this profile version and receive no implicit exemption.

Python entrypoints must come from the canonical checkout. Dirty or untracked
runtime source under the shared scripts/package roots blocks native approval;
testing an uncommitted runtime is not an unattended production permission grant.
Profile drift and approval-audit failure refuse before emitting an approval.
No profile means existing behavior. Unknown commands defer to existing native
permissions; the profile is not a replacement for the rest of the permission policy.

The new opt-in is Operations-only. It is not copied into the generic installer,
HPFetcher or Blog. Activation is a reviewed, merge-bound canonical fast-forward:
capture old HEAD and config hashes, verify clean canonical state, advance to the
exact reviewed merge, then verify module/profile bytes and fresh-session behavior.
Do not reset history or overwrite user settings for rollback. An activation
failure stops for an evidenced append-forward correction; no broad permission or
mode fallback is allowed. User/project settings, MCP configuration, hooks and
permission arrays are unchanged by this profile.

## Acceptance before PASS

Run the full adapter and meta-workflow suites, managed-asset parity/goldens and
source guard. Then use a compatible, already-installed Claude client in a fresh
session with normal hooks loaded. A unit test of exit zero is insufficient.
Require actual shell execution for context and scoped ledger reads, and prove
native explicit deny/ask precedence. In an isolated synthetic managed-project
fixture, prove real transactional begin with a bounded acceptance Bead, followed
by fresh-session task-worktree behavior. File-write capability is a separate
native permission and must not be smuggled into this command profile. Re-prove
observation/stop and adversarial refusals. Preserve all failed attempts and do not
close ga-e0t1 based only on parser or hook simulation results.

The opt-in remains task-scoped under the operator's standing authorization: normal
implementation steps and understood safe retries do not require renewed approval
for each command. A genuinely new access, disclosure, privileged, destructive, or
task boundary still needs authority. Independent review and actual live acceptance
are checkpoints, not requests to reauthorize the same edit/test cycle.

Protocol references: [Claude permissions](https://code.claude.com/docs/en/permissions)
and [PreToolUse hook decisions](https://code.claude.com/docs/en/hooks).
