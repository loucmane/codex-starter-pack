"""Native MCP client registration coverage for Aegis Foundation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_foundation import mcp_registration


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_claude_user_registration_command_uses_native_mcp_add() -> None:
    payload = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(client="claude", scope="user")
    )

    assert payload["client_argv"] == [
        "claude",
        "mcp",
        "add",
        "--scope",
        "user",
        "aegis",
        "-e",
        "UV_CACHE_DIR=.aegis/uv-cache",
        "-e",
        "UV_TOOL_DIR=.aegis/uv-tools",
        "--",
        "uvx",
        "--from",
        "aegis-foundation",
        "aegis-mcp-server",
        "--default-target-dir",
        ".",
        "--transport",
        "stdio",
    ]
    assert payload["rendered_command"] == (
        "claude mcp add --scope user aegis -e UV_CACHE_DIR=.aegis/uv-cache "
        "-e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation "
        "aegis-mcp-server --default-target-dir . --transport stdio"
    )
    assert payload["environment"] == {
        "UV_CACHE_DIR": ".aegis/uv-cache",
        "UV_TOOL_DIR": ".aegis/uv-tools",
    }
    assert payload["read_only"] is True
    assert "config-file-writes-are-fallback-only" in payload["safety_notes"]


def test_claude_project_and_codex_registration_commands_match_native_syntax() -> None:
    claude = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(client="claude", scope="project")
    )
    codex = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(client="codex")
    )

    assert claude["rendered_command"] == (
        "claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache "
        "-e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation "
        "aegis-mcp-server --default-target-dir . --transport stdio"
    )
    assert codex["client_argv"] == [
        "codex",
        "mcp",
        "add",
        "--env",
        "UV_CACHE_DIR=.aegis/uv-cache",
        "--env",
        "UV_TOOL_DIR=.aegis/uv-tools",
        "aegis",
        "--",
        "uvx",
        "--from",
        "aegis-foundation",
        "aegis-mcp-server",
        "--default-target-dir",
        ".",
        "--transport",
        "stdio",
    ]
    assert codex["rendered_command"] == (
        "codex mcp add --env UV_CACHE_DIR=.aegis/uv-cache "
        "--env UV_TOOL_DIR=.aegis/uv-tools aegis -- uvx --from aegis-foundation "
        "aegis-mcp-server --default-target-dir . --transport stdio"
    )


@pytest.mark.parametrize(
    ("registration_request", "expected"),
    [
        (
            mcp_registration.RegistrationRequest(client="claude", source_mode="pinned"),
            "aegis-foundation==0.1.0",
        ),
        (
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="pinned",
                package_version="0.2.0",
            ),
            "aegis-foundation==0.2.0",
        ),
        (
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="github",
                github_ref="v0.1.0",
            ),
            "git+https://github.com/loucmane/codex-starter-pack.git@v0.1.0",
        ),
        (
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="wheel",
                artifact="./dist/aegis_foundation-0.1.0-py3-none-any.whl",
            ),
            "./dist/aegis_foundation-0.1.0-py3-none-any.whl",
        ),
        (
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="source",
                artifact="/workspace/codex",
            ),
            "/workspace/codex",
        ),
    ],
)
def test_registration_source_modes_resolve_uvx_from_spec(
    registration_request: mcp_registration.RegistrationRequest,
    expected: str,
) -> None:
    payload = mcp_registration.registration_payload(registration_request)

    assert payload["package_spec"] == expected
    assert payload["mcp_server_argv"][0:3] == ["uvx", "--from", expected]
    assert "aegis-mcp-server" in payload["mcp_server_argv"]


def test_wheel_and_source_modes_require_artifact() -> None:
    with pytest.raises(ValueError, match="--artifact is required"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(client="claude", source_mode="wheel")
        )


def test_execute_registration_reports_missing_native_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(mcp_registration.shutil, "which", lambda name: None)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(args[0]))
        return subprocess.CompletedProcess(args[0], 0, "", "")

    monkeypatch.setattr(mcp_registration.subprocess, "run", fake_run)

    payload = mcp_registration.execute_registration(
        mcp_registration.RegistrationRequest(client="claude"),
        cwd="/tmp/project",
    )

    assert payload["status"] == "missing_client"
    assert payload["execution"]["returncode"] == 127
    assert payload["execution"]["argv"][0:3] == ["claude", "mcp", "add"]
    assert calls == []


def test_execute_registration_runs_exact_argv_without_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(mcp_registration.shutil, "which", lambda name: f"/bin/{name}")

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, "registered\n", "")

    monkeypatch.setattr(mcp_registration.subprocess, "run", fake_run)
    request = mcp_registration.RegistrationRequest(client="codex", target_dir="/tmp/project")

    payload = mcp_registration.execute_registration(request)

    assert payload["status"] == "passed"
    assert captured["argv"] == payload["client_argv"]
    assert captured["kwargs"]["cwd"] == Path("/tmp/project")
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["stdout"] is subprocess.PIPE
    assert captured["kwargs"]["stderr"] is subprocess.PIPE
    assert captured["kwargs"]["check"] is False
    assert "shell" not in captured["kwargs"]


def test_verify_registration_output_passes_for_claude_text() -> None:
    request = mcp_registration.RegistrationRequest(client="claude", scope="user")
    stdout = (
        "aegis\n"
        "command: uvx\n"
        "args: --from aegis-foundation aegis-mcp-server "
        "--default-target-dir . --transport stdio\n"
        "UV_CACHE_DIR=.aegis/uv-cache\n"
        "UV_TOOL_DIR=.aegis/uv-tools\n"
    )

    payload = mcp_registration.verify_registration_output(request, stdout=stdout)

    assert payload["status"] == "passed"
    assert payload["failed_required"] == 0


def test_verify_registration_output_fails_wrong_source_and_transport() -> None:
    request = mcp_registration.RegistrationRequest(client="codex")
    stdout = json.dumps(
        {
            "name": "aegis",
            "command": "uvx",
            "args": [
                "--from",
                "other-package",
                "aegis-mcp-server",
                "--default-target-dir",
                ".",
                "--transport",
                "sse",
            ],
        }
    )

    payload = mcp_registration.verify_registration_output(request, stdout=stdout)
    failed_ids = {check["id"] for check in payload["checks"] if check["status"] == "fail"}

    assert payload["status"] == "failed"
    assert {"source_spec", "transport"} <= failed_ids


def test_package_cli_generates_native_registration_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = aegis_cli.main(
        [
            "mcp",
            "generate-registration",
            "--client",
            "claude",
            "--scope",
            "project",
            "--source-mode",
            "pinned",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["package_spec"] == "aegis-foundation==0.1.0"
    assert payload["rendered_command"].startswith("claude mcp add --scope project aegis -e")


def test_package_cli_reports_invalid_source_mode_without_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = aegis_cli.main(
        [
            "mcp",
            "generate-registration",
            "--client",
            "claude",
            "--source-mode",
            "wheel",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "--artifact is required" in captured.err
    assert "Traceback" not in captured.err


def test_repo_wrapper_generates_native_registration_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/codex-task",
            "aegis",
            "mcp",
            "generate-registration",
            "--client",
            "codex",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["rendered_command"] == (
        "codex mcp add --env UV_CACHE_DIR=.aegis/uv-cache "
        "--env UV_TOOL_DIR=.aegis/uv-tools aegis -- uvx --from aegis-foundation "
        "aegis-mcp-server --default-target-dir . --transport stdio"
    )


def _write_fake_native_client(bin_dir: Path, name: str) -> Path:
    script = bin_dir / name
    script.write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

record = Path(os.environ["AEGIS_FAKE_MCP_RECORD"])
payload = {"client": Path(sys.argv[0]).name, "argv": sys.argv[1:], "cwd": os.getcwd()}
record.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

args = sys.argv[1:]
if len(args) >= 3 and args[0:2] == ["mcp", "add"]:
    print("registered aegis")
    raise SystemExit(0)
if len(args) >= 3 and args[0:2] == ["mcp", "get"]:
    print("aegis")
    print("command: uvx")
    print("args: --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio")
    print("UV_CACHE_DIR=.aegis/uv-cache")
    print("UV_TOOL_DIR=.aegis/uv-tools")
    raise SystemExit(0)

print("unsupported fake client invocation", file=sys.stderr)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


@pytest.mark.parametrize(
    ("client", "expected_prefix"),
    [
        (
            "claude",
            [
                "mcp",
                "add",
                "--scope",
                "user",
                "aegis",
                "-e",
                "UV_CACHE_DIR=.aegis/uv-cache",
                "-e",
                "UV_TOOL_DIR=.aegis/uv-tools",
                "--",
            ],
        ),
        (
            "codex",
            [
                "mcp",
                "add",
                "--env",
                "UV_CACHE_DIR=.aegis/uv-cache",
                "--env",
                "UV_TOOL_DIR=.aegis/uv-tools",
                "aegis",
                "--",
            ],
        ),
    ],
)
def test_native_registration_execute_and_verify_with_fake_client_on_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: mcp_registration.ClientName,
    expected_prefix: list[str],
) -> None:
    target = tmp_path / "fresh-project"
    target.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_native_client(bin_dir, client)
    record = tmp_path / "native-client-record.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("AEGIS_FAKE_MCP_RECORD", record.as_posix())

    request = mcp_registration.RegistrationRequest(client=client, target_dir=".")
    execute = mcp_registration.execute_registration(request, cwd=target)

    assert execute["status"] == "passed"
    add_record = json.loads(record.read_text(encoding="utf-8"))
    assert add_record["argv"][: len(expected_prefix)] == expected_prefix
    assert add_record["cwd"] == target.as_posix()

    verify = mcp_registration.verify_registration(request, cwd=target)

    assert verify["status"] == "passed"
    assert verify["failed_required"] == 0
    get_record = json.loads(record.read_text(encoding="utf-8"))
    assert get_record["argv"][0:2] == ["mcp", "get"]
