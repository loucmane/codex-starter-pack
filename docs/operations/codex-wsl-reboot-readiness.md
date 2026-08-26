# Codex Desktop + WSL + Gas City Reboot Readiness

`scripts/codex-wsl-readiness` is the repository entry point for a read-only doctor covering
the layers that must survive a Windows restart:

1. Codex Desktop configuration and installed-version compatibility;
2. WSL systemd boot and user linger;
3. the canonical Gas City user supervisor;
4. stale per-home supervisor units;
5. the managed signing service and socket;
6. Gas City controller and bead-store reachability; and
7. the future Windows logon bootstrap task.

The doctor never repairs, restarts, enables, disables, routes, resumes, signs, or deletes.

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
```

The default destination is `~/.local/bin/codex-wsl-readiness`. The installer performs an
atomic byte-for-byte replacement, sets mode `0755`, and checks the installed version. It does
not enable or restart any service.

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
history under `%LOCALAPPDATA%\GasCity\reboot-readiness`. A `DEGRADED` doctor result is accepted
as a completed observation; a malformed report or `FAILED` result makes the bootstrap fail.

The bootstrap targets the installed Windows PowerShell 5.1 runtime. It launches `wsl.exe`
through a waited process object with redirected output and reads that object's exit code; it
does not depend on ambient `$LASTEXITCODE` state or PowerShell 7-only JSON parameters.

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
