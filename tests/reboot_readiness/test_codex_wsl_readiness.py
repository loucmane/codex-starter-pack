from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from aegis_foundation.reboot_readiness import (
    CommandResult,
    DESKTOP_RETEST_SCHEMA,
    ProbeConfig,
    build_report,
    check_desktop,
    check_gc_status,
    check_gpg_signing_cache,
    check_obsidian,
    check_obsidian_reconciler,
    check_supervisor_units,
    check_windows_bootstrap,
    check_wsl_systemd,
    exit_code,
    render_human,
)


class FakeRunner:
    def __init__(self, responses: Mapping[tuple[str, ...], CommandResult]) -> None:
        self.responses = dict(responses)
        self.calls: list[tuple[str, ...]] = []
        self.environments: list[dict[str, str] | None] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        timeout: float = 15,
    ) -> CommandResult:
        key = tuple(argv)
        self.calls.append(key)
        self.environments.append(dict(env) if env is not None else None)
        if key not in self.responses:
            raise AssertionError(f"unexpected command: {key!r}")
        return self.responses[key]


def write_windows_config(path: Path, *, workaround: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "[desktop]",
        "runCodexInWindowsSubsystemForLinux = true",
        "",
    ]
    if workaround:
        lines.extend(
            [
                "[mcp_servers.codex_app]",
                'command = "/bin/false"',
                "enabled = false",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_config(tmp_path: Path, *, stale_units: int = 0) -> ProbeConfig:
    city = tmp_path / "gascity/city"
    city.mkdir(parents=True)
    windows_config = tmp_path / "windows/.codex/config.toml"
    write_windows_config(windows_config)
    wsl_config = tmp_path / "etc/wsl.conf"
    wsl_config.parent.mkdir(parents=True)
    wsl_config.write_text("[boot]\nsystemd=true\n", encoding="utf-8")
    boot_id = tmp_path / "proc/boot_id"
    boot_id.parent.mkdir(parents=True)
    boot_id.write_text("test-boot-id\n", encoding="utf-8")
    unit_dir = tmp_path / "systemd/user"
    wants_dir = tmp_path / "systemd/wants"
    unit_dir.mkdir(parents=True)
    wants_dir.mkdir(parents=True)
    canonical_name = "gascity-supervisor-home-test.service"
    canonical = unit_dir / canonical_name
    canonical.write_text(
        f'[Service]\nEnvironment=GC_HOME="{city.parent / "home"}"\n',
        encoding="utf-8",
    )
    (wants_dir / canonical_name).symlink_to(canonical)
    for index in range(stale_units):
        stale = unit_dir / f"gascity-supervisor-home-stale{index}.service"
        stale.write_text('[Service]\nEnvironment=GC_HOME="/tmp/stale"\n', encoding="utf-8")
        (wants_dir / stale.name).symlink_to(stale)
    return ProbeConfig(
        city=city,
        gc=Path("/managed/gc"),
        windows_config=windows_config,
        desktop_retest_attestation=tmp_path / "state/codex-desktop-transport-retest.json",
        wsl_config=wsl_config,
        boot_id_path=boot_id,
        user_unit_dir=unit_dir,
        user_wants_dir=wants_dir,
        supervisor_unit=canonical_name,
        user="tester",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_desktop_retest_attestation(
    config: ProbeConfig,
    *,
    desktop_version: str,
    extra: dict[str, object] | None = None,
) -> Path:
    assert config.desktop_retest_attestation is not None
    assert config.windows_config is not None
    rollback = config.windows_config.with_name("config.toml.rollback")
    rollback.write_text("rollback\n", encoding="utf-8")
    payload: dict[str, object] = {
        "schema": DESKTOP_RETEST_SCHEMA,
        "desktop_version": desktop_version,
        "windows_config": str(config.windows_config),
        "windows_config_sha256": sha256_file(config.windows_config),
        "rollback_backup": str(rollback),
        "rollback_backup_sha256": sha256_file(rollback),
        "new_wsl_task_passed": True,
        "resumed_wsl_task_passed": True,
        "outcome": "pass",
        "completed_at": "2026-09-01T20:00:00+02:00",
    }
    if extra:
        payload.update(extra)
    config.desktop_retest_attestation.parent.mkdir(parents=True)
    config.desktop_retest_attestation.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config.desktop_retest_attestation


def powershell_version_command() -> tuple[str, ...]:
    return (
        "powershell.exe",
        "-NoProfile",
        "-Command",
        "$p=Get-AppxPackage OpenAI.Codex -ErrorAction SilentlyContinue; "
        "if($null -eq $p){exit 3}; $p.Version.ToString()",
    )


def powershell_task_command(name: str = "GasCity-WSL-Bootstrap") -> tuple[str, ...]:
    return (
        "powershell.exe",
        "-NoProfile",
        "-Command",
        f"$t=Get-ScheduledTask -TaskName '{name}' -ErrorAction SilentlyContinue; "
        "if($null -eq $t){exit 3}; $a=@($t.Actions)[0]; $g=@($t.Triggers)[0]; "
        "[pscustomobject]@{State=$t.State.ToString();Execute=$a.Execute;"
        "Arguments=$a.Arguments;UserId=$t.Principal.UserId;"
        "RunLevel=$t.Principal.RunLevel.ToString();"
        "TriggerClass=$g.CimClass.CimClassName;Delay=$g.Delay} | "
        "ConvertTo-Json -Compress",
    )


def obsidian_vaults_command(config: ProbeConfig) -> tuple[str, ...]:
    return (str(config.obsidian_command), "vaults", "verbose")


def obsidian_read_command(config: ProbeConfig) -> tuple[str, ...]:
    return (
        str(config.obsidian_command),
        f"vault={config.obsidian_vault}",
        "read",
        f"path={config.obsidian_probe_path}",
    )


def gpg_readiness_command(config: ProbeConfig) -> tuple[str, ...]:
    return (str(config.gpg_readiness_command), "check", "--json")


def test_obsidian_reconciler_health_uses_source_current_result(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    config = ProbeConfig(
        **{
            **config.__dict__,
            "obsidian_reconciler_command": Path("/managed/aegis-obsidian-reconcile"),
            "obsidian_reconciler_registry": tmp_path / "registry.json",
            "obsidian_reconciler_state": tmp_path / "state",
        }
    )
    command = (
        "/managed/aegis-obsidian-reconcile",
        "check",
        "--registry",
        str(tmp_path / "registry.json"),
        "--state-dir",
        str(tmp_path / "state"),
    )
    healthy = check_obsidian_reconciler(
        config,
        FakeRunner(
            {
                command: CommandResult(
                    0,
                    json.dumps(
                        {
                            "ok": True,
                            "projects": [
                                {"id": "gas-city", "fresh": True, "age_seconds": 12, "problems": []}
                            ],
                        }
                    ),
                )
            }
        ),
        "host-wsl",
    )
    assert healthy.status == "pass"

    stale = check_obsidian_reconciler(
        config,
        FakeRunner(
            {
                command: CommandResult(
                    1,
                    json.dumps(
                        {
                            "ok": False,
                            "projects": [
                                {
                                    "id": "gas-city",
                                    "fresh": False,
                                    "age_seconds": 220,
                                    "problems": ["vault source digest is stale"],
                                }
                            ],
                        }
                    ),
                )
            }
        ),
        "host-wsl",
    )
    assert stale.status == "fail"
    assert stale.details["projects"][0]["fresh"] is False


def healthy_task() -> str:
    return json.dumps(
        {
            "State": "Ready",
            "Execute": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "Arguments": (
                "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "
                '"C:\\Users\\tester\\AppData\\Local\\GasCity\\bootstrap\\'
                'gas-city-wsl-bootstrap.ps1"'
            ),
            "UserId": r"TEST\tester",
            "RunLevel": "Limited",
            "TriggerClass": "MSFT_TaskLogonTrigger",
            "Delay": "PT30S",
        }
    )


def healthy_responses(config: ProbeConfig) -> dict[tuple[str, ...], CommandResult]:
    responses: dict[tuple[str, ...], CommandResult] = {
        ("loginctl", "show-user", "tester", "-p", "Linger", "--value"): CommandResult(0, "yes\n"),
        powershell_version_command(): CommandResult(0, "26.820.7780.0\n"),
        powershell_task_command(): CommandResult(0, healthy_task()),
        obsidian_vaults_command(config): CommandResult(
            0,
            f"{config.obsidian_vault}\t/home/tester/vaults/main\n",
        ),
        obsidian_read_command(config): CommandResult(
            0,
            "---\nbead_id: ga-zbmk\nstatus: closed\n---\n",
        ),
        gpg_readiness_command(config): CommandResult(
            0,
            json.dumps(
                {
                    "schema": "codex.gpg-readiness.v2",
                    "status": "ready",
                    "fingerprint": "FD5585922F5335BC378AD8D42ECF4432C7E7982D",
                    "keygrip": "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA",
                    "agent_running": True,
                    "cached": True,
                    "proof": "agent-cache",
                }
            ),
        ),
        (
            "/managed/gc",
            "--city",
            str(config.city),
            "status",
            "--json",
        ): CommandResult(
            0,
            json.dumps(
                {
                    "controller": {"running": True},
                    "beads": {"native_store_eligible": True},
                    "rigs": [{"name": "gascity", "suspended": True}],
                }
            ),
        ),
    }
    units = (
        (True, config.supervisor_unit),
        (False, config.signer_service),
        (False, config.signer_socket),
    )
    for user, unit in units:
        prefix = ("systemctl", "--user") if user else ("systemctl",)
        responses[(*prefix, "is-enabled", unit)] = CommandResult(0, "enabled\n")
        responses[(*prefix, "is-active", unit)] = CommandResult(0, "active\n")
    return responses


def by_key(report, key: str):
    return next(check for check in report.checks if check.key == key)


def test_affected_desktop_build_requires_workaround(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.820.7780.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    keyed = {check.key: check for check in checks}

    assert keyed["desktop.config"].status == "pass"
    assert keyed["desktop.wsl_mode"].status == "pass"
    assert keyed["desktop.version"].status == "warn"
    assert keyed["desktop.codex_app_workaround"].status == "pass"


def test_affected_desktop_build_without_workaround_fails(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    assert config.windows_config is not None
    write_windows_config(config.windows_config, workaround=False)
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.820.7780.0\n")})

    checks = check_desktop(config, runner, "host-wsl")

    assert next(check for check in checks if check.key.endswith("workaround")).status == "fail"


def test_newer_desktop_build_requests_controlled_retest(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.900.1.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    version = next(check for check in checks if check.key == "desktop.version")

    assert version.status == "warn"
    assert version.details["candidate_retest"] is True
    assert version.details["retest_attestation"]["status"] == "absent"


def test_newer_desktop_build_accepts_exact_transport_retest(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    assert config.windows_config is not None
    write_windows_config(config.windows_config, workaround=False)
    write_desktop_retest_attestation(config, desktop_version="26.900.1.0")
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.900.1.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    keyed = {check.key: check for check in checks}

    assert keyed["desktop.version"].status == "pass"
    assert keyed["desktop.version"].details["candidate_retest"] is False
    assert keyed["desktop.version"].details["retest_attestation"]["status"] == "verified"
    assert keyed["desktop.codex_app_workaround"].status == "pass"
    assert keyed["desktop.codex_app_workaround"].details["verified_newer_build"] is True


def test_affected_build_ignores_attestation_and_requires_workaround(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    assert config.windows_config is not None
    write_windows_config(config.windows_config, workaround=False)
    write_desktop_retest_attestation(config, desktop_version="26.820.7780.0")
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.820.7780.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    keyed = {check.key: check for check in checks}

    assert keyed["desktop.version"].status == "warn"
    assert keyed["desktop.codex_app_workaround"].status == "fail"
    assert keyed["desktop.codex_app_workaround"].details["verified_newer_build"] is False


def test_mismatched_transport_retest_remains_warning(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    assert config.windows_config is not None
    write_windows_config(config.windows_config, workaround=False)
    write_desktop_retest_attestation(
        config,
        desktop_version="26.900.1.0",
        extra={"windows_config_sha256": "0" * 64},
    )
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.900.1.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    keyed = {check.key: check for check in checks}

    assert keyed["desktop.version"].status == "warn"
    assert keyed["desktop.version"].details["retest_attestation"]["status"] == "mismatch"
    assert keyed["desktop.codex_app_workaround"].status == "warn"


def test_extra_attestation_field_is_rejected(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    assert config.windows_config is not None
    write_windows_config(config.windows_config, workaround=False)
    write_desktop_retest_attestation(
        config,
        desktop_version="26.900.1.0",
        extra={"comment": "not part of the authority schema"},
    )
    runner = FakeRunner({powershell_version_command(): CommandResult(0, "26.900.1.0\n")})

    checks = check_desktop(config, runner, "host-wsl")
    version = next(check for check in checks if check.key == "desktop.version")

    assert version.status == "warn"
    assert version.details["retest_attestation"]["status"] == "invalid-schema"


def test_wsl_systemd_false_is_a_real_failure(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    config.wsl_config.write_text("[boot]\nsystemd=false\n", encoding="utf-8")

    checks = check_wsl_systemd(config)

    assert checks[0].key == "wsl.systemd_config"
    assert checks[0].status == "fail"
    assert checks[1].status == "pass"


def test_exact_gpg_key_cache_is_ready(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(healthy_responses(config))

    check = check_gpg_signing_cache(config, runner, "host-wsl")

    assert check.status == "pass"
    assert check.details["cached"] is True
    assert check.details["fingerprint"] == "FD5585922F5335BC378AD8D42ECF4432C7E7982D"


def test_exact_gpg_agent_epoch_signature_is_ready(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    responses = healthy_responses(config)
    responses[gpg_readiness_command(config)] = CommandResult(
        0,
        json.dumps(
            {
                "schema": "codex.gpg-readiness.v2",
                "status": "ready",
                "fingerprint": "FD5585922F5335BC378AD8D42ECF4432C7E7982D",
                "keygrip": "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA",
                "agent_running": True,
                "cached": False,
                "proof": "agent-epoch-signature",
            }
        ),
    )

    check = check_gpg_signing_cache(config, FakeRunner(responses), "host-wsl")

    assert check.status == "pass"
    assert check.details["cached"] is False
    assert check.details["proof"] == "agent-epoch-signature"


def test_cold_exact_gpg_key_is_startup_warning(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            gpg_readiness_command(config): CommandResult(
                11,
                json.dumps(
                    {
                        "schema": "codex.gpg-readiness.v2",
                        "status": "cold",
                        "fingerprint": "FD5585922F5335BC378AD8D42ECF4432C7E7982D",
                        "keygrip": "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA",
                        "agent_running": True,
                        "cached": False,
                        "proof": "none",
                    }
                ),
            )
        }
    )

    check = check_gpg_signing_cache(config, runner, "host-wsl")

    assert check.status == "warn"
    assert "unlock-all" in (check.remediation or "")
    assert check.details["cached"] is False


def test_wrong_gpg_fingerprint_never_satisfies_readiness(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            gpg_readiness_command(config): CommandResult(
                0,
                json.dumps(
                    {
                        "schema": "codex.gpg-readiness.v2",
                        "status": "ready",
                        "fingerprint": "5BF9B6AC72EAE8319B07388152A63D29CFC7113F",
                        "keygrip": "AC8252EE2B169807CEEF076AB747CE8F9B18C81D",
                        "agent_running": True,
                        "cached": True,
                        "proof": "agent-cache",
                    }
                ),
            )
        }
    )

    check = check_gpg_signing_cache(config, runner, "host-wsl")

    assert check.status == "fail"
    assert "identity" in check.summary.lower()


def test_contradictory_gpg_readiness_evidence_fails_closed(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            gpg_readiness_command(config): CommandResult(
                0,
                json.dumps(
                    {
                        "schema": "codex.gpg-readiness.v2",
                        "status": "ready",
                        "fingerprint": "FD5585922F5335BC378AD8D42ECF4432C7E7982D",
                        "keygrip": "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA",
                        "agent_running": False,
                        "cached": True,
                        "proof": "agent-cache",
                    }
                ),
            )
        }
    )

    check = check_gpg_signing_cache(config, runner, "host-wsl")

    assert check.status == "fail"
    assert "unexpectedly" in check.summary.lower()


def test_stale_supervisor_units_are_reported_without_mutation(tmp_path: Path) -> None:
    config = make_config(tmp_path, stale_units=3)

    checks = check_supervisor_units(config)
    stale = next(check for check in checks if check.key == "gascity.stale_supervisor_units")

    assert stale.status == "warn"
    assert stale.details["stale_count"] == 3
    assert len(list(config.user_wants_dir.glob("*.service"))) == 4


def test_gc_status_pins_the_managed_gc_home(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(healthy_responses(config))

    check = check_gc_status(config, runner, "host-wsl")

    assert check.status == "pass"
    env = runner.environments[-1]
    assert env is not None
    assert env["GC_HOME"] == str(config.city.parent / "home")


def test_windows_bootstrap_contract_drift_fails(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    task = json.loads(healthy_task())
    task["RunLevel"] = "Highest"
    runner = FakeRunner({powershell_task_command(): CommandResult(0, json.dumps(task))})

    check = check_windows_bootstrap(config, runner, "host-wsl")

    assert check.status == "fail"
    assert "drifted" in check.summary


def test_sandbox_socket_denial_is_unknown_not_failure(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    command = (
        "/managed/gc",
        "--city",
        str(config.city),
        "status",
        "--json",
    )
    runner = FakeRunner(
        {
            command: CommandResult(
                0,
                json.dumps({"controller": {"running": False}}),
                "dial tcp 127.0.0.1:53381: socket: operation not permitted",
            )
        }
    )

    check = check_gc_status(config, runner, "codex-sandbox")

    assert check.status == "unknown"
    assert check.details["observer"] == "codex-sandbox"


def test_sandbox_obsidian_ipc_denial_is_unknown_not_closed(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            obsidian_vaults_command(config): CommandResult(
                1,
                stderr=(
                    "The CLI is unable to find Obsidian. "
                    "Please make sure Obsidian is running and try again."
                ),
            )
        }
    )

    check = check_obsidian(config, runner, "codex-sandbox")

    assert check.status == "unknown"
    assert check.details["observer"] == "codex-sandbox"
    assert check.details["authority"] == "observer-limited"
    assert "cannot establish" in check.summary.lower()


def test_host_wsl_obsidian_probe_reads_managed_note(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            obsidian_vaults_command(config): CommandResult(
                0,
                f"{config.obsidian_vault}\t/home/tester/vaults/main\n",
            ),
            obsidian_read_command(config): CommandResult(
                0,
                "---\nbead_id: ga-zbmk\nstatus: closed\n---\n",
            ),
        }
    )

    check = check_obsidian(config, runner, "host-wsl")

    assert check.status == "pass"
    assert check.details["observer"] == "host-wsl"
    assert check.details["authority"] == "host-wsl-live-ipc"
    assert check.details["vault"] == config.obsidian_vault
    assert check.details["probe_path"] == config.obsidian_probe_path


def test_host_wsl_stale_obsidian_index_recommends_supported_vault_reload(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            obsidian_vaults_command(config): CommandResult(
                0,
                f"{config.obsidian_vault}\t/home/tester/vaults/main\n",
            ),
            obsidian_read_command(config): CommandResult(
                1,
                stderr=f'Error: File "{config.obsidian_probe_path}" not found.',
            ),
        }
    )

    check = check_obsidian(config, runner, "host-wsl")

    assert check.status == "warn"
    assert "filesystem vault check first" in check.remediation.lower()
    assert f"obsidian vault={config.obsidian_vault} reload" in check.remediation


def test_host_wsl_closed_obsidian_is_warning_not_vault_failure(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(
        {
            obsidian_vaults_command(config): CommandResult(
                1,
                stderr="The CLI is unable to find Obsidian.",
            )
        }
    )

    check = check_obsidian(config, runner, "host-wsl")

    assert check.status == "warn"
    assert check.details["observer"] == "host-wsl"
    assert check.details["authority"] == "host-wsl-live-ipc"
    assert "filesystem" in check.remediation.lower()


def test_wsl_interop_vsock_denial_is_unknown_not_desktop_failure(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    denial = CommandResult(
        1,
        stderr="<3>WSL (4 - ) ERROR: UtilBindVsockAnyPort:307: socket failed 1",
    )
    runner = FakeRunner({powershell_version_command(): denial})

    checks = check_desktop(config, runner, "codex-sandbox")
    version = next(check for check in checks if check.key == "desktop.version")

    assert version.status == "unknown"
    assert version.details["observer"] == "codex-sandbox"


def test_full_report_is_degraded_for_mitigated_affected_build(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(healthy_responses(config))

    report = build_report(config, runner=runner, env={})

    assert report.overall == "degraded"
    assert report.observer == "host-wsl"
    assert report.authority == "host-control-plane"
    assert by_key(report, "desktop.version").status == "warn"
    assert by_key(report, "desktop.codex_app_workaround").status == "pass"
    assert by_key(report, "obsidian.host_ipc").status == "pass"
    assert by_key(report, "gascity.status").status == "pass"
    assert exit_code(report) == 1
    assert "Codex WSL reboot readiness: DEGRADED" in render_human(report)
    assert "Authority: host-control-plane" in render_human(report)


def test_full_report_allows_explicit_host_observer_for_approved_host_run(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    runner = FakeRunner(healthy_responses(config))

    report = build_report(
        config,
        runner=runner,
        env={"CODEX_PERMISSION_PROFILE": "managed"},
        observer_override="host-wsl",
    )

    assert report.observer == "host-wsl"
    assert report.authority == "host-control-plane"


def test_full_report_fails_when_supervisor_is_inactive(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    responses = healthy_responses(config)
    responses[("systemctl", "--user", "is-active", config.supervisor_unit)] = CommandResult(
        3, "inactive\n"
    )
    runner = FakeRunner(responses)

    report = build_report(config, runner=runner, env={})

    assert report.overall == "failed"
    assert by_key(report, "gascity.supervisor.active").status == "fail"
    assert exit_code(report) == 2
