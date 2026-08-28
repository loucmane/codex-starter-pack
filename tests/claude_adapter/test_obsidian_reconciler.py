from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pytest

from aegis_foundation import obsidian_reconciler
from aegis_foundation.obsidian_registry import RegistryError, load_registry


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    _run("git", "init", "-q", cwd=root)
    _run("git", "config", "user.email", "test@example.com", cwd=root)
    _run("git", "config", "user.name", "Test User", cwd=root)
    (root / "README.md").write_text("# Project\n", encoding="utf-8")
    _run("git", "add", "README.md", cwd=root)
    _run("git", "commit", "-qm", "initial", cwd=root)
    return root


def _beads(status: str = "open") -> bytes:
    return (
        json.dumps(
            [
                {
                    "id": "ga-eiyt",
                    "title": "Continuously reconcile Obsidian",
                    "status": status,
                    "priority": 1,
                    "issue_type": "bug",
                    "dependencies": [],
                    "metadata": {"gc.branch": "codex/ga-eiyt-obsidian-reconciler"},
                }
            ],
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _registry(tmp_path: Path, root: Path, output: Path) -> Path:
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "projects": [
                    {
                        "id": "gas-city",
                        "enabled": True,
                        "target_dir": str(root),
                        "output_dir": str(output),
                        "bead_export_argv": ["/usr/bin/bd", "list", "--json"],
                        "include_bead_content": False,
                        "freshness_sla_seconds": 180,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_registry_is_explicit_bounded_and_rejects_ambiguous_paths(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    registry_path = _registry(tmp_path, root, tmp_path / "vault")
    registry = load_registry(registry_path)
    assert registry.projects[0].id == "gas-city"
    assert registry.projects[0].bead_export_argv[0] == "/usr/bin/bd"
    assert registry.projects[0].freshness_sla_seconds == 180

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["projects"][0]["bead_export_argv"][0] = "bd"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="absolute executable"):
        load_registry(registry_path)

    payload["projects"][0]["bead_export_argv"][0] = "/usr/bin/bd"
    payload["projects"][0]["output_dir"] = str(root / "forbidden")
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="outside target_dir"):
        load_registry(registry_path)

    payload["projects"][0]["output_dir"] = str(root.parent)
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="must not overlap target_dir"):
        load_registry(registry_path)


def test_reconcile_publishes_changed_snapshot_and_noops_when_current(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    registry = load_registry(_registry(tmp_path, root, output))
    state_dir = tmp_path / "state"
    exports = [_beads(), _beads()]

    def export(_argv: tuple[str, ...], _timeout: int) -> bytes:
        return exports.pop(0)

    def clock() -> datetime:
        return datetime(2026, 8, 28, 20, 0, tzinfo=timezone.utc)

    first = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=export,
        event_reader=lambda _target: [],
        clock=clock,
    )
    assert first["ok"] is True
    assert first["projects"][0]["status"] == "built"
    assert (output / "Beads" / "ga-eiyt.md").is_file()
    before = (output / ".aegis-vault.json").read_bytes()

    second = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=export,
        event_reader=lambda _target: [],
        clock=clock,
        force=True,
    )
    assert second["ok"] is True
    assert second["projects"][0]["status"] == "current"
    assert (output / ".aegis-vault.json").read_bytes() == before
    state = json.loads((state_dir / "gas-city.json").read_text(encoding="utf-8"))
    assert state["last_success"]["source_digest"] == second["projects"][0]["source_digest"]
    assert state["last_error"] is None


def test_export_failure_retains_last_good_vault_and_records_error(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    registry = load_registry(_registry(tmp_path, root, output))
    state_dir = tmp_path / "state"

    obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        force=True,
    )
    before = {
        path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()
    }

    def fail(_argv: tuple[str, ...], _timeout: int) -> bytes:
        raise obsidian_reconciler.ReconcileError("Dolt unavailable")

    result = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=fail,
        event_reader=lambda _target: [],
        force=True,
    )
    assert result["ok"] is False
    assert "Dolt unavailable" in result["projects"][0]["error"]
    after = {
        path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()
    }
    assert after == before
    state = json.loads((state_dir / "gas-city.json").read_text(encoding="utf-8"))
    assert state["last_success"] is not None
    assert state["last_error"]["message"] == "Dolt unavailable"


def test_health_check_detects_source_staleness_not_just_old_timestamps(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    registry = load_registry(_registry(tmp_path, root, output))
    state_dir = tmp_path / "state"
    current = [_beads()]
    obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: current[0],
        event_reader=lambda _target: [],
        force=True,
    )

    healthy = obsidian_reconciler.check_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
    )
    assert healthy["ok"] is True

    stale = obsidian_reconciler.check_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads("closed"),
        event_reader=lambda _target: [],
    )
    assert stale["ok"] is False
    assert stale["projects"][0]["fresh"] is False
    assert "source digest" in stale["projects"][0]["problems"][0]
