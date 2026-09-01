# Aegis Derived Obsidian Vault

## Status

Task 243 introduced a read-only, disposable Obsidian-compatible projection over Aegis evidence.
Bead `ga-zbmk` makes the projection authority-aware: an explicitly supplied Gas City bead
snapshot is current work authority, while Taskmaster remains a read-only compatibility input for
historical repositories. The vault is a knowledge view, not a workflow database and not a
replacement for beads, Git, the passive ledger, the computed capsule, the delivery witness, or
preserved S:W:H:E narrative.

The authority chain is:

```text
Git + explicit Gas City bead snapshot + passive ledger + capsule + witness
                 + preserved legacy narrative
                                      |
                                      v
                       deterministic Obsidian projection
```

When no bead snapshot is supplied, the compatibility chain substitutes legacy Taskmaster for the
bead snapshot. Aegis never merges both authorities or guesses which bead store applies.

Nothing in the vault is read back into Aegis. Editing a generated note has no effect on task,
delivery, policy, or repository state, and the next build refuses to overwrite that edit rather
than silently discarding it.

## Commands

```bash
# Resolve the default path beside the out-of-worktree ledger.
aegis vault path --target-dir .

# Build or refresh atomically.
aegis vault build --target-dir .

# Beads-first build from an explicit, frozen host snapshot.
aegis vault build --target-dir . --beads-json /owner/evidence/beads.json

# Verify ownership, exact inventory, hashes, and source freshness.
aegis vault check --target-dir .

# Explicit workflow boundaries; never run after every mutation.
aegis vault gate --target-dir . --beads-json /owner/evidence/beads.json --phase readiness
aegis vault gate --target-dir . --beads-json /owner/evidence/beads.json --phase closeout
aegis vault gate --target-dir . --beads-json /owner/evidence/beads.json --phase publication

# Use a deliberate out-of-repository destination.
aegis vault build --target-dir . --output /safe/path/project-aegis-vault

# Host-maintained freshness from an explicit project registry.
aegis-obsidian-reconcile run --registry ~/.config/aegis/obsidian-projects.json
aegis-obsidian-reconcile check --registry ~/.config/aegis/obsidian-projects.json
aegis-obsidian-reconcile check --registry ~/.config/aegis/obsidian-projects.json --require-live-index
```

The bead snapshot may be a JSON array, a `beads`/`issues`/`records` envelope, or a Beads JSONL
export. It is read only, size bounded, duplicate-key checked, identifier validated, and never
discovered implicitly. Bead titles, labels, and descriptions are excluded by default; enable
them only with the deliberate `--include-bead-content` content-policy switch and use the same
switch for build, check, and gate. Assignee/owner identities are treated as human content and
follow the same opt-in policy.

The default is:

```text
${XDG_STATE_HOME:-~/.local/state}/aegis/<repository-key>/obsidian-vault
```

The generator rejects any output inside the source repository. The vault therefore cannot make
the product worktree dirty, enter a pull request accidentally, or become a competing tracked
state surface.

For the real WSL Obsidian vault, use one Aegis-owned subtree such as
`/home/loucmane/vaults/main/GasCity/<project>/Aegis`. The existing Gas City projector owns
`GasCity/<project>/Tasks/`, agents own `GasCity/<project>/Docs/worklogs/`, and humans own the
remaining vault. These ownership boundaries must never overlap.

## Continuous reconciliation

The generated vault stays disposable, but it is no longer dependent on an operator remembering a
manual refresh. One user-scoped systemd timer runs every minute and after boot. A strict registry
declares each enabled project with:

- a stable project id;
- an absolute Git target directory;
- a disjoint absolute output subtree;
- an exact absolute-argv read-only bead export;
- an explicit human-content policy;
- freshness, debounce, and export-timeout bounds.

An enabled project may also declare one strict `live_index` observer:

```json
{
  "obsidian_cli": "/home/example/.local/bin/obsidian",
  "vault": "main",
  "probe_path": "GasCity/example/Aegis/Beads/example-1.md",
  "timeout_seconds": 15
}
```

This is deliberately not an arbitrary command hook. The reconciler derives only the supported
`vault=<id> reload` and `vault=<id> read path=<managed-note>` invocations, executes the absolute
binary directly without a shell, bounds time and output, and refreshes only after a changed
publication has passed all filesystem gates. A byte-identical reconciliation performs no host
application call. If Obsidian is closed or unreachable, the valid filesystem projection remains
authoritative and the observer is recorded as unavailable. The explicit
`check --require-live-index` gate is the stronger host-only proof that a running Obsidian process
can read the configured managed note.

The reconciler never starts a rig or database, discovers a store, or edits a repository. It reads
whatever the declared host command can currently prove. Reconciliation and strict checks serialize
through the same non-blocking registry-cycle lock, so a check never compares a dashboard or project
against bytes from two different cycles. It retains the
last valid output on failure, records last-success and last-error state with mode `0600`, and runs
all three vault gates after every changed publication. Because publication is an atomic directory
exchange, the hardened service grants write access to each registered output's existing parent,
not the source repository or the rest of the home directory. The `check` surface re-exports
sources and recomputes the digest, so its health signal is source freshness rather than “the timer
ran.” Its default result remains filesystem-authoritative. Live host-application reachability is
reported separately and becomes blocking only when `--require-live-index` is requested.

The timer is intentionally not a per-edit hook. A one-minute coalescing window avoids turning a
large atomic vault into a write-amplifying workflow database while giving the readiness doctor a
short, enforceable freshness SLA.

## Graph Model

Generated Markdown notes use deterministic YAML properties and path-qualified wikilinks. The
first implementation emits:

- one bounded orientation note;
- bead notes from the explicit Gas City snapshot, or task/subtask notes from legacy Taskmaster;
- session, branch, agent, and worktree nodes observed in high-signal ledger events;
- witness, verification, delivery, bead/work/task-truth, operator-authority, risk, and tool-failure
  evidence notes;
- structural inventory notes for preserved session, plan, tracker, implementation, changelog,
  decision, finding, and handoff documents;
- activity and evidence indexes;
- `.base` views for all work, compatibility tasks, evidence, and legacy documents.

Obsidian turns internal links into graph edges; Properties provide typed note metadata; Bases
provide table views over those properties. The projection uses only those native formats, so it
does not install or require an Obsidian plugin:

- [Obsidian internal links](https://obsidian.md/help/links)
- [Obsidian Properties](https://obsidian.md/help/properties)
- [Obsidian Bases](https://obsidian.md/help/bases)
- [Obsidian Graph view](https://obsidian.md/help/plugins/graph)

The output deliberately does not generate `.obsidian/`, prescribe a theme, or modify a user's
Obsidian settings.

## Context And Output Budget

The ledger can contain tens of thousands of low-level mutation and gate events. Turning every
row into a note would create an unusable graph and would cause every read-only hook invocation to
make the vault stale. Therefore:

- only high-signal lifecycle, scope, work-truth, risk, verification, witness, delivery, authority, and
  failure events affect the graph;
- mutation and gate-decision rows remain queryable in the ledger but are not expanded into notes;
- a deduplicated identity edge set (agent, parent, session, branch, and worktree) is derived from
  all rows, so repeated low-level calls do not churn the graph while genuinely new topology is
  visible;
- event metadata is allowlisted and clipped;
- raw command strings are never copied;
- evidence, work-item, session, branch, agent, worktree, and legacy-document counts have hard limits
  (the legacy ceiling is 5,000 after source-repository dogfood measured 2,175 real documents);
- a limit violation fails before replacing a current vault.

This is an LLM-context design constraint as much as an Obsidian usability decision: navigating
the view must never dump the raw flight recorder into an agent's context window.

## Legacy Coexistence

Legacy workflow files remain valuable because they contain decisions, plans, narrative,
trade-offs, and failure context that cannot be reconstructed reliably from tool telemetry. The
vault inventories their human-authored content outside Aegis generated-marker blocks and links it
to matching work nodes. It records:

- repository-relative source path;
- document kind;
- byte size;
- human-authored nonblank line count;
- heading sample;
- checkbox and S:W:H:E counts;
- generated-block count;
- deterministic content digest;
- related task or bead IDs.

It does **not** copy the full prose by default. The repository document remains the narrative
authority. This makes unique legacy content measurable without turning the vault into an
uncontrolled duplicate or leaking arbitrary historical text into another storage surface.

The coexistence rule remains:

- ledger/capsule/witness own observed current truth and delivery proof;
- legacy S:W:H:E files retain or receive human narrative and durable handoff context;
- the vault supplies navigation and cross-surface relationships;
- no legacy surface is demoted or retired merely because a vault note exists.

## Safety And Atomicity

Every generated vault contains `.aegis-vault.json`, which declares the generator, source digest,
source HEAD, exact owned-file inventory, and SHA-256 hash of every generated file.

Before rebuilding, Aegis requires:

1. the directory is not a symlink;
2. the manifest identifies an Aegis-owned generated root;
3. the actual inventory exactly matches the manifest, except that a pure loss of generated owned
   files may be repaired when every survivor still matches the old manifest, no unknown file is
   present, and every regenerated overlapping file has the exact previously declared digest;
4. every owned file still matches its hash;
5. no unknown/manual file has appeared.

The complete next vault is written to a sibling staging directory and self-checked. Directory
replacement uses same-filesystem atomic renames, with the previous valid vault retained as a
rollback target until the replacement succeeds. The synchronous vault gate remains strict and
reports missing files until that digest-proven atomic repair completes. A byte-identical complete
source snapshot is a no-op.

The user-level installer stops the timer first, waits for any already-activated oneshot service to
finish, and issues a final idempotent service stop to cancel any queued activation before capturing
rollback snapshots. It installs and validates with the timer held inactive, starts the timer after
the strict check passes, and verifies the settled scheduler policy (`enabled/active/waiting` timer
plus inactive service) rather than comparing transient `running/start` substates observed before
quiescence. A rollback primes the restored runtime only when the post-quiescence baseline had a
successful service result; a previously failed result is preserved without replaying the known-bad
cycle.

The generator never:

- writes the source repository;
- appends ledger rows;
- updates beads or Taskmaster;
- compiles or rewrites the capsule;
- invokes GitHub;
- drains pending evidence;
- deletes or overwrites unknown files;
- follows output symlinks;
- imports changes from Obsidian.

## Privacy

Ledger capture-time redaction remains the first defense. The vault adds a second bounded
projection layer:

- only an allowlist of event metadata is rendered;
- raw commands and arbitrary `extra` payloads are omitted;
- common bearer, GitHub, OpenAI-style, and JWT token shapes are redacted;
- worktree and agent note filenames use fingerprints;
- legacy documents contribute structure and hashes, not full body text.

The generated vault still contains project and workflow metadata. Operators should protect its
XDG state directory with the same care as the ledger.

## Validation Contract

Acceptance requires:

- two builds over the same authoritative input are byte-identical and the second is a no-op;
- additional low-level gate/mutation traffic does not churn the graph;
- a new high-signal event changes the source digest;
- links connect tasks, sessions, branches, agents, worktrees, evidence, and legacy documents;
- in-repository, symlinked, unknown, or tampered outputs fail closed;
- a failed staged build leaves the previous valid vault intact;
- source files remain byte-identical;
- `aegis vault check` detects stale or modified output without writing;
- `aegis vault gate` blocks readiness, closeout, or publication when the projection is missing,
  stale, modified, empty for a declared authority, or built from the wrong authority;
- automatic reconciliation preserves the last valid tree on source/export/publication failure,
  becomes a byte no-op when current, and reports a stale source digest even inside the SLA window;
- the user timer is enabled, reboot-persistent, and writes only its private state plus registered
  Aegis output subtrees;
- realistic Blog and HP-Fetcher event volumes remain within the documented bounds.

## Non-Goals

This slice does not:

- migrate Taskmaster records into beads or mutate either authority;
- discover a bead database or start Dolt (the optional host reconciler executes only registry-pinned
  absolute argv and never invents a command);
- make the Obsidian graph authoritative or implement vault-to-beads writeback;
- require a vault write after each source mutation;
- replace the legacy S:W:H:E workflow;
- install Obsidian or the Kepano Obsidian skills;
- publish a multi-user knowledge service;
- treat the graph as proof of policy compliance.

Those decisions remain separate and require their own reviewed authority boundary.
