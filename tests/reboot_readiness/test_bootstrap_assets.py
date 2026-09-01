from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from aegis_foundation.reboot_readiness import DOCTOR_VERSION


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts/windows/gas-city-wsl-bootstrap.ps1"
WINDOWS_INSTALLER = ROOT / "scripts/windows/install-gas-city-wsl-bootstrap.ps1"
DOCTOR_INSTALLER = ROOT / "scripts/install-codex-wsl-readiness"
RETEST_RECORDER = ROOT / "scripts/record-codex-desktop-transport-retest"


def test_windows_bootstrap_is_read_only_except_evidence() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")

    assert "'--observer', 'host-wsl'" in text
    assert "'--json'" in text
    assert "@('ready', 'degraded')" in text
    assert "@(0, 1)" in text
    assert "latest.json" in text
    assert "Move-Item -LiteralPath $temporary" in text
    for forbidden in (
        "gc rig resume",
        "gc start",
        "systemctl",
        "Restart-Service",
        "Start-Service",
        "managed-git-commit",
    ):
        assert forbidden not in text


def test_windows_bootstrap_uses_powershell_51_compatible_process_capture() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")

    assert "Start-Process -FilePath $WslExe" in text
    assert "-RedirectStandardOutput $stdoutPath" in text
    assert "-RedirectStandardError $stderrPath" in text
    assert "$doctorExit = $process.ExitCode" in text
    assert "$LASTEXITCODE" not in text
    assert "ConvertFrom-Json -Depth" not in text


def test_windows_installer_pins_limited_delayed_logon_contract() -> None:
    text = WINDOWS_INSTALLER.read_text(encoding="utf-8")

    assert "New-ScheduledTaskTrigger -AtLogOn" in text
    assert "$trigger.Delay = 'PT30S'" in text
    assert "-RunLevel Limited" in text
    assert "-StartWhenAvailable" in text
    assert "-MultipleInstances IgnoreNew" in text
    assert "Get-FileHash" in text
    assert "Unregister-ScheduledTask" in text


def test_windows_assets_use_non_virtualized_userprofile_storage() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    installer = WINDOWS_INSTALLER.read_text(encoding="utf-8")

    assert "Join-Path $env:USERPROFILE '.gas-city\\reboot-readiness'" in bootstrap
    assert "Join-Path $env:USERPROFILE '.gas-city\\bootstrap'" in installer
    assert "$env:LOCALAPPDATA 'GasCity\\reboot-readiness'" not in bootstrap
    assert "$env:LOCALAPPDATA 'GasCity\\bootstrap'" not in installer


def test_windows_installer_compares_task_principal_by_canonical_sid() -> None:
    text = WINDOWS_INSTALLER.read_text(encoding="utf-8")

    assert "$CurrentIdentityName = $currentWindowsIdentity.Name" in text
    assert "$CurrentIdentitySid = $currentWindowsIdentity.User.Value" in text
    assert "function Resolve-PrincipalSid" in text
    assert "user_sid = Resolve-PrincipalSid -UserId ([string]$task.Principal.UserId)" in text
    assert "$Contract.user_sid -ne $CurrentIdentitySid" in text
    assert "scheduled task principal cannot resolve to a SID" in text
    assert "New-ScheduledTaskTrigger -AtLogOn -User $CurrentIdentityName" in text
    assert "New-ScheduledTaskPrincipal -UserId $CurrentIdentityName" in text
    assert "$Contract.user_id -ne $CurrentIdentity" not in text


def test_stable_doctor_installer_applies_and_checks_in_temp(tmp_path: Path) -> None:
    destination = tmp_path / "bin/codex-wsl-readiness"

    applied = subprocess.run(
        [str(DOCTOR_INSTALLER), "--apply", "--dest", str(destination)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, applied.stderr
    assert destination.stat().st_mode & 0o777 == 0o755
    assert f"codex-wsl-readiness {DOCTOR_VERSION}\n" == applied.stdout

    checked = subprocess.run(
        [str(DOCTOR_INSTALLER), "--check", "--dest", str(destination)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr


def test_transport_retest_recorder_is_private_idempotent_and_fail_closed(tmp_path: Path) -> None:
    config = tmp_path / "windows/config.toml"
    backup = tmp_path / "windows/config.toml.rollback"
    output = tmp_path / "state/retest.json"
    config.parent.mkdir(parents=True)
    config.write_text("[desktop]\nrunCodexInWindowsSubsystemForLinux = true\n", encoding="utf-8")
    backup.write_text("rollback\n", encoding="utf-8")
    command = [
        str(RETEST_RECORDER),
        "--output",
        str(output),
        "--desktop-version",
        "26.900.1.0",
        "--windows-config",
        str(config),
        "--rollback-backup",
        str(backup),
        "--completed-at",
        "2026-09-01T20:00:00+02:00",
        "--new-wsl-task-passed",
        "--resumed-wsl-task-passed",
    ]

    first = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    assert '"changed": true' in first.stdout
    assert output.stat().st_mode & 0o777 == 0o600
    first_bytes = output.read_bytes()
    first_digest = hashlib.sha256(first_bytes).hexdigest()

    second = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert '"changed": false' in second.stdout

    config.write_text("[desktop]\nrunCodexInWindowsSubsystemForLinux = false\n", encoding="utf-8")
    refused = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert refused.returncode == 2
    assert "already exists with different bytes" in refused.stderr

    replaced = subprocess.run(
        [*command, "--expect-existing-sha256", first_digest],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert replaced.returncode == 0, replaced.stderr
    assert '"changed": true' in replaced.stdout
    backup_path = output.with_name(f"{output.name}.bak-{first_digest}")
    assert backup_path.read_bytes() == first_bytes
    assert backup_path.stat().st_mode & 0o777 == 0o600
