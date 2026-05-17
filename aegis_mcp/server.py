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

from jsonschema import ValidationError
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from aegis_foundation.resources import packaged_asset_root_path
from scripts import _aegis_installer


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_NAME = "Aegis Foundation"
COMPATIBILITY_MATRIX_REL = "templates/registry/agent-compatibility-matrix.json"
ProfileName = Literal["generic"]
PrimaryAgentName = Literal["claude", "codex", "gemini", "multi", "none"]
AgentName = Literal["claude", "codex", "gemini"]
AgentList = Annotated[list[AgentName], Field(json_schema_extra={"uniqueItems": True})]
V1_TOOL_NAMES = (
    "aegis.inspect",
    "aegis.status",
    "aegis.plan_install",
    "aegis.install",
    "aegis.verify",
    "aegis.list_profiles",
    "aegis.explain_profile",
)
RESOURCE_URIS = (
    "aegis://manifest/current",
    "aegis://contract/current",
    "aegis://schemas/foundation-manifest",
    "aegis://schemas/profile",
    "aegis://schemas/install-plan",
    "aegis://profiles",
    "aegis://install-plan/latest",
    "aegis://verification/latest",
    "aegis://limitations",
    "aegis://managed-files",
)
PROMPT_NAMES = (
    "aegis.bootstrap_new_project",
    "aegis.migrate_existing_project",
    "aegis.verify_runtime",
    "aegis.prepare_agent_session",
    "aegis.close_agent_session",
)


class AegisMCPInputError(ValueError):
    """Raised when MCP inputs fail Aegis V1 safety constraints."""


@dataclass(frozen=True)
class AegisMCPConfig:
    """Runtime configuration for the Aegis MCP server."""

    source_root: Path
    default_target_dir: Path
    asset_origin: str = "source"

    @classmethod
    def from_paths(
        cls,
        *,
        source_root: str | Path | None = None,
        default_target_dir: str | Path | None = None,
    ) -> "AegisMCPConfig":
        """Create normalized server configuration from optional path inputs."""

        env_source_root = os.environ.get("AEGIS_SOURCE_ROOT")
        configured_source = source_root or env_source_root
        resolved_source = (
            Path(configured_source).expanduser().resolve()
            if configured_source
            else packaged_asset_root_path()
        )
        asset_origin = "source" if configured_source else "package"
        resolved_target = Path(
            default_target_dir
            or os.environ.get("AEGIS_DEFAULT_TARGET_DIR")
            or "."
        ).expanduser().resolve()
        return cls(
            source_root=resolved_source,
            default_target_dir=resolved_target,
            asset_origin=asset_origin,
        )

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-friendly representation for diagnostics and tests."""

        return {
            "distribution_name": "aegis-foundation",
            "asset_origin": self.asset_origin,
            "foundation_version": _aegis_installer.FOUNDATION_VERSION,
            "installer_version": _aegis_installer.INSTALLER_VERSION,
            "schema_version": _aegis_installer.SCHEMA_VERSION,
            "source_root": self.source_root.as_posix(),
            "default_target_dir": self.default_target_dir.as_posix(),
        }


def create_server(config: AegisMCPConfig | None = None) -> FastMCP:
    """Create the Aegis MCP server without starting a transport."""

    resolved_config = config or AegisMCPConfig.from_paths()
    server = FastMCP(SERVER_NAME, json_response=True)
    server.aegis_config = resolved_config  # type: ignore[attr-defined]
    server.aegis_installer = _aegis_installer  # type: ignore[attr-defined]
    server.aegis_latest_plan = None  # type: ignore[attr-defined]
    register_v1_tools(server)
    register_resources_and_prompts(server)
    return server


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


def _ok_tool_response(
    tool_name: str,
    *,
    result: dict[str, Any],
    read_only: bool,
) -> dict[str, Any]:
    return {
        "ok": True,
        "schema_version": _aegis_installer.SCHEMA_VERSION,
        "tool": tool_name,
        "read_only": read_only,
        "result": result,
    }


def _error_tool_response(
    tool_name: str,
    *,
    code: str,
    message: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "schema_version": _aegis_installer.SCHEMA_VERSION,
        "tool": tool_name,
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "details": details or {},
        },
    }


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _resource_ok(
    uri: str,
    *,
    result: dict[str, Any],
    source: str,
) -> str:
    return _json_text(
        {
            "ok": True,
            "schema_version": _aegis_installer.SCHEMA_VERSION,
            "resource": uri,
            "source": source,
            "result": result,
        }
    )


def _resource_error(
    uri: str,
    *,
    code: str,
    message: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> str:
    return _json_text(
        {
            "ok": False,
            "schema_version": _aegis_installer.SCHEMA_VERSION,
            "resource": uri,
            "error": {
                "code": code,
                "message": message,
                "status": status,
                "details": details or {},
            },
        }
    )


def register_v1_tools(server: FastMCP) -> FastMCP:
    """Register the V1-backed Aegis tool contracts on a FastMCP server."""

    config: AegisMCPConfig = server.aegis_config  # type: ignore[attr-defined]
    installer = server.aegis_installer  # type: ignore[attr-defined]

    def validate_core_payload(schema_name: str, payload: dict[str, Any]) -> None:
        installer._validate_with_schema(config.source_root, schema_name, payload)

    def run_tool(
        tool_name: str,
        *,
        read_only: bool,
        callback,
    ) -> dict[str, Any]:
        try:
            result = callback()
        except AegisMCPInputError as exc:
            return _error_tool_response(
                tool_name,
                code="invalid_input",
                message=str(exc),
                status="invalid_request",
            )
        except installer.AegisError as exc:
            return _error_tool_response(
                tool_name,
                code="aegis_error",
                message=str(exc),
                status="invalid_request",
            )
        except ValidationError as exc:
            return _error_tool_response(
                tool_name,
                code="schema_validation_failed",
                message=exc.message,
                status="invalid_response",
                details={
                    "path": list(exc.path),
                    "schema_path": list(exc.schema_path),
                },
            )
        if isinstance(result, dict) and result.get("ok") is False and "error" in result:
            return result
        return _ok_tool_response(tool_name, result=result, read_only=read_only)

    @server.tool(name="aegis.inspect")
    def aegis_inspect(
        target_dir: str,
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Inspect a target project for Aegis installation state."""

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            return installer.inspect_project(target_dir, profile=profile_value)

        return run_tool(
            "aegis.inspect",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.status")
    def aegis_status(target_dir: str) -> dict[str, Any]:
        """Report installed Aegis release state without mutating the target."""

        def call_core() -> dict[str, Any]:
            return installer.status(target_dir, source_root=config.source_root)

        return run_tool(
            "aegis.status",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.plan_install")
    def aegis_plan_install(
        target_dir: str,
        primary_agent: PrimaryAgentName,
        agents: AgentList,
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Plan a deterministic Aegis installation without mutating the target."""

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            selected = _validate_agent_selection(primary_agent=primary_agent, agents=agents)
            payload = installer.plan_install(
                target_dir,
                source_root=config.source_root,
                profile=profile_value,
                primary_agent=primary_agent,
                agents=selected,
            )
            validate_core_payload("install-plan.schema.json", payload)
            server.aegis_latest_plan = payload  # type: ignore[attr-defined]
            return payload

        return run_tool(
            "aegis.plan_install",
            read_only=True,
            callback=call_core,
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

        if apply is not True:
            return _error_tool_response(
                "aegis.install",
                code="apply_required",
                message="aegis.install requires apply=true; use aegis.plan_install for dry runs.",
                status="refused",
                details={"apply": apply},
            )

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            selected = _validate_agent_selection(primary_agent=primary_agent, agents=agents)
            report = installer.install(
                target_dir,
                source_root=config.source_root,
                profile=profile_value,
                primary_agent=primary_agent,
                agents=selected,
                apply=apply,
            )
            if report.get("status") == "refused":
                return _error_tool_response(
                    "aegis.install",
                    code="install_refused",
                    message=str(report.get("reason") or "Aegis install refused."),
                    status="refused",
                    details={"report": report},
                )
            if report.get("status") == "failed":
                return _error_tool_response(
                    "aegis.install",
                    code="install_failed",
                    message=str(report.get("reason") or "Aegis install failed."),
                    status="failed",
                    details={"report": report},
                )
            return report

        return run_tool(
            "aegis.install",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.verify")
    def aegis_verify(
        target_dir: str,
        acknowledge_report_write: bool,
    ) -> dict[str, Any]:
        """Verify an Aegis installation after acknowledging report writes."""

        if acknowledge_report_write is not True:
            return _error_tool_response(
                "aegis.verify",
                code="acknowledgement_required",
                message="aegis.verify writes verification reports and requires acknowledge_report_write=true.",
                status="refused",
                details={"acknowledge_report_write": acknowledge_report_write},
            )

        def call_core() -> dict[str, Any]:
            report = installer.verify(target_dir, source_root=config.source_root)
            if report.get("status") == "failed":
                return _error_tool_response(
                    "aegis.verify",
                    code="verification_failed",
                    message="Aegis verification failed.",
                    status="failed",
                    details={"report": report},
                )
            return report

        return run_tool(
            "aegis.verify",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.list_profiles")
    def aegis_list_profiles() -> dict[str, Any]:
        """List Aegis install profiles supported by the V1 installer."""

        return run_tool(
            "aegis.list_profiles",
            read_only=True,
            callback=lambda: installer.list_profiles(source_root=config.source_root),
        )

    @server.tool(name="aegis.explain_profile")
    def aegis_explain_profile(
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
    ) -> dict[str, Any]:
        """Explain the built-in Aegis install profile."""

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            payload = installer.explain_profile(profile_value, source_root=config.source_root)
            validate_core_payload("profile.schema.json", payload)
            return payload

        return run_tool(
            "aegis.explain_profile",
            read_only=True,
            callback=call_core,
        )

    return server


def register_resources_and_prompts(server: FastMCP) -> FastMCP:
    """Register read-only Aegis resources and advisory workflow prompts."""

    config: AegisMCPConfig = server.aegis_config  # type: ignore[attr-defined]
    installer = server.aegis_installer  # type: ignore[attr-defined]

    def target_path(relative_path: str) -> Path:
        return config.default_target_dir / relative_path

    def source_json(relative_path: str) -> dict[str, Any]:
        return json.loads((config.source_root / relative_path).read_text(encoding="utf-8"))

    def read_target_json_resource(uri: str, relative_path: str, missing_code: str) -> str:
        path = target_path(relative_path)
        payload = _read_json_file(path)
        if payload is None:
            return _resource_error(
                uri,
                code=missing_code,
                message=f"{relative_path} is not available for the configured target.",
                status=missing_code,
                details={"path": path.as_posix()},
            )
        return _resource_ok(
            uri,
            result={"path": path.as_posix(), "payload": payload},
            source="target",
        )

    @server.resource("aegis://manifest/current")
    def manifest_current() -> str:
        return read_target_json_resource(
            "aegis://manifest/current",
            _aegis_installer.AEGIS_MANIFEST_REL,
            "not_installed",
        )

    @server.resource("aegis://contract/current")
    def contract_current() -> str:
        uri = "aegis://contract/current"
        path = target_path(_aegis_installer.AEGIS_CONTRACT_REL)
        if not path.exists():
            return _resource_error(
                uri,
                code="not_installed",
                message=".aegis/contract.md is not available for the configured target.",
                status="not_installed",
                details={"path": path.as_posix()},
            )
        return _resource_ok(
            uri,
            result={
                "path": path.as_posix(),
                "content_type": "text/markdown",
                "content": path.read_text(encoding="utf-8"),
            },
            source="target",
        )

    @server.resource("aegis://schemas/foundation-manifest")
    def foundation_manifest_schema() -> str:
        return _resource_ok(
            "aegis://schemas/foundation-manifest",
            result=source_json("schemas/aegis/foundation-manifest.schema.json"),
            source="source",
        )

    @server.resource("aegis://schemas/profile")
    def profile_schema() -> str:
        return _resource_ok(
            "aegis://schemas/profile",
            result=source_json("schemas/aegis/profile.schema.json"),
            source="source",
        )

    @server.resource("aegis://schemas/install-plan")
    def install_plan_schema() -> str:
        return _resource_ok(
            "aegis://schemas/install-plan",
            result=source_json("schemas/aegis/install-plan.schema.json"),
            source="source",
        )

    @server.resource("aegis://profiles")
    def profiles() -> str:
        return _resource_ok(
            "aegis://profiles",
            result=installer.list_profiles(source_root=config.source_root),
            source="source",
        )

    @server.resource("aegis://profiles/{name}")
    def profile(name: str) -> str:
        uri = f"aegis://profiles/{name}"
        try:
            payload = installer.explain_profile(name, source_root=config.source_root)
        except installer.AegisError as exc:
            return _resource_error(
                uri,
                code="profile_not_available",
                message=str(exc),
                status="not_available",
                details={"profile": name},
            )
        return _resource_ok(uri, result=payload, source="source")

    @server.resource("aegis://install-plan/latest")
    def latest_install_plan() -> str:
        uri = "aegis://install-plan/latest"
        cached = server.aegis_latest_plan  # type: ignore[attr-defined]
        if isinstance(cached, dict):
            return _resource_ok(uri, result=cached, source="session_cache")
        report = _read_json_file(target_path(_aegis_installer.AEGIS_PLAN_REPORT_REL))
        if report is not None:
            return _resource_ok(uri, result=report, source="target_report")
        return _resource_error(
            uri,
            code="not_available",
            message="No install plan is cached for this MCP session and no target report exists.",
            status="not_available",
            details={"path": target_path(_aegis_installer.AEGIS_PLAN_REPORT_REL).as_posix()},
        )

    @server.resource("aegis://verification/latest")
    def latest_verification() -> str:
        return read_target_json_resource(
            "aegis://verification/latest",
            _aegis_installer.AEGIS_VERIFY_REPORT_REL,
            "not_available",
        )

    @server.resource("aegis://limitations")
    def limitations() -> str:
        manifest = _read_json_file(target_path(_aegis_installer.AEGIS_MANIFEST_REL))
        gates = manifest.get("gates", []) if manifest else installer._gates(("claude", "codex"))
        policy_gates = [
            {
                "id": gate.get("id"),
                "enforcement": gate.get("enforcement"),
                "unsupported_reason": gate.get("unsupported_reason"),
            }
            for gate in gates
            if isinstance(gate, dict) and gate.get("enforcement") == "policy"
        ]
        return _resource_ok(
            "aegis://limitations",
            result={
                "policy_only_gates": policy_gates,
                "deferred_tools": [
                    "aegis.plan_update",
                    "aegis.update",
                    "aegis.rollback",
                ],
                "prompt_limitations": [
                    "Prompts are guidance only; tool calls and reports are required evidence.",
                    "Agents must not write .aegis/ directly; use Aegis tools.",
                ],
            },
            source="source+target",
        )

    @server.resource("aegis://managed-files")
    def managed_files() -> str:
        uri = "aegis://managed-files"
        manifest = _read_json_file(target_path(_aegis_installer.AEGIS_MANIFEST_REL))
        if manifest is None:
            return _resource_error(
                uri,
                code="not_installed",
                message="Aegis managed files are unavailable until the target has an Aegis manifest.",
                status="not_installed",
                details={"path": target_path(_aegis_installer.AEGIS_MANIFEST_REL).as_posix()},
            )
        return _resource_ok(
            uri,
            result={
                "target_root": config.default_target_dir.as_posix(),
                "managed_files": manifest.get("managed_files", []),
                "agents": manifest.get("agents", {}),
            },
            source="target",
        )

    def compatibility_notes() -> str:
        matrix = source_json(COMPATIBILITY_MATRIX_REL)
        agent_lines = []
        for agent in matrix.get("agents", []):
            if isinstance(agent, dict):
                agent_lines.append(
                    f"- {agent.get('id')}: status={agent.get('status')}, entrypoint={agent.get('entrypoint')}"
                )
        return "\n".join(agent_lines)

    def workflow_prompt(title: str, body: str) -> str:
        return "\n".join(
            [
                f"# {title}",
                "",
                "Aegis prompts are advisory. Do not claim success from prompt text.",
                "Use MCP tool results, `.aegis/reports/*`, and guard output as evidence.",
                "Do not write `.aegis/` directly; use `aegis.plan_install`, `aegis.install`, and `aegis.verify`.",
                "Common resources: `aegis://contract/current`, `aegis://limitations`, `aegis://verification/latest`.",
                "Distinguish mechanical gates from policy-only limitations.",
                "",
                "## Compatibility",
                compatibility_notes(),
                "",
                body,
            ]
        )

    @server.prompt(name="aegis.bootstrap_new_project")
    def bootstrap_new_project(target_dir: str = ".") -> str:
        return workflow_prompt(
            "Bootstrap New Aegis Project",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    "1. Run `aegis.inspect` and read `aegis://limitations`.",
                    "2. Run `aegis.plan_install` with explicit primary_agent and agents.",
                    "3. Ask the user to approve the plan; approval is required before `aegis.install`.",
                    "4. Run `aegis.install` with `apply=true` only after approval.",
                    "5. Run `aegis.verify` with `acknowledge_report_write=true` and cite `aegis://verification/latest`.",
                    "Mechanical gates are evidence; policy-only limitations are not proof of enforcement.",
                ]
            ),
        )

    @server.prompt(name="aegis.migrate_existing_project")
    def migrate_existing_project(target_dir: str = ".") -> str:
        return workflow_prompt(
            "Migrate Existing Project To Aegis",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    "1. Run `aegis.inspect` and review existing agent files.",
                    "2. Read `aegis://managed-files` and `aegis://contract/current` if installed.",
                    "3. Run `aegis.plan_install`; conflicts or manual-review operations must stop for user review.",
                    "4. Get explicit user approval before `aegis.install apply=true`.",
                    "5. Verify with `aegis.verify` and cite report evidence, not prompt text.",
                ]
            ),
        )

    @server.prompt(name="aegis.verify_runtime")
    def verify_runtime(target_dir: str = ".") -> str:
        return workflow_prompt(
            "Verify Aegis Runtime",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    "1. Read `aegis://manifest/current`, `aegis://contract/current`, and `aegis://limitations`.",
                    "2. Run `aegis.verify` with `acknowledge_report_write=true`.",
                    "3. Read `aegis://verification/latest` and report failed mechanical gates separately from policy-only limitations.",
                    "4. Do not describe the runtime as healthy unless the verification tool returns passing evidence.",
                ]
            ),
        )

    @server.prompt(name="aegis.prepare_agent_session")
    def prepare_agent_session(agent: str = "claude", target_dir: str = ".") -> str:
        return workflow_prompt(
            "Prepare Agent Session",
            "\n".join(
                [
                    f"Agent: `{agent}`",
                    f"Target: `{target_dir}`",
                    "1. Read `aegis://contract/current`, `aegis://managed-files`, and `aegis://limitations`.",
                    "2. Confirm the agent entrypoint and gates from the compatibility notes.",
                    "3. Use the agent-specific readiness/workflow gate before any persistent mutation.",
                    "4. Treat memory as continuity only; tracked reports and workflow files are evidence.",
                ]
            ),
        )

    @server.prompt(name="aegis.close_agent_session")
    def close_agent_session(agent: str = "claude", target_dir: str = ".") -> str:
        return workflow_prompt(
            "Close Agent Session",
            "\n".join(
                [
                    f"Agent: `{agent}`",
                    f"Target: `{target_dir}`",
                    "1. Run the agent's required verification gates and capture evidence.",
                    "2. Run or request `aegis.verify` when runtime files changed.",
                    "3. Update tracked session, work-tracking, handoff, findings, and decisions files.",
                    "4. Cite `aegis://verification/latest`; never use this prompt as completion evidence.",
                ]
            ),
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
