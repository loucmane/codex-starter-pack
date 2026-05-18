"""Local end-to-end target validation for the Aegis MCP surface."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from aegis_mcp.server import (
    AegisMCPConfig,
    PROMPT_NAMES,
    RESOURCE_URIS,
    V1_TOOL_NAMES,
    create_server,
)
from scripts._aegis_installer import (
    AEGIS_CONTRACT_REL,
    AEGIS_MANIFEST_REL,
    AEGIS_VERIFY_REPORT_REL,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path.as_posix()


def _relative_snapshot(target: Path, rel_paths: list[str]) -> dict[str, bytes]:
    return {
        rel_path: (target / rel_path).read_bytes()
        for rel_path in sorted(rel_paths)
    }


def _call_tool_payload(server: FastMCP, name: str, arguments: dict | None = None) -> dict:
    content, structured_payload = asyncio.run(server.call_tool(name, arguments or {}))
    assert len(content) == 1
    payload = json.loads(content[0].text)
    assert structured_payload == payload
    return payload


def _read_resource_payload(server: FastMCP, uri: str) -> dict:
    contents = asyncio.run(server.read_resource(uri))
    assert len(contents) == 1
    return json.loads(contents[0].content)


def _listed_tools(server: FastMCP) -> set[str]:
    return {tool.name for tool in asyncio.run(server.list_tools())}


def _listed_resources(server: FastMCP) -> set[str]:
    return {str(resource.uri) for resource in asyncio.run(server.list_resources())}


def _listed_prompts(server: FastMCP) -> set[str]:
    return {prompt.name for prompt in asyncio.run(server.list_prompts())}


def _server_for(target: Path) -> FastMCP:
    config = AegisMCPConfig.from_paths(default_target_dir=target)
    assert config.asset_origin == "package"
    return create_server(config)


def _empty_project(target: Path) -> list[str]:
    target.mkdir(parents=True)
    return []


def _python_project(target: Path) -> list[str]:
    target.mkdir(parents=True)
    return [
        _write(
            target / "pyproject.toml",
            "\n".join(
                [
                    "[project]",
                    'name = "example-python-app"',
                    'version = "0.1.0"',
                    'requires-python = ">=3.11"',
                    "",
                ]
            ),
        ),
        _write(target / "README.md", "# Example Python App\n"),
        _write(target / "src" / "example_app" / "__init__.py", "__version__ = '0.1.0'\n"),
    ]


def _web_project(target: Path) -> list[str]:
    target.mkdir(parents=True)
    return [
        _write(
            target / "package.json",
            '{"name": "example-web-app", "version": "0.1.0", "type": "module"}\n',
        ),
        _write(target / "index.html", "<div id=\"app\"></div>\n"),
        _write(target / "src" / "main.ts", "document.body.dataset.ready = 'true';\n"),
    ]


def _backend_project(target: Path) -> list[str]:
    target.mkdir(parents=True)
    return [
        _write(
            target / "pyproject.toml",
            "\n".join(
                [
                    "[project]",
                    'name = "example-backend"',
                    'version = "0.1.0"',
                    "dependencies = []",
                    "",
                ]
            ),
        ),
        _write(target / "app" / "main.py", "def health() -> dict[str, str]:\n    return {'ok': 'true'}\n"),
        _write(target / "tests" / "test_health.py", "from app.main import health\n\n\ndef test_health():\n    assert health()['ok'] == 'true'\n"),
    ]


def _docs_heavy_project(target: Path) -> list[str]:
    target.mkdir(parents=True)
    return [
        _write(target / "README.md", "# Docs Heavy Project\n"),
        _write(target / "docs" / "index.md", "# Handbook\n"),
        _write(target / "docs" / "architecture.md", "# Architecture\n"),
        _write(target / "docs" / "runbooks" / "deploy.md", "# Deploy\n"),
    ]


TARGET_FACTORIES: list[tuple[str, Callable[[Path], list[str]]]] = [
    ("empty", _empty_project),
    ("python-app", _python_project),
    ("web-app", _web_project),
    ("backend-server", _backend_project),
    ("docs-heavy", _docs_heavy_project),
]


@pytest.mark.parametrize(("target_name", "factory"), TARGET_FACTORIES)
def test_mcp_e2e_installs_and_verifies_representative_targets(
    tmp_path: Path,
    target_name: str,
    factory: Callable[[Path], list[str]],
) -> None:
    target = tmp_path / target_name
    seed_files = [
        Path(path).relative_to(target).as_posix()
        for path in factory(target)
    ]
    seed_snapshot = _relative_snapshot(target, seed_files)
    server = _server_for(target)

    assert _listed_tools(server) == set(V1_TOOL_NAMES)
    assert _listed_resources(server) == set(RESOURCE_URIS)
    assert _listed_prompts(server) == set(PROMPT_NAMES)

    inspect_payload = _call_tool_payload(
        server,
        "aegis.inspect",
        {"target_dir": target.as_posix()},
    )
    assert inspect_payload["ok"] is True
    assert inspect_payload["read_only"] is True
    assert inspect_payload["result"]["aegis"]["installed"] is False

    status_before = _call_tool_payload(
        server,
        "aegis.status",
        {"target_dir": target.as_posix()},
    )
    assert status_before["ok"] is True
    assert status_before["read_only"] is True
    assert status_before["result"]["status"] == "not_installed"

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
    assert plan_payload["result"]["summary"]["creates"] > 0
    assert plan_payload["result"]["summary"]["manual_reviews"] == 0
    assert not (target / ".aegis").exists()

    latest_plan = _read_resource_payload(server, "aegis://install-plan/latest")
    assert latest_plan["ok"] is True
    assert latest_plan["source"] == "session_cache"
    assert latest_plan["result"]["mode"] == "dry_run"

    refused_install = _call_tool_payload(
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
    assert refused_install["ok"] is False
    assert refused_install["error"]["code"] == "apply_required"
    assert not (target / ".aegis").exists()

    refused_verify = _call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": False,
        },
    )
    assert refused_verify["ok"] is False
    assert refused_verify["error"]["code"] == "acknowledgement_required"
    assert not (target / AEGIS_VERIFY_REPORT_REL).exists()

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
    assert (target / AEGIS_MANIFEST_REL).is_file()

    verify_payload = _call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
        },
    )
    assert verify_payload["ok"] is True
    assert verify_payload["read_only"] is False
    assert verify_payload["result"]["status"] == "passed"

    status_after = _call_tool_payload(
        server,
        "aegis.status",
        {"target_dir": target.as_posix()},
    )
    assert status_after["ok"] is True
    assert status_after["read_only"] is True
    assert status_after["result"]["status"] == "current"

    manifest = _read_resource_payload(server, "aegis://manifest/current")
    contract = _read_resource_payload(server, "aegis://contract/current")
    managed_files = _read_resource_payload(server, "aegis://managed-files")
    verification = _read_resource_payload(server, "aegis://verification/latest")

    assert manifest["ok"] is True
    assert manifest["result"]["payload"]["primary_agent"] == "claude"
    assert contract["ok"] is True
    assert "Aegis Foundation Contract" in contract["result"]["content"]
    assert managed_files["ok"] is True
    assert any(item["path"] == "CLAUDE.md" for item in managed_files["result"]["managed_files"])
    assert verification["ok"] is True
    assert verification["result"]["payload"]["status"] == "passed"
    assert _relative_snapshot(target, seed_files) == seed_snapshot


def test_mcp_partial_install_resources_are_structured(tmp_path: Path) -> None:
    target = tmp_path / "partial-aegis"
    target.mkdir()
    _write(target / AEGIS_CONTRACT_REL, "# Existing Partial Contract\n")
    server = _server_for(target)

    inspect_payload = _call_tool_payload(server, "aegis.inspect", {"target_dir": target.as_posix()})
    status_payload = _call_tool_payload(server, "aegis.status", {"target_dir": target.as_posix()})
    manifest = _read_resource_payload(server, "aegis://manifest/current")
    contract = _read_resource_payload(server, "aegis://contract/current")
    managed_files = _read_resource_payload(server, "aegis://managed-files")

    assert inspect_payload["ok"] is True
    assert inspect_payload["result"]["aegis"]["installed"] is False
    assert status_payload["ok"] is True
    assert status_payload["result"]["status"] == "not_installed"
    assert manifest["ok"] is False
    assert manifest["error"]["code"] == "not_installed"
    assert contract["ok"] is True
    assert contract["result"]["content"] == "# Existing Partial Contract\n"
    assert managed_files["ok"] is False
    assert managed_files["error"]["code"] == "not_installed"


def test_mcp_conflict_target_refuses_unsafe_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "conflict-target"
    target.mkdir()
    _write(target / "CLAUDE.md", "# Existing Claude Instructions\n")
    before = (target / "CLAUDE.md").read_bytes()
    server = _server_for(target)

    plan_payload = _call_tool_payload(
        server,
        "aegis.plan_install",
        {
            "target_dir": target.as_posix(),
            "primary_agent": "claude",
            "agents": ["claude"],
        },
    )
    operations = plan_payload["result"]["operations"]
    claude_operation = next(operation for operation in operations if operation["path"] == "CLAUDE.md")

    assert plan_payload["ok"] is True
    assert plan_payload["result"]["summary"]["manual_reviews"] >= 1
    assert claude_operation["classification"] == "manual-review"
    assert claude_operation["safe_to_apply"] is False

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

    assert install_payload["ok"] is False
    assert install_payload["error"]["code"] == "install_refused"
    assert install_payload["error"]["status"] == "refused"
    assert any(
        operation["path"] == "CLAUDE.md"
        for operation in install_payload["error"]["details"]["report"]["unsafe_operations"]
    )
    assert (target / "CLAUDE.md").read_bytes() == before
    assert not (target / AEGIS_MANIFEST_REL).exists()
