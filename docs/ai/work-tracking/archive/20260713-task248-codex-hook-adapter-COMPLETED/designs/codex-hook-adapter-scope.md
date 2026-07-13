# Task 248 Scope — First-Class Codex Hook Adapter

## Problem statement

Codex 0.144.3 can match canonical `apply_patch` tool calls through either the
`apply_patch` matcher or the `Edit`/`Write` aliases. The hook payload is not
renamed by the alias: stdin still carries `tool_name: "apply_patch"` and the
entire patch in `tool_input.command`.

The current Aegis runtime does not classify that canonical tool name:

- `FILE_MUTATION_TOOLS` contains only Claude edit tool names.
- `HOOKABLE_TOOLS`, required-field validation, degraded classification,
  mutation classification, observation policy, evidence extraction, and
  handler attribution therefore omit `apply_patch`.
- `file_paths_from_payload` extracts only a single Claude `file_path` or
  `notebook_path`, while one patch can mutate several source and destination
  paths atomically.

The hook can consequently fire while Aegis treats the call as non-hookable.
Task 248 closes that gap and promotes Codex hooks from planned documentation to
an installed, verified adapter.

## Authoritative runtime contract

The parser accepts exactly one patch envelope:

1. The first non-empty line is `*** Begin Patch`.
2. The last non-empty line is `*** End Patch`.
3. The envelope contains at least one operation header.
4. Operation headers are exactly `*** Add File:`, `*** Update File:`, or
   `*** Delete File:` followed by a non-empty path.
5. `*** Move to:` is valid only once inside an Update operation and contributes
   a distinct destination path.
6. Unknown `*** ...` directives, nested envelopes, trailing material,
   path-control characters, duplicate/ambiguous move directives, and empty
   patches fail classification safely.

Every path is resolved lexically against the repository root, normalized to a
repository-relative POSIX path, and rejected if it escapes the root. Source
and destination paths are retained in operation order with stable de-duplication.
Policy checks operate over the complete path set; no primary or safe first path
can suppress a protected or workflow-owned later path.

The parsed representation contains:

- operation type (`add`, `update`, `delete`, `move` metadata on update);
- normalized source and optional destination;
- ordered `affected_paths`;
- primary evidence path (first normalized affected path);
- SHA-256 digest of the exact patch command bytes.

## Gate and evidence integration

Canonical `apply_patch` becomes a first-class hookable file mutation:

- required input: non-empty `tool_input.command`;
- readiness: identical to existing file mutations;
- observation: denied as a persistent mutation;
- protected/workflow paths: every parsed path is checked;
- strict/advisory: existing verdict machinery remains authoritative;
- degraded mode: malformed or classifier-failed patches fail closed in strict
  mode and record `would_block` in advisory mode;
- PostToolUse: one successful tool call creates exactly one pending event;
- event metadata: `handler=codex:apply_patch`, primary `evidence`, complete
  `affected_paths`, operation records, and deterministic `patch_digest`.

The event remains one atomic unit even for multiple files. Existing Claude and
MCP event formats remain backward-compatible; the new fields are additive.

## Installer and adapter boundary

The installer will own `.codex/hooks.json` when the Codex adapter is enabled.
The file uses project-relative git-root resolution so sessions started in a
subdirectory still dispatch to the installed Aegis scripts. PreToolUse and
PostToolUse match `Bash`, canonical `apply_patch`, and MCP tools. Stop remains
unmatched because Codex ignores matchers for Stop.

Codex dispatch must not depend on Claude being selected. Codex-only installs
therefore receive the shared hook runtime scripts needed by the Codex hook
file even when `.claude/settings.json` and `CLAUDE.md` are absent. Multi-agent
installs share the same runtime bytes and do not duplicate hook logic.

Installer behavior remains conservative:

- absent managed files can be created;
- byte-identical or previously managed files can be updated idempotently;
- pre-existing unowned `.codex/hooks.json` is adopted only when semantically
  safe under the existing installer contract;
- conflicting manual content is surfaced for manual review and never silently
  overwritten;
- creating or changing Codex hook definitions emits a Codex client-reload and
  `/hooks` exact-hash trust requirement;
- verification records adapter entrypoint, hook registration, managed files,
  gate coverage, and reload/trust guidance.

Only after runtime, installer, and live smoke acceptance pass will the adapter
contract move Codex from `planned` to `implemented`.

## Verification matrix

Focused tests must prove:

- READY allow and BLOCKED readiness handling;
- Add, Update, Delete, and Update-with-Move parsing;
- multi-file and safe-first/protected-later classification;
- protected and workflow-owned source/destination paths;
- malformed, empty, ambiguous, escaping, and unsupported patches;
- strict and advisory degraded behavior;
- exactly one PostToolUse pending event with every affected path and a stable
  digest;
- live/package `gate_lib.py` byte parity;
- installer preview/apply/idempotence and conflict refusal;
- Codex-only and Codex+Claude profiles;
- manifest/profile/schema/verification records;
- a real `codex-cli 0.144.3` hook smoke showing canonical stdin and Aegis
  dispatch without bypassing persisted hook trust.

## Non-goals

- No PR-4 retirement of legacy sessions, plans, trackers, handoffs, or S:W:H:E.
- No hash chain, OS sandbox, policy DSL, or unrelated installer refactor.
- No direct writes to local `.aegis` state.
- No Blog mutation until the upstream Task 248 merge is synchronized.
- No hook-trust bypass during the Blog rollout.

## Delivery boundary

Task 248 is delivered through the repository's normal protected CI and
evidence-gated policy. After merge, Blog receives the supported Aegis update
preview/apply/strict-verify flow. The rollout stops at `/hooks` so the owner can
review and trust the exact generated hook hashes.
