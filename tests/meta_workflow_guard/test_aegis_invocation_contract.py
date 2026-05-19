"""External invocation contract coverage for Aegis Foundation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aegis_mcp.server import PROMPT_NAMES, RESOURCE_URIS, V1_TOOL_NAMES
from aegis_foundation import DISTRIBUTION_NAME, FOUNDATION_VERSION, INSTALLER_VERSION, SCHEMA_VERSION
from scripts import _aegis_installer as aegis


REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_TASK = REPO_ROOT / "scripts" / "codex-task"
AEGIS_MCP_SERVER = REPO_ROOT / "scripts" / "aegis-mcp-server"
INVOCATION_DOC = REPO_ROOT / "docs" / "aegis" / "invocation-contract.md"


def _write_files(root: Path, files: dict[str, str]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return files


def _snapshot_files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _run_local_checkout(target: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", CODEX_TASK.as_posix(), "aegis", *args],
        cwd=target,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _json_local_checkout(target: Path, args: list[str]) -> dict:
    result = _run_local_checkout(target, args)
    assert result.returncode == 0, result.stderr
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def _create_editable_aegis_install(tmp_path: Path) -> Path:
    venv_dir = tmp_path / "aegis-venv"
    result = subprocess.run(
        [sys.executable, "-m", "venv", venv_dir.as_posix()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    python = venv_dir / "bin" / "python"
    result = subprocess.run(
        [
            python.as_posix(),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-e",
            REPO_ROOT.as_posix(),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    aegis_bin = venv_dir / "bin" / "aegis"
    assert aegis_bin.exists()
    return aegis_bin


def _run_package_aegis(aegis_bin: Path, target: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [aegis_bin.as_posix(), *args],
        cwd=target,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _json_package_aegis(aegis_bin: Path, target: Path, args: list[str]) -> dict:
    result = _run_package_aegis(aegis_bin, target, args)
    assert result.returncode == 0, result.stderr
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def _run_command(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


async def _run_stdio_surface_smoke(target: Path) -> tuple[set[str], set[str], set[str]]:
    params = StdioServerParameters(
        command="python3",
        args=[
            AEGIS_MCP_SERVER.as_posix(),
            "--source-root",
            REPO_ROOT.as_posix(),
            "--default-target-dir",
            ".",
        ],
        cwd=target.as_posix(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            prompts = await session.list_prompts()
    return (
        {tool.name for tool in tools.tools},
        {str(resource.uri) for resource in resources.resources},
        {prompt.name for prompt in prompts.prompts},
    )


def _assert_user_files_preserved(target: Path, expected: dict[str, str]) -> None:
    for rel_path, content in expected.items():
        assert (target / rel_path).read_text(encoding="utf-8") == content


def test_local_checkout_cli_invocation_works_from_external_cwd(tmp_path: Path) -> None:
    target = tmp_path / "external-python-service"
    seeded_files = _write_files(
        target,
        {
            "README.md": "# External Python Service\n",
            "pyproject.toml": (
                "[project]\n"
                'name = "external-python-service"\n'
                'version = "0.1.0"\n'
            ),
            "src/external_service/__init__.py": "__version__ = '0.1.0'\n",
        },
    )
    target_before = _snapshot_files(target)

    inspect_payload = _json_local_checkout(target, ["inspect", "--target-dir", "."])
    assert inspect_payload["target_root"] == target.resolve().as_posix()
    assert inspect_payload["aegis"]["installed"] is False
    assert _snapshot_files(target) == target_before

    plan_payload = _json_local_checkout(
        target,
        [
            "plan-install",
            "--target-dir",
            ".",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ],
    )
    assert plan_payload["mode"] == "dry_run"
    assert plan_payload["apply_confirmed"] is False
    assert plan_payload["target_root"] == "."
    assert not (target / ".aegis").exists()
    assert _snapshot_files(target) == target_before

    install_payload = _json_local_checkout(
        target,
        [
            "install",
            "--target-dir",
            ".",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ],
    )
    assert install_payload["status"] == "applied"
    assert install_payload["target_root"] == target.resolve().as_posix()

    verify_payload = _json_local_checkout(target, ["verify", "--target-dir", "."])
    assert verify_payload["status"] == "passed"
    assert verify_payload["target_root"] == target.resolve().as_posix()
    assert verify_payload["summary"]["failed_required"] == 0

    _assert_user_files_preserved(target, seeded_files)
    assert (target / aegis.AEGIS_MANIFEST_REL).exists()
    assert (target / aegis.AEGIS_PLAN_REPORT_REL).exists()
    assert (target / aegis.AEGIS_INSTALL_REPORT_REL).exists()
    assert (target / aegis.AEGIS_VERIFY_REPORT_REL).exists()
    assert (target / ".aegis" / "contract.md").exists()
    assert (target / "schemas" / "aegis" / "foundation-manifest.schema.json").exists()
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "scripts" / "pretooluse-gate.sh").exists()

    source_root_text = REPO_ROOT.as_posix()
    scanned_rel_paths = [
        ".aegis/contract.md",
        aegis.AEGIS_PLAN_REPORT_REL,
        aegis.AEGIS_INSTALL_REPORT_REL,
        aegis.AEGIS_VERIFY_REPORT_REL,
    ]
    for rel_path in scanned_rel_paths:
        assert source_root_text not in (target / rel_path).read_text(encoding="utf-8")


def test_invocation_contract_documents_local_checkout_adoption_commands() -> None:
    text = INVOCATION_DOC.read_text(encoding="utf-8")

    required_snippets = [
        "aegis --source-root /path/to/codex inspect --target-dir .",
        "aegis --source-root /path/to/codex plan-install --target-dir . --primary-agent claude --agent claude",
        "aegis --source-root /path/to/codex status --target-dir .",
        "aegis --source-root /path/to/codex install --target-dir . --primary-agent claude --agent claude --apply",
        "aegis --source-root /path/to/codex verify --target-dir .",
        "aegis --source-root /path/to/codex kickoff --target-dir . --task 1 --slug first-task --title \"First Task\"",
        "aegis --source-root /path/to/codex log --target-dir . --handler claude-live-write",
        "python3 /path/to/codex/scripts/aegis-mcp-server",
        "--source-root /path/to/codex",
        "--default-target-dir /path/to/project",
    ]
    for snippet in required_snippets:
        assert snippet in text

    assert "foundation." not in text
    assert "foundation://" not in text


def test_editable_package_aegis_cli_invocation_works_from_external_cwd(tmp_path: Path) -> None:
    aegis_bin = _create_editable_aegis_install(tmp_path)
    target = tmp_path / "package-style-project"
    seeded_files = _write_files(
        target,
        {
            "README.md": "# Package Style Project\n",
            "package.json": '{\n  "name": "package-style-project",\n  "private": true\n}\n',
            "app/page.tsx": "export default function Page() { return <main>Aegis</main>; }\n",
        },
    )
    target_before = _snapshot_files(target)

    inspect_payload = _json_package_aegis(aegis_bin, target, ["inspect", "--target-dir", "."])
    assert inspect_payload["target_root"] == target.resolve().as_posix()
    assert inspect_payload["aegis"]["installed"] is False
    assert _snapshot_files(target) == target_before

    plan_payload = _json_package_aegis(
        aegis_bin,
        target,
        [
            "plan-install",
            "--target-dir",
            ".",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ],
    )
    assert plan_payload["mode"] == "dry_run"
    assert plan_payload["apply_confirmed"] is False
    assert not (target / ".aegis").exists()
    assert _snapshot_files(target) == target_before

    install_payload = _json_package_aegis(
        aegis_bin,
        target,
        [
            "install",
            "--target-dir",
            ".",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ],
    )
    assert install_payload["status"] == "applied"

    verify_payload = _json_package_aegis(aegis_bin, target, ["verify", "--target-dir", "."])
    assert verify_payload["status"] == "passed"
    assert verify_payload["summary"]["failed_required"] == 0

    _assert_user_files_preserved(target, seeded_files)
    assert (target / aegis.AEGIS_MANIFEST_REL).exists()
    assert (target / aegis.AEGIS_PLAN_REPORT_REL).exists()
    assert (target / aegis.AEGIS_INSTALL_REPORT_REL).exists()
    assert (target / aegis.AEGIS_VERIFY_REPORT_REL).exists()
    assert (target / ".claude" / "scripts" / "pretooluse-gate.sh").exists()


def test_invocation_contract_documents_editable_package_style_commands() -> None:
    text = INVOCATION_DOC.read_text(encoding="utf-8")

    required_snippets = [
        "python3 -m venv .venv-aegis",
        ".venv-aegis/bin/python -m pip install -e /path/to/codex",
        "aegis inspect --target-dir .",
        "aegis status --target-dir .",
        "aegis plan-install --target-dir . --primary-agent claude --agent claude",
        "aegis install --target-dir . --primary-agent claude --agent claude --apply",
        "aegis verify --target-dir .",
        "aegis kickoff --target-dir . --task 1 --slug first-task --title \"First Task\"",
        "aegis log --target-dir . --handler claude-live-write",
    ]
    for snippet in required_snippets:
        assert snippet in text


def test_local_checkout_mcp_describe_config_works_from_external_cwd(tmp_path: Path) -> None:
    target = tmp_path / "mcp-local-checkout-project"
    target.mkdir()

    result = _run_command(
        target,
        [
            "python3",
            AEGIS_MCP_SERVER.as_posix(),
            "--source-root",
            REPO_ROOT.as_posix(),
            "--default-target-dir",
            ".",
            "--describe-config",
        ],
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "distribution_name": DISTRIBUTION_NAME,
        "asset_origin": "source",
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_root": REPO_ROOT.as_posix(),
        "default_target_dir": target.resolve().as_posix(),
    }
    assert (Path(payload["source_root"]) / "schemas" / "aegis" / "foundation-manifest.schema.json").is_file()


def test_editable_package_mcp_describe_config_works_from_external_cwd(tmp_path: Path) -> None:
    aegis_bin = _create_editable_aegis_install(tmp_path)
    mcp_bin = aegis_bin.parent / "aegis-mcp-server"
    target = tmp_path / "mcp-package-style-project"
    target.mkdir()

    result = _run_command(
        target,
        [
            mcp_bin.as_posix(),
            "--default-target-dir",
            ".",
            "--describe-config",
        ],
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "distribution_name": DISTRIBUTION_NAME,
        "asset_origin": "package",
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_root": (REPO_ROOT / "aegis_foundation" / "assets").as_posix(),
        "default_target_dir": target.resolve().as_posix(),
    }
    assert (Path(payload["source_root"]) / "schemas" / "aegis" / "foundation-manifest.schema.json").is_file()


def test_local_checkout_stdio_mcp_lists_aegis_surfaces_from_external_cwd(tmp_path: Path) -> None:
    target = tmp_path / "mcp-stdio-project"
    target.mkdir()

    tools, resources, prompts = asyncio.run(_run_stdio_surface_smoke(target))

    assert tools == set(V1_TOOL_NAMES)
    assert resources == set(RESOURCE_URIS)
    assert prompts == set(PROMPT_NAMES)


def test_invocation_contract_documents_external_mcp_startup_commands() -> None:
    text = INVOCATION_DOC.read_text(encoding="utf-8")

    required_snippets = [
        "python3 /path/to/codex/scripts/aegis-mcp-server",
        "--source-root /path/to/codex",
        "--default-target-dir /path/to/project",
        "--describe-config",
        "aegis-mcp-server --default-target-dir .",
        "aegis.install",
        "apply=true",
        "aegis.status",
        "aegis.verify",
        "acknowledge_report_write=true",
        "aegis.log",
        "S:W:H:E",
    ]
    for snippet in required_snippets:
        assert snippet in text
