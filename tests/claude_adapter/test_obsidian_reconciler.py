from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pytest

from aegis_foundation import obsidian_live_index, obsidian_reconciler
from aegis_foundation.obsidian_reconcile_cli import build_parser
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


def _registry(
    tmp_path: Path,
    root: Path,
    output: Path,
    *,
    live_index: dict[str, object] | None = None,
) -> Path:
    path = tmp_path / "registry.json"
    project: dict[str, object] = {
        "id": "gas-city",
        "enabled": True,
        "target_dir": str(root),
        "output_dir": str(output),
        "bead_export_argv": ["/usr/bin/bd", "list", "--json"],
        "include_bead_content": False,
        "freshness_sla_seconds": 180,
    }
    if live_index is not None:
        project["live_index"] = live_index
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "projects": [project],
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


def test_registry_live_index_contract_is_strict_and_not_arbitrary_argv(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    live_index = {
        "obsidian_cli": "/home/example/.local/bin/obsidian",
        "vault": "main",
        "probe_path": "GasCity/gas-city-operations/Aegis/Beads/ga-a9ap.md",
        "timeout_seconds": 15,
    }
    registry_path = _registry(tmp_path, root, tmp_path / "vault", live_index=live_index)
    registry = load_registry(registry_path)
    configured = registry.projects[0].live_index
    assert configured is not None
    assert configured.obsidian_cli == Path("/home/example/.local/bin/obsidian")
    assert configured.vault == "main"
    assert configured.probe_path == "GasCity/gas-city-operations/Aegis/Beads/ga-a9ap.md"
    assert configured.timeout_seconds == 15

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["projects"][0]["live_index"]["obsidian_cli"] = "obsidian"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="absolute executable"):
        load_registry(registry_path)

    payload["projects"][0]["live_index"]["obsidian_cli"] = "/usr/bin/obsidian"
    payload["projects"][0]["live_index"]["probe_path"] = "../outside.md"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="safe relative path"):
        load_registry(registry_path)

    payload["projects"][0]["live_index"]["probe_path"] = "Aegis/Beads/ga-a9ap.md"
    payload["projects"][0]["live_index"]["refresh_argv"] = ["/bin/sh", "-c", "anything"]
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="unknown live_index fields"):
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


def test_changed_publication_refreshes_and_probes_live_index_once(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    live_index = {
        "obsidian_cli": "/usr/bin/obsidian",
        "vault": "main",
        "probe_path": "GasCity/gas-city-operations/Aegis/Beads/ga-eiyt.md",
        "timeout_seconds": 15,
    }
    registry = load_registry(_registry(tmp_path, root, output, live_index=live_index))
    state_dir = tmp_path / "state"
    calls: list[tuple[tuple[str, ...], int]] = []

    def run(argv: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[bytes]:
        calls.append((argv, timeout))
        return subprocess.CompletedProcess(argv, 0, b"ok\n", b"")

    first = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=run,
        force=True,
    )
    assert first["ok"] is True
    assert first["projects"][0]["live_index"]["status"] == "confirmed"
    assert calls == [
        (("/usr/bin/obsidian", "vault=main", "reload"), 15),
        (
            (
                "/usr/bin/obsidian",
                "vault=main",
                "read",
                "path=GasCity/gas-city-operations/Aegis/Beads/ga-eiyt.md",
            ),
            15,
        ),
    ]
    state = json.loads((state_dir / "gas-city.json").read_text(encoding="utf-8"))
    assert state["last_success"]["live_index"]["status"] == "confirmed"

    calls.clear()
    second = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=run,
        force=True,
    )
    assert second["ok"] is True
    assert second["projects"][0]["status"] == "current"
    assert second["projects"][0]["live_index"]["status"] == "not-run-no-change"
    assert calls == []


def test_closed_obsidian_is_observer_unavailable_not_publication_failure(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    registry = load_registry(
        _registry(
            tmp_path,
            root,
            output,
            live_index={
                "obsidian_cli": "/usr/bin/obsidian",
                "vault": "main",
                "probe_path": "GasCity/gas-city-operations/Aegis/Home.md",
            },
        )
    )

    def unavailable(
        argv: tuple[str, ...], _timeout: int
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            argv,
            1,
            b"",
            b"The CLI is unable to find Obsidian. Please make sure Obsidian is running.",
        )

    result = obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=tmp_path / "state",
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=unavailable,
        force=True,
    )
    assert result["ok"] is True
    project = result["projects"][0]
    assert project["status"] == "built"
    assert project["live_index"]["status"] == "unavailable"
    assert project["live_index"]["authority"] == "observer-limited"
    assert (output / "Beads" / "ga-eiyt.md").is_file()


def test_live_index_is_optional_for_filesystem_check_and_explicitly_gateable(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "vault"
    registry = load_registry(
        _registry(
            tmp_path,
            root,
            output,
            live_index={
                "obsidian_cli": "/usr/bin/obsidian",
                "vault": "main",
                "probe_path": "GasCity/gas-city-operations/Aegis/Beads/ga-eiyt.md",
            },
        )
    )
    state_dir = tmp_path / "state"

    def ok_runner(argv: tuple[str, ...], _timeout: int) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(argv, 0, b"ok\n", b"")

    obsidian_reconciler.reconcile_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=ok_runner,
        force=True,
    )

    def failed_probe(argv: tuple[str, ...], _timeout: int) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(argv, 2, b"", b"managed note not indexed")

    filesystem = obsidian_reconciler.check_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=failed_probe,
    )
    assert filesystem["ok"] is True

    live = obsidian_reconciler.check_registry(
        registry,
        state_dir=state_dir,
        bead_exporter=lambda _argv, _timeout: _beads(),
        event_reader=lambda _target: [],
        live_index_runner=failed_probe,
        require_live_index=True,
    )
    assert live["ok"] is False
    assert live["projects"][0]["filesystem_ok"] is True
    assert live["projects"][0]["live_index"]["status"] == "failed"
    assert "live Obsidian index" in live["projects"][0]["problems"][-1]


def test_live_index_timeout_and_output_overflow_are_bounded(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    registry = load_registry(
        _registry(
            tmp_path,
            root,
            tmp_path / "vault",
            live_index={
                "obsidian_cli": "/usr/bin/obsidian",
                "vault": "main",
                "probe_path": "GasCity/Aegis/Home.md",
            },
        )
    )
    config = registry.projects[0].live_index
    assert config is not None

    def timeout(_argv: tuple[str, ...], seconds: int) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired("obsidian", seconds)

    timed_out = obsidian_live_index.observe(config, refresh=True, runner=timeout)
    assert timed_out["ok"] is False
    assert timed_out["status"] == "timeout"
    assert timed_out["probe"] is None

    def overflow(argv: tuple[str, ...], _seconds: int) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            argv,
            0,
            b"x" * (obsidian_live_index.MAX_OUTPUT_BYTES + 1),
            b"",
        )

    too_large = obsidian_live_index.observe(config, refresh=False, runner=overflow)
    assert too_large["ok"] is False
    assert too_large["status"] == "failed"
    assert "bounded size" in too_large["probe"]["detail"]


def test_cli_has_explicit_live_index_gate_only_on_check() -> None:
    parser = build_parser()
    check = parser.parse_args(
        [
            "check",
            "--registry",
            "/tmp/registry.json",
            "--require-live-index",
        ]
    )
    assert check.require_live_index is True
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "run",
                "--registry",
                "/tmp/registry.json",
                "--require-live-index",
            ]
        )


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
