# Codex Desktop + WSL + Gas City Reboot Readiness

`scripts/codex-wsl-readiness` is the repository entry point for a read-only doctor covering
the layers that must survive a Windows restart:

1. Codex Desktop configuration and installed-version compatibility;
2. WSL systemd boot and user linger;
3. the canonical Gas City user supervisor;
4. stale per-home supervisor units;
5. the managed signing service and socket;
6. Gas City controller and bead-store reachability;
7. the exact personal operator-signing subkey cache state;
8. live host-WSL Obsidian IPC and managed-note readability; and
9. the Windows logon bootstrap task.

The doctor never repairs, restarts, enables, disables, routes, resumes, signs, or deletes.
Gas City subprocesses run with a deterministic `GC_HOME` derived from the managed city
layout (`<city-parent>/home`), matching the canonical supervisor unit instead of any legacy
`~/.gc` state inherited from the operator shell.

## Run it

From an ordinary WSL terminal:

```bash
cd /home/loucmane/codex
python3 scripts/codex-wsl-readiness
```

If an approved host-context run inherits Codex sandbox environment markers, declare the
vantage explicitly so the evidence is labelled honestly:

```bash
python3 scripts/codex-wsl-readiness --observer host-wsl
```

For machine-readable evidence:

```bash
cd /home/loucmane/codex
python3 scripts/codex-wsl-readiness --json
```

The Windows bootstrap does not depend on the repository path. Install the exact reviewed
doctor bytes into the stable user-tool path first:

```bash
scripts/install-codex-wsl-readiness --apply
scripts/install-codex-wsl-readiness --check
scripts/install-codex-gpg-readiness --apply
scripts/install-codex-gpg-readiness --check
```

The default destination is `~/.local/bin/codex-wsl-readiness`. The installer performs an
atomic byte-for-byte replacement, sets mode `0755`, and checks the installed version. It does
not enable or restart any service.

## Personal GPG readiness

The operator key and the Gas City managed signer are intentionally separate. Automated
workers use the dedicated managed signer and its v2 receipts. Human-authored operator commits
use subkey `FD5585922F5335BC378AD8D42ECF4432C7E7982D!` through the personal GPG agent.

`scripts/codex-gpg-readiness` fixes the ambiguity created by an any-key cache probe. It
queries only keygrip `640406DD1B34A5EA0BB7CB46F21071BB3DB370FA`; a cached retired,
revoked, unrelated, or primary key can never satisfy readiness. Its `check` operation uses
`gpg-connect-agent --no-autostart`, so the reboot doctor remains read-only.

Its attended `unlock` operation starts the existing agent and signs `/dev/null` with the exact
`FD55…!` subkey, leaving no signature artifact. It explicitly selects normal agent pinentry
mode. If GnuPG requests the passphrase, pinentry owns that prompt and the helper never sees or
stores the secret. Some GnuPG configurations can complete the exact signing proof while
`KEYINFO` still reports no ordinary passphrase-cache entry. In that case the helper records a
mode-`0600`, non-secret readiness proof under `$XDG_RUNTIME_DIR`, bound to the exact
fingerprint, keygrip, WSL boot ID, GPG-agent PID, and a 30-day expiry. A new agent, reboot,
expired proof, ownership/mode drift, or identity mismatch fails closed and requires a fresh
exact-key proof.

Install the helper and managed shell integration, then source the snippet once from `.zshrc`:

```zsh
source "$HOME/.config/codex/gpg-readiness.zsh"
```

The existing `unlock-all` function may continue coordinating SSH and GPG. The managed snippet
replaces only `gpg_cache_ready` and `gpg-unlock` with exact-key implementations. On the first
interactive terminal after a WSL restart, `unlock-all` performs one exact-key proof and prompts
only if GnuPG requires it. Later shells remain silent while either the exact agent cache or the
agent-epoch proof remains valid.

The encrypted passphrase is never stored. A WSL or Windows restart destroys the runtime proof
and in-memory GPG state, so one attended exact-key proof per WSL boot is the security boundary,
not a failure. The reboot doctor reports a cold state as `WARN` with the single remediation
`unlock-all`; it never launches the agent, signs, or attempts to obtain a secret.

Exit status:

- `0`: `READY` — every required check passed;
- `1`: `DEGRADED` — at least one warning or observer-limited unknown, no failures;
- `2`: `FAILED` — an authoritative required check failed.

## Observer truth

Codex worker sandboxes may be unable to connect to the user/system systemd buses, Windows
interop, the Gas City controller socket, or the local Dolt TCP endpoint. The doctor detects
the known denial signatures and reports those checks as `UNKNOWN(observer sandbox)` rather
than claiming the service is down.

An ordinary WSL terminal or the future Windows logon task is the authoritative execution
context for host service checks. Empty cross-UID `/proc` results are never accepted as proof
that a system service is absent.

`--observer` changes only the evidence label. It grants no access and must never be used to
turn an observer-limited `UNKNOWN` into a synthetic pass.

The same rule applies to host applications. A sandbox result such as `The CLI is unable to
find Obsidian` proves only that the sandbox could not reach Obsidian's host-side IPC. It does
not prove that the application is closed. The doctor therefore records that result as
`UNKNOWN(observer=codex-sandbox, authority=observer-limited)`. Only a real host-WSL run may
report live Obsidian reachability or its absence.

## Obsidian: projection authority versus live-app observation

These are deliberately separate contracts:

- `aegis vault build`, `aegis vault check`, and `aegis vault gate` operate on filesystem bytes.
  They are the authoritative publication checks and do not require Obsidian to be open.
- `obsidian vaults verbose` plus a managed-note read is an optional host-application smoke. It
  proves only that the running Obsidian process can see the projected bytes.
- `aegis-obsidian-reconcile check` is the host-side automatic-freshness proof. It re-exports the
  registered bead sources and recomputes the vault digest without mutating the vault.

The Aegis publisher atomically replaces its managed subtree. Windows-side Obsidian file watching
over WSL can keep the previous index after that directory swap even though the new filesystem
bytes and all vault gates are correct. A configured continuous reconciler therefore runs the
supported bounded `obsidian vault=<id> reload` command after a changed, fully gated publication
and immediately reads one configured managed note. It records this observer result separately;
a closed or unreachable app never invalidates correct filesystem bytes. A byte-identical timer
run does not reload the app. The host-only `aegis-obsidian-reconcile check
--require-live-index` gate repeats the managed-note read when live application proof is required.

The default doctor smoke targets vault `main` and
`GasCity/gas-city-operations/Aegis/Beads/ga-zbmk.md`. Other projects use the same doctor with
their own stable managed-note path:

```bash
python3 scripts/codex-wsl-readiness \
  --observer host-wsl \
  --obsidian-vault main \
  --obsidian-probe-path GasCity/<project>/Aegis/Beads/<stable-bead>.md
```

The project contract is uniform:

| Project class | Work authority | Durable Aegis output | Host-only evidence |
| --- | --- | --- | --- |
| Gas City operations | primary Gas City bead | `GasCity/gas-city-operations/Aegis/` | supervisor, signer, cross-UID process truth, Obsidian IPC |
| HPFetcher | HPFetcher rig bead | `GasCity/hpfetcher/Aegis/` | project services and Obsidian IPC |
| Blog | Blog rig bead | `GasCity/blog/Aegis/` | project services and Obsidian IPC |
| New project | project bead from initialization | `GasCity/<project>/Aegis/` | only the host checks declared by that project |

All projects are entries in one strict registry and share one reboot-persistent user timer. A new
project does not clone a daemon. Its adoption gate adds one enabled registry entry, regenerates the
same user unit so its output parent is explicitly write-allowed, proves one initial atomic
publication, then requires the timer and source-current doctor check to remain healthy.

Workers prove only repository, bead, receipt, and evidence facts visible inside their own
namespace. Host-only checks stay in the operator/readiness layer. An empty cross-UID process
scan, an unreachable local socket, or failed host-app IPC from a worker is always `UNKNOWN`,
never absence evidence.

## Codex Desktop workaround lifecycle

Desktop versions `26.820.60940.0` and `26.820.7780.0` are locally classified as affected by
the WSL `mcp_servers.codex_app` transport regression. On those builds the doctor requires:

```toml
[mcp_servers.codex_app]
command = "/bin/false"
enabled = false
```

When a newer build appears, the doctor reports `candidate_retest=true`; it does not remove the
workaround. The attended retest is:

1. verify a byte-exact config backup and an external PowerShell rollback command;
2. ensure Gas City is suspended with no critical work in flight;
3. fully quit Codex Desktop;
4. remove only the reviewed workaround block;
5. relaunch and test both a new WSL task and resuming an older disposable WSL task;
6. restore externally and fully restart on any failure.

## Current known degradation

The stale supervisor-unit inventory is clear: only the canonical per-home unit remains enabled.
The accepted live warning is the affected Codex Desktop build, which keeps the `codex_app`
workaround pinned until a newer-build retest passes.

## Planned boot acceptance

The Windows bootstrap is intentionally not installed by the doctor. The reviewed assets are:

- `scripts/windows/gas-city-wsl-bootstrap.ps1`: wakes the configured WSL distro and runs the
  stable doctor up to 12 times, five seconds apart;
- `scripts/windows/install-gas-city-wsl-bootstrap.ps1`: checks, installs, or removes one
  scheduled task named `GasCity-WSL-Bootstrap`.

The task contract is deliberately narrow: current interactive user, limited privileges, one
logon trigger delayed by 30 seconds, one hidden non-interactive PowerShell action, at most one
instance, and a five-minute execution limit. It records `latest.json` plus immutable timestamped
history under `%USERPROFILE%\.gas-city\reboot-readiness`. A `DEGRADED` doctor result is accepted
as a completed observation; a malformed report or `FAILED` result makes the bootstrap fail.

The bootstrap targets the installed Windows PowerShell 5.1 runtime. It launches `wsl.exe`
through a waited process object with redirected output and reads that object's exit code; it
does not depend on ambient `$LASTEXITCODE` state or PowerShell 7-only JSON parameters.
Both the installed bootstrap and its evidence live under `%USERPROFILE%\.gas-city`, outside
packaged-app `%LOCALAPPDATA%` virtualization, so Codex Desktop and an ordinary scheduled task
observe the same bytes.

Neither script starts, resumes, repairs, or restarts Gas City. Removal unregisters only the
named task and installed bootstrap script; it preserves readiness evidence.

## Reboot drill

Installation is not accepted as durable until both drills pass:

1. **WSL-only drill:** with every rig suspended, run `wsl.exe --shutdown`, start the distro,
   and require the stable doctor to report only the previously accepted warnings.
2. **Full Windows restart:** restart Windows, log in normally, wait for the delayed task, and
   verify the fresh `latest.json`, canonical supervisor, signer service/socket, controller,
   store, and suspended-rig state.

On any failure, preserve the JSON record and stop. Diagnose the reported layer; do not use a
broad restart or resume as a substitute for evidence.
