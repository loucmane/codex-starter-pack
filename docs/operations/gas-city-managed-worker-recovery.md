# Gas City managed-worker recovery and upgrade runbook

This runbook defines the supported recovery path for Gas City managed workers. It applies to Gas
City itself and to registered project rigs such as HPFetcher and Blog. Beads is the work authority;
Aegis and the Obsidian projection are the audit and publication layers.

## Safety contract

- Keep every unrelated rig suspended. Resume at most the one rig named by a reviewed proof.
- Treat a PID, systemd start timestamp, configuration digest, source tree, request, receipt, and
  worktree state as one precondition set. A mismatch is drift, not permission to repair.
- Workers prove only facts visible in their namespace: their bead, session, worktree, Git state,
  helper result, signature, and receipt. Service identity, cross-UID process state, cgroups, and
  host tmux residue are operator/readiness facts.
- Do not use a missing cross-UID `/proc` entry, an unreachable socket, or an empty sandbox process
  scan as proof that a host service or process is absent.
- Never force-close, signal, delete, reset, or clean evidence to make a failed attempt look clean.
- A failed attempt remains a failed evidence object. Continue append-forward after its exact state
  is understood.

## Preflight

Use the managed operator path and the real managed home:

```bash
export HOME=/home/loucmane
export GC_HOME=/home/loucmane/gascity/home
export PATH=/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin
```

Before routing or changing live state:

1. Read the authoritative bead from the intended rig store.
2. Require the target branch/worktree to match the reviewed base and expected cleanliness.
3. Require all unrelated rigs suspended and no unexplained sessions, workers, or tmux servers.
4. Record the supervisor, signer, and broker service epochs and restart counts.
5. Pin relevant installed binaries, managed fragments, resolved configuration, and receipts.
6. Run strict configuration validation and the applicable read-only doctor.

The host reboot/readiness authority is:

```bash
/home/loucmane/.local/bin/codex-wsl-readiness --observer host-wsl --json
```

The automatic Obsidian freshness and live-index authority is:

```bash
/home/loucmane/.local/bin/aegis-obsidian-reconcile check \
  --registry /home/loucmane/.config/aegis/obsidian-projects.json \
  --state-dir /home/loucmane/.local/state/aegis/obsidian-reconciler \
  --require-live-index
```

The installed registry is a generated projection of the canonical workflow project registry. It
must contain Gas City Operations, Gas City, HPFetcher, and Blog, plus any later validated project;
do not add projects by hand to the installed JSON. Every host registry entry declares the exact
absolute `rig_root`; never derive it from the city name or project ID. Regenerate the tracked source from the
canonical checkout and require an exact check before installation:

```bash
python3 plugins/gas-city-workflow/scripts/build_obsidian_registry.py --write --validate-roots
python3 plugins/gas-city-workflow/scripts/build_obsidian_registry.py --check --validate-roots
```

Each project is published only under `GasCity/<project-id>/Aegis`. The same timer also publishes
`GasCity/Continuity/Status.md` and `report.json`, derived directly from the machine continuity
report's Now, Next, Blocked, and Drift classifications. Project or dashboard publication failure
fails the whole reconciliation; a later surface is never presented as current after an earlier
project failed. Byte-identical cycles probe the live managed note without reloading Obsidian.
The installer stops the timer before capturing rollback state. A failed refresh restores the
installed files, private reconciler state, every managed output tree, the service result, and the
timer's enabled/active state before another attempt is eligible.

## Recovery classification

Classify the stopped attempt before taking another action:

| State | Allowed continuation |
| --- | --- |
| Pre-mutation refusal | Correct the proven cause and retry under the same still-applicable scope. |
| Idempotent operation already applied | Read back the exact target state; continue from the observed state instead of replaying. |
| Live mutation fully rolled back | Verify the complete predecessor state and corrected cause before an append-forward retry. |
| Ambiguous or partial mutation | Stop. Preserve everything and require a separately reviewed disposition. |
| Secret, pinentry, key, or unexplained security failure | Stop. Do not retry or weaken the check. |

Build, test, Git staging, network, hosted CI, and other non-live operations may be retried after
proving the previous attempt made no unintended durable mutation. Live service transitions,
signing, migrations, publication, and canaries require either a proven pre-mutation stop or a
complete rollback plus an understood correction.

## Session and tmux residue

The session ledger and host tmux state are separate evidence surfaces. A session may be absent
while its `tmux -L city` server remains as a childless process.

Residue detection must recognize both absolute and bare tmux invocations:

```python
os.path.basename(argv[0]) == "tmux" and "-L" in argv and "city" in argv
```

Do not use `argv[0].endswith("/tmux")`; it misses servers launched with `argv[0] == "tmux"`.

For an orphan server, record and reverify at execution time:

- boot ID, PID, session ID, parent PID, UID, kernel start ticks, and command-line digest;
- zero child processes and zero hosted tmux sessions;
- the supervisor, signer, and broker outside the process tree and on their pinned epochs.

Only then may recovery run exactly one graceful:

```bash
tmux -L city kill-server
```

Do not send a PID or process-group signal and do not add a fallback target. Afterward require the
verified PID to disappear, all authorities to remain stable, no new session to start, and two
stable reconciliation observations. If the server has a child or hosted session, stop instead.

## Worker failure and mailbox continuity

Closing a failed session releases ordinary claimed work but must not rewrite messaging-class bead
assignment. Unread named-session mail is mailbox addressing, not a worker assignment. Core source
must preserve that distinction so a stable named mailbox can recover unread delivery after an
abnormal pre-read close without duplicating the message.

Close the implementation bead honestly as PASS or FAIL only after its own acceptance evidence is
complete. Never reuse a failed canary bead as a later success.

## Managed signing and project access

- Invoke the managed helper once with the literal bead and observed session identifiers required by
  its policy. Do not hide classifier-relevant arguments behind variables, wrappers, or an `env`
  prefix.
- Treat the helper JSON, Git commit/tree/parent, signature fingerprint, and v2 receipt as one chain.
- Keep service/cgroup/epoch verification on the host side.
- Linked worktree profiles may grant only the project worktree root and the minimum main-repository
  Git metadata root. Blog therefore exposes `/home/loucmane/dev/blog/.git` to its managed profile,
  not unrelated repositories or the full home directory.
- A future project is onboarded through the reviewed declarative signing registration and generated
  bundle. Wildcard signing roots, cross-policy helpers, raw signing, and arbitrary broker paths are
  forbidden.

## Upgrade paths

Normal managed component replacement uses only an installed fixed broker operation with:

1. merge-bound artifact bytes and exact pre-state digests;
2. a signed bounded request;
3. atomic replacement of only the operation's fixed destinations;
4. the minimum named service transition;
5. a PASS receipt and stable post-transition epochs; and
6. byte-exact rollback on technical failure.

The broker cannot replace its own executable while serving a request. Its self-upgrader is the
single attended root bootstrap boundary. Use a merge-bound plan and expected plan ID, run `check`
first, and accept `apply` only when its built-in post-check proves the reviewed capability mask,
`NoNewPrivileges`, stable socket/service state, and a non-mutating smoke. Do not substitute an
ad-hoc root script.

## Reboot survival

A new reboot is required only when the acceptance contract changes. Otherwise reuse a recorded
boot transition and prove the current boot:

- WSL systemd enabled and boot ID readable;
- user linger enabled;
- the Windows `GasCity-WSL-Bootstrap` logon task matches its reviewed limited contract;
- canonical user supervisor enabled and active, with no stale enabled supervisor units;
- signer service/socket and broker socket/service enabled or active as designed;
- automatic Aegis/Obsidian reconciliation current and live-index readable;
- all project rigs suspended with zero unexplained sessions or process residue.

The known Codex Desktop WSL transport workaround remains an accepted warning only on a classified
affected build. Removing it is a separate attended retest with an external rollback path.

## Closeout

Before closing the coordinating recovery bead:

1. Re-run host readiness and require zero failures or unknowns.
2. Require the Obsidian reconciler filesystem and live-index checks to pass.
3. Require all non-HQ rigs suspended, zero sessions, and zero unexplained `tmux -L city` residue.
4. Read back every implementation/follow-up bead and bind its terminal evidence.
5. Record focused tests, Git state, installed digests, service epochs, receipts, and rollback facts.
6. Close the bead through the supported Beads API.
7. Force or await the supported reconciler publication, then prove the terminal managed note and a
   subsequent byte-identical no-op. Never hand-edit the managed vault subtree.
