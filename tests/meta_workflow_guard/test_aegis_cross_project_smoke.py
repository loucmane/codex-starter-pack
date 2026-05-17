"""Cross-project smoke coverage for Aegis Foundation installs."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import _aegis_installer as aegis


REPO_ROOT = Path(__file__).resolve().parents[2]


SeedFunc = Callable[[Path], dict[str, str]]


def _write_files(root: Path, files: dict[str, str]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return files


def _seed_empty_repo(root: Path) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    return {}


def _seed_python_library_repo(root: Path) -> dict[str, str]:
    return _write_files(
        root,
        {
            "README.md": "# Fixture Python Library\n",
            "pyproject.toml": (
                "[project]\n"
                'name = "fixture-python-library"\n'
                'version = "0.1.0"\n'
            ),
            "src/fixture_library/__init__.py": "__version__ = '0.1.0'\n",
            "tests/test_smoke.py": "def test_smoke():\n    assert True\n",
        },
    )


def _seed_web_app_repo(root: Path) -> dict[str, str]:
    return _write_files(
        root,
        {
            "README.md": "# Fixture Web App\n",
            "package.json": '{\n  "name": "fixture-web-app",\n  "private": true\n}\n',
            "app/page.tsx": "export default function Page() { return <main>Fixture</main>; }\n",
            "public/robots.txt": "User-agent: *\nAllow: /\n",
            "docs/architecture.md": "# Architecture\n",
        },
    )


def _seed_docs_heavy_repo(root: Path) -> dict[str, str]:
    return _write_files(
        root,
        {
            "README.md": "# Fixture Documentation Site\n",
            "docs/index.md": "# Docs\n",
            "docs/guides/getting-started.md": "# Getting Started\n",
            "mkdocs.yml": "site_name: Fixture Docs\n",
        },
    )


def _snapshot_files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _source_fingerprint() -> dict[str, bytes]:
    rel_paths = [
        "scripts/_aegis_installer.py",
        "scripts/codex-task",
        "aegis_mcp/server.py",
        "schemas/aegis/foundation-manifest.schema.json",
    ]
    return {rel_path: (REPO_ROOT / rel_path).read_bytes() for rel_path in rel_paths}


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/codex-task", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _json_cli(args: list[str]) -> dict:
    result = _run_cli(args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _assert_user_files_preserved(target: Path, expected: dict[str, str]) -> None:
    for rel_path, content in expected.items():
        assert (target / rel_path).read_text(encoding="utf-8") == content


def _assert_installed_target(target: Path, *, primary_agent: str, agents: list[str]) -> None:
    manifest_path = target / aegis.AEGIS_MANIFEST_REL
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["foundation_name"] == "Aegis Foundation"
    assert manifest["profile"] == "generic"
    assert manifest["primary_agent"] == primary_agent
    assert manifest["agents"]["claude"]["enabled"] is ("claude" in agents)
    assert manifest["agents"]["codex"]["enabled"] is ("codex" in agents)
    assert (target / ".aegis" / "contract.md").exists()
    assert (target / ".aegis" / "reports" / "install-plan.json").exists()
    assert (target / ".aegis" / "reports" / "install-report.json").exists()
    assert (target / ".aegis" / "reports" / "verification-report.json").exists()
    assert (target / "schemas" / "aegis" / "foundation-manifest.schema.json").exists()
    assert (target / "AGENTS.md").exists()

    if "claude" in agents:
        assert (target / "CLAUDE.md").exists()
        assert (target / ".claude" / "settings.json").exists()
        assert (target / ".claude" / "scripts" / "readiness.sh").exists()
        assert (target / ".claude" / "scripts" / "pretooluse-gate.sh").exists()
        assert (target / ".claude" / "scripts" / "bash-command-guard.sh").exists()
        assert (target / ".claude" / "scripts" / "codex-path-guard.sh").exists()

    if "codex" in agents:
        assert (target / "CODEX.md").exists()
        assert (target / "scripts" / "codex-guard").exists()


@pytest.mark.parametrize(
    ("shape_name", "seed", "primary_agent", "agents"),
    [
        ("empty-repo", _seed_empty_repo, "claude", ["claude"]),
        ("python-library", _seed_python_library_repo, "multi", ["claude", "codex"]),
        ("web-app", _seed_web_app_repo, "claude", ["claude"]),
        ("docs-heavy", _seed_docs_heavy_repo, "claude", ["claude"]),
    ],
)
def test_aegis_cli_installs_and_verifies_realistic_project_shapes(
    tmp_path: Path,
    shape_name: str,
    seed: SeedFunc,
    primary_agent: str,
    agents: list[str],
) -> None:
    target = tmp_path / shape_name
    seeded_files = seed(target)
    source_before = _source_fingerprint()
    target_before = _snapshot_files(target)

    inspect_payload = _json_cli(["aegis", "inspect", "--target-dir", target.as_posix()])
    assert inspect_payload["target_root"] == target.resolve().as_posix()
    assert inspect_payload["aegis"]["installed"] is False
    assert _snapshot_files(target) == target_before

    plan_payload = _json_cli(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            target.as_posix(),
            "--primary-agent",
            primary_agent,
            *[arg for agent in agents for arg in ("--agent", agent)],
        ]
    )
    assert plan_payload["mode"] == "dry_run"
    assert plan_payload["apply_confirmed"] is False
    assert plan_payload["summary"]["creates"] > 0
    assert not (target / ".aegis").exists()
    assert _snapshot_files(target) == target_before

    install_payload = _json_cli(
        [
            "aegis",
            "install",
            "--target-dir",
            target.as_posix(),
            "--profile",
            "generic",
            "--primary-agent",
            primary_agent,
            *[arg for agent in agents for arg in ("--agent", agent)],
            "--apply",
        ]
    )
    assert install_payload["status"] == "applied"

    verify_payload = _json_cli(["aegis", "verify", "--target-dir", target.as_posix()])
    assert verify_payload["status"] == "passed"
    assert verify_payload["summary"]["failed_required"] == 0

    _assert_user_files_preserved(target, seeded_files)
    _assert_installed_target(target, primary_agent=primary_agent, agents=agents)
    assert _source_fingerprint() == source_before


def test_aegis_cli_dry_run_install_does_not_mutate_target(tmp_path: Path) -> None:
    target = tmp_path / "dry-run-target"
    seeded_files = _seed_python_library_repo(target)
    target_before = _snapshot_files(target)

    payload = _json_cli(
        [
            "aegis",
            "install",
            "--target-dir",
            target.as_posix(),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )

    assert payload["mode"] == "dry_run"
    assert payload["apply_confirmed"] is False
    assert not (target / ".aegis").exists()
    assert _snapshot_files(target) == target_before
    _assert_user_files_preserved(target, seeded_files)
