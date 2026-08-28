from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from aegis_foundation import obsidian_install

REPO_ROOT = Path(__file__).parents[2]


def test_rendered_user_units_are_reboot_persistent_and_output_scoped(tmp_path: Path) -> None:
    home = tmp_path / "home"
    output = home / "vaults" / "main" / "GasCity" / "Aegis"
    registry = home / ".config" / "aegis" / "obsidian-projects.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "projects": [
                    {
                        "id": "gas-city",
                        "enabled": True,
                        "target_dir": str(home / "codex"),
                        "output_dir": str(output),
                        "bead_export_argv": ["/usr/bin/bd", "list", "--json"],
                        "freshness_sla_seconds": 180,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assets = obsidian_install.render_assets(home=home, registry_path=registry)
    service = assets["aegis-obsidian-reconcile.service"].decode()
    timer = assets["aegis-obsidian-reconcile.timer"].decode()

    assert (
        f'ExecStart="{home}/.local/bin/aegis-obsidian-reconcile" run '
        f'--registry "{registry}"' in service
    )
    assert f'ReadWritePaths="{output.parent}"' in service
    assert f'ReadWritePaths="{output}"\n' not in service
    assert f'ReadWritePaths="{home}/.local/state/aegis/obsidian-reconciler"' in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service
    assert "OnBootSec=45s" in timer
    assert "OnUnitActiveSec=60s" in timer
    assert "Persistent=true" in timer


def test_runtime_archive_is_byte_deterministic(tmp_path: Path) -> None:
    first = obsidian_install.build_runtime_bytes(Path(__file__).parents[2])
    second = obsidian_install.build_runtime_bytes(Path(__file__).parents[2])
    assert first == second
    assert first.startswith(b"#!/usr/bin/env python3\nPK")
    runtime = tmp_path / "aegis-obsidian-reconcile"
    runtime.write_bytes(first)
    runtime.chmod(0o755)
    result = subprocess.run(
        [str(runtime), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "run" in result.stdout
    assert "check" in result.stdout


def test_source_installer_plans_from_external_working_directory(tmp_path: Path) -> None:
    home = tmp_path / "home"
    registry = _source_registry(tmp_path, home)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/install-aegis-obsidian-reconciler"),
            "--plan",
            "--registry-source",
            str(registry),
            "--home",
            str(home),
            "--source-root",
            str(REPO_ROOT),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["schema_version"] == "1"


def _source_registry(tmp_path: Path, home: Path) -> Path:
    path = tmp_path / "registry-source.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "projects": [
                    {
                        "id": "gas-city",
                        "enabled": True,
                        "target_dir": str(home / "codex"),
                        "output_dir": str(home / "vaults/main/GasCity/Aegis"),
                        "bead_export_argv": ["/usr/bin/bd", "list", "--json"],
                        "freshness_sla_seconds": 180,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_install_applies_exact_user_files_and_enables_timer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    registry = _source_registry(tmp_path, home)
    output_parent = home / "vaults/main/GasCity"
    output_parent.mkdir(parents=True)
    systemctl_calls: list[tuple[str, ...]] = []

    def systemctl(*arguments: str) -> subprocess.CompletedProcess[str]:
        systemctl_calls.append(arguments)
        if arguments[:2] == ("start", "aegis-obsidian-reconcile.service"):
            state = home / ".local/state/aegis/obsidian-reconciler"
            assert state.is_dir()
            assert state.stat().st_mode & 0o777 == 0o700
        if arguments[0] == "is-enabled":
            return subprocess.CompletedProcess(arguments, 0, "enabled\n", "")
        if arguments[0] == "is-active":
            return subprocess.CompletedProcess(arguments, 0, "active\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(obsidian_install, "_run_systemctl", systemctl)
    monkeypatch.setattr(
        obsidian_install.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, '{"ok":true}\n', ""),
    )

    result = obsidian_install.install(
        home=home,
        source_root=Path(__file__).parents[2],
        registry_source=registry,
    )

    assert result["ok"] is True
    assert (home / ".local/bin/aegis-obsidian-reconcile").stat().st_mode & 0o777 == 0o755
    assert (home / ".config/aegis/obsidian-projects.json").stat().st_mode & 0o777 == 0o600
    assert (home / ".local/state/aegis/obsidian-reconciler/install-manifest.json").is_file()
    assert ("enable", "--now", "aegis-obsidian-reconcile.timer") in systemctl_calls
    assert ("start", "aegis-obsidian-reconcile.service") in systemctl_calls


def test_install_failure_rolls_back_new_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    registry = _source_registry(tmp_path, home)
    (home / "vaults/main/GasCity").mkdir(parents=True)

    def systemctl(*arguments: str) -> subprocess.CompletedProcess[str]:
        if arguments[:2] == ("start", "aegis-obsidian-reconcile.service"):
            return subprocess.CompletedProcess(arguments, 1, "", "simulated refusal")
        if arguments[0] in {"is-enabled", "is-active"}:
            return subprocess.CompletedProcess(arguments, 1, "disabled\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(obsidian_install, "_run_systemctl", systemctl)

    with pytest.raises(RuntimeError, match="initial reconciliation failed"):
        obsidian_install.install(
            home=home,
            source_root=Path(__file__).parents[2],
            registry_source=registry,
        )

    assert not (home / ".local/bin/aegis-obsidian-reconcile").exists()
    assert not (home / ".config/aegis/obsidian-projects.json").exists()
    assert not (home / ".config/systemd/user/aegis-obsidian-reconcile.service").exists()
    assert not (home / ".local/state/aegis/obsidian-reconciler/install-manifest.json").exists()


def test_install_refuses_missing_output_parent_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    registry = _source_registry(tmp_path, home)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        obsidian_install,
        "_run_systemctl",
        lambda *arguments: calls.append(arguments)
        or subprocess.CompletedProcess(arguments, 0, "", ""),
    )

    with pytest.raises(RuntimeError, match="output parent is missing or unsafe"):
        obsidian_install.install(
            home=home,
            source_root=Path(__file__).parents[2],
            registry_source=registry,
        )

    assert calls == []
    assert not (home / ".local/bin/aegis-obsidian-reconcile").exists()
    assert not (home / ".local/state/aegis/obsidian-reconciler").exists()
