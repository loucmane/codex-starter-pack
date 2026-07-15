"""Task 255 coverage for host-scoped Codex Remote Control trust management."""

from __future__ import annotations

import json
from pathlib import Path
import stat
import subprocess
import sys
import tomllib

import pytest

from aegis_foundation import cli
from aegis_foundation import codex_remote_trust as trust

REPO_ROOT = Path(__file__).resolve().parents[2]
APPROVED_AT = "2026-07-15T12:00:00Z"


def _toml_key(value: str | Path) -> str:
    return json.dumps(Path(value).as_posix())


def _base_remote_config(*, extra: str = "") -> bytes:
    return (
        'approval_policy = "never"\n'
        'model = "gpt-5-codex"\n'
        "\n[features]\n"
        "remote_control = true\n"
        "\n[mcp_servers.remote-only]\n"
        'command = "remote-mcp"\n'
        "\n[hooks.state]\n"
        '"/remote/source/.codex/hooks.json:old-hash" = "trusted"\n'
        f"{extra}"
    ).encode("utf-8")


def _make_bridge(tmp_path: Path, *, remote_config: bytes | None = None) -> tuple[
    trust.BridgePaths,
    Path,
]:
    normal_home = tmp_path / "normal-home"
    remote_home = tmp_path / "remote-home"
    project = tmp_path / "project"
    normal_home.mkdir()
    remote_home.mkdir()
    project.mkdir()
    (normal_home / "config.toml").write_text(
        (
            f"[projects.{_toml_key(project)}]\n"
            'trust_level = "trusted"\n'
            "\n[hooks.state]\n"
            f'{_toml_key((project / ".codex/hooks.json").as_posix() + ":normal-hash")} = "trusted"\n'
            "\n[mcp_servers.normal-only]\n"
            'command = "normal-mcp"\n'
        ),
        encoding="utf-8",
    )
    remote_path = remote_home / "config.toml"
    remote_path.write_bytes(remote_config or _base_remote_config())
    remote_path.chmod(0o640)
    paths = trust.resolve_bridge_paths(
        normal_codex_home=normal_home,
        remote_codex_home=remote_home,
        environment={},
    )
    return paths, project


def _apply_add(paths: trust.BridgePaths, project: Path) -> dict[str, object]:
    return trust.trust_change(
        paths,
        action="add",
        project=project,
        reason="owner approved Remote Control for this project",
        approved_by="owner",
        approved_at=APPROVED_AT,
        apply=True,
    )


def _write_guidance(project: Path, **overrides: object) -> None:
    gate: dict[str, object] = {
        "id": "codex.hook_trust",
        "settings_path": ".codex/hooks.json",
        "review_command": "/hooks",
        "hash_scope": "exact_hook_definition",
        "bypass_allowed": False,
    }
    gate.update(overrides)
    manifest = project / ".aegis/foundation-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"gates": [gate]}), encoding="utf-8")


def _parse(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _write_allowlist(path: Path, content: bytes) -> None:
    path.write_bytes(content)
    path.chmod(0o600)


def test_bridge_path_resolution_keeps_security_contexts_separate(tmp_path: Path) -> None:
    paths, _ = _make_bridge(tmp_path)

    assert paths.normal_home != paths.remote_home
    assert paths.allowlist == paths.remote_home / "trusted-projects.toml"
    assert paths.backup == paths.remote_home / "config.toml.aegis-last-known-good"

    with pytest.raises(trust.RemoteTrustValidationError, match="must remain separate"):
        trust.resolve_bridge_paths(
            normal_codex_home=paths.normal_home,
            remote_codex_home=paths.normal_home,
            environment={},
        )


@pytest.mark.parametrize("project", ["relative/project", "/"])
def test_project_identity_rejects_unsafe_paths(project: str) -> None:
    with pytest.raises(trust.RemoteTrustValidationError):
        trust.canonical_project_path(project, require_exists=False)


def test_status_diagnoses_effective_home_mismatch_without_writing(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    before = paths.remote_config.read_bytes()

    payload = trust.bridge_status(
        paths,
        project=project,
        environment={"CODEX_HOME": paths.remote_home.as_posix()},
    )

    assert payload["status"] == "uninitialized"
    project_payload = payload["project_status"]
    assert project_payload["normal_project_trust"]["status"] == "trusted"
    assert project_payload["remote_allowlist"]["status"] == "missing"
    assert project_payload["remote_effective_project_trust"]["status"] == "missing"
    assert project_payload["effective_context"] == {
        "active_CODEX_HOME": paths.remote_home.as_posix(),
        "normal_home_active": False,
        "remote_home_active": True,
        "homes_separate": True,
    }
    assert paths.remote_config.read_bytes() == before
    assert not paths.allowlist.exists()
    assert not paths.lock.exists()
    assert not paths.backup.exists()


def test_trust_add_is_preview_only_until_apply(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    before = paths.remote_config.read_bytes()

    payload = trust.trust_change(
        paths,
        action="add",
        project=project,
        reason="preview owner authorization",
        approved_by="owner",
        approved_at=APPROVED_AT,
        apply=False,
    )

    assert payload["status"] == "would_apply"
    assert payload["apply_requested"] is False
    assert payload["allowlist_before_count"] == 0
    assert payload["allowlist_after_count"] == 1
    assert paths.remote_config.read_bytes() == before
    assert not paths.allowlist.exists()
    assert not paths.lock.exists()
    assert not paths.backup.exists()


def test_authority_timestamp_must_be_utc(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)

    with pytest.raises(trust.RemoteTrustValidationError, match="must use UTC"):
        trust.trust_change(
            paths,
            action="add",
            project=project,
            reason="timezone is part of the durable authority contract",
            approved_by="owner",
            approved_at="2026-07-15T14:00:00+02:00",
            apply=False,
        )


def test_add_apply_preserves_unowned_remote_state_and_never_copies_normal_state(
    tmp_path: Path,
) -> None:
    paths, project = _make_bridge(tmp_path)
    before = paths.remote_config.read_bytes()
    normal_before = paths.normal_config.read_bytes()

    payload = _apply_add(paths, project)

    assert payload["status"] == "applied"
    assert paths.backup.read_bytes() == before
    assert paths.normal_config.read_bytes() == normal_before
    assert stat.S_IMODE(paths.allowlist.stat().st_mode) == 0o600
    assert stat.S_IMODE(paths.backup.stat().st_mode) == 0o600
    assert stat.S_IMODE(paths.remote_config.stat().st_mode) == 0o640
    config = paths.remote_config.read_text(encoding="utf-8")
    assert config.startswith(before.decode("utf-8"))
    assert trust.MANAGED_BEGIN in config
    assert f"[projects.{_toml_key(project)}]" in config
    assert "normal-mcp" not in config
    assert "normal-hash" not in config
    assert _parse(paths.remote_config)["mcp_servers"]["remote-only"]["command"] == "remote-mcp"
    entries = trust.load_allowlist(paths.allowlist, require_existing_projects=True)
    assert entries == (
        trust.TrustEntry(
            path=project.resolve().as_posix(),
            approved_by="owner",
            approved_at=APPROVED_AT,
            reason="owner approved Remote Control for this project",
        ),
    )


def test_bridge_plan_and_apply_project_an_existing_allowlist(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    before = paths.remote_config.read_bytes()
    entry = trust.TrustEntry(
        path=project.resolve().as_posix(),
        approved_by="owner",
        approved_at=APPROVED_AT,
        reason="pre-existing explicit authority",
    )
    _write_allowlist(paths.allowlist, trust.render_allowlist((entry,)))

    preview = trust.bridge_plan(paths)
    assert preview["status"] == "would_apply"
    assert preview["changed"] is True
    assert paths.remote_config.read_bytes() == before
    assert not paths.lock.exists()

    applied = trust.bridge_apply(paths)
    assert applied["status"] == "applied"
    assert paths.backup.read_bytes() == before
    assert _parse(paths.remote_config)["projects"][project.as_posix()] == {"trust_level": "trusted"}
    assert trust.bridge_apply(paths)["status"] == "current"


def test_bridge_apply_validation_failure_restores_last_known_good(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths, project = _make_bridge(tmp_path)
    before = paths.remote_config.read_bytes()
    entry = trust.TrustEntry(
        path=project.resolve().as_posix(),
        approved_by="owner",
        approved_at=APPROVED_AT,
        reason="pre-existing explicit authority",
    )
    _write_allowlist(paths.allowlist, trust.render_allowlist((entry,)))

    def fail_validation(_path: Path, _entries: object) -> None:
        raise trust.RemoteTrustValidationError("injected bridge validation failure")

    monkeypatch.setattr(trust, "_validate_config_file", fail_validation)
    with pytest.raises(trust.RemoteTrustError, match="rolled back"):
        trust.bridge_apply(paths)

    assert paths.remote_config.read_bytes() == before
    assert paths.backup.read_bytes() == before


def test_add_apply_is_idempotent_without_rewriting_host_files(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    _apply_add(paths, project)
    snapshots = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (paths.allowlist, paths.remote_config, paths.backup)
    }

    payload = trust.trust_change(
        paths,
        action="add",
        project=project,
        reason="a different repeat reason must not rewrite authority",
        approved_by="another-identity",
        approved_at="2026-07-16T12:00:00Z",
        apply=True,
    )

    assert payload["status"] == "current"
    assert payload["rollback"] == {"required": False, "performed": False}
    for path, (content, modified) in snapshots.items():
        assert path.read_bytes() == content
        assert path.stat().st_mtime_ns == modified


def test_remove_apply_removes_only_aegis_owned_projection(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    original = paths.remote_config.read_bytes()
    _apply_add(paths, project)

    preview = trust.trust_change(
        paths,
        action="remove",
        project=project,
        reason="owner revoked Remote Control access",
        approved_by="owner",
        apply=False,
    )
    assert preview["status"] == "would_apply"
    assert trust.MANAGED_BEGIN in paths.remote_config.read_text(encoding="utf-8")

    applied = trust.trust_change(
        paths,
        action="remove",
        project=project,
        reason="owner revoked Remote Control access",
        approved_by="owner",
        apply=True,
    )

    assert applied["status"] == "applied"
    assert trust.load_allowlist(paths.allowlist) == ()
    assert paths.remote_config.read_bytes() == original


def test_existing_exact_unmanaged_trust_is_externally_satisfied(tmp_path: Path) -> None:
    project = tmp_path / "project"
    extra = f'\n[projects.{_toml_key(project)}]\ntrust_level = "trusted"\n'
    paths, project = _make_bridge(tmp_path, remote_config=_base_remote_config(extra=extra))
    before = paths.remote_config.read_bytes()

    payload = _apply_add(paths, project)

    assert payload["status"] == "applied"
    assert payload["changed"] is False
    assert payload["managed_projects"] == []
    assert payload["externally_satisfied_projects"] == [project.resolve().as_posix()]
    assert paths.remote_config.read_bytes() == before
    assert not paths.backup.exists()


@pytest.mark.parametrize("trust_level", ["untrusted", "ask", ""])
def test_existing_unmanaged_nontrusted_entry_fails_closed(
    tmp_path: Path,
    trust_level: str,
) -> None:
    project = tmp_path / "project"
    extra = f"\n[projects.{_toml_key(project)}]\ntrust_level = {json.dumps(trust_level)}\n"
    paths, project = _make_bridge(tmp_path, remote_config=_base_remote_config(extra=extra))

    with pytest.raises(trust.RemoteTrustConflictError, match="conflicts"):
        trust.trust_change(
            paths,
            action="add",
            project=project,
            reason="must not override unowned policy",
            approved_by="owner",
            approved_at=APPROVED_AT,
            apply=False,
        )


def test_unmanaged_alias_conflict_fails_closed(tmp_path: Path) -> None:
    real = tmp_path / "real"
    alias = tmp_path / "alias"
    real.mkdir()
    alias.symlink_to(real, target_is_directory=True)
    extra = f'\n[projects.{_toml_key(alias)}]\ntrust_level = "trusted"\n'
    paths, _ = _make_bridge(tmp_path, remote_config=_base_remote_config(extra=extra))

    with pytest.raises(trust.RemoteTrustConflictError, match="aliases requested trust"):
        trust.trust_change(
            paths,
            action="add",
            project=real,
            reason="alias conflicts remain operator-owned",
            approved_by="owner",
            approved_at=APPROVED_AT,
            apply=False,
        )


def test_added_symlink_path_is_stored_canonically_and_manual_alias_is_rejected(
    tmp_path: Path,
) -> None:
    paths, real = _make_bridge(tmp_path)
    alias = tmp_path / "project-alias"
    alias.symlink_to(real, target_is_directory=True)

    _apply_add(paths, alias)
    entries = trust.load_allowlist(paths.allowlist, require_existing_projects=True)
    assert entries[0].path == real.resolve().as_posix()

    _write_allowlist(
        paths.allowlist,
        trust.render_allowlist(
            (
                trust.TrustEntry(
                    path=alias.as_posix(),
                    approved_by="owner",
                    approved_at=APPROVED_AT,
                    reason="manually introduced alias",
                ),
            )
        ),
    )
    with pytest.raises(trust.RemoteTrustValidationError, match="stored canonically"):
        trust.bridge_plan(paths)


@pytest.mark.parametrize(
    "content",
    [
        b"schema_version = 2\nprojects = []\n",
        b"schema_version = 1\nunknown = true\nprojects = []\n",
        b"schema_version = 1\nprojects = {}\n",
        b"schema_version = 1\n[[projects]]\npath = '/tmp/x'\n",
        b"not = [valid TOML\n",
    ],
)
def test_malformed_allowlist_fails_closed(tmp_path: Path, content: bytes) -> None:
    paths, _ = _make_bridge(tmp_path)
    _write_allowlist(paths.allowlist, content)

    with pytest.raises(trust.RemoteTrustValidationError):
        trust.bridge_plan(paths)


def test_duplicate_and_alias_allowlist_entries_fail_closed(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    duplicate = trust.TrustEntry(project.as_posix(), "owner", APPROVED_AT, "one")
    _write_allowlist(paths.allowlist, trust.render_allowlist((duplicate, duplicate)))
    with pytest.raises(trust.RemoteTrustValidationError, match="duplicate"):
        trust.load_allowlist(paths.allowlist)

    alias = tmp_path / "project-alias"
    alias.symlink_to(project, target_is_directory=True)
    alias_entry = trust.TrustEntry(alias.as_posix(), "owner", APPROVED_AT, "alias")
    _write_allowlist(paths.allowlist, trust.render_allowlist((duplicate, alias_entry)))
    with pytest.raises(trust.RemoteTrustValidationError, match="same project"):
        trust.load_allowlist(paths.allowlist)


@pytest.mark.parametrize(
    "markers",
    [
        f"{trust.MANAGED_BEGIN}\n",
        f"{trust.MANAGED_END}\n",
        f"{trust.MANAGED_END}\n{trust.MANAGED_BEGIN}\n",
        f"{trust.MANAGED_BEGIN}\n{trust.MANAGED_BEGIN}\n{trust.MANAGED_END}\n",
    ],
)
def test_malformed_managed_markers_fail_closed(tmp_path: Path, markers: str) -> None:
    paths, _ = _make_bridge(
        tmp_path,
        remote_config=_base_remote_config(extra=f"\n{markers}"),
    )
    _write_allowlist(paths.allowlist, trust.render_allowlist(()))

    with pytest.raises(trust.RemoteTrustValidationError, match="markers"):
        trust.bridge_plan(paths)


def test_symlinked_host_state_is_never_followed(tmp_path: Path) -> None:
    paths, _ = _make_bridge(tmp_path)
    real_allowlist = tmp_path / "outside-allowlist.toml"
    _write_allowlist(real_allowlist, trust.render_allowlist(()))
    paths.allowlist.symlink_to(real_allowlist)

    with pytest.raises(trust.RemoteTrustValidationError, match="symlink"):
        trust.bridge_plan(paths)

    paths.allowlist.unlink()
    _write_allowlist(paths.allowlist, trust.render_allowlist(()))
    real_config = tmp_path / "outside-config.toml"
    real_config.write_bytes(paths.remote_config.read_bytes())
    paths.remote_config.unlink()
    paths.remote_config.symlink_to(real_config)
    with pytest.raises(trust.RemoteTrustValidationError, match="symlink"):
        trust.bridge_plan(paths)


def test_allowlist_permissions_and_lock_symlinks_fail_closed(tmp_path: Path) -> None:
    paths, _ = _make_bridge(tmp_path)
    _write_allowlist(paths.allowlist, trust.render_allowlist(()))
    paths.allowlist.chmod(0o644)
    with pytest.raises(trust.RemoteTrustValidationError, match="permissions must be 0600"):
        trust.bridge_plan(paths)

    paths.allowlist.chmod(0o600)
    outside_lock = tmp_path / "outside.lock"
    outside_lock.write_text("", encoding="utf-8")
    paths.lock.symlink_to(outside_lock)
    with pytest.raises(trust.RemoteTrustValidationError, match="must not be a symlink"):
        with trust.bridge_lock(paths.lock):
            pass


def test_apply_failure_restores_exact_config_and_allowlist(monkeypatch, tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    config_before = paths.remote_config.read_bytes()

    def fail_validation(_path: Path, _entries: object) -> None:
        raise trust.RemoteTrustValidationError("injected post-write validation failure")

    monkeypatch.setattr(trust, "_validate_config_file", fail_validation)
    with pytest.raises(trust.RemoteTrustError, match="rolled back"):
        _apply_add(paths, project)

    assert paths.remote_config.read_bytes() == config_before
    assert paths.backup.read_bytes() == config_before
    assert not paths.allowlist.exists()


def test_incomplete_rollback_is_a_terminal_error(monkeypatch, tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)

    def fail_validation(_path: Path, _entries: object) -> None:
        raise trust.RemoteTrustValidationError("injected validation failure")

    def fail_allowlist_restore(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected allowlist rollback failure")

    monkeypatch.setattr(trust, "_validate_config_file", fail_validation)
    monkeypatch.setattr(trust, "_restore_snapshot", fail_allowlist_restore)
    with pytest.raises(trust.RemoteTrustRollbackError, match="rollback was incomplete"):
        _apply_add(paths, project)


def test_lock_timeout_fails_without_writing(tmp_path: Path) -> None:
    paths, _ = _make_bridge(tmp_path)
    _write_allowlist(paths.allowlist, trust.render_allowlist(()))
    before = paths.remote_config.read_bytes()
    program = (
        "from pathlib import Path; "
        "from aegis_foundation.codex_remote_trust import bridge_lock, RemoteTrustLockTimeout; "
        "import sys; "
        "\ntry:\n"
        "  with bridge_lock(Path(sys.argv[1]), timeout=0.1): pass\n"
        "except RemoteTrustLockTimeout:\n"
        "  raise SystemExit(17)\n"
    )
    with trust.bridge_lock(paths.lock):
        result = subprocess.run(
            [sys.executable, "-c", program, paths.lock.as_posix()],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 17, result.stderr
    assert paths.remote_config.read_bytes() == before


def test_concurrent_adds_serialize_without_lost_authority(tmp_path: Path) -> None:
    paths, first = _make_bridge(tmp_path)
    second = tmp_path / "second-project"
    second.mkdir()
    program = """
from pathlib import Path
import sys
from aegis_foundation.codex_remote_trust import resolve_bridge_paths, trust_change

paths = resolve_bridge_paths(
    normal_codex_home=sys.argv[1],
    remote_codex_home=sys.argv[2],
    environment={},
)
trust_change(
    paths,
    action="add",
    project=sys.argv[3],
    reason="concurrent explicit authorization",
    approved_by="owner",
    approved_at="2026-07-15T12:00:00Z",
    apply=True,
    timeout=5,
)
"""
    commands = [
        [
            sys.executable,
            "-c",
            program,
            paths.normal_home.as_posix(),
            paths.remote_home.as_posix(),
            project.as_posix(),
        ]
        for project in (first, second)
    ]
    processes = [
        subprocess.Popen(command, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for command in commands
    ]
    results = [process.communicate(timeout=10) for process in processes]

    assert [process.returncode for process in processes] == [0, 0], results
    entries = trust.load_allowlist(paths.allowlist, require_existing_projects=True)
    assert {entry.path for entry in entries} == {
        first.resolve().as_posix(),
        second.resolve().as_posix(),
    }
    projects = _parse(paths.remote_config)["projects"]
    assert projects[first.resolve().as_posix()]["trust_level"] == "trusted"
    assert projects[second.resolve().as_posix()]["trust_level"] == "trusted"


def test_hook_guidance_and_client_hash_trust_remain_distinct(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    _write_guidance(project)
    hooks = project / ".codex/hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{"hooks": {"PreToolUse": []}}\n', encoding="utf-8")
    _apply_add(paths, project)

    first = trust.project_status(
        paths,
        project=project,
        environment={"CODEX_HOME": paths.remote_home.as_posix()},
    )

    assert first["status"] == "hook_review_required"
    assert first["project_trust_status"] == "ready"
    assert first["tracked_hook_guidance"]["valid"] is True
    assert first["client_hook_state"]["client_trust_asserted"] is False
    assert first["client_hook_state"]["review_command"] == "/hooks"
    first_digest = first["client_hook_state"]["definition_sha256"]

    hooks.write_text('{"hooks": {"PreToolUse": [{"matcher": "Bash"}]}}\n', encoding="utf-8")
    second = trust.project_status(paths, project=project)
    assert second["client_hook_state"]["definition_sha256"] != first_digest
    assert second["client_hook_state"]["client_trust_asserted"] is False
    assert second["client_hook_state"]["review_required"] is True


@pytest.mark.parametrize(
    "override",
    [
        {"settings_path": ".claude/settings.json"},
        {"review_command": "yes"},
        {"hash_scope": "path_only"},
        {"bypass_allowed": True},
    ],
)
def test_malformed_tracked_hook_guidance_is_reported_not_promoted(
    tmp_path: Path,
    override: dict[str, object],
) -> None:
    paths, project = _make_bridge(tmp_path)
    _write_guidance(project, **override)
    _apply_add(paths, project)

    payload = trust.project_status(paths, project=project)

    assert payload["tracked_hook_guidance"]["present"] is True
    assert payload["tracked_hook_guidance"]["valid"] is False
    assert payload["client_hook_state"]["client_trust_asserted"] is False


def test_missing_and_duplicate_hook_guidance_are_invalid(tmp_path: Path) -> None:
    paths, project = _make_bridge(tmp_path)
    _apply_add(paths, project)
    assert trust.project_status(paths, project=project)["tracked_hook_guidance"] == {
        "present": False,
        "valid": False,
        "path": (project / ".aegis/foundation-manifest.json").as_posix(),
    }

    _write_guidance(project)
    manifest_path = project / ".aegis/foundation-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gates"].append(dict(manifest["gates"][0]))
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    duplicate = trust.project_status(paths, project=project)["tracked_hook_guidance"]
    assert duplicate["valid"] is False
    assert duplicate["matching_gate_count"] == 2


def test_cli_add_status_plan_apply_remove_lifecycle(tmp_path: Path, capsys) -> None:
    paths, project = _make_bridge(tmp_path)
    homes = [
        "--normal-codex-home",
        paths.normal_home.as_posix(),
        "--remote-codex-home",
        paths.remote_home.as_posix(),
    ]

    assert (
        cli.main(
            [
                "codex",
                "trust",
                "add",
                *homes,
                "--project",
                project.as_posix(),
                "--reason",
                "CLI lifecycle approval",
                "--approved-by",
                "owner",
            ]
        )
        == 0
    )
    preview = json.loads(capsys.readouterr().out)
    assert preview["status"] == "would_apply"
    assert not paths.allowlist.exists()

    assert (
        cli.main(
            [
                "codex",
                "trust",
                "add",
                *homes,
                "--project",
                project.as_posix(),
                "--reason",
                "CLI lifecycle approval",
                "--approved-by",
                "owner",
                "--apply",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "applied"

    assert cli.main(["codex", "bridge", "plan", *homes]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "current"
    assert cli.main(["codex", "trust", "status", *homes, "--project", str(project)]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["project_trust_status"] == "ready"
    assert status_payload["client_hook_state"]["client_trust_asserted"] is False

    assert (
        cli.main(
            [
                "codex",
                "trust",
                "remove",
                *homes,
                "--project",
                project.as_posix(),
                "--reason",
                "CLI lifecycle revocation",
                "--apply",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "applied"
    assert trust.load_allowlist(paths.allowlist) == ()


def test_cli_reports_validation_failure_without_traceback(tmp_path: Path, capsys) -> None:
    paths, _ = _make_bridge(tmp_path)

    result = cli.main(
        [
            "codex",
            "trust",
            "add",
            "--normal-codex-home",
            paths.normal_home.as_posix(),
            "--remote-codex-home",
            paths.remote_home.as_posix(),
            "--project",
            "relative/project",
            "--reason",
            "invalid relative project",
            "--apply",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "project path must be absolute" in captured.err
    assert "Traceback" not in captured.err


def test_source_and_packaged_remote_trust_docs_are_byte_identical() -> None:
    source = REPO_ROOT / "docs/aegis/codex-remote-control-trust.md"
    packaged = REPO_ROOT / "aegis_foundation/assets/docs/aegis/codex-remote-control-trust.md"

    assert source.read_bytes() == packaged.read_bytes()
    text = source.read_text(encoding="utf-8")
    assert "never copies hook hashes" in text
    assert "aegis codex trust add" in text
    assert "/hooks" in text
    assert "symlink" in text.lower()
