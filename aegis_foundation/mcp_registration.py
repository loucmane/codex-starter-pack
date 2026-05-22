"""Native MCP client registration helpers for Aegis Foundation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any, Literal, Sequence

from aegis_foundation.version import DISTRIBUTION_NAME, PACKAGE_VERSION


SERVER_NAME = "aegis"
SERVER_COMMAND = "aegis-mcp-server"
DEFAULT_TRANSPORT = "stdio"
DEFAULT_TARGET_DIR = "."
DEFAULT_GITHUB_URL = "https://github.com/loucmane/codex-starter-pack.git"
DEFAULT_UV_CACHE_DIR = ".aegis/uv-cache"
DEFAULT_UV_TOOL_DIR = ".aegis/uv-tools"

ClientName = Literal["claude", "codex"]
SourceMode = Literal["package", "pinned", "github", "wheel", "source"]


@dataclass(frozen=True)
class RegistrationRequest:
    """Inputs required to render or execute a native MCP registration."""

    client: ClientName
    scope: str | None = None
    source_mode: SourceMode = "package"
    package_spec: str | None = None
    package_version: str | None = None
    github_url: str = DEFAULT_GITHUB_URL
    github_ref: str | None = None
    artifact: str | None = None
    target_dir: str = DEFAULT_TARGET_DIR
    transport: str = DEFAULT_TRANSPORT
    uv_cache_dir: str | None = DEFAULT_UV_CACHE_DIR
    uv_tool_dir: str | None = DEFAULT_UV_TOOL_DIR


def shell_join(argv: Sequence[str]) -> str:
    """Return a shell-display string derived from argv for docs and JSON output."""

    return shlex.join(list(argv))


def source_spec(request: RegistrationRequest) -> str:
    """Resolve the uvx --from source spec for the request."""

    if request.package_spec:
        return request.package_spec
    if request.source_mode == "package":
        return DISTRIBUTION_NAME
    if request.source_mode == "pinned":
        version = request.package_version or PACKAGE_VERSION
        return f"{DISTRIBUTION_NAME}=={version}"
    if request.source_mode == "github":
        url = request.github_url
        if not url.startswith("git+"):
            url = f"git+{url}"
        if request.github_ref:
            url = f"{url}@{request.github_ref}"
        return url
    if request.source_mode == "wheel":
        if not request.artifact:
            raise ValueError("--artifact is required for source mode 'wheel'")
        artifact = Path(request.artifact).expanduser().resolve()
        if not artifact.is_file():
            raise ValueError(f"Wheel artifact does not exist: {artifact.as_posix()}")
        if artifact.suffix != ".whl":
            raise ValueError(f"Wheel artifact must end with .whl: {artifact.as_posix()}")
        return artifact.as_posix()
    if request.source_mode == "source":
        if not request.artifact:
            raise ValueError("--artifact is required for source mode 'source'")
        artifact = Path(request.artifact).expanduser().resolve()
        if not artifact.is_dir():
            raise ValueError(f"Source artifact must be an existing directory: {artifact.as_posix()}")
        if not (artifact / "pyproject.toml").is_file():
            raise ValueError(f"Source artifact must contain pyproject.toml: {artifact.as_posix()}")
        return artifact.as_posix()
    raise ValueError(f"Unsupported source mode: {request.source_mode}")


def mcp_server_argv(request: RegistrationRequest) -> list[str]:
    """Build the MCP server argv registered behind the native client."""

    return [
        "uvx",
        "--from",
        source_spec(request),
        SERVER_COMMAND,
        "--default-target-dir",
        request.target_dir,
        "--transport",
        request.transport,
    ]


def client_argv(request: RegistrationRequest) -> list[str]:
    """Build the native client argv for registering the Aegis MCP server."""

    server_args = mcp_server_argv(request)
    env_pairs = registration_env(request)
    if request.client == "claude":
        scope = request.scope or "user"
        return [
            "claude",
            "mcp",
            "add",
            "--scope",
            scope,
            SERVER_NAME,
            *[part for key, value in env_pairs.items() for part in ("-e", f"{key}={value}")],
            "--",
            *server_args,
        ]
    if request.client == "codex":
        return [
            "codex",
            "mcp",
            "add",
            *[part for key, value in env_pairs.items() for part in ("--env", f"{key}={value}")],
            SERVER_NAME,
            "--",
            *server_args,
        ]
    raise ValueError(f"Unsupported native MCP client: {request.client}")


def inspect_argv(client: ClientName) -> list[str]:
    """Build the native client argv used to inspect an existing Aegis registration."""

    if client == "claude":
        return ["claude", "mcp", "get", SERVER_NAME]
    if client == "codex":
        return ["codex", "mcp", "get", "--json", SERVER_NAME]
    raise ValueError(f"Unsupported native MCP client: {client}")


def registration_env(request: RegistrationRequest) -> dict[str, str]:
    """Return environment variables registered with the native MCP client."""

    env: dict[str, str] = {}
    if request.uv_cache_dir:
        env["UV_CACHE_DIR"] = request.uv_cache_dir
    if request.uv_tool_dir:
        env["UV_TOOL_DIR"] = request.uv_tool_dir
    return env


def registration_payload(request: RegistrationRequest) -> dict[str, Any]:
    """Return stable JSON-friendly registration details."""

    server_args = mcp_server_argv(request)
    native_args = client_argv(request)
    return {
        "status": "generated",
        "server": SERVER_NAME,
        "client": request.client,
        "scope": request.scope or ("user" if request.client == "claude" else None),
        "source_mode": request.source_mode,
        "package_spec": source_spec(request),
        "target_dir": request.target_dir,
        "transport": request.transport,
        "environment": registration_env(request),
        "mcp_server_argv": server_args,
        "mcp_server_command": shell_join(server_args),
        "client_argv": native_args,
        "rendered_command": shell_join(native_args),
        "read_only": True,
        "safety_notes": [
            "native-client-registration-is-primary",
            "config-file-writes-are-fallback-only",
            "package-mode-does-not-require-local-source-checkout",
            "uv-cache-and-tool-dir-are-project-local-for-sandboxed-clients",
        ],
    }


def run_native_client(argv: Sequence[str], *, cwd: str | Path = ".") -> dict[str, Any]:
    """Run a native MCP client command with exact argv and structured output."""

    executable = shutil.which(argv[0])
    payload: dict[str, Any] = {
        "argv": list(argv),
        "rendered_command": shell_join(argv),
        "cwd": Path(cwd).as_posix(),
    }
    if executable is None:
        return {
            **payload,
            "status": "missing_client",
            "returncode": 127,
            "stdout": "",
            "stderr": f"Native MCP client not found on PATH: {argv[0]}",
        }
    completed = subprocess.run(
        list(argv),
        cwd=Path(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        **payload,
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def execute_registration(request: RegistrationRequest, *, cwd: str | Path | None = None) -> dict[str, Any]:
    """Execute native client registration and return a structured report."""

    registration = registration_payload(request)
    execution = run_native_client(registration["client_argv"], cwd=cwd or request.target_dir)
    return {
        **registration,
        "read_only": False,
        "execution": execution,
        "status": execution["status"],
    }


def _output_text(stdout: str, stderr: str = "") -> str:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    try:
        parsed = json.loads(combined)
    except json.JSONDecodeError:
        return combined
    return json.dumps(parsed, sort_keys=True)


def verify_registration_output(
    request: RegistrationRequest,
    *,
    stdout: str,
    stderr: str = "",
    returncode: int = 0,
) -> dict[str, Any]:
    """Check native client inspection output for the expected Aegis registration."""

    text = _output_text(stdout, stderr)
    expected_source = source_spec(request)
    checks = [
        {
            "id": "client_inspection_exit",
            "status": "pass" if returncode == 0 else "fail",
            "expected": 0,
            "observed": returncode,
        },
        {
            "id": "server_name",
            "status": "pass" if SERVER_NAME in text else "fail",
            "expected": SERVER_NAME,
        },
        {
            "id": "uvx_command",
            "status": "pass" if "uvx" in text else "fail",
            "expected": "uvx",
        },
        {
            "id": "source_spec",
            "status": "pass" if expected_source in text else "fail",
            "expected": expected_source,
        },
        {
            "id": "server_command",
            "status": "pass" if SERVER_COMMAND in text else "fail",
            "expected": SERVER_COMMAND,
        },
        {
            "id": "default_target_dir",
            "status": "pass" if "--default-target-dir" in text and request.target_dir in text else "fail",
            "expected": request.target_dir,
        },
        {
            "id": "transport",
            "status": "pass" if "--transport" in text and request.transport in text else "fail",
            "expected": request.transport,
        },
    ]
    for key, value in registration_env(request).items():
        checks.append(
            {
                "id": f"env_{key.lower()}",
                "status": "pass" if key in text and value in text else "fail",
                "expected": f"{key}={value}",
            }
        )
    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "status": "passed" if not failed else "failed",
        "client": request.client,
        "server": SERVER_NAME,
        "package_spec": expected_source,
        "checks": checks,
        "failed_required": len(failed),
        "inspection_output": text,
    }


def verify_registration(request: RegistrationRequest, *, cwd: str | Path | None = None) -> dict[str, Any]:
    """Inspect a native MCP client registration and verify the Aegis command."""

    argv = inspect_argv(request.client)
    execution = run_native_client(argv, cwd=cwd or request.target_dir)
    if execution["status"] == "missing_client":
        return {
            "status": "missing_client",
            "client": request.client,
            "server": SERVER_NAME,
            "inspection": execution,
            "expected_registration": registration_payload(request),
        }
    verification = verify_registration_output(
        request,
        stdout=execution["stdout"],
        stderr=execution["stderr"],
        returncode=execution["returncode"],
    )
    return {
        **verification,
        "inspection": execution,
        "expected_registration": registration_payload(request),
    }
