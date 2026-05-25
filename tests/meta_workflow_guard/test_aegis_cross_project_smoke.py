"""Cross-project smoke coverage for Aegis Foundation installs."""

from __future__ import annotations

import json
import subprocess
import asyncio
from collections.abc import Callable
from pathlib import Path

import pytest

from aegis_mcp.server import AegisMCPConfig, create_server
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


def _json_cli_result(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = _run_cli(args)
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)


def _call_tool_payload(server, name: str, arguments: dict | None = None) -> dict:
    content, structured_payload = asyncio.run(server.call_tool(name, arguments or {}))
    assert len(content) == 1
    payload = json.loads(content[0].text)
    assert structured_payload == payload
    return payload


def _read_resource_payload(server, uri: str) -> dict:
    contents = asyncio.run(server.read_resource(uri))
    assert len(contents) == 1
    return json.loads(contents[0].content)


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


def test_aegis_mcp_tools_preserve_core_install_and_verify_contract(tmp_path: Path) -> None:
    target = tmp_path / "mcp-python-library"
    seeded_files = _seed_python_library_repo(target)
    source_before = _source_fingerprint()
    target_before = _snapshot_files(target)
    server = create_server(AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target))

    inspect_payload = _call_tool_payload(server, "aegis.inspect", {"target_dir": target.as_posix()})
    assert inspect_payload["ok"] is True
    assert inspect_payload["read_only"] is True
    assert inspect_payload["result"]["aegis"]["installed"] is False
    assert _snapshot_files(target) == target_before

    plan_payload = _call_tool_payload(
        server,
        "aegis.plan_install",
        {
            "target_dir": target.as_posix(),
            "primary_agent": "claude",
            "agents": ["claude"],
        },
    )
    assert plan_payload["ok"] is True
    assert plan_payload["read_only"] is True
    assert plan_payload["result"]["mode"] == "dry_run"
    assert plan_payload["result"]["apply_confirmed"] is False
    assert not (target / ".aegis").exists()
    assert _snapshot_files(target) == target_before

    dry_run_install_payload = _call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": False,
        },
    )
    assert dry_run_install_payload["ok"] is False
    assert dry_run_install_payload["error"]["code"] == "apply_required"
    assert dry_run_install_payload["error"]["status"] == "refused"
    assert not (target / ".aegis").exists()

    install_payload = _call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    assert install_payload["ok"] is True
    assert install_payload["read_only"] is False
    assert install_payload["result"]["status"] == "applied"

    verify_without_ack = _call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": False,
        },
    )
    assert verify_without_ack["ok"] is False
    assert verify_without_ack["error"]["code"] == "acknowledgement_required"
    assert not (target / ".aegis" / "reports" / "verification-report.json").exists()

    verify_payload = _call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
        },
    )
    assert verify_payload["ok"] is True
    assert verify_payload["result"]["status"] == "passed"

    _assert_user_files_preserved(target, seeded_files)
    _assert_installed_target(target, primary_agent="claude", agents=["claude"])

    manifest_resource = _read_resource_payload(server, "aegis://manifest/current")
    managed_resource = _read_resource_payload(server, "aegis://managed-files")
    plan_resource = _read_resource_payload(server, "aegis://install-plan/latest")
    verification_resource = _read_resource_payload(server, "aegis://verification/latest")

    assert manifest_resource["ok"] is True
    assert manifest_resource["result"]["payload"]["primary_agent"] == "claude"
    assert managed_resource["ok"] is True
    assert any(item["path"] == "CLAUDE.md" for item in managed_resource["result"]["managed_files"])
    assert plan_resource["ok"] is True
    assert plan_resource["result"]["mode"] == "dry_run"
    assert verification_resource["ok"] is True
    assert verification_resource["result"]["payload"]["status"] == "passed"
    assert _source_fingerprint() == source_before


def test_aegis_mcp_existing_claude_merge_preserves_core_report_shape(tmp_path: Path) -> None:
    mcp_target = tmp_path / "mcp-existing-claude"
    core_target = tmp_path / "core-existing-claude"
    for target in (mcp_target, core_target):
        _write_files(target, {"CLAUDE.md": "# Existing Claude instructions\n"})

    server = create_server(AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=mcp_target))
    mcp_payload = _call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": mcp_target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    core_report = aegis.install(
        core_target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert mcp_payload["ok"] is True
    mcp_report = mcp_payload["result"]
    assert mcp_report["status"] == core_report["status"] == "applied"
    for target, report in ((mcp_target, mcp_report), (core_target, core_report)):
        claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
        assert aegis.AEGIS_CLAUDE_BLOCK_BEGIN in claude_text
        assert "# Existing Claude instructions" in claude_text
        claude_operation = next(operation for operation in report["plan"]["operations"] if operation["path"] == "CLAUDE.md")
        assert claude_operation["classification"] == "modify"
        assert claude_operation["safe_to_apply"] is True
        assert (target / aegis.AEGIS_MANIFEST_REL).exists()


def test_aegis_cli_refuses_partial_existing_manifest_without_partial_writes(tmp_path: Path) -> None:
    target = tmp_path / "partial-existing-aegis"
    _write_files(
        target,
        {
            ".aegis/foundation-manifest.json": '{"foundation_name": "Other Foundation"}\n',
            "README.md": "# Existing project\n",
        },
    )
    before = _snapshot_files(target)

    result, payload = _json_cli_result(
        [
            "aegis",
            "install",
            "--target-dir",
            target.as_posix(),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ]
    )

    assert result.returncode != 0
    assert "refused unsafe overwrite" in result.stderr
    assert payload["status"] == "refused"
    assert any(operation["path"] == aegis.AEGIS_MANIFEST_REL for operation in payload["unsafe_operations"])
    assert _snapshot_files(target) == before
    assert not (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()


def test_aegis_cli_verify_missing_required_gate_is_structured_failure(tmp_path: Path) -> None:
    target = tmp_path / "missing-required-gate"
    _seed_empty_repo(target)
    _json_cli(
        [
            "aegis",
            "install",
            "--target-dir",
            target.as_posix(),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ]
    )
    (target / ".claude" / "scripts" / "readiness.sh").unlink()

    result, payload = _json_cli_result(["aegis", "verify", "--target-dir", target.as_posix()])

    assert result.returncode != 0
    assert "Aegis verification failed" in result.stderr
    assert payload["status"] == "failed"
    assert any(
        check["gate_id"] == "claude.readiness" and check["status"] == "fail"
        for check in payload["checks"]
    )
    assert (target / ".aegis" / "reports" / "verification-report.json").exists()


def test_aegis_mcp_failed_apply_uses_core_cleanup_without_deleting_user_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "mcp-failed-apply"
    _write_files(target, {"README.md": "# Keep me\n"})
    server = create_server(AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target))
    original_write_asset = server.aegis_installer._write_asset

    def fail_on_claude_entrypoint(target_root: Path, asset: aegis.Asset) -> None:
        if asset.path == "CLAUDE.md":
            raise aegis.AegisError("simulated MCP write failure")
        original_write_asset(target_root, asset)

    monkeypatch.setattr(server.aegis_installer, "_write_asset", fail_on_claude_entrypoint)

    payload = _call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "install_failed"
    assert payload["error"]["status"] == "failed"
    report = payload["error"]["details"]["report"]
    assert report["status"] == "failed"
    assert report["cleanup"]["status"] == "completed"
    assert report["cleanup"]["removed_paths"]
    assert "simulated MCP write failure" in report["reason"]
    assert (target / "README.md").read_text(encoding="utf-8") == "# Keep me\n"
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".aegis" / "contract.md").exists()
    assert not (target / aegis.AEGIS_MANIFEST_REL).exists()
