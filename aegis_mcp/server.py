"""MCP server scaffold for Aegis Foundation.

Task 110 keeps protocol wiring in this package and deterministic install behavior in
``scripts._aegis_installer``. Later subtasks register tools, resources, and prompts against
the server returned by ``create_server``.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Sequence

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from scripts import _aegis_installer


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_NAME = "Aegis Foundation"
ProfileName = Literal["generic"]
PrimaryAgentName = Literal["claude", "codex", "gemini", "multi", "none"]
AgentName = Literal["claude", "codex", "gemini"]
AgentList = Annotated[list[AgentName], Field(json_schema_extra={"uniqueItems": True})]
V1_TOOL_NAMES = (
    "aegis.inspect",
    "aegis.plan_install",
    "aegis.install",
    "aegis.verify",
    "aegis.list_profiles",
    "aegis.explain_profile",
)


class AegisMCPInputError(ValueError):
    """Raised when MCP inputs fail Aegis V1 safety constraints."""


@dataclass(frozen=True)
class AegisMCPConfig:
    """Runtime configuration for the Aegis MCP server."""

    source_root: Path
    default_target_dir: Path

    @classmethod
    def from_paths(
        cls,
        *,
        source_root: str | Path | None = None,
        default_target_dir: str | Path | None = None,
    ) -> "AegisMCPConfig":
        """Create normalized server configuration from optional path inputs."""

        resolved_source = Path(
            source_root or os.environ.get("AEGIS_SOURCE_ROOT") or REPO_ROOT
        ).expanduser().resolve()
        resolved_target = Path(
            default_target_dir
            or os.environ.get("AEGIS_DEFAULT_TARGET_DIR")
            or resolved_source
        ).expanduser().resolve()
        return cls(source_root=resolved_source, default_target_dir=resolved_target)

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-friendly representation for diagnostics and tests."""

        return {
            "source_root": self.source_root.as_posix(),
            "default_target_dir": self.default_target_dir.as_posix(),
        }


def create_server(config: AegisMCPConfig | None = None) -> FastMCP:
    """Create the Aegis MCP server without starting a transport."""

    resolved_config = config or AegisMCPConfig.from_paths()
    server = FastMCP(SERVER_NAME, json_response=True)
    server.aegis_config = resolved_config  # type: ignore[attr-defined]
    server.aegis_installer = _aegis_installer  # type: ignore[attr-defined]
    return register_v1_tools(server)


def _validate_profile(profile: str) -> str:
    if profile != _aegis_installer.PROFILE_GENERIC:
        raise AegisMCPInputError(f"Unsupported Aegis profile in V1: {profile}")
    return profile


def _validate_unique_agents(agents: Sequence[str]) -> tuple[str, ...]:
    unknown = sorted(set(agents) - _aegis_installer.AGENT_CHOICES)
    if unknown:
        raise AegisMCPInputError(f"Unsupported enabled agent(s): {', '.join(unknown)}")
    deduped = tuple(dict.fromkeys(agents))
    if len(deduped) != len(tuple(agents)):
        raise AegisMCPInputError("agents must be unique")
    return deduped


def _validate_agent_selection(
    *,
    primary_agent: str,
    agents: Sequence[str],
) -> tuple[str, ...]:
    if primary_agent not in _aegis_installer.PRIMARY_AGENT_CHOICES:
        raise AegisMCPInputError(f"Unsupported primary agent: {primary_agent}")
    selected = _validate_unique_agents(agents)
    if primary_agent == "none":
        if selected:
            raise AegisMCPInputError("primary_agent=none cannot be combined with enabled agents")
        return ()
    if not selected:
        raise AegisMCPInputError("Aegis install requires at least one explicit agent")
    if primary_agent == "multi" and len(selected) < 2:
        raise AegisMCPInputError("primary_agent=multi requires at least two enabled agents")
    if primary_agent in _aegis_installer.AGENT_CHOICES and primary_agent not in selected:
        raise AegisMCPInputError(
            f"primary_agent={primary_agent} must also be listed in agents"
        )
    return selected


def _require_true(value: bool, field: str) -> None:
    if value is not True:
        raise AegisMCPInputError(f"{field} must be true for this Aegis MCP operation")


def _deferred_tool_response(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _aegis_installer.SCHEMA_VERSION,
        "tool": tool_name,
        "status": "handler_deferred",
        "message": "Input schema and safety validation passed; core handler wiring is owned by Task 110.3.",
        "validated_arguments": arguments,
    }


def register_v1_tools(server: FastMCP) -> FastMCP:
    """Register the V1-backed Aegis tool contracts on a FastMCP server."""

    @server.tool(name="aegis.inspect")
    def aegis_inspect(
        target_dir: str,
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Inspect a target project for Aegis installation state."""

        profile_value = _validate_profile(profile)
        return _deferred_tool_response(
            "aegis.inspect",
            {
                "target_dir": target_dir,
                "profile": profile_value,
            },
        )

    @server.tool(name="aegis.plan_install")
    def aegis_plan_install(
        target_dir: str,
        primary_agent: PrimaryAgentName,
        agents: AgentList,
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Plan a deterministic Aegis installation without mutating the target."""

        profile_value = _validate_profile(profile)
        selected = _validate_agent_selection(primary_agent=primary_agent, agents=agents)
        return _deferred_tool_response(
            "aegis.plan_install",
            {
                "target_dir": target_dir,
                "profile": profile_value,
                "primary_agent": primary_agent,
                "agents": list(selected),
            },
        )

    @server.tool(name="aegis.install")
    def aegis_install(
        target_dir: str,
        profile: ProfileName,
        primary_agent: PrimaryAgentName,
        agents: AgentList,
        apply: bool,
    ) -> dict[str, Any]:
        """Apply an Aegis installation after explicit apply confirmation."""

        profile_value = _validate_profile(profile)
        selected = _validate_agent_selection(primary_agent=primary_agent, agents=agents)
        _require_true(apply, "apply")
        return _deferred_tool_response(
            "aegis.install",
            {
                "target_dir": target_dir,
                "profile": profile_value,
                "primary_agent": primary_agent,
                "agents": list(selected),
                "apply": apply,
            },
        )

    @server.tool(name="aegis.verify")
    def aegis_verify(
        target_dir: str,
        acknowledge_report_write: bool,
    ) -> dict[str, Any]:
        """Verify an Aegis installation after acknowledging report writes."""

        _require_true(acknowledge_report_write, "acknowledge_report_write")
        return _deferred_tool_response(
            "aegis.verify",
            {
                "target_dir": target_dir,
                "acknowledge_report_write": acknowledge_report_write,
            },
        )

    @server.tool(name="aegis.list_profiles")
    def aegis_list_profiles() -> dict[str, Any]:
        """List Aegis install profiles supported by the V1 installer."""

        return _deferred_tool_response("aegis.list_profiles", {})

    @server.tool(name="aegis.explain_profile")
    def aegis_explain_profile(
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Explain the built-in Aegis install profile."""

        profile_value = _validate_profile(profile)
        return _deferred_tool_response(
            "aegis.explain_profile",
            {
                "profile": profile_value,
            },
        )

    return server


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the stdio entrypoint parser."""

    parser = argparse.ArgumentParser(description="Run the Aegis Foundation MCP server.")
    parser.add_argument(
        "--source-root",
        help="Path to the Aegis foundation source repository; defaults to this repository.",
    )
    parser.add_argument(
        "--default-target-dir",
        help="Default target directory for read-only operations; mutating tools still require explicit targets.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default="stdio",
        help="MCP transport to run; stdio is the project-local default.",
    )
    parser.add_argument(
        "--describe-config",
        action="store_true",
        help="Print resolved configuration as JSON and exit without starting the server.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Aegis MCP server entrypoint."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)
    config = AegisMCPConfig.from_paths(
        source_root=args.source_root,
        default_target_dir=args.default_target_dir,
    )
    if args.describe_config:
        print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
        return 0
    create_server(config).run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
