"""Local end-to-end target validation for the Aegis MCP surface."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
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
    AEGIS_CLOSEOUT_REPORT_REL,
    AEGIS_CURRENT_WORK_REL,
    AEGIS_INSTALL_REPORT_REL,
    AEGIS_LOCAL_BIN_REL,
    AEGIS_MANIFEST_REL,
    AEGIS_PENDING_TRACKING_REL,
    AEGIS_PLAN_REPORT_REL,
    AEGIS_VERIFY_REPORT_REL,
    AEGIS_WORKFLOW_TEMPLATE_NAMES,
    AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_TARGET_FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "aegis-target-projects"


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


def _init_git_main(target: Path) -> None:
    result = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _run_target_readiness(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--quick", "--root", str(target)],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _run_target_pretooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def _run_target_posttooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "posttooluse-tracking.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def _run_target_stop_gate(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "tracking-stop-gate.sh")],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def _run_target_aegis_cli(target: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"}
    return subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", *args],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def _run_target_aegis_shim(target: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [f"./{AEGIS_LOCAL_BIN_REL}", *args],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


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

REAL_TARGET_PROJECTS = (
    "python-new",
    "python-started",
    "web-new",
    "web-started",
    "backend-new",
    "backend-started",
)


def _snapshot_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_snapshot_preserved(root: Path, before: dict[str, bytes]) -> None:
    for rel_path, expected in before.items():
        assert (root / rel_path).read_bytes() == expected, rel_path


def _assert_full_workflow_scaffold(target: Path, current_work: dict) -> None:
    paths = current_work["paths"]
    work_root = target / paths["work_tracking"]
    assert paths["workflow_templates"] == AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT
    assert (target / AEGIS_LOCAL_BIN_REL).is_file()
    assert os.access(target / AEGIS_LOCAL_BIN_REL, os.X_OK)
    assert (target / paths["session"]).is_file()
    assert (target / paths["plan"]).is_file()
    assert (target / paths["reports"]).is_dir()
    assert (work_root / "designs").is_dir()
    assert (work_root / "reports").is_dir()

    for template_name in AEGIS_WORKFLOW_TEMPLATE_NAMES:
        assert (target / AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT / template_name).is_file(), template_name

    session_text = (target / paths["session"]).read_text(encoding="utf-8")
    plan_text = (target / paths["plan"]).read_text(encoding="utf-8")
    tracker_text = (work_root / "TRACKER.md").read_text(encoding="utf-8")
    findings_text = (work_root / "FINDINGS.md").read_text(encoding="utf-8")
    decisions_text = (work_root / "DECISIONS.md").read_text(encoding="utf-8")
    handoff_text = (work_root / "HANDOFF.md").read_text(encoding="utf-8")
    implementation_text = (work_root / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    changelog_text = (work_root / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "### Session Validation" in session_text
    assert "### Session Goals" in session_text
    assert "### Progress Log" in session_text
    assert "[S:" in session_text and "|W:" in session_text and "|H:" in session_text and "|E:" in session_text
    assert "## Plan Table" in plan_text
    assert "plan-step-scope" in plan_text
    assert "plan-step-implement" in plan_text
    assert "plan-step-verify" in plan_text
    assert "## Evidence Checklist" in plan_text
    assert "## Emergency Bypass Protocol" in plan_text
    assert "## Progress Log" in tracker_text
    assert "## Plan Compliance Checklist" in tracker_text
    assert "## Current State" in tracker_text
    assert "## Next Steps" in tracker_text
    assert "## Dependencies & Notes" in tracker_text
    assert "## Findings" in findings_text and "## Progress Log" in findings_text
    assert "## Decisions" in decisions_text and "## Progress Log" in decisions_text
    assert "## Current State" in handoff_text and "## Next Steps" in handoff_text
    assert "## Planned Workstreams" in implementation_text and "## Progress Log" in implementation_text
    assert "## Progress Log" in changelog_text


def _payload_from_stdio_tool(result) -> dict:
    assert len(result.content) == 1
    return json.loads(result.content[0].text)


def _payload_from_stdio_resource(result) -> dict:
    assert len(result.contents) == 1
    content = result.contents[0]
    text = getattr(content, "text", None)
    if text is None:
        text = getattr(content, "content", None)
    assert text is not None
    return json.loads(text)


async def _run_wheel_mcp_real_project_flow(
    *,
    uvx: str,
    wheel: Path,
    target: Path,
) -> dict[str, object]:
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
        env={
            key: value
            for key, value in {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            }.items()
            if key not in {"AEGIS_SOURCE_ROOT", "AEGIS_DEFAULT_TARGET_DIR"}
        },
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            prompts = await session.list_prompts()
            inspect_before = _payload_from_stdio_tool(
                await session.call_tool("aegis.inspect", {"target_dir": "."})
            )
            plan = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.plan_install",
                    {
                        "target_dir": ".",
                        "primary_agent": "claude",
                        "agents": ["claude"],
                    },
                )
            )
            refused_install = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.install",
                    {
                        "target_dir": ".",
                        "profile": "generic",
                        "primary_agent": "claude",
                        "agents": ["claude"],
                        "apply": False,
                    },
                )
            )
            install = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.install",
                    {
                        "target_dir": ".",
                        "profile": "generic",
                        "primary_agent": "claude",
                        "agents": ["claude"],
                        "apply": True,
                    },
                )
            )
            kickoff = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.kickoff",
                    {
                        "target_dir": ".",
                        "task": "1",
                        "slug": "real-target-smoke",
                        "title": "Real Target Smoke",
                        "goals": ["Prove installed project can reach READY without Taskmaster or Serena"],
                        "apply": True,
                    },
                )
            )
            work_after_kickoff = _payload_from_stdio_resource(
                await session.read_resource("aegis://work/current")
            )
            current_work = work_after_kickoff["result"]["payload"]
            scope_log = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.log",
                    {
                        "target_dir": ".",
                        "handler": "wheel-mcp:scope",
                        "evidence": f"{current_work['paths']['work_tracking']}/FINDINGS.md",
                        "note": "Confirmed local wheel MCP proof scope",
                        "surfaces": ["findings", "decisions"],
                        "plan_step": "plan-step-scope",
                        "plan_status": "completed",
                        "apply": True,
                    },
                )
            )
            task_evidence = Path(current_work["paths"]["reports"]) / "local-wheel-mcp-proof.txt"
            (target / task_evidence).parent.mkdir(parents=True, exist_ok=True)
            (target / task_evidence).write_text("local wheel MCP proof evidence\n", encoding="utf-8")
            implementation_log = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.log",
                    {
                        "target_dir": ".",
                        "handler": "wheel-mcp:write",
                        "evidence": task_evidence.as_posix(),
                        "note": "Recorded local wheel MCP proof evidence",
                        "plan_step": "plan-step-implement",
                        "plan_status": "completed",
                        "apply": True,
                    },
                )
            )
            verify = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.verify",
                    {
                        "target_dir": ".",
                        "acknowledge_report_write": True,
                        "strict": True,
                    },
                )
            )
            verify_log = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.log",
                    {
                        "target_dir": ".",
                        "handler": "wheel-mcp:verify",
                        "evidence": AEGIS_VERIFY_REPORT_REL,
                        "note": "Recorded local wheel MCP strict verification evidence",
                        "plan_step": "plan-step-verify",
                        "plan_status": "completed",
                        "apply": True,
                    },
                )
            )
            closeout = _payload_from_stdio_tool(
                await session.call_tool(
                    "aegis.closeout",
                    {
                        "target_dir": ".",
                        "acknowledge_report_write": True,
                        "update_handoff": True,
                    },
                )
            )
            status = _payload_from_stdio_tool(
                await session.call_tool("aegis.status", {"target_dir": "."})
            )
            manifest = _payload_from_stdio_resource(
                await session.read_resource("aegis://manifest/current")
            )
            contract = _payload_from_stdio_resource(
                await session.read_resource("aegis://contract/current")
            )
            verification = _payload_from_stdio_resource(
                await session.read_resource("aegis://verification/latest")
            )
            work = _payload_from_stdio_resource(
                await session.read_resource("aegis://work/current")
            )

    return {
        "tools": {tool.name for tool in tools.tools},
        "resources": {str(resource.uri) for resource in resources.resources},
        "prompts": {prompt.name for prompt in prompts.prompts},
        "inspect_before": inspect_before,
        "plan": plan,
        "refused_install": refused_install,
        "install": install,
        "kickoff": kickoff,
        "scope_log": scope_log,
        "implementation_log": implementation_log,
        "verify": verify,
        "verify_log": verify_log,
        "closeout": closeout,
        "status": status,
        "manifest": manifest,
        "contract": contract,
        "verification": verification,
        "work": work,
    }


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


def test_mcp_kickoff_reaches_ready_without_taskmaster_or_serena(tmp_path: Path) -> None:
    target = tmp_path / "portable-ready"
    seed_files = [
        Path(path).relative_to(target).as_posix()
        for path in _python_project(target)
    ]
    seed_snapshot = _relative_snapshot(target, seed_files)
    _init_git_main(target)
    server = _server_for(target)

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

    refused_kickoff = _call_tool_payload(
        server,
        "aegis.kickoff",
        {
            "target_dir": target.as_posix(),
            "task": "1",
            "slug": "portable-ready",
            "title": "Portable Ready",
            "goals": ["Prove MCP kickoff creates READY state"],
            "apply": False,
        },
    )
    assert refused_kickoff["ok"] is False
    assert refused_kickoff["error"]["code"] == "apply_required"
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()

    kickoff_payload = _call_tool_payload(
        server,
        "aegis.kickoff",
        {
            "target_dir": target.as_posix(),
            "task": "1",
            "slug": "portable-ready",
            "title": "Portable Ready",
            "goals": ["Prove MCP kickoff creates READY state"],
            "apply": True,
        },
    )
    assert kickoff_payload["ok"] is True
    assert kickoff_payload["read_only"] is False
    assert kickoff_payload["result"]["status"] == "started"
    assert kickoff_payload["result"]["branch"]["current"] == "feat/task-1-portable-ready"

    work = _read_resource_payload(server, "aegis://work/current")
    assert work["ok"] is True
    assert work["result"]["payload"]["task"]["id"] == "1"
    assert work["result"]["payload"]["integrations"]["taskmaster"]["detected"] is False
    assert work["result"]["payload"]["integrations"]["serena"]["detected"] is False
    _assert_full_workflow_scaffold(target, work["result"]["payload"])

    readiness = subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--quick", "--root", str(target)],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert readiness.stdout.strip().startswith("READY | task=1")
    assert not (target / ".taskmaster").exists()
    assert not (target / ".serena").exists()
    assert _relative_snapshot(target, seed_files) == seed_snapshot


@pytest.mark.parametrize("fixture_name", REAL_TARGET_PROJECTS)
def test_installed_real_target_claude_like_runtime_creates_scaffold_and_runs_task(
    tmp_path: Path,
    fixture_name: str,
) -> None:
    fixture = REAL_TARGET_FIXTURE_ROOT / fixture_name
    target = tmp_path / fixture_name
    shutil.copytree(fixture, target)
    original_snapshot = _snapshot_files(target)
    _init_git_main(target)
    server = _server_for(target)

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
    for installed_path in (
        AEGIS_MANIFEST_REL,
        AEGIS_CONTRACT_REL,
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/settings.json",
        ".claude/scripts/readiness.sh",
        ".claude/scripts/pretooluse-gate.sh",
        ".claude/scripts/posttooluse-tracking.sh",
        ".claude/scripts/tracking-stop-gate.sh",
        ".claude/scripts/gate_lib.py",
    ):
        assert (target / installed_path).is_file(), installed_path
    for template_name in AEGIS_WORKFLOW_TEMPLATE_NAMES:
        assert (target / AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT / template_name).is_file(), template_name

    blocked = _run_target_readiness(target)
    assert blocked.returncode == 2
    assert "branch 'main' does not contain a task ID" in blocked.stdout

    blocked_write = _run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "claude-smoke-test.txt"}},
    )
    assert blocked_write.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_write.stderr
    assert not (target / "claude-smoke-test.txt").exists()

    blocked_bash = _run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "printf 'should not land\\n' > claude-smoke-bash.txt"}},
    )
    assert blocked_bash.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_bash.stderr
    assert not (target / "claude-smoke-bash.txt").exists()

    blocked_verify = _run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "aegis verify --target-dir ."}},
    )
    assert blocked_verify.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_verify.stderr

    kickoff_gate = _run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'aegis kickoff --target-dir . --task 1 --slug real-target-matrix --title "Real Target Matrix"'
            },
        },
    )
    assert kickoff_gate.returncode == 0, kickoff_gate.stderr

    refused_kickoff = _call_tool_payload(
        server,
        "aegis.kickoff",
        {
            "target_dir": target.as_posix(),
            "task": "1",
            "slug": "real-target-matrix",
            "title": "Real Target Matrix",
            "goals": ["Prove installed target runtime can bootstrap to READY"],
            "apply": False,
        },
    )
    assert refused_kickoff["ok"] is False
    assert refused_kickoff["error"]["code"] == "apply_required"
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()

    kickoff_cli = _run_target_aegis_cli(
        target,
        [
            "kickoff",
            "--target-dir",
            ".",
            "--task",
            "1",
            "--slug",
            "real-target-matrix",
            "--title",
            "Real Target Matrix",
            "--goal",
            "Prove installed target runtime can bootstrap to READY",
        ],
    )
    assert kickoff_cli.returncode == 0, kickoff_cli.stdout + kickoff_cli.stderr
    kickoff = json.loads(kickoff_cli.stdout)
    assert kickoff["status"] == "started"
    assert kickoff["branch"]["current"] == "feat/task-1-real-target-matrix"

    ready = _run_target_readiness(target)
    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert ready.stdout.strip().startswith("READY | task=1")

    work = _read_resource_payload(server, "aegis://work/current")
    assert work["ok"] is True
    current_work = work["result"]["payload"]
    assert current_work["task"]["id"] == "1"
    assert current_work["integrations"]["taskmaster"] == {"detected": False, "required": False}
    assert current_work["integrations"]["serena"] == {"detected": False, "required": False}
    assert (target / current_work["paths"]["session"]).is_file()
    assert (target / current_work["paths"]["plan"]).is_file()
    assert (target / current_work["paths"]["work_tracking"] / "TRACKER.md").is_file()
    for work_file in ("TRACKER.md", "FINDINGS.md", "DECISIONS.md", "HANDOFF.md", "IMPLEMENTATION.md", "CHANGELOG.md"):
        assert (target / current_work["paths"]["work_tracking"] / work_file).is_file(), work_file
    assert (target / "sessions" / "current").is_symlink()
    assert (target / "plans" / "current").is_symlink()
    _assert_full_workflow_scaffold(target, current_work)

    allowed_write = _run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{current_work['paths']['reports']}/claude-ready-write-test.txt"
            },
        },
    )
    assert allowed_write.returncode == 0, allowed_write.stderr

    allowed_bash = _run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"printf 'ready\\n' > {current_work['paths']['reports']}/claude-ready-bash-test.txt"
            },
        },
    )
    assert allowed_bash.returncode == 0, allowed_bash.stderr

    task_output = Path(current_work["paths"]["reports"]) / "claude-actual-task-output.txt"
    allowed_task_write = _run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": task_output.as_posix()
            },
        },
    )
    assert allowed_task_write.returncode == 0, allowed_task_write.stderr
    (target / task_output).write_text(f"task output for {fixture_name}\n", encoding="utf-8")
    assert (target / task_output).read_text(encoding="utf-8") == f"task output for {fixture_name}\n"

    posttool_payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": task_output.as_posix()
        },
    }
    pending_recorded = _run_target_posttooluse(target, posttool_payload)
    assert pending_recorded.returncode == 0, pending_recorded.stderr
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    assert pending_payload["events"][0]["evidence"] == task_output.as_posix()
    assert pending_payload["events"][0]["task"] == {"id": "1", "slug": "real-target-matrix"}

    blocked_pending = _run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{current_work['paths']['reports']}/second-write-before-log.txt"
            },
        },
    )
    assert blocked_pending.returncode == 2
    assert "pending S:W:H:E tracking must be logged" in blocked_pending.stderr

    blocked_stop = _run_target_stop_gate(target)
    assert blocked_stop.returncode == 2
    assert "pending S:W:H:E tracking remains before session stop" in blocked_stop.stderr

    log_command = (
        "./.aegis/bin/aegis log --target-dir . --handler claude-live-write "
        f"--evidence {task_output.as_posix()} --note 'Recorded task output evidence' "
        "--plan-step plan-step-implement --plan-status in-progress"
    )
    allowed_log = _run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": log_command}},
    )
    assert allowed_log.returncode == 0, allowed_log.stderr

    logged = _run_target_aegis_shim(
        target,
        [
            "log",
            "--target-dir",
            ".",
            "--handler",
            "claude-live-write",
            "--evidence",
            task_output.as_posix(),
            "--note",
            "Recorded task output evidence",
            "--plan-step",
            "plan-step-implement",
            "--plan-status",
            "in-progress",
        ],
    )
    assert logged.returncode == 0, logged.stdout + logged.stderr
    logged_payload = json.loads(logged.stdout)
    assert logged_payload["status"] == "logged"
    assert logged_payload["pending"]["cleared"] == 1
    assert logged_payload["plan"] == {
        "updated": True,
        "step": "plan-step-implement",
        "status": "in-progress",
        "evidence": task_output.as_posix(),
    }
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    swhe = f"[S:20"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(encoding="utf-8")
    implementation_text = (target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff_text = (target / current_work["paths"]["work_tracking"] / "HANDOFF.md").read_text(encoding="utf-8")
    expected_token = f"|W:task1-real-target-matrix|H:claude-live-write|E:{task_output.as_posix()}]"
    assert swhe in session_text and expected_token in session_text
    assert swhe in tracker_text and expected_token in tracker_text
    assert swhe in implementation_text and expected_token in implementation_text
    assert swhe in changelog_text and expected_token in changelog_text
    assert swhe in handoff_text and expected_token in handoff_text
    assert f"; {task_output.as_posix()} | in-progress |" in plan_text

    allowed_after_log = _run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{current_work['paths']['reports']}/second-write-after-log.txt"
            },
        },
    )
    assert allowed_after_log.returncode == 0, allowed_after_log.stderr

    allowed_stop = _run_target_stop_gate(target)
    assert allowed_stop.returncode == 0, allowed_stop.stderr

    protected_write = _run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "CODEX.md"}},
    )
    assert protected_write.returncode == 2
    assert "Protected path(s):" in protected_write.stderr
    assert "CODEX.md" in protected_write.stderr

    protected_bash = _run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "printf 'should not land\\n' >> CODEX.md"}},
    )
    assert protected_bash.returncode == 2
    assert "redirection targets protected path CODEX.md" in protected_bash.stderr
    assert not (target / ".taskmaster").exists()
    assert not (target / ".serena").exists()
    _assert_snapshot_preserved(target, original_snapshot)


def test_installed_web_target_real_feature_change_updates_full_workflow(tmp_path: Path) -> None:
    """Prove a normal "add a button" task drives source changes plus workflow evidence."""

    target = tmp_path / "web-started"
    shutil.copytree(REAL_TARGET_FIXTURE_ROOT / "web-started", target)
    _init_git_main(target)
    server = _server_for(target)

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
    claude_entrypoint = (target / "CLAUDE.md").read_text(encoding="utf-8")
    contract_text = (target / ".aegis/contract.md").read_text(encoding="utf-8")
    assert "Normal feature-work loop:" in claude_entrypoint
    assert "aegis verify --strict" in claude_entrypoint
    assert "aegis closeout --update-handoff" in claude_entrypoint
    assert "do not report the task complete until closeout passes" in claude_entrypoint
    assert "Normal feature work is:" in contract_text
    assert "aegis verify --strict" in contract_text
    assert "aegis closeout" in contract_text

    kickoff = _run_target_aegis_cli(
        target,
        [
            "kickoff",
            "--target-dir",
            ".",
            "--task",
            "42",
            "--slug",
            "add-cart-button",
            "--title",
            "Add Cart Button",
            "--goal",
            "Add a visible cart button to the web page",
            "--goal",
            "Record session, plan, and work-tracking evidence",
        ],
    )
    assert kickoff.returncode == 0, kickoff.stdout + kickoff.stderr
    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    assert current_work["task"] == {
        "id": "42",
        "slug": "add-cart-button",
        "title": "Add Cart Button",
        "status": "in-progress",
    }
    _assert_full_workflow_scaffold(target, current_work)

    readiness = _run_target_readiness(target)
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert readiness.stdout.strip().startswith("READY | task=42")

    scope_log = _run_target_aegis_shim(
        target,
        [
            "log",
            "--target-dir",
            ".",
            "--handler",
            "claude:scope",
            "--evidence",
            f"{current_work['paths']['work_tracking']}/FINDINGS.md",
            "--note",
            "Confirmed cart button scope before implementation",
            "--surface",
            "findings",
            "--surface",
            "decisions",
            "--plan-step",
            "plan-step-scope",
            "--plan-status",
            "completed",
        ],
    )
    assert scope_log.returncode == 0, scope_log.stdout + scope_log.stderr

    source_rel = "src/main.ts"
    source_path = target / source_rel
    allowed_source_edit = _run_target_pretooluse(
        target,
        {"tool_name": "Edit", "tool_input": {"file_path": source_rel}},
    )
    assert allowed_source_edit.returncode == 0, allowed_source_edit.stderr

    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "\n"
        + "const cartButton = document.createElement('button');\n"
        + "cartButton.textContent = 'Add to cart';\n"
        + "cartButton.dataset.action = 'add-to-cart';\n"
        + "document.body.appendChild(cartButton);\n",
        encoding="utf-8",
    )
    assert "Add to cart" in source_path.read_text(encoding="utf-8")

    recorded_source_edit = _run_target_posttooluse(
        target,
        {"tool_name": "Edit", "tool_input": {"file_path": source_rel}},
    )
    assert recorded_source_edit.returncode == 0, recorded_source_edit.stderr
    pending = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    assert pending["events"][0]["handler"] == "claude:Edit"
    assert pending["events"][0]["evidence"] == source_rel
    assert pending["events"][0]["task"] == {"id": "42", "slug": "add-cart-button"}

    blocked_second_mutation = _run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "src/another-change.ts"}},
    )
    assert blocked_second_mutation.returncode == 2
    assert "pending S:W:H:E tracking must be logged" in blocked_second_mutation.stderr

    implementation_log = _run_target_aegis_shim(
        target,
        [
            "log",
            "--target-dir",
            ".",
            "--handler",
            "claude:Edit",
            "--evidence",
            source_rel,
            "--note",
            "Added the cart button to the web page",
            "--plan-step",
            "plan-step-implement",
            "--plan-status",
            "completed",
        ],
    )
    assert implementation_log.returncode == 0, implementation_log.stdout + implementation_log.stderr
    implementation_payload = json.loads(implementation_log.stdout)
    assert implementation_payload["status"] == "logged"
    assert implementation_payload["pending"]["cleared"] == 1
    assert implementation_payload["plan"] == {
        "updated": True,
        "step": "plan-step-implement",
        "status": "completed",
        "evidence": source_rel,
    }
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    verify_log = _run_target_aegis_shim(
        target,
        [
            "log",
            "--target-dir",
            ".",
            "--handler",
            "verify:source-inspection",
            "--evidence",
            "cmd`rg \"Add to cart\" src/main.ts`",
            "--note",
            "Verified the cart button source change",
            "--plan-step",
            "plan-step-verify",
            "--plan-status",
            "completed",
        ],
    )
    assert verify_log.returncode == 0, verify_log.stdout + verify_log.stderr

    strict_verify = _run_target_aegis_shim(target, ["verify", "--target-dir", ".", "--strict"])
    assert strict_verify.returncode == 0, strict_verify.stdout + strict_verify.stderr
    strict_payload = json.loads(strict_verify.stdout)
    assert strict_payload["status"] == "passed"
    assert strict_payload["mode"] == "strict"

    strict_verify_log = _run_target_aegis_shim(
        target,
        [
            "log",
            "--target-dir",
            ".",
            "--handler",
            "aegis:verify",
            "--evidence",
            AEGIS_VERIFY_REPORT_REL,
            "--note",
            "Recorded strict verification evidence",
            "--plan-step",
            "plan-step-verify",
            "--plan-status",
            "completed",
        ],
    )
    assert strict_verify_log.returncode == 0, strict_verify_log.stdout + strict_verify_log.stderr

    closeout = _run_target_aegis_shim(target, ["closeout", "--target-dir", ".", "--update-handoff"])
    assert closeout.returncode == 0, closeout.stdout + closeout.stderr
    closeout_payload = json.loads(closeout.stdout)
    assert closeout_payload["status"] == "passed"
    assert closeout_payload["summary"]["failed_required"] == 0
    assert closeout_payload["strict_verify"]["status"] == "passed"
    assert closeout_payload["git"]["legacy_manual_only"] == ["gac"]
    assert "git commit -m \"<type(scope): summary>\"" in closeout_payload["git"]["guidance"]
    assert (target / AEGIS_CLOSEOUT_REPORT_REL).is_file()
    closeout_resource = _read_resource_payload(server, "aegis://closeout/latest")
    assert closeout_resource["ok"] is True
    assert closeout_resource["result"]["payload"]["status"] == "passed"

    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    work_root = target / current_work["paths"]["work_tracking"]
    tracker_text = (work_root / "TRACKER.md").read_text(encoding="utf-8")
    implementation_text = (work_root / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    changelog_text = (work_root / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff_text = (work_root / "HANDOFF.md").read_text(encoding="utf-8")
    findings_text = (work_root / "FINDINGS.md").read_text(encoding="utf-8")
    decisions_text = (work_root / "DECISIONS.md").read_text(encoding="utf-8")

    feature_token = f"|W:task42-add-cart-button|H:claude:Edit|E:{source_rel}]"
    verify_token = "|W:task42-add-cart-button|H:verify:source-inspection|E:cmd`rg \"Add to cart\" src/main.ts`]"
    strict_verify_token = f"|W:task42-add-cart-button|H:aegis:verify|E:{AEGIS_VERIFY_REPORT_REL}]"
    scope_token = (
        f"|W:task42-add-cart-button|H:claude:scope|E:{current_work['paths']['work_tracking']}/FINDINGS.md]"
    )
    for text in (session_text, tracker_text):
        assert scope_token in text
        assert feature_token in text
        assert verify_token in text
        assert strict_verify_token in text
    for text in (implementation_text, changelog_text, handoff_text):
        assert feature_token in text
        assert verify_token in text
        assert strict_verify_token in text
    assert scope_token in findings_text
    assert scope_token in decisions_text
    assert "| plan-step-scope |" in plan_text and "| completed |" in plan_text
    assert f"; {source_rel} | completed |" in plan_text
    assert 'cmd`rg "Add to cart" src/main.ts`' in plan_text
    assert f"{AEGIS_VERIFY_REPORT_REL} | completed |" in plan_text
    assert AEGIS_CLOSEOUT_REPORT_REL in handoff_text
    assert "- [x] plan-step-scope" in tracker_text
    assert "- [x] plan-step-implement" in tracker_text
    assert "- [x] plan-step-verify" in tracker_text

    stop_gate = _run_target_stop_gate(target)
    assert stop_gate.returncode == 0, stop_gate.stderr


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


def test_real_target_project_fixtures_cover_new_and_started_matrix() -> None:
    expected = set(REAL_TARGET_PROJECTS)

    assert {path.name for path in REAL_TARGET_FIXTURE_ROOT.iterdir() if path.is_dir()} == expected
    for fixture_name in expected:
        fixture = REAL_TARGET_FIXTURE_ROOT / fixture_name
        assert (fixture / "README.md").is_file(), fixture_name
        if fixture_name.startswith(("python-", "backend-")):
            assert (fixture / "pyproject.toml").is_file(), fixture_name
        if fixture_name.startswith("web-"):
            assert (fixture / "package.json").is_file(), fixture_name


def test_local_wheel_mcp_real_target_project_smoke_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE") != "1":
        pytest.skip("Set AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1 to run real target-project MCP smoke.")
    uv = shutil.which("uv")
    uvx = shutil.which("uvx")
    if uv is None or uvx is None:
        pytest.skip("uv and uvx are required for the real target-project MCP smoke.")

    dist_dir = tmp_path / "dist"
    targets_root = tmp_path / "targets"

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

        for fixture_name in REAL_TARGET_PROJECTS:
            fixture = REAL_TARGET_FIXTURE_ROOT / fixture_name
            target = targets_root / fixture_name
            shutil.copytree(fixture, target)
            before = _snapshot_files(target)
            _init_git_main(target)

            payloads = asyncio.run(
                _run_wheel_mcp_real_project_flow(
                    uvx=uvx,
                    wheel=wheel,
                    target=target,
                )
            )

            assert payloads["tools"] == set(V1_TOOL_NAMES)
            assert payloads["resources"] == set(RESOURCE_URIS)
            assert payloads["prompts"] == set(PROMPT_NAMES)

            inspect_before = payloads["inspect_before"]
            assert inspect_before["ok"] is True
            assert inspect_before["read_only"] is True
            assert inspect_before["result"]["target_root"] == target.resolve().as_posix()
            assert inspect_before["result"]["aegis"]["installed"] is False

            plan = payloads["plan"]
            assert plan["ok"] is True
            assert plan["read_only"] is True
            assert plan["result"]["mode"] == "dry_run"
            assert plan["result"]["summary"]["creates"] > 0
            assert plan["result"]["summary"]["manual_reviews"] == 0

            refused_install = payloads["refused_install"]
            assert refused_install["ok"] is False
            assert refused_install["error"]["code"] == "apply_required"

            install = payloads["install"]
            assert install["ok"] is True
            assert install["read_only"] is False
            assert install["result"]["status"] == "applied"

            kickoff = payloads["kickoff"]
            assert kickoff["ok"] is True
            assert kickoff["read_only"] is False
            assert kickoff["result"]["status"] == "started"
            assert kickoff["result"]["branch"]["current"] == "feat/task-1-real-target-smoke"

            verify = payloads["verify"]
            assert verify["ok"] is True
            assert verify["read_only"] is False
            assert verify["result"]["status"] == "passed"
            assert verify["result"]["mode"] == "strict"

            scope_log = payloads["scope_log"]
            assert scope_log["ok"] is True
            assert scope_log["result"]["status"] == "logged"
            implementation_log = payloads["implementation_log"]
            assert implementation_log["ok"] is True
            assert implementation_log["result"]["status"] == "logged"
            verify_log = payloads["verify_log"]
            assert verify_log["ok"] is True
            assert verify_log["result"]["status"] == "logged"
            closeout = payloads["closeout"]
            assert closeout["ok"] is True
            assert closeout["result"]["status"] == "passed"
            assert closeout["result"]["summary"]["failed_required"] == 0

            status = payloads["status"]
            assert status["ok"] is True
            assert status["read_only"] is True
            assert status["result"]["status"] == "current"

            manifest = payloads["manifest"]
            assert manifest["ok"] is True
            assert manifest["result"]["payload"]["primary_agent"] == "claude"
            contract = payloads["contract"]
            assert contract["ok"] is True
            assert "Aegis Foundation Contract" in contract["result"]["content"]
            verification = payloads["verification"]
            assert verification["ok"] is True
            assert verification["result"]["payload"]["status"] == "passed"
            work = payloads["work"]
            assert work["ok"] is True
            assert work["result"]["payload"]["task"]["id"] == "1"
            assert work["result"]["payload"]["integrations"]["taskmaster"]["required"] is False
            assert work["result"]["payload"]["integrations"]["serena"]["required"] is False

            readiness = subprocess.run(
                ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--quick", "--root", str(target)],
                cwd=target,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert readiness.returncode == 0, readiness.stdout + readiness.stderr
            assert readiness.stdout.strip().startswith("READY | task=1")

            _assert_snapshot_preserved(target, before)
            assert (target / AEGIS_MANIFEST_REL).is_file()
            assert (target / AEGIS_PLAN_REPORT_REL).is_file()
            assert (target / AEGIS_INSTALL_REPORT_REL).is_file()
            assert (target / AEGIS_VERIFY_REPORT_REL).is_file()
            assert (target / AEGIS_CLOSEOUT_REPORT_REL).is_file()
            assert (target / AEGIS_CURRENT_WORK_REL).is_file()
            verify_report = json.loads(
                (target / AEGIS_VERIFY_REPORT_REL).read_text(encoding="utf-8")
            )
            assert verify_report["status"] == "passed"
            closeout_report = json.loads(
                (target / AEGIS_CLOSEOUT_REPORT_REL).read_text(encoding="utf-8")
            )
            assert closeout_report["status"] == "passed"

            current_work = work["result"]["payload"]
            work_root = target / current_work["paths"]["work_tracking"]
            evidence_rel = f"{current_work['paths']['reports']}/local-wheel-mcp-proof.txt"
            expected_token = f"|W:task1-real-target-smoke|H:wheel-mcp:write|E:{evidence_rel}]"
            for rel_path in (
                current_work["paths"]["session"],
                f"{current_work['paths']['work_tracking']}/TRACKER.md",
                f"{current_work['paths']['work_tracking']}/IMPLEMENTATION.md",
                f"{current_work['paths']['work_tracking']}/CHANGELOG.md",
                f"{current_work['paths']['work_tracking']}/HANDOFF.md",
            ):
                assert expected_token in (target / rel_path).read_text(encoding="utf-8")
            plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
            assert f"; {evidence_rel} | completed |" in plan_text
            assert "- [x] plan-step-scope" in (work_root / "TRACKER.md").read_text(encoding="utf-8")
            assert "- [x] plan-step-implement" in (work_root / "TRACKER.md").read_text(encoding="utf-8")
            assert "- [x] plan-step-verify" in (work_root / "TRACKER.md").read_text(encoding="utf-8")

            source_root_text = REPO_ROOT.as_posix()
            for rel_path in (
                ".aegis/contract.md",
                AEGIS_PLAN_REPORT_REL,
                AEGIS_INSTALL_REPORT_REL,
                AEGIS_VERIFY_REPORT_REL,
                AEGIS_CLOSEOUT_REPORT_REL,
                current_work["paths"]["session"],
                current_work["paths"]["plan"],
                f"{current_work['paths']['work_tracking']}/TRACKER.md",
            ):
                assert source_root_text not in (target / rel_path).read_text(encoding="utf-8")
    finally:
        shutil.rmtree(REPO_ROOT / "aegis_foundation.egg-info", ignore_errors=True)
        shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)
