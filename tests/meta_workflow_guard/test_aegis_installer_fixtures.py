"""Fixture and cleanup coverage for the Aegis generic-profile installer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import _aegis_installer as aegis


REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_empty_repo(root: Path) -> dict[str, str]:
    root.mkdir(parents=True)
    return {}


def _seed_basic_python_tool(root: Path) -> dict[str, str]:
    package = root / "src" / "fixture_tool"
    package.mkdir(parents=True)
    files = {
        "pyproject.toml": (
            "[project]\n"
            'name = "fixture-tool"\n'
            'version = "0.1.0"\n'
        ),
        "README.md": "# Fixture Tool\n",
        "src/fixture_tool/__init__.py": "__version__ = '0.1.0'\n",
    }
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return files


@pytest.mark.parametrize(
    ("fixture_name", "seed", "primary_agent", "agents"),
    [
        ("empty-repo", _seed_empty_repo, "claude", ["claude"]),
        ("basic-python-tool", _seed_basic_python_tool, "multi", ["claude", "codex"]),
    ],
)
def test_generic_profile_installs_verifies_and_stays_idempotent_for_fixture_shapes(
    tmp_path: Path,
    fixture_name: str,
    seed,
    primary_agent: str,
    agents: list[str],
) -> None:
    target = tmp_path / fixture_name
    original_files = seed(target)

    inspect_before = aegis.inspect_project(target)
    assert inspect_before["aegis"]["installed"] is False

    dry_run_plan = aegis.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
    )
    assert dry_run_plan["mode"] == "dry_run"
    assert dry_run_plan["summary"]["creates"] > 0
    assert dry_run_plan["summary"]["manual_reviews"] == 0
    assert not (target / ".aegis").exists()

    first_report = aegis.install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
        apply=True,
    )
    assert first_report["status"] == "applied"
    assert (target / aegis.AEGIS_MANIFEST_REL).exists()
    assert not (target / ".codex" / "foundation-manifest.json").exists()

    for rel_path, content in original_files.items():
        assert (target / rel_path).read_text(encoding="utf-8") == content

    manifest = json.loads((target / aegis.AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    assert manifest["profile"] == "generic"
    assert manifest["primary_agent"] == primary_agent
    assert manifest["agents"]["claude"]["enabled"] is ("claude" in agents)
    assert manifest["agents"]["codex"]["enabled"] is ("codex" in agents)
    assert all(not item["path"].startswith(".codex/foundation-manifest") for item in manifest["managed_files"])

    verification = aegis.verify(target, source_root=REPO_ROOT)
    assert verification["status"] == "passed"
    expected_unsupported = 1 + int("codex" in agents)
    assert verification["summary"]["unsupported"] == expected_unsupported

    second_plan = aegis.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
    )
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["conflicts"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}

    second_report = aegis.install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
        apply=True,
    )
    assert second_report["status"] == "applied"

    second_verification = aegis.verify(target, source_root=REPO_ROOT)
    assert second_verification["status"] == "passed"


def test_conflicting_existing_aegis_manifest_is_refused_without_partial_writes(tmp_path: Path) -> None:
    target = tmp_path / "partial-aegis-install"
    target.mkdir()
    manifest = target / aegis.AEGIS_MANIFEST_REL
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"foundation_name": "Other System"}\n', encoding="utf-8")

    plan = aegis.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    manifest_operation = next(operation for operation in plan["operations"] if operation["path"] == aegis.AEGIS_MANIFEST_REL)
    assert manifest_operation["classification"] == "manual-review"
    assert manifest_operation["safe_to_apply"] is False

    report = aegis.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "refused"
    assert manifest.read_text(encoding="utf-8") == '{"foundation_name": "Other System"}\n'
    assert not (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".aegis" / "contract.md").exists()


def test_apply_failure_cleans_files_created_during_failed_attempt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "failed-apply-cleanup"
    target.mkdir()
    original_write_asset = aegis._write_asset

    def fail_on_claude_entrypoint(target_root: Path, asset: aegis.Asset) -> None:
        if asset.path == "CLAUDE.md":
            raise aegis.AegisError("simulated write failure")
        original_write_asset(target_root, asset)

    monkeypatch.setattr(aegis, "_write_asset", fail_on_claude_entrypoint)

    report = aegis.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert report["status"] == "failed"
    assert report["cleanup"]["status"] == "completed"
    assert report["cleanup"]["removed_paths"]
    assert "simulated write failure" in report["reason"]
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".aegis" / "contract.md").exists()
    assert not (target / "schemas" / "aegis" / "foundation-manifest.schema.json").exists()
    assert not (target / aegis.AEGIS_MANIFEST_REL).exists()
    assert not (target / ".aegis" / "reports" / "install-report.json").exists()
