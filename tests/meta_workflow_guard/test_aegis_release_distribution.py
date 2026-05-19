"""Release distribution metadata coverage for Aegis Foundation."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aegis_foundation import (
    DISTRIBUTION_NAME,
    FOUNDATION_NAME,
    FOUNDATION_VERSION,
    INSTALLER_VERSION,
    PACKAGE_VERSION,
    SCHEMA_VERSION,
    __version__,
)
from aegis_foundation import cli as aegis_cli
from aegis_foundation.resources import packaged_asset_root
from aegis_mcp import server as aegis_mcp_server
from aegis_mcp.server import PROMPT_NAMES, RESOURCE_URIS, V1_TOOL_NAMES
from scripts import _aegis_installer


REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
INVOCATION_DOC = REPO_ROOT / "docs" / "aegis" / "invocation-contract.md"
DISTRIBUTION_DOC = REPO_ROOT / "docs" / "aegis" / "distribution.md"
RELEASE_POLICY_DOC = REPO_ROOT / "docs" / "aegis" / "release-policy.md"
UPDATE_ROLLBACK_DOC = REPO_ROOT / "docs" / "aegis" / "update-rollback.md"
CI_INSTALL_TEMPLATES_DOC = REPO_ROOT / "docs" / "aegis" / "ci-install-templates.md"
RELEASE_VERIFICATION_MATRIX_DOC = REPO_ROOT / "docs" / "aegis" / "release-verification-matrix.md"
MCP_CLIENT_SETUP_DOC = REPO_ROOT / "docs" / "aegis" / "mcp-client-setup.md"


async def _run_wheel_mcp_stdio_smoke(
    *,
    uvx: str,
    wheel: Path,
    target: Path,
) -> tuple[set[str], set[str], set[str], dict]:
    params = StdioServerParameters(
        command=uvx,
        args=[
            "--from",
            wheel.as_posix(),
            "aegis-mcp-server",
            "--default-target-dir",
            target.as_posix(),
            "--transport",
            "stdio",
        ],
        cwd=target.as_posix(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            prompts = await session.list_prompts()
            inspect = await session.call_tool("aegis.inspect", {"target_dir": "."})

    assert len(inspect.content) == 1
    inspect_payload = json.loads(inspect.content[0].text)
    return (
        {tool.name for tool in tools.tools},
        {str(resource.uri) for resource in resources.resources},
        {prompt.name for prompt in prompts.prompts},
        inspect_payload,
    )


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _snapshot_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_public_package_metadata_contract_is_release_ready() -> None:
    data = _pyproject()
    project = data["project"]

    assert project["name"] == DISTRIBUTION_NAME == "aegis-foundation"
    assert project["version"] == PACKAGE_VERSION == __version__
    assert "Aegis" in project["description"]
    assert project["requires-python"] == ">=3.11"
    assert project["readme"]["file"] == "README.md"
    assert project["readme"]["content-type"] == "text/markdown"
    assert project["license"] == "LicenseRef-Proprietary"
    assert project["authors"] == [{"name": "loucmane"}]
    assert project["maintainers"] == [{"name": "loucmane"}]
    assert {"agents", "aegis", "mcp", "workflow"} <= set(project["keywords"])
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]
    assert "Programming Language :: Python :: 3.12" in project["classifiers"]
    assert project["urls"]["Repository"].endswith("codex-starter-pack")

    scripts = project["scripts"]
    assert scripts["aegis"] == "aegis_foundation.cli:main"
    assert scripts["aegis-mcp-server"] == "aegis_mcp.server:main"

    package_find = data["tool"]["setuptools"]["packages"]["find"]
    assert package_find["where"] == ["."]
    assert {"aegis_foundation*", "aegis_mcp*", "scripts"} <= set(package_find["include"])
    assert package_find["namespaces"] is True

    package_data = set(data["tool"]["setuptools"]["package-data"]["aegis_foundation"])
    assert "assets/.claude/scripts/*" in package_data
    assert "assets/schemas/aegis/*.json" in package_data
    assert "assets/scripts/*" in package_data
    assert data.get("tool", {}).get("uv", {}).get("package") is not False


def test_version_constants_are_aligned_across_cli_installer_and_schema() -> None:
    assert FOUNDATION_NAME == _aegis_installer.FOUNDATION_NAME == "Aegis Foundation"
    assert FOUNDATION_VERSION == _aegis_installer.FOUNDATION_VERSION == PACKAGE_VERSION
    assert INSTALLER_VERSION == _aegis_installer.INSTALLER_VERSION == PACKAGE_VERSION
    assert SCHEMA_VERSION == _aegis_installer.SCHEMA_VERSION == "1.0.0"

    project = _pyproject()["project"]
    assert project["version"] == PACKAGE_VERSION


def test_aegis_cli_version_reports_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        aegis_cli.main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"aegis {PACKAGE_VERSION}"


def test_aegis_status_reports_current_and_migration_without_writes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "status-target"
    target.mkdir()
    with packaged_asset_root() as asset_root:
        install = _aegis_installer.install(
            target,
            source_root=asset_root,
            primary_agent="claude",
            agents=["claude"],
            apply=True,
        )
        assert install["status"] == "applied"
        before = _snapshot_files(target)
        current = _aegis_installer.status(target, source_root=asset_root)

    assert _snapshot_files(target) == before
    assert current["status"] == "current"
    assert current["migration_required"] is False
    assert current["read_only"] is True

    manifest_path = target / _aegis_installer.AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["foundation_version"] = "0.0.0"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    before_migration_check = _snapshot_files(target)
    with packaged_asset_root() as asset_root:
        migration = _aegis_installer.status(target, source_root=asset_root)

    assert _snapshot_files(target) == before_migration_check
    assert migration["status"] == "migration_required"
    assert migration["migration_required"] is True
    assert any(
        check["id"] == "foundation_version" and check["status"] == "fail"
        for check in migration["checks"]
    )

    result = aegis_cli.main(["status", "--target-dir", target.as_posix()])

    assert result == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["status"] == "migration_required"
    assert cli_payload["migration_required"] is True


def test_mcp_describe_config_reports_release_version_fields(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "external-target"
    target.mkdir()

    result = aegis_mcp_server.main(
        [
            "--source-root",
            REPO_ROOT.as_posix(),
            "--default-target-dir",
            target.as_posix(),
            "--describe-config",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["distribution_name"] == DISTRIBUTION_NAME
    assert payload["asset_origin"] == "source"
    assert payload["foundation_version"] == FOUNDATION_VERSION
    assert payload["installer_version"] == INSTALLER_VERSION
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["default_target_dir"] == target.resolve().as_posix()


def test_mcp_packaged_default_uses_cwd_as_target_and_package_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "mcp-package-default-target"
    target.mkdir()
    monkeypatch.chdir(target)
    monkeypatch.delenv("AEGIS_SOURCE_ROOT", raising=False)
    monkeypatch.delenv("AEGIS_DEFAULT_TARGET_DIR", raising=False)

    config = aegis_mcp_server.AegisMCPConfig.from_paths()

    assert config.default_target_dir == target.resolve()
    assert config.asset_origin == "package"
    assert config.source_root == (REPO_ROOT / "aegis_foundation" / "assets").resolve()
    assert (config.source_root / "schemas" / "aegis" / "foundation-manifest.schema.json").is_file()


def test_invocation_contract_documents_release_identity() -> None:
    text = INVOCATION_DOC.read_text(encoding="utf-8")

    assert "Task 113 uses `aegis-foundation` as the working public distribution name." in text
    assert "aegis --version" in text
    assert "aegis-mcp-server --describe-config" in text
    assert "foundation, installer, and schema versions" in text
    assert "docs/aegis/distribution.md" in text


def test_packaged_asset_bundle_contains_required_runtime_assets() -> None:
    expected = {
        "CODEX.md",
        ".claude/scripts/readiness.sh",
        ".claude/scripts/pretooluse-gate.sh",
        ".claude/scripts/posttooluse-tracking.sh",
        ".claude/scripts/tracking-stop-gate.sh",
        ".claude/scripts/bash-command-guard.sh",
        ".claude/scripts/codex-path-guard.sh",
        ".claude/scripts/gate_lib.py",
        "schemas/aegis/foundation-manifest.schema.json",
        "schemas/aegis/profile.schema.json",
        "schemas/aegis/install-plan.schema.json",
        "scripts/_aegis_installer.py",
        "scripts/codex-task",
        "scripts/codex-guard",
        "scripts/_repo_structure.py",
        "scripts/template_registry.py",
        "scripts/template_governance.py",
        "scripts/template_versioning.py",
        "docs/aegis/invocation-contract.md",
        "docs/aegis/distribution.md",
        "docs/aegis/release-policy.md",
        "docs/aegis/update-rollback.md",
        "docs/aegis/ci-install-templates.md",
        "docs/aegis/release-verification-matrix.md",
        "docs/aegis/mcp-client-setup.md",
        "templates/registry/agent-compatibility-matrix.json",
    }

    with packaged_asset_root() as asset_root:
        for rel_path in expected:
            assert (asset_root / rel_path).is_file(), rel_path


def test_packaged_asset_root_can_drive_install_plan_without_checkout(tmp_path: Path) -> None:
    target = tmp_path / "packaged-assets-target"
    target.mkdir()

    with packaged_asset_root() as asset_root:
        assert aegis_cli._looks_like_source_root(asset_root)
        payload = _aegis_installer.plan_install(
            target,
            source_root=asset_root,
            primary_agent="claude",
            agents=["claude"],
    )

    assert payload["mode"] == "dry_run"
    planned_paths = {entry["path"] for entry in payload["operations"]}
    assert ".claude/scripts/pretooluse-gate.sh" in planned_paths
    assert ".claude/scripts/posttooluse-tracking.sh" in planned_paths
    assert ".claude/scripts/tracking-stop-gate.sh" in planned_paths
    assert "schemas/aegis/foundation-manifest.schema.json" in planned_paths


def test_distribution_doc_includes_public_and_local_install_snippets() -> None:
    text = DISTRIBUTION_DOC.read_text(encoding="utf-8")

    required_snippets = [
        "python3 -m pip install aegis-foundation",
        "uvx --from aegis-foundation aegis inspect --target-dir .",
        "uvx --from aegis-foundation aegis status --target-dir .",
        "pipx run --spec aegis-foundation aegis inspect --target-dir .",
        "pipx run --spec aegis-foundation aegis status --target-dir .",
        "uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .",
        "pipx run --spec ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .",
        "aegis-mcp-server --default-target-dir . --transport stdio",
        "uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio",
        "pipx run --spec aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio",
        '"asset_origin": "package"',
        "uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --describe-config",
        "uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio",
    ]
    for snippet in required_snippets:
        assert snippet in text

    assert "Hosted MCP service deployment is a supported release pattern" in text
    assert "does not publish a hosted service in Task 113" in text
    assert "docs/aegis/release-policy.md" in text
    assert "docs/aegis/update-rollback.md" in text
    assert "docs/aegis/ci-install-templates.md" in text
    assert "docs/aegis/release-verification-matrix.md" in text
    assert "docs/aegis/mcp-client-setup.md" in text


def test_mcp_client_setup_doc_covers_cross_agent_release_candidate_configs() -> None:
    text = MCP_CLIENT_SETUP_DOC.read_text(encoding="utf-8")
    asset_text = (
        REPO_ROOT
        / "aegis_foundation"
        / "assets"
        / "docs"
        / "aegis"
        / "mcp-client-setup.md"
    ).read_text(encoding="utf-8")

    assert asset_text == text
    for snippet in (
        "Task 114 validates local wheel and sdist artifacts",
        "GitHub release artifacts",
        "PyPI publication is a later explicit release task",
        "[mcp_servers.aegis]",
        '"mcpServers"',
        '"name": "aegis"',
        "uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio",
        "aegis-foundation==0.1.0",
        '"asset_origin": "package"',
        "stdio tool/resource/prompt discovery",
    ):
        assert snippet in text


def test_release_policy_docs_cover_update_rollback_and_signing() -> None:
    release_policy = RELEASE_POLICY_DOC.read_text(encoding="utf-8")
    update_rollback = UPDATE_ROLLBACK_DOC.read_text(encoding="utf-8")

    for snippet in (
        "semantic versioning",
        "Sigstore keyless signing",
        "checksums",
        "provenance",
        "Prerelease builds",
        "uvx --from aegis-foundation==0.1.0 aegis status --target-dir .",
        "Hosted MCP service deployment",
    ):
        assert snippet in release_policy

    for snippet in (
        "aegis status",
        "aegis plan-install",
        "aegis install --apply",
        "aegis verify",
        "Rollback is intentionally Git-first",
        "Downgrades are treated as migrations",
        "Do not write `.aegis/` directly",
        "aegis.rollback",
    ):
        assert snippet in update_rollback


def test_ci_templates_and_release_matrix_cover_distribution_dimensions() -> None:
    ci_templates = CI_INSTALL_TEMPLATES_DOC.read_text(encoding="utf-8")
    matrix = RELEASE_VERIFICATION_MATRIX_DOC.read_text(encoding="utf-8")

    for snippet in (
        "actions/setup-python@v5",
        "aegis-foundation==0.1.0",
        "install-method: [pip, uvx, pipx]",
        "uv build --sdist --wheel --out-dir dist",
        "pipx run --spec aegis-foundation==0.1.0 aegis inspect --target-dir .",
        "uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis status --target-dir .",
        "aegis-mcp-server --default-target-dir . --describe-config",
        ".aegis/reports/install-plan.json",
        ".aegis/reports/install-report.json",
        ".aegis/reports/verification-report.json",
    ):
        assert snippet in ci_templates

    for snippet in (
        "`ubuntu-latest`, `macos-latest`",
        "`3.11`, `3.12`",
        "`pip`, `uvx`, `pipx`, `local-wheel`, `editable`",
        "`aegis`, `aegis-mcp-server`",
        "`aegis --version`, `aegis inspect`, `aegis status`, `aegis plan-install`, `aegis install --apply`, `aegis verify`, `aegis kickoff`, `aegis log`",
        "`aegis-mcp-server --describe-config`, stdio startup, `aegis.inspect`, `aegis.status`, `aegis.kickoff`, `aegis.log`, `aegis://work/current`, tool/resource/prompt discovery",
        "`package`, `source`",
        "online package resolution, offline/local wheel",
        "empty repository",
        "Python/library repository",
        "web/app repository",
        "docs-heavy Task 101-style repository",
        "partial existing Aegis install",
        "local-wheel MCP stdio validation works against concrete new and already-started Python, web, and backend fixture projects",
        "installed projects can reach `READY` through Aegis-native kickoff without `.taskmaster/` or `.serena/`",
        "installed projects with stale optional `.taskmaster/` state still reach `READY` through Aegis-native current work unless Taskmaster is explicitly required",
        "installed kickoff renders packaged workflow templates into session, plan, tracker, findings, decisions, implementation, changelog, handoff, designs, and reports surfaces comparable to this repository's workflow model",
        "installed Claude runtime records pending S:W:H:E tracking after successful task mutations",
        "Policy-only claims are not release evidence.",
    ):
        assert snippet in matrix


def test_local_wheel_cli_smoke_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("AEGIS_RUN_WHEEL_SMOKE") != "1":
        pytest.skip("Set AEGIS_RUN_WHEEL_SMOKE=1 to run the local wheel CLI smoke.")
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required for the local wheel CLI smoke.")

    dist_dir = tmp_path / "dist"
    venv_dir = tmp_path / "venv"
    target = tmp_path / "external-target"
    target.mkdir()

    try:
        build = subprocess.run(
            [uv, "build", "--wheel", "--out-dir", dist_dir.as_posix()],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert build.returncode == 0, build.stdout
        wheel = next(dist_dir.glob("aegis_foundation-*.whl"))

        venv = subprocess.run(
            [sys.executable, "-m", "venv", venv_dir.as_posix()],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert venv.returncode == 0, venv.stderr

        python = venv_dir / "bin" / "python"
        install = subprocess.run(
            [python.as_posix(), "-m", "pip", "install", wheel.as_posix()],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert install.returncode == 0, install.stdout

        aegis_bin = venv_dir / "bin" / "aegis"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("AEGIS_SOURCE_ROOT", None)

        version = subprocess.run(
            [aegis_bin.as_posix(), "--version"],
            cwd=target,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert version.returncode == 0, version.stderr
        assert version.stdout.strip() == f"aegis {PACKAGE_VERSION}"

        for args in (
            ["inspect", "--target-dir", "."],
            ["plan-install", "--target-dir", ".", "--primary-agent", "claude", "--agent", "claude"],
            ["install", "--target-dir", ".", "--primary-agent", "claude", "--agent", "claude", "--apply"],
            ["status", "--target-dir", "."],
            ["verify", "--target-dir", "."],
        ):
            result = subprocess.run(
                [aegis_bin.as_posix(), *args],
                cwd=target,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)

        source_root_text = REPO_ROOT.as_posix()
        for rel_path in (
            ".aegis/contract.md",
            _aegis_installer.AEGIS_PLAN_REPORT_REL,
            _aegis_installer.AEGIS_INSTALL_REPORT_REL,
            _aegis_installer.AEGIS_VERIFY_REPORT_REL,
        ):
            assert source_root_text not in (target / rel_path).read_text(encoding="utf-8")
    finally:
        shutil.rmtree(REPO_ROOT / "aegis_foundation.egg-info", ignore_errors=True)
        shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)


def test_local_wheel_mcp_stdio_smoke_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("AEGIS_RUN_WHEEL_MCP_SMOKE") != "1":
        pytest.skip("Set AEGIS_RUN_WHEEL_MCP_SMOKE=1 to run the local wheel MCP smoke.")
    uv = shutil.which("uv")
    uvx = shutil.which("uvx")
    if uv is None or uvx is None:
        pytest.skip("uv and uvx are required for the local wheel MCP smoke.")

    dist_dir = tmp_path / "dist"
    target = tmp_path / "external-mcp-target"
    target.mkdir()

    try:
        build = subprocess.run(
            [uv, "build", "--wheel", "--out-dir", dist_dir.as_posix()],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert build.returncode == 0, build.stdout
        wheel = next(dist_dir.glob("aegis_foundation-*.whl"))

        tools, resources, prompts, inspect_payload = asyncio.run(
            _run_wheel_mcp_stdio_smoke(uvx=uvx, wheel=wheel, target=target)
        )

        assert tools == set(V1_TOOL_NAMES)
        assert resources == set(RESOURCE_URIS)
        assert prompts == set(PROMPT_NAMES)
        assert inspect_payload["ok"] is True
        assert inspect_payload["tool"] == "aegis.inspect"
        assert inspect_payload["read_only"] is True
        assert inspect_payload["result"]["target_root"] == target.resolve().as_posix()
        assert inspect_payload["result"]["aegis"]["installed"] is False
    finally:
        shutil.rmtree(REPO_ROOT / "aegis_foundation.egg-info", ignore_errors=True)
        shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)
