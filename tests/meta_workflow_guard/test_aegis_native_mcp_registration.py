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
                source_mode="private-github",
                github_ref="main",
            ),
            "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main",
        ),
        (
            mcp_registration.RegistrationRequest(
                client="codex",
                source_mode="private-github",
                github_url="git@github.com:loucmane/codex-starter-pack.git",
                github_ref="task-134",
            ),
            "git+ssh://git@github.com/loucmane/codex-starter-pack.git@task-134",
        ),
        (
            mcp_registration.RegistrationRequest(client="claude", source_mode="package"),
            "aegis-foundation",
        ),
    ],
)
def test_package_registration_source_modes_resolve_uvx_from_spec(
    registration_request: mcp_registration.RegistrationRequest,
    expected: str,
) -> None:
    payload = mcp_registration.registration_payload(registration_request)

    assert payload["package_spec"] == expected
    assert payload["mcp_server_argv"][0:3] == ["uvx", "--from", expected]
    assert "aegis-mcp-server" in payload["mcp_server_argv"]


def test_private_github_registration_command_uses_native_auth_source() -> None:
    payload = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(
            client="codex",
            source_mode="private-github",
            github_ref="main",
        )
    )

    assert payload["package_spec"] == "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main"
    assert payload["rendered_command"] == (
        "codex mcp add --env UV_CACHE_DIR=.aegis/uv-cache "
        "--env UV_TOOL_DIR=.aegis/uv-tools aegis -- uvx --from "
        "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main "
        "aegis-mcp-server --default-target-dir . --transport stdio"
    )
    assert "private-github-requires-native-git-auth" in payload["safety_notes"]


def test_local_wheel_and_source_modes_resolve_absolute_uvx_from_spec(tmp_path: Path) -> None:
    wheel = tmp_path / "dist" / "aegis_foundation-0.1.0-py3-none-any.whl"
    wheel.parent.mkdir()
    wheel.write_bytes(b"placeholder wheel for registration path validation")
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text("[project]\nname = 'aegis-foundation'\n", encoding="utf-8")

    wheel_payload = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(
            client="claude",
            source_mode="wheel",
            artifact=str(wheel),
        )
    )
    source_payload = mcp_registration.registration_payload(
        mcp_registration.RegistrationRequest(
            client="claude",
            source_mode="source",
            artifact=str(source),
        )
    )

    assert wheel_payload["package_spec"] == wheel.resolve().as_posix()
    assert source_payload["package_spec"] == source.resolve().as_posix()
    assert wheel_payload["mcp_server_argv"][0:3] == ["uvx", "--from", wheel.resolve().as_posix()]
    assert source_payload["mcp_server_argv"][0:3] == ["uvx", "--from", source.resolve().as_posix()]


def test_wheel_and_source_modes_require_artifact() -> None:
    with pytest.raises(ValueError, match="--artifact is required"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(client="claude", source_mode="wheel")
        )

    with pytest.raises(ValueError, match="--artifact is required"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(client="claude", source_mode="source")
        )


def test_local_modes_validate_artifact_shape(tmp_path: Path) -> None:
    missing_wheel = tmp_path / "missing.whl"
    source_without_pyproject = tmp_path / "source"
    source_without_pyproject.mkdir()
    wrong_extension = tmp_path / "aegis_foundation-0.1.0.zip"
    wrong_extension.write_bytes(b"not a wheel")

    with pytest.raises(ValueError, match="Wheel artifact does not exist"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="wheel",
                artifact=str(missing_wheel),
            )
        )
    with pytest.raises(ValueError, match="Wheel artifact must end with .whl"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="wheel",
                artifact=str(wrong_extension),
            )
        )
    with pytest.raises(ValueError, match="Source artifact must contain pyproject.toml"):
        mcp_registration.registration_payload(
            mcp_registration.RegistrationRequest(
                client="claude",
                source_mode="source",
                artifact=str(source_without_pyproject),
            )
        )


def test_execute_registration_reports_missing_native_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(mcp_registration.shutil, "which", lambda name, path=None: None)

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
    monkeypatch.setattr(mcp_registration.shutil, "which", lambda name, path=None: f"/bin/{name}")

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
    assert captured["kwargs"]["env"] is None
    assert "shell" not in captured["kwargs"]


def test_execute_registration_honors_environment_path_for_client_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_which(name: str, *, path: str | None = None) -> str | None:
        captured["which"] = {"name": name, "path": path}
        return f"/isolated/bin/{name}"

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["run"] = {"argv": argv, "kwargs": kwargs}
        return subprocess.CompletedProcess(argv, 0, "registered\n", "")

    monkeypatch.setattr(mcp_registration.shutil, "which", fake_which)
    monkeypatch.setattr(mcp_registration.subprocess, "run", fake_run)

    env = {"PATH": "/isolated/bin", "HOME": "/tmp/smoke/home"}
    payload = mcp_registration.execute_registration(
        mcp_registration.RegistrationRequest(client="codex"),
        env=env,
    )

    assert payload["status"] == "passed"
    assert captured["which"] == {"name": "codex", "path": "/isolated/bin"}
    assert captured["run"]["kwargs"]["env"] == env


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


def test_verify_registration_output_passes_for_private_github_source() -> None:
    request = mcp_registration.RegistrationRequest(
        client="codex",
        source_mode="private-github",
        github_ref="main",
    )
    stdout = json.dumps(
        {
            "name": "aegis",
            "command": "uvx",
            "args": [
                "--from",
                "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main",
                "aegis-mcp-server",
                "--default-target-dir",
                ".",
                "--transport",
                "stdio",
            ],
            "env": {
                "UV_CACHE_DIR": ".aegis/uv-cache",
                "UV_TOOL_DIR": ".aegis/uv-tools",
            },
        }
    )

    payload = mcp_registration.verify_registration_output(request, stdout=stdout)

    assert payload["status"] == "passed"
    assert payload["failed_required"] == 0


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


def test_package_cli_generates_private_github_registration_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = aegis_cli.main(
        [
            "mcp",
            "generate-registration",
            "--client",
            "claude",
            "--scope",
            "user",
            "--source-mode",
            "private-github",
            "--github-ref",
            "main",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["package_spec"] == "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main"
    assert payload["rendered_command"].startswith("claude mcp add --scope user aegis -e")
    assert "private-github-requires-native-git-auth" in payload["safety_notes"]


def test_package_cli_public_register_delegates_to_native_registration(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request: dict[str, Any] = {}

    def fake_execute(request: mcp_registration.RegistrationRequest, *, cwd: str | Path | None = None) -> dict[str, Any]:
        captured_request["request"] = request
        captured_request["cwd"] = cwd
        return {
            "status": "passed",
            "client": request.client,
            "scope": request.scope,
            "source_mode": request.source_mode,
            "target_dir": request.target_dir,
        }

    monkeypatch.setattr(aegis_cli.mcp_registration, "execute_registration", fake_execute)

    result = aegis_cli.main(["mcp", "register", "claude"])

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"
    assert payload["client"] == "claude"
    assert payload["scope"] == "user"
    request = captured_request["request"]
    assert request.client == "claude"
    assert request.scope == "user"
    assert request.source_mode == "package"
    assert request.target_dir == "."
    assert captured_request["cwd"] == "."


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


def test_repo_wrapper_generates_private_github_registration_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/codex-task",
            "aegis",
            "mcp",
            "generate-registration",
            "--client",
            "codex",
            "--source-mode",
            "private-github",
            "--github-ref",
            "main",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["package_spec"] == "git+ssh://git@github.com/loucmane/codex-starter-pack.git@main"


def test_repo_wrapper_smoke_registration_with_missing_clients_returns_structured_skip(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/codex-task",
            "aegis",
            "mcp",
            "smoke-registration",
            "--client",
            "codex",
            "--smoke-root",
            str(tmp_path / "smoke"),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": ""},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "skipped"
    assert payload["clients"][0]["client"] == "codex"
    assert payload["clients"][0]["status"] == "missing_client"


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


def _write_fake_smoke_client(bin_dir: Path, name: str) -> Path:
    script = bin_dir / name
    script.write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

record_dir = Path(os.environ["AEGIS_FAKE_MCP_RECORD_DIR"])
record_dir.mkdir(parents=True, exist_ok=True)
client = Path(sys.argv[0]).name
args = sys.argv[1:]
record_name = f"{client}-{'-'.join(args[0:2]) if len(args) >= 2 else 'unknown'}.json"
record = {
    "client": client,
    "argv": args,
    "cwd": os.getcwd(),
    "env": {
        key: os.environ[key]
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR")
        if key in os.environ
    },
}
(record_dir / record_name).write_text(json.dumps(record, sort_keys=True), encoding="utf-8")

if len(args) >= 3 and args[0:2] == ["mcp", "add"]:
    print("registered aegis")
    raise SystemExit(0)

if len(args) >= 3 and args[0:2] == ["mcp", "get"]:
    source = os.environ["AEGIS_FAKE_SOURCE_SPEC"]
    print(json.dumps({
        "name": "aegis",
        "command": "uvx",
        "args": ["--from", source, "aegis-mcp-server", "--default-target-dir", ".", "--transport", "stdio"],
        "env": {"UV_CACHE_DIR": ".aegis/uv-cache", "UV_TOOL_DIR": ".aegis/uv-tools"},
    }))
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


def test_smoke_registration_uses_isolated_homes_for_fake_clients(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_smoke_client(bin_dir, "codex")
    _write_fake_smoke_client(bin_dir, "claude")
    record_dir = tmp_path / "records"
    smoke_root = tmp_path / "smoke"
    request = mcp_registration.RegistrationRequest(
        client="codex",
        source_mode="private-github",
        github_ref="aegis-private-github-20260531",
    )
    source = mcp_registration.source_spec(request)
    parent_env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "HOME": "/real/home/should-not-be-used",
        "CODEX_HOME": "/real/codex/should-not-be-used",
        "AEGIS_FAKE_MCP_RECORD_DIR": record_dir.as_posix(),
        "AEGIS_FAKE_SOURCE_SPEC": source,
    }

    payload = mcp_registration.smoke_registration(
        request,
        smoke_root=smoke_root,
        keep_temp=True,
        parent_env=parent_env,
    )

    assert payload["status"] == "passed"
    assert payload["package_spec"] == source
    assert payload["temp_cleaned"] is False
    assert {result["client"]: result["status"] for result in payload["clients"]} == {
        "claude": "passed",
        "codex": "passed",
    }
    codex_add = json.loads((record_dir / "codex-mcp-add.json").read_text(encoding="utf-8"))
    claude_add = json.loads((record_dir / "claude-mcp-add.json").read_text(encoding="utf-8"))
    assert codex_add["env"]["HOME"].startswith(smoke_root.as_posix())
    assert codex_add["env"]["CODEX_HOME"].startswith(smoke_root.as_posix())
    assert Path(codex_add["env"]["CODEX_HOME"]).is_dir()
    assert claude_add["env"]["HOME"].startswith(smoke_root.as_posix())
    assert "CODEX_HOME" not in claude_add["env"]
    assert "/real/" not in json.dumps(codex_add)
    assert "/real/" not in json.dumps(claude_add)
    for result in payload["clients"]:
        assert result["environment"]["all_paths_under_smoke_root"] is True
        assert "real-user-config-not-touched" in result["safety_notes"]


def test_smoke_registration_missing_clients_skips_cleanly(tmp_path: Path) -> None:
    payload = mcp_registration.smoke_registration(
        mcp_registration.RegistrationRequest(client="codex"),
        smoke_root=tmp_path / "smoke",
        parent_env={"PATH": ""},
    )

    assert payload["status"] == "skipped"
    assert {result["status"] for result in payload["clients"]} == {"missing_client"}
    assert all(result["registration"]["status"] == "missing_client" for result in payload["clients"])


def test_smoke_registration_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    payload = {
        "status": "passed",
        "source_mode": "private-github",
        "package_spec": "git+ssh://example/repo.git@tag",
        "smoke_root": (tmp_path / "smoke").as_posix(),
        "temp_cleaned": True,
        "clients": [
            {
                "client": "codex",
                "status": "passed",
                "environment": {"home": "/tmp/home", "work_dir": "/tmp/work"},
                "registration": {"status": "passed"},
                "verification": {"status": "passed"},
            }
        ],
    }
    report = tmp_path / "reports" / "smoke.json"
    markdown = tmp_path / "reports" / "smoke.md"

    mcp_registration.write_smoke_reports(payload, report_file=report, markdown_report_file=markdown)

    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "passed"
    assert "# Aegis Native MCP Registration Smoke" in markdown.read_text(encoding="utf-8")


def test_package_cli_smoke_registration_writes_reports(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}

    def fake_smoke(
        request: mcp_registration.RegistrationRequest,
        *,
        clients: tuple[mcp_registration.ClientName, ...],
        smoke_root: str | Path | None = None,
        keep_temp: bool = False,
    ) -> dict[str, Any]:
        captured.update(
            {
                "request": request,
                "clients": clients,
                "smoke_root": smoke_root,
                "keep_temp": keep_temp,
            }
        )
        return {
            "status": "passed",
            "source_mode": request.source_mode,
            "package_spec": mcp_registration.source_spec(request),
            "smoke_root": str(smoke_root),
            "temp_cleaned": not keep_temp,
            "clients": [],
        }

    monkeypatch.setattr(aegis_cli.mcp_registration, "smoke_registration", fake_smoke)
    report = tmp_path / "smoke.json"
    markdown = tmp_path / "smoke.md"

    result = aegis_cli.main(
        [
            "mcp",
            "smoke-registration",
            "--client",
            "codex",
            "--source-mode",
            "private-github",
            "--github-ref",
            "main",
            "--smoke-root",
            str(tmp_path / "root"),
            "--keep-temp",
            "--report-file",
            str(report),
            "--markdown-report-file",
            str(markdown),
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"
    assert captured["clients"] == ("codex",)
    assert captured["request"].source_mode == "private-github"
    assert captured["request"].github_ref == "main"
    assert captured["keep_temp"] is True
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "passed"
    assert markdown.read_text(encoding="utf-8").startswith("# Aegis Native MCP Registration Smoke")
