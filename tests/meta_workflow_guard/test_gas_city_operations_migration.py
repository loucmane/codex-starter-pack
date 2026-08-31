"""Coverage for the Gas City Operations naming and migration contract."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "gas-city-operations-migration"
MANIFEST = REPO_ROOT / "config" / "gas-city-operations-migration.json"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _fixture(tmp_path: Path, *, origin: str) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "remote", "add", "origin", origin)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "fixture")
    return root


def _manifest(tmp_path: Path, *, old_root: Path, new_root: Path) -> Path:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["workspace"]["legacy_root"] = str(old_root)
    payload["workspace"]["canonical_root"] = str(new_root)
    path = tmp_path / "migration.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(
    root: Path,
    manifest: Path,
    phase: str,
    *,
    tracked_only: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        str(SCRIPT),
        "inventory",
        "--repository",
        str(root),
        "--scan-root",
        str(root),
        "--manifest",
        str(manifest),
        "--phase",
        phase,
    ]
    if tracked_only:
        command.append("--tracked-only")
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_naming_contract_keeps_the_four_identities_distinct() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert payload["identity"] == {
        "repository_product": "Gas City Operations",
        "portable_workflow_product": "Aegis Foundation",
        "runtime_product": "Gas City",
        "workflow_plugin": "Gas City Workflow",
    }
    assert payload["compatibility"]["branch_namespace"] == "codex/*"
    assert payload["compatibility"]["python_distribution"] == "aegis-foundation"
    assert payload["workspace"]["strategy"] == "fresh-clone"
    assert payload["workspace"]["legacy_retirement"] == "user-hooks-and-shared-root-policy"
    assert "tests/fixtures" in payload["historical_roots"]
    assert "docs/aegis/AEGIS_VNEXT_PROGRAM.md" in payload["historical_roots"]


def test_pre_rename_inventory_classifies_active_and_historical_references(tmp_path: Path) -> None:
    old_root = tmp_path / "legacy"
    old_root.mkdir()
    root = _fixture(
        tmp_path,
        origin="https://github.com/loucmane/codex-starter-pack.git",
    )
    (root / "active.txt").write_text("loucmane/codex-starter-pack\n", encoding="utf-8")
    historical = root / "sessions"
    historical.mkdir()
    (historical / "old.md").write_text(str(old_root), encoding="utf-8")
    current_session = historical / "current-session.md"
    current_session.write_text(str(old_root), encoding="utf-8")
    (historical / "current").symlink_to(current_session.name)
    nested_environment = root / "worktrees" / "nested" / ".venv" / "lib"
    nested_environment.mkdir(parents=True)
    (nested_environment / "generated.txt").write_text(
        "loucmane/codex-starter-pack\n",
        encoding="utf-8",
    )
    manifest = _manifest(tmp_path, old_root=old_root, new_root=tmp_path / "new")

    completed = _run(root, manifest, "pre-rename")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["checks"]["origin_uses_legacy_name"] is True
    assert [item["path"] for item in payload["references"]["active"]] == [
        "active.txt",
        "sessions/current-session.md",
    ]
    assert [item["path"] for item in payload["references"]["historical"]] == ["sessions/old.md"]


def test_post_rename_refuses_active_legacy_reference_then_passes_when_removed(
    tmp_path: Path,
) -> None:
    old_root = tmp_path / "legacy"
    old_root.mkdir()
    new_root = tmp_path / "new"
    root = _fixture(
        tmp_path,
        origin="https://github.com/loucmane/gas-city-operations.git",
    )
    new_root.mkdir()
    active = root / "consumer.toml"
    active.write_text(f'root = "{old_root}"\n', encoding="utf-8")
    manifest = _manifest(tmp_path, old_root=old_root, new_root=new_root)

    refused = _run(root, manifest, "post-rename")
    assert refused.returncode == 1
    assert json.loads(refused.stdout)["checks"]["active_legacy_references_absent"] is False

    active.unlink()
    passed = _run(root, manifest, "post-rename")
    assert passed.returncode == 0, passed.stderr
    assert json.loads(passed.stdout)["ok"] is True


def test_script_is_read_only_for_repository_and_scan_tree(tmp_path: Path) -> None:
    old_root = tmp_path / "legacy"
    old_root.mkdir()
    root = _fixture(
        tmp_path,
        origin="https://github.com/loucmane/codex-starter-pack.git",
    )
    manifest = _manifest(tmp_path, old_root=old_root, new_root=tmp_path / "new")
    before = sorted(
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )

    completed = _run(root, manifest, "inventory")

    assert completed.returncode == 0, completed.stderr
    after = sorted(
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    assert after == before
    assert shutil.which("git") is not None


def test_tracked_only_ignores_untracked_runtime_and_cache_files(tmp_path: Path) -> None:
    old_root = tmp_path / "legacy"
    old_root.mkdir()
    root = _fixture(
        tmp_path,
        origin="https://github.com/loucmane/codex-starter-pack.git",
    )
    tracked = root / "tracked.txt"
    tracked.write_text("loucmane/codex-starter-pack\n", encoding="utf-8")
    _git(root, "add", "tracked.txt")
    _git(root, "commit", "-m", "tracked migration fixture")
    (root / "untracked.txt").write_text(str(old_root), encoding="utf-8")
    cache = root / ".cache"
    cache.mkdir()
    (cache / "generated.txt").write_text(str(old_root), encoding="utf-8")
    manifest = _manifest(tmp_path, old_root=old_root, new_root=tmp_path / "new")

    completed = _run(root, manifest, "pre-rename", tracked_only=True)

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["scan_mode"] == "tracked-only"
    assert [item["path"] for item in payload["references"]["active"]] == ["tracked.txt"]
