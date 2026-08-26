from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts/windows/gas-city-wsl-bootstrap.ps1"
WINDOWS_INSTALLER = ROOT / "scripts/windows/install-gas-city-wsl-bootstrap.ps1"
DOCTOR_INSTALLER = ROOT / "scripts/install-codex-wsl-readiness"


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
    assert "2026.08.26.1" in applied.stdout

    checked = subprocess.run(
        [str(DOCTOR_INSTALLER), "--check", "--dest", str(destination)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr
