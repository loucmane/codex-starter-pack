"""Task 256 coverage for canonical Codex-home topology diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from aegis_foundation import cli
from aegis_foundation import codex_remote_trust as trust
from aegis_foundation import codex_topology as topology

REPO_ROOT = Path(__file__).resolve().parents[2]
THREAD_ID = "019f417f-980b-79e1-b1f0-46bbc740a7bf"
PROJECT_TRUSTED_AT = "2026-07-15T12:00:00Z"


def _toml_key(value: str | Path) -> str:
    return json.dumps(Path(value).as_posix())


def _make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    manifest = project / ".aegis" / "foundation-manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps(
            {
                "gates": [
                    {
                        "id": "codex.hook_trust",
                        "settings_path": ".codex/hooks.json",
                        "review_command": "/hooks",
                        "hash_scope": "exact_hook_definition",
                        "bypass_allowed": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    hooks = project / ".codex" / "hooks.json"
    hooks.parent.mkdir()
    hooks.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "safe-hook"}],
                        }
                    ]
                }
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return project


def _make_home(
    tmp_path: Path,
    name: str,
    *,
    project: Path | None = None,
    trusted: bool = False,
    approved_at: str | None = None,
    version: str = "0.144.4",
    with_sessions: bool = True,
    with_sqlite: bool = True,
) -> tuple[Path, Path]:
    home = tmp_path / name
    home.mkdir()
    config = 'model = "gpt-5-codex"\n'
    if project is not None and trusted:
        config += f"\n[projects.{_toml_key(project)}]\n" 'trust_level = "trusted"\n'
    (home / "config.toml").write_text(config, encoding="utf-8")

    release = home / "packages" / "standalone" / "releases" / f"{version}-test-platform"
    binary = release / "bin" / "codex"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    current = home / "packages" / "standalone" / "current"
    current.parent.mkdir(parents=True, exist_ok=True)
    current.symlink_to(release)

    if with_sessions:
        (home / "sessions").mkdir()
    if with_sqlite:
        sqlite_dir = home / "sqlite"
        sqlite_dir.mkdir()
        (sqlite_dir / "state_5.sqlite").write_bytes(b"fixture-sqlite")

    if project is not None and approved_at is not None:
        allowlist = home / trust.ALLOWLIST_FILENAME
        allowlist.write_bytes(
            trust.render_allowlist(
                (
                    trust.TrustEntry(
                        path=project.resolve().as_posix(),
                        approved_by="owner",
                        approved_at=approved_at,
                        reason="fixture authority",
                    ),
                )
            )
        )
        allowlist.chmod(0o600)
    return home, binary


def _write_session(
    home: Path,
    *,
    thread_id: str = THREAD_ID,
    started_at: str = "2026-07-15T11:00:00Z",
    cwd: Path,
) -> Path:
    folder = home / "sessions" / "2026" / "07" / "15"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"rollout-2026-07-15T11-00-00-{thread_id}.jsonl"
    metadata = {
        "type": "session_meta",
        "payload": {
            "id": thread_id,
            "timestamp": started_at,
            "cwd": cwd.as_posix(),
            "source": "cli",
            "originator": "codex-tui",
        },
    }
    path.write_text(
        json.dumps(metadata)
        + "\n"
        + json.dumps({"type": "response_item", "payload": {"secret": "TRANSCRIPT_SECRET"}})
        + "\n",
        encoding="utf-8",
    )
    return path


def _make_proc(
    tmp_path: Path,
    *,
    pid: int,
    binary: Path,
    arguments: list[str],
    ppid: int = 1,
    open_sqlite: Path | None = None,
) -> Path:
    proc = tmp_path / "proc"
    proc.mkdir(exist_ok=True)
    process = proc / str(pid)
    process.mkdir()
    (process / "exe").symlink_to(binary)
    (process / "cmdline").write_bytes(
        b"\x00".join(item.encode("utf-8") for item in arguments) + b"\x00"
    )
    (process / "status").write_text(f"Name:\tcodex\nPPid:\t{ppid}\n", encoding="utf-8")
    if open_sqlite is not None:
        descriptors = process / "fd"
        descriptors.mkdir()
        (descriptors / "9").symlink_to(open_sqlite)
    return proc


def _snapshot(root: Path) -> dict[str, tuple[Any, ...]]:
    result: dict[str, tuple[Any, ...]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if path.is_symlink():
            result[relative] = ("symlink", mode, os.readlink(path))
        elif path.is_file():
            content = path.read_bytes()
            result[relative] = ("file", mode, hashlib.sha256(content).hexdigest())
        elif path.is_dir():
            result[relative] = ("directory", mode)
        else:
            result[relative] = ("other", mode)
    return result


def _status(
    canonical_home: Path,
    *,
    candidate_homes: tuple[Path, ...] = (),
    project: Path | None = None,
    thread_ids: tuple[str, ...] = (),
    proc_root: Path | None = None,
    codex_commands: tuple[Path, ...] = (),
    active_work_state: str = "drained",
) -> dict[str, Any]:
    return topology.topology_status(
        canonical_codex_home=canonical_home,
        candidate_codex_homes=candidate_homes,
        projects=(project,) if project is not None else (),
        thread_ids=thread_ids,
        proc_root=proc_root or (canonical_home.parent / "empty-proc"),
        process_scope="fixture",
        codex_commands=codex_commands,
        active_work_state=active_work_state,
        environment={"PATH": ""},
    )


def test_single_canonical_home_is_healthy_and_task257_ready(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(
        tmp_path,
        "canonical",
        project=project,
        trusted=True,
        approved_at=PROJECT_TRUSTED_AT,
    )
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(
        home,
        project=project,
        proc_root=proc,
        codex_commands=(binary,),
    )
    plan = topology.topology_migration_plan(status)

    assert status["status"] == "healthy"
    assert status["split_brain"] == {"detected": False, "indicators": []}
    assert status["security"] == {
        "selected_nonsecret_config_values_emitted": True,
        "unrequested_config_values_emitted": False,
        "auth_read": False,
        "transcript_text_read": False,
        "hook_trust_store_read": False,
        "hook_trust_asserted": False,
        "process_arguments_emitted": False,
        "lifecycle_contacted": False,
    }
    assert status["projects"][0]["tracked_hook_guidance"]["valid"] is True
    assert status["projects"][0]["client_hook_trust"]["asserted"] is False
    assert plan["status"] == "ready_for_task257"
    assert plan["blockers"] == []
    assert all(phase["task256_execute"] is False for phase in plan["phases"])


def test_dual_home_sessions_sqlite_executables_and_servers_are_split_brain(
    tmp_path: Path,
) -> None:
    canonical, canonical_binary = _make_home(tmp_path, "canonical")
    remote, remote_binary = _make_home(tmp_path, "remote")
    _write_session(canonical, thread_id="canonical-thread", cwd=tmp_path)
    _write_session(remote, thread_id="remote-thread", cwd=tmp_path)
    proc = _make_proc(
        tmp_path,
        pid=101,
        binary=canonical_binary,
        arguments=[canonical_binary.as_posix(), "app-server", "--remote-control"],
    )
    _make_proc(
        tmp_path,
        pid=202,
        binary=remote_binary,
        arguments=[remote_binary.as_posix(), "app-server", "--remote-control"],
    )

    status = _status(
        canonical,
        candidate_homes=(remote,),
        proc_root=proc,
        codex_commands=(canonical_binary, remote_binary),
    )

    codes = {item["code"] for item in status["split_brain"]["indicators"]}
    assert status["status"] == "split_brain"
    assert {
        "multiple_session_stores",
        "multiple_sqlite_stores",
        "multiple_server_homes",
        "multiple_executable_identities",
    } <= codes
    plan = topology.topology_migration_plan(status)
    assert plan["status"] == "blocked"
    assert any(
        item["code"] == "noncanonical_state_requires_disposition" for item in plan["blockers"]
    )


def test_multiple_control_sockets_are_split_brain_even_without_visible_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical, _ = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    remote, _ = _make_home(tmp_path, "remote", with_sessions=False, with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()
    original_path_surface = topology._path_surface

    def socket_aware_path_surface(path: Path, *, label: str) -> dict[str, Any]:
        if path.name == "app-server-control.sock":
            return {
                "path": path.as_posix(),
                "kind": "socket",
                "resolved": {
                    "value": path.as_posix(),
                    "state": "known",
                    "source": path.as_posix(),
                    "observed": True,
                    "detail": "fixture socket identity",
                },
            }
        return original_path_surface(path, label=label)

    monkeypatch.setattr(topology, "_path_surface", socket_aware_path_surface)
    status = _status(canonical, candidate_homes=(remote,), proc_root=proc)

    assert status["status"] == "split_brain"
    assert any(
        item["code"] == "multiple_control_sockets" for item in status["split_brain"]["indicators"]
    )


def test_unknown_process_inventory_scope_blocks_task257_even_when_procfs_is_readable(
    tmp_path: Path,
) -> None:
    canonical, _ = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()

    status = topology.topology_status(
        canonical_codex_home=canonical,
        proc_root=proc,
        active_work_state="drained",
        environment={"PATH": ""},
    )
    plan = topology.topology_migration_plan(status)

    assert status["status"] == "attention_required"
    assert status["process_inventory"]["scope"]["state"] == "unknown"
    assert {item["code"] for item in status["issues"]} >= {"process_inventory_scope_unknown"}
    assert plan["status"] == "blocked"
    assert {item["code"] for item in plan["blockers"]} >= {"process_inventory_scope_unknown"}


def test_multiple_canonical_sqlite_roots_require_explicit_authority_selection(
    tmp_path: Path,
) -> None:
    canonical, _ = _make_home(tmp_path, "canonical", with_sessions=False)
    (canonical / "state_5.sqlite").write_bytes(b"second-root")
    proc = tmp_path / "proc"
    proc.mkdir()

    ambiguous = _status(canonical, proc_root=proc)
    blocked = topology.topology_migration_plan(ambiguous)
    explicit = topology.topology_status(
        canonical_codex_home=canonical,
        canonical_sqlite_home=canonical / "sqlite",
        proc_root=proc,
        process_scope="fixture",
        active_work_state="drained",
        environment={"PATH": ""},
    )

    assert any(
        item["code"] == "multiple_sqlite_roots" for item in ambiguous["split_brain"]["indicators"]
    )
    assert any(item["code"] == "sqlite_authority_ambiguous" for item in ambiguous["issues"])
    assert any(item["code"] == "sqlite_authority_ambiguous" for item in blocked["blockers"])
    assert not any(item["code"] == "sqlite_authority_ambiguous" for item in explicit["issues"])


def test_configured_sqlite_home_has_precedence_and_invalid_relative_value_blocks(
    tmp_path: Path,
) -> None:
    canonical, _ = _make_home(tmp_path, "canonical", with_sessions=False)
    configured = tmp_path / "configured-sqlite"
    configured.mkdir()
    (configured / "state_5.sqlite").write_bytes(b"configured")
    environment_sqlite = tmp_path / "environment-sqlite"
    environment_sqlite.mkdir()
    (canonical / "config.toml").write_text(
        f"sqlite_home = {json.dumps(configured.as_posix())}\n",
        encoding="utf-8",
    )
    proc = tmp_path / "proc"
    proc.mkdir()

    configured_status = topology.topology_status(
        canonical_codex_home=canonical,
        proc_root=proc,
        process_scope="fixture",
        active_work_state="drained",
        environment={
            "PATH": "",
            "CODEX_SQLITE_HOME": environment_sqlite.as_posix(),
        },
    )

    assert configured_status["canonical_architecture"]["codex_sqlite_home"] == configured.as_posix()
    assert (
        configured_status["homes"][0]["sqlite"]["effective_home"]["source"]
        == f"{canonical.as_posix()}/config.toml::sqlite_home"
    )
    assert configured_status["homes"][0]["sqlite"]["selection_explicit"]["value"] is True

    (canonical / "config.toml").write_text('sqlite_home = "relative/sqlite"\n', encoding="utf-8")
    invalid_status = _status(canonical, proc_root=proc)
    invalid_plan = topology.topology_migration_plan(invalid_status)

    assert any(item["code"] == "sqlite_home_invalid" for item in invalid_status["issues"])
    assert any(item["code"] == "sqlite_home_invalid" for item in invalid_plan["blockers"])


def test_context_routed_wrapper_is_reported_without_emitting_source(tmp_path: Path) -> None:
    home, _ = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()
    wrapper = tmp_path / "codex"
    wrapper.write_text(
        "#!/bin/sh\n"
        "pwd >/dev/null\n"
        "CODEX_HOME=$CODEX_GLOBAL_DIR\n"
        "AEGIS_REMOTE_CONTROL_HOME=/private/remote-control\n"
        "exec /private/codex\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    status = _status(home, proc_root=proc, codex_commands=(wrapper,))
    encoded = json.dumps(status, sort_keys=True)

    assert any(
        item["code"] == "context_routed_wrapper" for item in status["split_brain"]["indicators"]
    )
    assert "/private/remote-control" not in encoded
    command = next(item for item in status["commands"] if item["path"] == wrapper.as_posix())
    assert command["wrapper"]["home_routing"] is True
    assert "sets_CODEX_HOME" in command["wrapper"]["signals"]


def test_stale_thread_message_requires_durable_trust_timestamp(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(
        tmp_path,
        "canonical",
        project=project,
        trusted=True,
        approved_at=PROJECT_TRUSTED_AT,
    )
    _write_session(home, cwd=project, started_at="2026-07-15T11:00:00Z")
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )

    thread = status["threads"][0]
    assert thread["freshness"] == "stale"
    assert thread["message"] == topology.STALE_THREAD_MESSAGE
    assert thread["hook_execution_asserted"] is False
    assert thread["hook_trust_asserted"] is False


def test_newer_thread_does_not_claim_hooks_loaded_or_trusted(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(
        tmp_path,
        "canonical",
        project=project,
        trusted=True,
        approved_at=PROJECT_TRUSTED_AT,
    )
    _write_session(home, cwd=project, started_at="2026-07-15T13:00:00Z")
    proc = tmp_path / "proc"
    proc.mkdir()

    thread = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )["threads"][0]

    assert thread["freshness"] == "not_predating_trust"
    assert thread["message"] != topology.STALE_THREAD_MESSAGE
    assert thread["hook_execution_asserted"] is False
    assert thread["hook_trust_asserted"] is False


def test_config_trust_without_durable_timestamp_keeps_freshness_unknown(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(tmp_path, "canonical", project=project, trusted=True)
    _write_session(home, cwd=project)
    proc = tmp_path / "proc"
    proc.mkdir()

    thread = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )["threads"][0]

    assert thread["freshness"] == "unknown"
    assert topology.STALE_THREAD_MESSAGE not in thread["message"]


def test_same_thread_in_two_homes_is_ambiguous_and_blocks_plan(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    canonical, canonical_binary = _make_home(tmp_path, "canonical", project=project, trusted=True)
    remote, remote_binary = _make_home(tmp_path, "remote", project=project, trusted=True)
    _write_session(canonical, cwd=project)
    _write_session(remote, cwd=project)
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(
        canonical,
        candidate_homes=(remote,),
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(canonical_binary, remote_binary),
    )

    assert status["threads"][0]["ownership"] == "ambiguous"
    assert any(item["code"] == "thread_ownership_ambiguous" for item in status["issues"])
    assert any(
        item["code"] == "thread_ownership_ambiguous"
        for item in topology.topology_migration_plan(status)["blockers"]
    )


def test_malformed_config_fails_closed_without_exposing_content(tmp_path: Path) -> None:
    home, binary = _make_home(tmp_path, "canonical")
    (home / "config.toml").write_text('token = "CONFIG_SECRET"\n[broken', encoding="utf-8")
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(home, proc_root=proc, codex_commands=(binary,))
    encoded = json.dumps(status, sort_keys=True)

    assert status["status"] == "attention_required"
    assert any(item["code"] == "config_invalid" for item in status["issues"])
    assert "CONFIG_SECRET" not in encoded
    assert any(
        item["code"] == "config_invalid"
        for item in topology.topology_migration_plan(status)["blockers"]
    )


def test_auth_transcripts_and_unrequested_config_values_are_never_emitted(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(
        tmp_path,
        "canonical",
        project=project,
        trusted=True,
        approved_at=PROJECT_TRUSTED_AT,
    )
    with (home / "config.toml").open("a", encoding="utf-8") as handle:
        handle.write('\nsecret_value = "CONFIG_SECRET"\n')
    (home / "auth.json").write_text('{"token":"AUTH_SECRET"}', encoding="utf-8")
    _write_session(home, cwd=project)
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )
    encoded = json.dumps(status, sort_keys=True)

    for forbidden in ("AUTH_SECRET", "CONFIG_SECRET", "TRANSCRIPT_SECRET"):
        assert forbidden not in encoded
    assert status["security"]["auth_read"] is False
    assert status["security"]["transcript_text_read"] is False


def test_status_and_plan_are_byte_preserving_and_deterministic(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(
        tmp_path,
        "canonical",
        project=project,
        trusted=True,
        approved_at=PROJECT_TRUSTED_AT,
    )
    _write_session(home, cwd=project)
    proc = tmp_path / "proc"
    proc.mkdir()
    before = _snapshot(tmp_path)

    first = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )
    first_plan = topology.topology_migration_plan(first)
    second = _status(
        home,
        project=project,
        thread_ids=(THREAD_ID,),
        proc_root=proc,
        codex_commands=(binary,),
    )
    second_plan = topology.topology_migration_plan(second)

    assert first == second
    assert first_plan == second_plan
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "state, blocker", [("unknown", "active_work_unknown"), ("present", "active_work_present")]
)
def test_active_work_unknown_or_present_blocks_cutover(
    tmp_path: Path,
    state: str,
    blocker: str,
) -> None:
    home, binary = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()

    status = _status(
        home,
        proc_root=proc,
        codex_commands=(binary,),
        active_work_state=state,
    )
    plan = topology.topology_migration_plan(status)

    assert plan["status"] == "blocked"
    assert any(item["code"] == blocker for item in plan["blockers"])


def test_missing_procfs_and_unknown_server_owner_fail_closed(tmp_path: Path) -> None:
    home, binary = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    missing_proc = tmp_path / "missing-proc"

    missing_status = _status(
        home,
        proc_root=missing_proc,
        codex_commands=(binary,),
    )
    assert any(
        item["code"] == "process_inventory_unknown"
        for item in topology.topology_migration_plan(missing_status)["blockers"]
    )

    outside = tmp_path / "outside" / "codex"
    outside.parent.mkdir()
    outside.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    outside.chmod(0o755)
    proc = _make_proc(
        tmp_path,
        pid=404,
        binary=outside,
        arguments=[outside.as_posix(), "app-server", "--remote-control"],
    )
    status = _status(home, proc_root=proc, codex_commands=(binary,))
    assert any(
        item["code"] == "server_owner_unknown"
        for item in topology.topology_migration_plan(status)["blockers"]
    )


def test_session_search_bound_fails_closed_instead_of_claiming_thread_absence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home, _ = _make_home(tmp_path, "canonical", with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()
    for index in range(3):
        (home / "sessions" / f"unrelated-{index}.jsonl").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(topology, "MAX_SESSION_FILES", 2)

    status = _status(home, thread_ids=(THREAD_ID,), proc_root=proc)
    plan = topology.topology_migration_plan(status)

    requested = status["homes"][0]["requested_threads"][0]
    assert requested["state"] == "unknown"
    assert requested["error"] == "session_search_incomplete"
    assert any(item["code"] == "session_metadata_unknown" for item in status["issues"])
    assert any(item["code"] == "session_metadata_unknown" for item in plan["blockers"])


def test_process_scan_bound_is_unknown_and_blocks_lifecycle_planning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home, binary = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    proc = _make_proc(
        tmp_path,
        pid=101,
        binary=binary,
        arguments=[binary.as_posix(), "app-server"],
    )
    _make_proc(
        tmp_path,
        pid=202,
        binary=binary,
        arguments=[binary.as_posix(), "app-server"],
    )
    monkeypatch.setattr(topology, "MAX_PROCESSES", 1)

    status = _status(home, proc_root=proc)
    plan = topology.topology_migration_plan(status)

    assert status["process_inventory"]["state"] == "unknown"
    assert status["process_inventory"]["scan_truncated"] is True
    assert status["process_inventory"]["scanned_pid_count"] == 1
    assert any(item["code"] == "process_inventory_unknown" for item in plan["blockers"])


def test_open_sqlite_fd_can_prove_server_home_without_reading_process_environment(
    tmp_path: Path,
) -> None:
    home, binary = _make_home(tmp_path, "canonical", with_sessions=False)
    outside = tmp_path / "outside" / "codex"
    outside.parent.mkdir()
    outside.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    outside.chmod(0o755)
    sqlite_path = home / "sqlite" / "state_5.sqlite"
    proc = _make_proc(
        tmp_path,
        pid=405,
        binary=outside,
        arguments=[outside.as_posix(), "app-server", "--remote-control"],
        open_sqlite=sqlite_path,
    )

    status = _status(home, proc_root=proc, codex_commands=(binary,))
    process = status["process_inventory"]["processes"][0]

    assert process["home"] == home.as_posix()
    assert process["home_source"] == "open_sqlite_path"
    assert process["open_sqlite_paths"] == [sqlite_path.as_posix()]
    assert not any(
        item["code"] == "server_owner_unknown"
        for item in topology.topology_migration_plan(status)["blockers"]
    )


def test_changed_hook_definition_changes_digest_but_never_asserts_trust(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    home, binary = _make_home(tmp_path, "canonical", project=project, trusted=True)
    proc = tmp_path / "proc"
    proc.mkdir()

    before = _status(home, project=project, proc_root=proc, codex_commands=(binary,))
    hooks = project / ".codex" / "hooks.json"
    hooks.write_text('{"hooks":{"Stop":[]}}', encoding="utf-8")
    after = _status(home, project=project, proc_root=proc, codex_commands=(binary,))

    assert (
        before["projects"][0]["hook_definition"]["sha256"]
        != after["projects"][0]["hook_definition"]["sha256"]
    )
    assert after["projects"][0]["client_hook_trust"]["asserted"] is False
    assert after["security"]["hook_trust_store_read"] is False


def test_invalid_thread_id_is_rejected_before_filesystem_search(tmp_path: Path) -> None:
    home, _ = _make_home(tmp_path, "canonical")

    with pytest.raises(topology.CodexTopologyError, match="unsafe thread ID"):
        _status(home, thread_ids=("../../auth.json",))


@pytest.mark.parametrize("unsafe_home", ("relative-home", "/"))
def test_unsafe_codex_home_roots_are_rejected(unsafe_home: str) -> None:
    with pytest.raises(topology.CodexTopologyError, match="canonical CODEX_HOME"):
        topology.topology_status(
            canonical_codex_home=unsafe_home,
            environment={"PATH": ""},
        )


def test_cli_status_and_plan_are_bounded_read_only_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    home, binary = _make_home(tmp_path, "canonical", with_sessions=False, with_sqlite=False)
    proc = tmp_path / "proc"
    proc.mkdir()
    common = [
        "--canonical-codex-home",
        home.as_posix(),
        "--codex-command",
        binary.as_posix(),
        "--proc-root",
        proc.as_posix(),
        "--process-scope",
        "host",
        "--active-work-state",
        "drained",
        "--all",
        "--json",
    ]

    assert cli.main(["codex", "topology", "status", *common]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["operation"] == "codex_topology_status"
    assert status["read_only"] is True

    assert cli.main(["codex", "topology", "plan", *common]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["operation"] == "codex_topology_plan"
    assert plan["read_only"] is True


def test_cli_invalid_input_returns_clean_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    home, _ = _make_home(tmp_path, "canonical")

    result = cli.main(
        [
            "codex",
            "topology",
            "status",
            "--canonical-codex-home",
            home.as_posix(),
            "--thread",
            "../unsafe",
        ]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "unsafe thread ID" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("relative_path", "required_marker"),
    (
        (
            "canonical-codex-home-architecture.md",
            b"Host cutover: **deferred to Task 257**",
        ),
        (
            "task257-canonical-codex-home-cutover-plan.md",
            b"One coherent ownership model is.",
        ),
    ),
)
def test_source_and_packaged_architecture_docs_are_byte_identical(
    relative_path: str,
    required_marker: bytes,
) -> None:
    source = REPO_ROOT / "docs/aegis" / relative_path
    packaged = REPO_ROOT / "aegis_foundation/assets/docs/aegis" / relative_path

    assert source.read_bytes() == packaged.read_bytes()
    assert required_marker in source.read_bytes()


@pytest.mark.parametrize(
    "schema_name",
    (
        "codex-topology-status.schema.json",
        "codex-topology-plan.schema.json",
    ),
)
def test_topology_schemas_are_valid_and_packaged_byte_identically(schema_name: str) -> None:
    source = REPO_ROOT / "schemas/aegis" / schema_name
    packaged = REPO_ROOT / "aegis_foundation/assets/schemas/aegis" / schema_name
    schema = json.loads(source.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert source.read_bytes() == packaged.read_bytes()


def test_status_and_plan_payloads_validate_against_tracked_schemas(tmp_path: Path) -> None:
    home, binary = _make_home(tmp_path, "canonical")
    proc = tmp_path / "proc"
    proc.mkdir()
    status = _status(home, proc_root=proc, codex_commands=(binary,))
    plan = topology.topology_migration_plan(status)
    status_schema = json.loads(
        (REPO_ROOT / "schemas/aegis/codex-topology-status.schema.json").read_text(encoding="utf-8")
    )
    plan_schema = json.loads(
        (REPO_ROOT / "schemas/aegis/codex-topology-plan.schema.json").read_text(encoding="utf-8")
    )

    Draft202012Validator(status_schema).validate(status)
    Draft202012Validator(plan_schema).validate(plan)

    status["security"]["hook_trust_asserted"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(status_schema).validate(status)

    plan["phases"][0]["task256_execute"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(plan_schema).validate(plan)
