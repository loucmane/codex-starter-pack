"""Golden consumer and compatibility coverage for the extracted managed-update core."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from aegis_foundation import managed_update
from scripts import _aegis_installer as installer

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = REPO_ROOT / "tests/fixtures/aegis/managed-update-golden-plans.json"
PACKAGED_INSTALLER_PATH = REPO_ROOT / "aegis_foundation/assets/scripts/_aegis_installer.py"


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _seed_project_owned_files(target: Path, case_name: str) -> None:
    if case_name == "codex":
        _write(target / "CODEX.md", b"# Existing Codex instructions\n")
    elif case_name == "hp-fetcher":
        _write(target / "AGENTS.md", b"# HP-Fetcher agent instructions\n")
        _write(target / "CLAUDE.md", b"# HP-Fetcher Claude instructions\n")
    elif case_name == "blog":
        _write(target / "AGENTS.md", b"# Blog agent instructions\n")
        _write(target / "CLAUDE.md", b"# Blog Claude instructions\n")
        _write(target / "CODEX.md", b"# Blog Codex instructions\n")
    if case_name in {"codex", "blog"}:
        hooks = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "custom",
                        "hooks": [{"type": "command", "command": "echo custom"}],
                    }
                ]
            }
        }
        _write(
            target / installer.CODEX_HOOKS_REL,
            (json.dumps(hooks) + "\n").encode("utf-8"),
        )


def _seed_known_stale_update(target: Path, case: dict[str, object]) -> None:
    stale_path = str(case["stale_path"])
    stale_content = str(case["stale_content"]).encode("utf-8")
    _write(target / stale_path, stale_content)
    manifest_path = target / installer.AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["managed_files"]
        if isinstance(item, dict) and item.get("path") == stale_path
    )
    record["checksum"] = installer._content_checksum(stale_content)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _operations_digest(operations: list[dict[str, object]]) -> str:
    encoded = json.dumps(
        operations,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stable_plan(plan: dict[str, object]) -> dict[str, object]:
    return {
        "agent_selection": plan["agent_selection"],
        "operations": plan["operations"],
        "expected_manifest": plan["expected_manifest"],
        "verification_requirements": plan["verification_requirements"],
        "summary": plan["summary"],
    }


def test_installer_exports_the_authoritative_managed_update_asset_type() -> None:
    assert installer.Asset is managed_update.Asset


def test_source_and_packaged_installer_render_identical_assets_and_plans(
    tmp_path: Path,
) -> None:
    packaged = _load_module(PACKAGED_INSTALLER_PATH, "aegis_packaged_managed_update_test")
    target = tmp_path / "multi-agent-target"
    target.mkdir()
    _seed_project_owned_files(target, "blog")

    live_assets = installer._assets_for_target(
        target,
        installer._managed_assets(REPO_ROOT, "multi", ["claude", "codex"]),
    )
    packaged_assets = packaged._assets_for_target(
        target,
        packaged._managed_assets(REPO_ROOT, "multi", ["claude", "codex"]),
    )
    assert live_assets == packaged_assets

    live_plan = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
    )
    packaged_plan = packaged.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
    )
    assert _stable_plan(live_plan) == _stable_plan(packaged_plan)


@pytest.mark.parametrize("case_name", ["codex", "hp-fetcher", "blog"])
def test_golden_consumer_install_and_update_plans(
    tmp_path: Path,
    case_name: str,
) -> None:
    fixture = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    case = fixture["cases"][case_name]
    target = tmp_path / case_name
    target.mkdir()
    _seed_project_owned_files(target, case_name)

    primary_agent = str(case["primary_agent"])
    agents = [str(agent) for agent in case["agents"]]
    if case["kind"] == "known_stale_update":
        installed = installer.install(
            target,
            source_root=REPO_ROOT,
            primary_agent=primary_agent,
            agents=agents,
            apply=True,
        )
        assert installed["status"] == "applied"
        _seed_known_stale_update(target, case)

    before = _snapshot(target)
    plan = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
    )
    assert _snapshot(target) == before
    assert plan["summary"] == case["expected_summary"]
    assert _operations_digest(plan["operations"]) == case["operations_sha256"]
    modified = {
        operation["path"]: operation["classification"]
        for operation in plan["operations"]
        if operation["classification"] == "modify"
    }
    assert modified == case["expected_non_skip"]
    assert all(operation["safe_to_apply"] is True for operation in plan["operations"])

    if case["kind"] == "known_stale_update":
        report = installer.project_update(
            target,
            source_root=REPO_ROOT,
            apply=False,
        )
        assert report["status"] == "preview"
        assert report["product_file_safety"]["safe"] is True
        assert report["install"]["plan"]["operations"] == plan["operations"]
        assert _snapshot(target) == before


def test_extracted_core_keeps_unrecoverable_semantic_divergence_fail_closed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "diverged-target"
    target.mkdir()
    installed = installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert installed["status"] == "applied"

    path = target / ".claude/scripts/brief_lib.py"
    path.write_text("# locally hardened behavior\n", encoding="utf-8")
    plan = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    operation = next(
        item for item in plan["operations"] if item["path"] == ".claude/scripts/brief_lib.py"
    )
    assert operation["classification"] == "manual-review"
    assert operation["safe_to_apply"] is False
    assert "refusing semantic overwrite" in operation["reason"]
