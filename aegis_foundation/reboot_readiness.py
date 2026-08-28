#!/usr/bin/env python3
"""Read-only reboot readiness diagnostics for Codex Desktop + WSL + Gas City.

The probe deliberately separates file-observable facts from host-control-plane facts.
When a Codex sandbox cannot reach systemd, Windows interop, local service sockets, or
host-WSL application IPC, the affected check is UNKNOWN rather than a false failure.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import pwd
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Protocol, Sequence


DEFAULT_CITY = Path("/home/loucmane/gascity/city")
DEFAULT_GC = Path("/home/loucmane/gascity/bin/gc")
DEFAULT_SUPERVISOR_UNIT = "gascity-supervisor-home-42adab5d.service"
DEFAULT_SIGNER_SERVICE = "gas-city-managed-git-signerd.service"
DEFAULT_SIGNER_SOCKET = "gas-city-managed-git-signerd.socket"
DEFAULT_WINDOWS_TASK = "GasCity-WSL-Bootstrap"
DEFAULT_OBSIDIAN = Path("/home/loucmane/.local/bin/obsidian")
DEFAULT_OBSIDIAN_VAULT = "main"
DEFAULT_OBSIDIAN_PROBE_PATH = "GasCity/gas-city-operations/Aegis/Beads/ga-zbmk.md"
DEFAULT_GPG_READINESS = Path("/home/loucmane/.local/bin/codex-gpg-readiness")
OPERATOR_SIGNING_FINGERPRINT = "FD5585922F5335BC378AD8D42ECF4432C7E7982D"
OPERATOR_SIGNING_KEYGRIP = "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA"
OPERATOR_GPG_READINESS_SCHEMA = "codex.gpg-readiness.v2"
MANAGED_PATH = "/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin"
KNOWN_AFFECTED_DESKTOP_VERSIONS = frozenset({"26.820.60940.0", "26.820.7780.0"})
STATUS_ORDER = {"pass": 0, "unknown": 1, "warn": 2, "fail": 3}
DOCTOR_VERSION = "2026.08.28.3"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class Runner(Protocol):
    def run(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        timeout: float = 15,
    ) -> CommandResult: ...


class SubprocessRunner:
    def run(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        timeout: float = 15,
    ) -> CommandResult:
        try:
            completed = subprocess.run(
                list(argv),
                capture_output=True,
                text=True,
                check=False,
                env=dict(env) if env is not None else None,
                timeout=timeout,
            )
        except (FileNotFoundError, PermissionError) as exc:
            return CommandResult(127, stderr=str(exc))
        except subprocess.TimeoutExpired as exc:
            return CommandResult(124, stdout=exc.stdout or "", stderr=exc.stderr or "timeout")
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


@dataclass(frozen=True)
class Check:
    key: str
    status: str
    summary: str
    details: Mapping[str, object]
    remediation: str | None = None

    def __post_init__(self) -> None:
        if self.status not in STATUS_ORDER:
            raise ValueError(f"unsupported readiness status: {self.status}")


@dataclass(frozen=True)
class Report:
    schema_version: str
    generated_at: str
    overall: str
    observer: str
    authority: str
    checks: tuple[Check, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["summary"] = {
            status: sum(check.status == status for check in self.checks)
            for status in STATUS_ORDER
        }
        return payload


@dataclass(frozen=True)
class ProbeConfig:
    city: Path = DEFAULT_CITY
    gc: Path = DEFAULT_GC
    windows_config: Path | None = None
    wsl_config: Path = Path("/etc/wsl.conf")
    boot_id_path: Path = Path("/proc/sys/kernel/random/boot_id")
    user_unit_dir: Path | None = None
    user_wants_dir: Path | None = None
    supervisor_unit: str = DEFAULT_SUPERVISOR_UNIT
    signer_service: str = DEFAULT_SIGNER_SERVICE
    signer_socket: str = DEFAULT_SIGNER_SOCKET
    windows_task: str = DEFAULT_WINDOWS_TASK
    obsidian_command: Path = DEFAULT_OBSIDIAN
    obsidian_vault: str = DEFAULT_OBSIDIAN_VAULT
    obsidian_probe_path: str = DEFAULT_OBSIDIAN_PROBE_PATH
    gpg_readiness_command: Path = DEFAULT_GPG_READINESS
    user: str | None = None


def _observer_kind(env: Mapping[str, str]) -> str:
    if env.get("CODEX_PERMISSION_PROFILE") or env.get("CODEX_THREAD_ID"):
        return "codex-sandbox"
    if Path("/.dockerenv").exists():
        return "container"
    return "host-wsl"


def _observer_authority(observer: str) -> str:
    return "host-control-plane" if observer == "host-wsl" else "observer-limited"


def _control_plane_unobservable(result: CommandResult) -> bool:
    text = f"{result.stdout}\n{result.stderr}".lower()
    markers = (
        "operation not permitted",
        "permission denied",
        "failed to connect to bus",
        "socket: operation not permitted",
        "network is unreachable",
        "utilbindvsockanyport",
    )
    return any(marker in text for marker in markers)


def _version_tuple(value: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in value.strip().split("."))
    except ValueError:
        return None


def _default_windows_config() -> Path | None:
    configured = os.environ.get("CODEX_WINDOWS_CONFIG")
    if configured:
        return Path(configured)
    users_root = Path("/mnt/c/Users")
    if not users_root.is_dir():
        return None
    candidates = sorted(users_root.glob("*/.codex/config.toml"))
    return candidates[0] if len(candidates) == 1 else None


def _toml(path: Path) -> Mapping[str, object]:
    with path.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("TOML root is not a table")
    return payload


def check_wsl_systemd(config: ProbeConfig) -> list[Check]:
    checks: list[Check] = []
    try:
        parser = configparser.ConfigParser()
        with config.wsl_config.open(encoding="utf-8") as handle:
            parser.read_file(handle)
        enabled = parser.getboolean("boot", "systemd", fallback=False)
    except (OSError, configparser.Error, ValueError) as exc:
        checks.append(
            Check(
                "wsl.systemd_config",
                "fail",
                "WSL systemd configuration is unreadable",
                {"path": str(config.wsl_config), "error": str(exc)},
                "Restore /etc/wsl.conf with [boot] systemd=true, then restart WSL.",
            )
        )
    else:
        checks.append(
            Check(
                "wsl.systemd_config",
                "pass" if enabled else "fail",
                "WSL systemd boot is enabled" if enabled else "WSL systemd boot is disabled",
                {"path": str(config.wsl_config), "enabled": enabled},
                None if enabled else "Set [boot] systemd=true and restart WSL.",
            )
        )

    try:
        boot_id = config.boot_id_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        checks.append(
            Check(
                "wsl.boot_id",
                "fail",
                "WSL boot identity is unavailable",
                {"path": str(config.boot_id_path), "error": str(exc)},
            )
        )
    else:
        checks.append(
            Check(
                "wsl.boot_id",
                "pass" if boot_id else "fail",
                "WSL boot identity is readable" if boot_id else "WSL boot identity is empty",
                {"boot_id": boot_id},
            )
        )
    return checks


def check_gpg_signing_cache(config: ProbeConfig, runner: Runner, observer: str) -> Check:
    result = runner.run([str(config.gpg_readiness_command), "check", "--json"])
    if result.returncode == 127:
        return Check(
            "credentials.gpg_operator_key",
            "warn",
            "The exact-key GPG readiness helper is not installed",
            {
                "path": str(config.gpg_readiness_command),
                "observer": observer,
                "error": result.stderr.strip(),
            },
            "Install the reviewed helper; never replace this check with an any-key probe.",
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return Check(
            "credentials.gpg_operator_key",
            "fail",
            "The GPG readiness helper returned malformed evidence",
            {
                "path": str(config.gpg_readiness_command),
                "returncode": result.returncode,
                "error": str(exc),
                "stderr": result.stderr.strip(),
            },
        )
    if not isinstance(payload, dict):
        return Check(
            "credentials.gpg_operator_key",
            "fail",
            "The GPG readiness helper returned the wrong evidence shape",
            {"path": str(config.gpg_readiness_command)},
        )

    fingerprint = payload.get("fingerprint")
    keygrip = payload.get("keygrip")
    schema = payload.get("schema")
    details = {"observer": observer, **payload}
    if schema != OPERATOR_GPG_READINESS_SCHEMA:
        return Check(
            "credentials.gpg_operator_key",
            "fail",
            "The GPG readiness helper returned the wrong evidence schema",
            details,
            "Restore the reviewed exact-key helper before signing.",
        )
    identity_matches = (
        fingerprint == OPERATOR_SIGNING_FINGERPRINT
        and keygrip == OPERATOR_SIGNING_KEYGRIP
    )
    if not identity_matches:
        return Check(
            "credentials.gpg_operator_key",
            "fail",
            "GPG readiness evidence is bound to the wrong signing identity",
            details,
            "Restore the reviewed FD55 fingerprint/keygrip binding before signing.",
        )

    cached = payload.get("cached") is True
    agent_running = payload.get("agent_running") is True
    proof = payload.get("proof")
    proof_is_valid = (cached and proof == "agent-cache") or (
        not cached and proof == "agent-epoch-signature"
    )
    ready = (
        result.returncode == 0
        and payload.get("status") == "ready"
        and agent_running
        and proof_is_valid
    )
    if ready:
        return Check(
            "credentials.gpg_operator_key",
            "pass",
            "The exact FD55 operator signing key is ready in this agent epoch",
            details,
        )
    cold = (
        result.returncode == 11
        and payload.get("status") == "cold"
        and agent_running
        and not cached
        and proof == "none"
    )
    unavailable = (
        result.returncode == 10
        and payload.get("status") == "agent-unavailable"
        and payload.get("agent_running") is False
        and not cached
        and proof == "none"
    )
    if cold or unavailable:
        return Check(
            "credentials.gpg_operator_key",
            "warn",
            "The exact FD55 operator signing key needs its one-time WSL-boot unlock",
            details,
            "Open one interactive WSL terminal and run unlock-all; never store the passphrase.",
        )
    return Check(
        "credentials.gpg_operator_key",
        "fail",
        "The exact FD55 GPG readiness check failed unexpectedly",
        {**details, "returncode": result.returncode, "stderr": result.stderr.strip()},
    )


def check_linger(config: ProbeConfig, runner: Runner, observer: str) -> Check:
    user = config.user or pwd.getpwuid(os.getuid()).pw_name
    result = runner.run(["loginctl", "show-user", user, "-p", "Linger", "--value"])
    if _control_plane_unobservable(result):
        return Check(
            "wsl.user_linger",
            "unknown",
            "User linger cannot be observed from this sandbox",
            {"user": user, "observer": observer, "error": result.stderr.strip()},
            "Run the doctor from an ordinary WSL terminal for host truth.",
        )
    linger = result.stdout.strip().lower()
    if result.returncode != 0:
        return Check(
            "wsl.user_linger",
            "fail",
            "Unable to read user linger state",
            {"user": user, "returncode": result.returncode, "error": result.stderr.strip()},
        )
    enabled = linger == "yes"
    return Check(
        "wsl.user_linger",
        "pass" if enabled else "fail",
        "User linger is enabled" if enabled else "User linger is disabled",
        {"user": user, "linger": linger},
        None if enabled else "Enable linger so the user supervisor starts with WSL systemd.",
    )


def _desktop_version(runner: Runner, observer: str) -> tuple[str | None, Check]:
    script = (
        "$p=Get-AppxPackage OpenAI.Codex -ErrorAction SilentlyContinue; "
        "if($null -eq $p){exit 3}; $p.Version.ToString()"
    )
    result = runner.run(["powershell.exe", "-NoProfile", "-Command", script], timeout=20)
    if _control_plane_unobservable(result) or result.returncode == 127:
        return None, Check(
            "desktop.version",
            "unknown",
            "Codex Desktop version cannot be observed from this context",
            {"observer": observer, "error": result.stderr.strip()},
            "Run the doctor from an ordinary WSL terminal.",
        )
    version = result.stdout.strip()
    if result.returncode != 0 or not version:
        return None, Check(
            "desktop.version",
            "fail",
            "Codex Desktop package is not discoverable",
            {"returncode": result.returncode, "error": result.stderr.strip()},
        )
    if version in KNOWN_AFFECTED_DESKTOP_VERSIONS:
        return version, Check(
            "desktop.version",
            "warn",
            "Installed Codex Desktop version is affected by the WSL codex_app transport bug",
            {"version": version, "known_affected": True, "issue": "openai/codex#40819"},
            "Keep the disabled codex_app workaround until a controlled newer-build retest passes.",
        )
    newest_affected = max(_version_tuple(item) or () for item in KNOWN_AFFECTED_DESKTOP_VERSIONS)
    parsed = _version_tuple(version)
    if parsed is not None and parsed > newest_affected:
        return version, Check(
            "desktop.version",
            "warn",
            "A newer Codex Desktop build is installed and is eligible for a controlled retest",
            {"version": version, "known_affected": False, "candidate_retest": True},
            "Do not remove the workaround in place; run the backup/quit/relaunch/rollback drill.",
        )
    return version, Check(
        "desktop.version",
        "warn",
        "Codex Desktop version is not in the local compatibility table",
        {"version": version, "known_affected": False, "candidate_retest": False},
        "Keep the workaround until this build is verified in a controlled drill.",
    )


def check_desktop(config: ProbeConfig, runner: Runner, observer: str) -> list[Check]:
    path = config.windows_config or _default_windows_config()
    if path is None:
        config_check = Check(
            "desktop.config",
            "unknown",
            "Windows Codex config path is ambiguous",
            {},
            "Pass --windows-config or set CODEX_WINDOWS_CONFIG.",
        )
        payload: Mapping[str, object] = {}
    else:
        try:
            payload = _toml(path)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            config_check = Check(
                "desktop.config",
                "fail",
                "Windows Codex config is unreadable",
                {"path": str(path), "error": str(exc)},
                "Restore the byte-exact config backup before launching Codex Desktop.",
            )
            payload = {}
        else:
            config_check = Check(
                "desktop.config",
                "pass",
                "Windows Codex config parses",
                {"path": str(path)},
            )

    desktop = payload.get("desktop") if isinstance(payload, dict) else None
    wsl_mode = (
        desktop.get("runCodexInWindowsSubsystemForLinux")
        if isinstance(desktop, dict)
        else None
    )
    mode_check = Check(
        "desktop.wsl_mode",
        "pass" if wsl_mode is True else "fail",
        "Codex Desktop uses WSL" if wsl_mode is True else "Codex Desktop WSL mode is not enabled",
        {"runCodexInWindowsSubsystemForLinux": wsl_mode},
        None if wsl_mode is True else "Restore the reviewed WSL-mode setting.",
    )

    version, version_check = _desktop_version(runner, observer)
    servers = payload.get("mcp_servers") if isinstance(payload, dict) else None
    codex_app = servers.get("codex_app") if isinstance(servers, dict) else None
    workaround = (
        isinstance(codex_app, dict)
        and codex_app.get("enabled") is False
        and codex_app.get("command") == "/bin/false"
    )
    if version in KNOWN_AFFECTED_DESKTOP_VERSIONS:
        workaround_status = "pass" if workaround else "fail"
        workaround_summary = (
            "Affected-build codex_app workaround is present"
            if workaround
            else "Affected-build codex_app workaround is missing"
        )
    elif workaround:
        workaround_status = "pass"
        workaround_summary = "codex_app workaround remains safely pinned pending retest"
    else:
        workaround_status = "warn"
        workaround_summary = "codex_app workaround is absent on an unverified build"
    workaround_check = Check(
        "desktop.codex_app_workaround",
        workaround_status,
        workaround_summary,
        {
            "command": codex_app.get("command") if isinstance(codex_app, dict) else None,
            "enabled": codex_app.get("enabled") if isinstance(codex_app, dict) else None,
            "desktop_version": version,
        },
        None
        if workaround
        else "Restore command=/bin/false and enabled=false, then fully restart Codex Desktop.",
    )
    return [config_check, mode_check, version_check, workaround_check]


def _obsidian_vault_inventory(stdout: str) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for line in stdout.splitlines():
        if not line.strip():
            continue
        name, separator, path = line.partition("\t")
        if not separator or not name.strip() or not path.strip():
            continue
        inventory[name.strip()] = path.strip()
    return inventory


def check_obsidian(config: ProbeConfig, runner: Runner, observer: str) -> Check:
    """Probe live Obsidian IPC without confusing observer limits with app absence.

    The deterministic filesystem projection remains the Aegis authority. This check only
    proves that the host-side Obsidian process can currently enumerate the configured vault
    and read one managed note through its CLI IPC surface.
    """

    host_authoritative = observer == "host-wsl"
    authority = "host-wsl-live-ipc" if host_authoritative else "observer-limited"
    vaults = runner.run([str(config.obsidian_command), "vaults", "verbose"])
    common_details = {
        "observer": observer,
        "authority": authority,
        "vault": config.obsidian_vault,
        "probe_path": config.obsidian_probe_path,
    }
    if vaults.returncode != 0 or _control_plane_unobservable(vaults):
        details = {
            **common_details,
            "returncode": vaults.returncode,
            "error": (vaults.stderr or vaults.stdout).strip(),
        }
        if not host_authoritative or _control_plane_unobservable(vaults):
            return Check(
                "obsidian.host_ipc",
                "unknown",
                "This observer cannot establish live Obsidian host-IPC state",
                details,
                (
                    "Repeat the read-only probe from host WSL; do not infer that Obsidian "
                    "is closed from a sandbox result."
                ),
            )
        return Check(
            "obsidian.host_ipc",
            "warn",
            "Host WSL cannot currently reach the live Obsidian CLI",
            details,
            (
                "The filesystem-native Aegis vault remains authoritative; open Obsidian "
                "only when live GUI access is required."
            ),
        )

    inventory = _obsidian_vault_inventory(vaults.stdout)
    vault_path = inventory.get(config.obsidian_vault)
    if vault_path is None:
        details = {**common_details, "known_vaults": sorted(inventory)}
        return Check(
            "obsidian.host_ipc",
            "warn" if host_authoritative else "unknown",
            (
                f"Obsidian does not expose configured vault {config.obsidian_vault!r}"
                if host_authoritative
                else "This observer cannot establish the configured Obsidian vault"
            ),
            details,
            "Verify the vault from host WSL; never repair or recreate it from the doctor.",
        )

    read = runner.run(
        [
            str(config.obsidian_command),
            f"vault={config.obsidian_vault}",
            "read",
            f"path={config.obsidian_probe_path}",
        ]
    )
    if read.returncode != 0 or not read.stdout.strip():
        details = {
            **common_details,
            "vault_path": vault_path,
            "returncode": read.returncode,
            "error": (read.stderr or read.stdout).strip(),
        }
        return Check(
            "obsidian.host_ipc",
            "warn" if host_authoritative else "unknown",
            (
                "Host WSL reached Obsidian but could not read the managed probe note"
                if host_authoritative
                else "This observer cannot establish managed-note readability in Obsidian"
            ),
            details,
            (
                "Run the filesystem vault check first. If it passes after an atomic WSL "
                f"publication, run `obsidian vault={config.obsidian_vault} reload` from "
                "host WSL, then repeat this optional live-app probe."
            ),
        )

    return Check(
        "obsidian.host_ipc",
        "pass",
        "Host-side Obsidian exposes the managed Aegis note",
        {
            **common_details,
            "vault_path": vault_path,
            "probe_bytes": len(read.stdout.encode("utf-8")),
        },
    )


def check_windows_bootstrap(config: ProbeConfig, runner: Runner, observer: str) -> Check:
    script = (
        f"$t=Get-ScheduledTask -TaskName '{config.windows_task}' "
        "-ErrorAction SilentlyContinue; if($null -eq $t){exit 3}; "
        "$a=@($t.Actions)[0]; $g=@($t.Triggers)[0]; "
        "[pscustomobject]@{State=$t.State.ToString();Execute=$a.Execute;"
        "Arguments=$a.Arguments;UserId=$t.Principal.UserId;"
        "RunLevel=$t.Principal.RunLevel.ToString();"
        "TriggerClass=$g.CimClass.CimClassName;Delay=$g.Delay} | "
        "ConvertTo-Json -Compress"
    )
    result = runner.run(["powershell.exe", "-NoProfile", "-Command", script], timeout=20)
    if _control_plane_unobservable(result) or result.returncode == 127:
        return Check(
            "windows.bootstrap_task",
            "unknown",
            "Windows bootstrap task cannot be observed from this context",
            {"task": config.windows_task, "observer": observer, "error": result.stderr.strip()},
            "Run the doctor from an ordinary WSL terminal.",
        )
    if result.returncode == 3:
        return Check(
            "windows.bootstrap_task",
            "warn",
            "No Windows logon task starts WSL and verifies Gas City",
            {"task": config.windows_task, "present": False},
            "Install the reviewed logon bootstrap after its bounded package is approved.",
        )
    if result.returncode != 0:
        return Check(
            "windows.bootstrap_task",
            "fail",
            "Windows bootstrap task query failed",
            {"task": config.windows_task, "error": result.stderr.strip()},
        )
    try:
        task = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return Check(
            "windows.bootstrap_task",
            "fail",
            "Windows bootstrap task returned malformed configuration evidence",
            {"task": config.windows_task, "error": str(exc)},
        )
    if not isinstance(task, dict):
        return Check(
            "windows.bootstrap_task",
            "fail",
            "Windows bootstrap task configuration evidence has the wrong shape",
            {"task": config.windows_task},
        )
    state = str(task.get("State", ""))
    execute = str(task.get("Execute", ""))
    arguments = str(task.get("Arguments", ""))
    run_level = str(task.get("RunLevel", ""))
    trigger_class = str(task.get("TriggerClass", ""))
    delay = str(task.get("Delay", ""))
    valid = (
        state.lower() in {"ready", "running"}
        and execute.lower().endswith("powershell.exe")
        and "gas-city-wsl-bootstrap.ps1" in arguments
        and "-NoProfile" in arguments
        and "-NonInteractive" in arguments
        and run_level.lower() == "limited"
        and trigger_class == "MSFT_TaskLogonTrigger"
        and delay == "PT30S"
    )
    return Check(
        "windows.bootstrap_task",
        "pass" if valid else "fail",
        "Windows logon bootstrap task is installed with the reviewed contract"
        if valid
        else "Windows bootstrap task exists but its contract has drifted",
        {"task": config.windows_task, **task},
        None
        if valid
        else "Restore the reviewed limited logon task; do not repair it from the doctor.",
    )


def _systemctl_check(
    *,
    key: str,
    unit: str,
    user: bool,
    runner: Runner,
    observer: str,
) -> list[Check]:
    prefix = ["systemctl", "--user"] if user else ["systemctl"]
    checks: list[Check] = []
    for verb in ("is-enabled", "is-active"):
        result = runner.run([*prefix, verb, unit])
        suffix = "enabled" if verb == "is-enabled" else "active"
        if _control_plane_unobservable(result):
            checks.append(
                Check(
                    f"{key}.{suffix}",
                    "unknown",
                    f"{unit} {suffix} state is hidden from this sandbox",
                    {"unit": unit, "observer": observer, "error": result.stderr.strip()},
                    "Run the doctor from an ordinary WSL terminal.",
                )
            )
            continue
        value = result.stdout.strip()
        ok = result.returncode == 0 and value in {"enabled", "active", "static"}
        checks.append(
            Check(
                f"{key}.{suffix}",
                "pass" if ok else "fail",
                f"{unit} is {value or suffix}" if ok else f"{unit} is not {suffix}",
                {"unit": unit, "state": value, "returncode": result.returncode},
                None if ok else f"Inspect {unit}; do not restart it from the doctor.",
            )
        )
    return checks


def check_supervisor_units(config: ProbeConfig) -> list[Check]:
    home = Path.home()
    unit_dir = config.user_unit_dir or home / ".local/share/systemd/user"
    wants_dir = config.user_wants_dir or home / ".config/systemd/user/default.target.wants"
    canonical = unit_dir / config.supervisor_unit
    checks: list[Check] = []
    if not canonical.is_file():
        checks.append(
            Check(
                "gascity.supervisor_unit_file",
                "fail",
                "Canonical Gas City supervisor unit is missing",
                {"path": str(canonical)},
            )
        )
    else:
        text = canonical.read_text(encoding="utf-8")
        expected_home = str(config.city.parent / "home")
        has_expected_home = f'Environment=GC_HOME="{expected_home}"' in text
        checks.append(
            Check(
                "gascity.supervisor_unit_file",
                "pass" if has_expected_home else "fail",
                "Canonical supervisor unit targets the managed Gas City home"
                if has_expected_home
                else "Canonical supervisor unit targets an unexpected GC_HOME",
                {"path": str(canonical), "expected_gc_home": expected_home},
            )
        )

    enabled = sorted(wants_dir.glob("gascity-supervisor-home-*.service"))
    names = [path.name for path in enabled]
    stale = [name for name in names if name != config.supervisor_unit]
    checks.append(
        Check(
            "gascity.stale_supervisor_units",
            "pass" if not stale else "warn",
            "Only the canonical per-home supervisor unit is enabled"
            if not stale
            else f"{len(stale)} stale per-home supervisor units remain enabled",
            {
                "enabled_count": len(names),
                "canonical": config.supervisor_unit,
                "stale_count": len(stale),
                "stale_units": stale,
            },
            None
            if not stale
            else "Use the separately reviewed stale-unit cleanup; the doctor never disables units.",
        )
    )
    return checks


def check_gc_status(config: ProbeConfig, runner: Runner, observer: str) -> Check:
    env = dict(os.environ)
    env["PATH"] = MANAGED_PATH
    # The managed supervisor is deliberately isolated from the legacy
    # ~/.gc home. Bind every gc subprocess to the same home encoded in the
    # canonical unit so stale operator-shell state cannot create a false
    # readiness failure.
    env["GC_HOME"] = str(config.city.parent / "home")
    result = runner.run(
        [str(config.gc), "--city", str(config.city), "status", "--json"],
        env=env,
        timeout=30,
    )
    if _control_plane_unobservable(result):
        return Check(
            "gascity.status",
            "unknown",
            "Gas City controller/store sockets are hidden from this sandbox",
            {"observer": observer, "error": result.stderr.strip()},
            "Run the doctor from an ordinary WSL terminal for controller and Dolt truth.",
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = None
    if result.returncode != 0 or not isinstance(payload, dict):
        return Check(
            "gascity.status",
            "fail",
            "Gas City status did not return valid JSON",
            {"returncode": result.returncode, "error": result.stderr.strip()},
        )
    controller = payload.get("controller")
    running = controller.get("running") if isinstance(controller, dict) else None
    beads = payload.get("beads")
    store_eligible = beads.get("native_store_eligible") if isinstance(beads, dict) else None
    ok = running is True and store_eligible is not False
    rigs = payload.get("rigs") if isinstance(payload.get("rigs"), list) else []
    return Check(
        "gascity.status",
        "pass" if ok else "fail",
        "Gas City controller and bead-store context are usable"
        if ok
        else "Gas City controller or bead-store context is not usable",
        {
            "controller_running": running,
            "native_store_eligible": store_eligible,
            "rigs": [
                {"name": rig.get("name"), "suspended": rig.get("suspended")}
                for rig in rigs
                if isinstance(rig, dict)
            ],
        },
        None
        if ok
        else "Inspect the supervisor and store; the doctor performs no restart or repair.",
    )


def build_report(
    config: ProbeConfig | None = None,
    *,
    runner: Runner | None = None,
    env: Mapping[str, str] | None = None,
    observer_override: str | None = None,
) -> Report:
    probe = config or ProbeConfig()
    command_runner = runner or SubprocessRunner()
    environment = dict(os.environ if env is None else env)
    observer = observer_override or _observer_kind(environment)
    if observer not in {"codex-sandbox", "container", "host-wsl"}:
        raise ValueError(f"unsupported observer context: {observer}")
    checks: list[Check] = []
    checks.extend(check_wsl_systemd(probe))
    checks.append(check_gpg_signing_cache(probe, command_runner, observer))
    checks.append(check_linger(probe, command_runner, observer))
    checks.extend(check_desktop(probe, command_runner, observer))
    checks.append(check_obsidian(probe, command_runner, observer))
    checks.append(check_windows_bootstrap(probe, command_runner, observer))
    checks.extend(check_supervisor_units(probe))
    checks.extend(
        _systemctl_check(
            key="gascity.supervisor",
            unit=probe.supervisor_unit,
            user=True,
            runner=command_runner,
            observer=observer,
        )
    )
    checks.extend(
        _systemctl_check(
            key="signer.service",
            unit=probe.signer_service,
            user=False,
            runner=command_runner,
            observer=observer,
        )
    )
    checks.extend(
        _systemctl_check(
            key="signer.socket",
            unit=probe.signer_socket,
            user=False,
            runner=command_runner,
            observer=observer,
        )
    )
    checks.append(check_gc_status(probe, command_runner, observer))

    highest = max((STATUS_ORDER[check.status] for check in checks), default=0)
    overall = "failed" if highest == STATUS_ORDER["fail"] else "degraded" if highest else "ready"
    return Report(
        schema_version="1",
        generated_at=datetime.now(timezone.utc).isoformat(),
        overall=overall,
        observer=observer,
        authority=_observer_authority(observer),
        checks=tuple(checks),
    )


def render_human(report: Report) -> str:
    labels = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "unknown": "UNKNOWN"}
    lines = [
        f"Codex WSL reboot readiness: {report.overall.upper()}",
        f"Observer: {report.observer}",
        f"Authority: {report.authority}",
        "",
    ]
    for check in report.checks:
        lines.append(f"[{labels[check.status]:7}] {check.key}: {check.summary}")
        if check.remediation:
            lines.append(f"          next: {check.remediation}")
    return "\n".join(lines)


def exit_code(report: Report) -> int:
    if report.overall == "failed":
        return 2
    if report.overall == "degraded":
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        description="Read-only Codex Desktop, WSL, and Gas City reboot-readiness doctor."
    )
    cli.add_argument("--json", action="store_true", help="Emit structured JSON.")
    cli.add_argument("--city", type=Path, default=DEFAULT_CITY)
    cli.add_argument("--gc", type=Path, default=DEFAULT_GC)
    cli.add_argument("--windows-config", type=Path)
    cli.add_argument("--supervisor-unit", default=DEFAULT_SUPERVISOR_UNIT)
    cli.add_argument("--obsidian-command", type=Path, default=DEFAULT_OBSIDIAN)
    cli.add_argument("--obsidian-vault", default=DEFAULT_OBSIDIAN_VAULT)
    cli.add_argument("--obsidian-probe-path", default=DEFAULT_OBSIDIAN_PROBE_PATH)
    cli.add_argument("--version", action="version", version=f"%(prog)s {DOCTOR_VERSION}")
    cli.add_argument(
        "--observer",
        choices=("auto", "host-wsl", "codex-sandbox", "container"),
        default="auto",
        help=(
            "Declare the execution vantage. Use host-wsl when an approved host-context "
            "run inherits Codex environment markers; auto is the safe default."
        ),
    )
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report = build_report(
        ProbeConfig(
            city=args.city,
            gc=args.gc,
            windows_config=args.windows_config,
            supervisor_unit=args.supervisor_unit,
            obsidian_command=args.obsidian_command,
            obsidian_vault=args.obsidian_vault,
            obsidian_probe_path=args.obsidian_probe_path,
        ),
        observer_override=None if args.observer == "auto" else args.observer,
    )
    if args.json:
        json.dump(report.to_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render_human(report))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
