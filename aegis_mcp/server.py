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
    "aegis.next",
    "aegis.doctor",
    "aegis.reconcile",
    "aegis.repair",
    "aegis.plan_install",
    "aegis.install",
    "aegis.init",
    "aegis.verify",
    "aegis.closeout",
    "aegis.closeout_ready",
    "aegis.handoff_repair",
    "aegis.kickoff",
    "aegis.start",
    "aegis.log",
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
    "aegis://closeout/latest",
    "aegis://work/current",
    "aegis://limitations",
    "aegis://managed-files",
)
PROMPT_NAMES = (
    "aegis.bootstrap",
    "aegis.start_task",
    "aegis.implement_task",
    "aegis.closeout_task",
    "aegis.bootstrap_new_project",
    "aegis.migrate_existing_project",
    "aegis.verify_runtime",
    "aegis.prepare_agent_session",
    "aegis.close_agent_session",
)


class AegisMCPInputError(ValueError):
    """Raised when MCP inputs fail Aegis V1 safety constraints."""


class AegisMCPToolError(ValueError):
    """Raised when an MCP tool should return a structured error response."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status: str = "invalid_request",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


@dataclass(frozen=True)
class AegisMCPConfig:
    """Runtime configuration for the Aegis MCP server."""

    source_root: Path
    default_target_dir: Path
    default_primary_agent: str = "claude"
    default_agents: tuple[str, ...] = ("claude",)
    asset_origin: str = "source"

    @classmethod
    def from_paths(
        cls,
        *,
        source_root: str | Path | None = None,
        default_target_dir: str | Path | None = None,
        default_primary_agent: str | None = None,
        default_agents: Sequence[str] | None = None,
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
        resolved_target = (
            Path(default_target_dir or os.environ.get("AEGIS_DEFAULT_TARGET_DIR") or ".")
            .expanduser()
            .resolve()
        )
        primary = (
            default_primary_agent
            or os.environ.get("AEGIS_DEFAULT_PRIMARY_AGENT")
            or os.environ.get("AEGIS_PRIMARY_AGENT")
            or "claude"
        )
        if primary not in _aegis_installer.PRIMARY_AGENT_CHOICES:
            primary = "claude"
        env_agents = os.environ.get("AEGIS_DEFAULT_AGENTS") or os.environ.get("AEGIS_AGENTS")
        selected_agents = tuple(dict.fromkeys(default_agents or ()))
        if not selected_agents and env_agents:
            selected_agents = tuple(
                dict.fromkeys(agent.strip() for agent in env_agents.split(",") if agent.strip())
            )
        if not selected_agents and primary in _aegis_installer.AGENT_CHOICES:
            selected_agents = (primary,)
        if primary == "none":
            selected_agents = ()
        if any(agent not in _aegis_installer.AGENT_CHOICES for agent in selected_agents):
            primary = "claude"
            selected_agents = ("claude",)
        return cls(
            source_root=resolved_source,
            default_target_dir=resolved_target,
            default_primary_agent=primary,
            default_agents=selected_agents,
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
            "default_primary_agent": self.default_primary_agent,
            "default_agents": list(self.default_agents),
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
        raise AegisMCPInputError(f"primary_agent={primary_agent} must also be listed in agents")
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


def _client_reload_required_response(tool_name: str, report: dict[str, Any]) -> dict[str, Any]:
    """Return a hard-stop MCP result after an install that changed Claude hooks."""

    if tool_name == "aegis.init":
        client_reload = (
            report.get("install", {}).get("client_reload", {})
            if isinstance(report.get("install"), dict)
            else {}
        )
    else:
        client_reload = (
            report.get("client_reload", {}) if isinstance(report.get("client_reload"), dict) else {}
        )
    return _error_tool_response(
        tool_name,
        code="client_reload_required",
        status="blocked",
        message=(
            "HARD STOP: Aegis installed or changed Claude hooks/settings, but this Claude "
            "session has not loaded those hooks. Do not edit source, run project verification, "
            "mutate Taskmaster, or call aegis.start/aegis.kickoff. Tell the user to restart "
            "Claude in this project, then continue with aegis.next."
        ),
        details={
            "install_applied": True,
            "must_stop": True,
            "client_reload": client_reload,
            "forbidden_until_reload": client_reload.get("forbidden_until_reload", []),
            "allowed_until_reload": client_reload.get("allowed_until_reload", []),
            "next_allowed_action": "Restart Claude in this project, then call aegis.next.",
            "report": report,
        },
    )


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


def _resolve_confined_target_dir(target_dir: str | Path, allowed_root: Path) -> Path:
    """Resolve an MCP target under the configured target root."""

    base = allowed_root.expanduser().resolve()
    raw = Path(target_dir or ".").expanduser()
    candidate = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
    if candidate == base or base in candidate.parents:
        return candidate
    raise AegisMCPToolError(
        code="invalid_target",
        status="invalid_request",
        message="target_dir must resolve inside this Aegis MCP server's configured target root",
        details={
            "target_dir": str(target_dir),
            "resolved_target_dir": candidate.as_posix(),
            "allowed_root": base.as_posix(),
        },
    )


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
        except AegisMCPToolError as exc:
            return _error_tool_response(
                tool_name,
                code=exc.code,
                message=str(exc),
                status=exc.status,
                details=exc.details,
            )
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
        """Use proactively at the start of a normal coding task to detect Aegis workflow state; if not installed, call MCP aegis.init before source edits, using CLI fallback only when aegis is on PATH."""

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.inspect_project(
                target,
                profile=profile_value,
                source_root=config.source_root,
                default_primary_agent=config.default_primary_agent,
                default_agents=config.default_agents,
            )

        return run_tool(
            "aegis.inspect",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.status")
    def aegis_status(target_dir: str) -> dict[str, Any]:
        """Report installed Aegis release state and embedded next workflow guidance without mutating the target."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.status(
                target,
                source_root=config.source_root,
                default_primary_agent=config.default_primary_agent,
                default_agents=config.default_agents,
            )

        return run_tool(
            "aegis.status",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.next")
    def aegis_next(target_dir: str) -> dict[str, Any]:
        """Tell the agent the next required Aegis workflow action for a normal request; read-only, no source edits, no .aegis writes."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.next_action(
                target,
                source_root=config.source_root,
                default_primary_agent=config.default_primary_agent,
                default_agents=config.default_agents,
            )

        return run_tool(
            "aegis.next",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.doctor")
    def aegis_doctor(target_dir: str) -> dict[str, Any]:
        """Read-only state diagnostic with a safe repair plan for installed Aegis projects."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.doctor(
                target,
                source_root=config.source_root,
                default_primary_agent=config.default_primary_agent,
                default_agents=config.default_agents,
            )

        return run_tool(
            "aegis.doctor",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.reconcile")
    def aegis_reconcile(
        target_dir: str,
        base_ref: str = "origin/main",
        use_github: bool = True,
        preview_candidates: bool = False,
    ) -> dict[str, Any]:
        """Read-only Taskmaster/Aegis/git/PR drift report; optional inert preview never auto-mutates status."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.reconcile(
                target,
                source_root=config.source_root,
                base_ref=base_ref,
                use_github=use_github,
                preview_candidates=preview_candidates,
            )

        return run_tool(
            "aegis.reconcile",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.repair")
    def aegis_repair(
        target_dir: str,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Preview or apply safe Aegis state repairs; preview mode is read-only."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.repair(target, source_root=config.source_root, apply=apply)

        return run_tool(
            "aegis.repair",
            read_only=not apply,
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
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            payload = installer.plan_install(
                target,
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
        """Apply an Aegis installation; if Claude hooks changed, returns client_reload_required as a HARD STOP before edits."""

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
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            report = installer.install(
                target,
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
            client_reload = report.get("client_reload")
            if isinstance(client_reload, dict) and client_reload.get("required") is True:
                return _client_reload_required_response("aegis.install", report)
            return report

        return run_tool(
            "aegis.install",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.init")
    def aegis_init(
        target_dir: str,
        apply: bool,
        profile: ProfileName = _aegis_installer.PROFILE_GENERIC,
        primary_agent: PrimaryAgentName | None = None,
        agents: AgentList | None = None,
        verify_after_install: bool = True,
    ) -> dict[str, Any]:
        """Public project setup: install the Aegis project workflow using this MCP server's default agent selection unless explicitly overridden."""

        if apply is not True:
            return _error_tool_response(
                "aegis.init",
                code="apply_required",
                message="aegis.init installs project files and requires apply=true.",
                status="refused",
                details={"apply": apply},
            )

        def call_core() -> dict[str, Any]:
            profile_value = _validate_profile(profile)
            primary = primary_agent or config.default_primary_agent
            selected = _validate_agent_selection(
                primary_agent=primary,
                agents=agents or list(config.default_agents),
            )
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            report = installer.initialize_project(
                target,
                source_root=config.source_root,
                profile=profile_value,
                primary_agent=primary,
                agents=selected,
                verify_after_install=verify_after_install,
            )
            if report.get("status") == "refused":
                return _error_tool_response(
                    "aegis.init",
                    code="init_refused",
                    message="Aegis init refused unsafe install operations.",
                    status="refused",
                    details={"report": report},
                )
            if report.get("status") == "failed":
                return _error_tool_response(
                    "aegis.init",
                    code="init_failed",
                    message="Aegis init failed.",
                    status="failed",
                    details={"report": report},
                )
            client_reload = (
                report.get("install", {}).get("client_reload", {})
                if isinstance(report.get("install"), dict)
                else {}
            )
            if isinstance(client_reload, dict) and client_reload.get("required") is True:
                return _client_reload_required_response("aegis.init", report)
            return report

        return run_tool(
            "aegis.init",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.verify")
    def aegis_verify(
        target_dir: str,
        acknowledge_report_write: bool,
        strict: bool = False,
    ) -> dict[str, Any]:
        """Write an Aegis verification report; after strict pass, log its pending event before closeout."""

        if acknowledge_report_write is not True:
            return _error_tool_response(
                "aegis.verify",
                code="acknowledgement_required",
                message="aegis.verify writes verification reports and requires acknowledge_report_write=true.",
                status="refused",
                details={"acknowledge_report_write": acknowledge_report_write},
            )

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            report = installer.verify(
                target,
                source_root=config.source_root,
                strict=strict,
                default_primary_agent=config.default_primary_agent,
                default_agents=config.default_agents,
            )
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

    @server.tool(name="aegis.closeout")
    def aegis_closeout(
        target_dir: str,
        acknowledge_report_write: bool,
        update_handoff: bool = False,
        require_clean_git: bool = False,
        include_git_guidance: bool = True,
    ) -> dict[str, Any]:
        """Run the final completion gate after scope, implement, verify, and pending tracking are complete."""

        if acknowledge_report_write is not True:
            return _error_tool_response(
                "aegis.closeout",
                code="acknowledgement_required",
                message="aegis.closeout writes closeout reports and requires acknowledge_report_write=true.",
                status="refused",
                details={"acknowledge_report_write": acknowledge_report_write},
            )

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            report = installer.closeout(
                target,
                source_root=config.source_root,
                update_handoff=update_handoff,
                require_clean_git=require_clean_git,
                include_git_guidance=include_git_guidance,
            )
            if report.get("status") == "failed":
                return _error_tool_response(
                    "aegis.closeout",
                    code="closeout_failed",
                    message="Aegis closeout failed.",
                    status="failed",
                    details={"report": report},
                )
            return report

        return run_tool(
            "aegis.closeout",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.closeout_ready")
    def aegis_closeout_ready(
        target_dir: str,
        update_handoff: bool = False,
        require_clean_git: bool = False,
        include_git_guidance: bool = True,
    ) -> dict[str, Any]:
        """Read-only pre-closeout gate check; reports whether closeout would pass without writing state."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.closeout(
                target,
                source_root=config.source_root,
                update_handoff=update_handoff,
                require_clean_git=require_clean_git,
                include_git_guidance=include_git_guidance,
                dry_run=True,
            )

        return run_tool(
            "aegis.closeout_ready",
            read_only=True,
            callback=call_core,
        )

    @server.tool(name="aegis.handoff_repair")
    def aegis_handoff_repair(
        target_dir: str,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Preview or apply deterministic HANDOFF.md semantic-section repair after closeout_ready reports gaps."""

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            report = installer.repair_handoff(
                target,
                source_root=config.source_root,
                dry_run=not apply,
            )
            if report.get("status") == "failed":
                return _error_tool_response(
                    "aegis.handoff_repair",
                    code="handoff_repair_failed",
                    message=str(report.get("reason") or "Aegis handoff repair failed."),
                    status="failed",
                    details={"report": report},
                )
            return report

        return run_tool(
            "aegis.handoff_repair",
            read_only=not apply,
            callback=call_core,
        )

    @server.tool(name="aegis.kickoff")
    def aegis_kickoff(
        target_dir: str,
        task: str,
        slug: str,
        title: str,
        goals: list[str] | None = None,
        create_branch: bool = True,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Start Aegis current work from an explicit external numeric task id such as a Taskmaster task; next action is logging plan-step-scope before source edits; requires apply=true."""

        if apply is not True:
            return _error_tool_response(
                "aegis.kickoff",
                code="apply_required",
                message="aegis.kickoff creates workflow state and requires apply=true.",
                status="refused",
                details={"apply": apply},
            )

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.kickoff(
                target,
                task_id=task,
                slug=slug,
                title=title,
                goals=goals or [],
                create_branch=create_branch,
                source_root=config.source_root,
            )

        return run_tool(
            "aegis.kickoff",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.start")
    def aegis_start(
        target_dir: str,
        title: str,
        slug: str = "",
        goals: list[str] | None = None,
        create_branch: bool = True,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Public local-task kickoff: allocate a local task id from a normal title and create workflow state."""

        if apply is not True:
            return _error_tool_response(
                "aegis.start",
                code="apply_required",
                message="aegis.start creates workflow state and requires apply=true.",
                status="refused",
                details={"apply": apply},
            )

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.start_local_work(
                target,
                title=title,
                slug=slug or None,
                goals=goals or [],
                create_branch=create_branch,
                source_root=config.source_root,
            )

        return run_tool(
            "aegis.start",
            read_only=False,
            callback=call_core,
        )

    @server.tool(name="aegis.log")
    def aegis_log(
        target_dir: str,
        note: str,
        handler: str = "",
        evidence: str = "",
        surfaces: list[str] | None = None,
        event_class: Literal["scope", "implementation", "verification", "note"] | None = None,
        pending_event_id: str = "",
        plan_step: str = "",
        plan_status: str = "in-progress",
        apply: bool = False,
    ) -> dict[str, Any]:
        """Append S:W:H:E entries; prefer pending_event_id=current and plan_step=auto when the step is deterministic."""

        if apply is not True:
            return _error_tool_response(
                "aegis.log",
                code="apply_required",
                message="aegis.log writes workflow progress surfaces and requires apply=true.",
                status="refused",
                details={"apply": apply},
            )

        def call_core() -> dict[str, Any]:
            target = _resolve_confined_target_dir(target_dir, config.default_target_dir)
            return installer.log_work(
                target,
                handler=handler,
                evidence=evidence,
                note=note,
                surfaces=surfaces,
                event_class=event_class,
                pending_event_id=pending_event_id,
                plan_step=plan_step,
                plan_status=plan_status,
            )

        return run_tool(
            "aegis.log",
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

    @server.resource("aegis://closeout/latest")
    def latest_closeout() -> str:
        return read_target_json_resource(
            "aegis://closeout/latest",
            _aegis_installer.AEGIS_CLOSEOUT_REPORT_REL,
            "not_available",
        )

    @server.resource("aegis://work/current")
    def current_work() -> str:
        return read_target_json_resource(
            "aegis://work/current",
            _aegis_installer.AEGIS_CURRENT_WORK_REL,
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
                "Do not write `.aegis/` directly; use Aegis MCP tools or the project-local `./.aegis/bin/aegis` shim.",
                "Common resources: `aegis://contract/current`, `aegis://limitations`, `aegis://verification/latest`.",
                "Distinguish mechanical gates from policy-only limitations.",
                "",
                "## Compatibility",
                compatibility_notes(),
                "",
                body,
            ]
        )

    @server.prompt(name="aegis.bootstrap")
    def bootstrap(target_dir: str = ".", primary_agent: str = "claude") -> str:
        return workflow_prompt(
            "Bootstrap Aegis",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    f"Primary agent: `{primary_agent}`",
                    "1. Run `aegis.inspect` to classify the project shape.",
                    "2. Run read-only `aegis.status` and `aegis.next`; if not installed, run `aegis.plan_install`.",
                    "3. Review the install plan with the user before calling mutating `aegis.install apply=true`.",
                    "4. Run `aegis.verify` with `acknowledge_report_write=true` after install and cite the report.",
                    "5. If the install report says `client_reload.required=true`, ask the user to restart Claude before source edits; hooks from `.claude/settings.json` load at Claude session start.",
                    "6. Treat prompts as setup guidance only; installed files, hooks, and reports are the evidence.",
                ]
            ),
        )

    @server.prompt(name="aegis.start_task")
    def start_task(
        target_dir: str = ".", title: str = "<task title>", task: str = "", slug: str = ""
    ) -> str:
        return workflow_prompt(
            "Start Aegis Task",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    f"Title: `{title}`",
                    "1. Run `aegis.status` and `aegis.next` first.",
                    "2. If `aegis.next` returns `restart_claude_before_mutation`, stop and ask the user to restart Claude before source edits.",
                    "3. If `.taskmaster/` exists, run `task-master next` and `task-master show <id>` or the Taskmaster MCP equivalents before choosing a start path.",
                    "4. Use `aegis.kickoff apply=true` with the Taskmaster numeric task id when Taskmaster returns available work.",
                    "5. If no current work exists and no external task id is available, call `aegis.start apply=true` with a short normal-language title.",
                    "6. Use `aegis.kickoff apply=true` only when the user, Taskmaster, or project gives an explicit external numeric task id.",
                    "7. Confirm readiness is READY after start/kickoff.",
                    "8. Before source edits, log scope with `aegis.log apply=true`, `plan_step=auto`, and `plan_status=completed`.",
                    "9. Native agent tools do implementation; Aegis records workflow state and evidence.",
                    f"External task id if explicitly provided: `{task or '<none>'}`",
                    f"Slug override if explicitly provided: `{slug or '<auto>'}`",
                ]
            ),
        )

    @server.prompt(name="aegis.implement_task")
    def implement_task(target_dir: str = ".", evidence: str = "<changed-file-or-report>") -> str:
        return workflow_prompt(
            "Implement Aegis Task",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    f"Evidence: `{evidence}`",
                    "1. Run readiness and `aegis.next`; follow the returned next_required_action.",
                    "2. Use native agent tools for source reads, edits, and project tests.",
                    "3. After each persistent mutation, consume pending tracking with `aegis.log apply=true`, `pending_event_id=current`, and `plan_step=auto`.",
                    "4. If `plan_step=auto` is ambiguous, stop and provide an explicit plan-step id instead of guessing.",
                    "5. Do not continue to another mutation while `.aegis/state/pending-tracking.json` exists.",
                ]
            ),
        )

    @server.prompt(name="aegis.closeout_task")
    def closeout_task(target_dir: str = ".") -> str:
        return workflow_prompt(
            "Close Out Aegis Task",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    "1. Run task-specific verification and log it with `plan_step=auto`.",
                    "2. Run `aegis.verify` with `strict=true` and `acknowledge_report_write=true`.",
                    "3. Log the strict verification pending event with `pending_event_id=current`, `plan_step=auto`, and `plan_status=completed`.",
                    "4. Run read-only `aegis.closeout_ready` or CLI `aegis closeout --dry-run --update-handoff`.",
                    "5. If handoff semantic gates fail, call `aegis.handoff_repair` with `apply=true`, then re-run closeout readiness. Do not hand-edit HANDOFF.md for deterministic repairable handoff gates.",
                    "6. Apply any remaining repair guidance until dry-run passes, then call mutating `aegis.closeout` with `acknowledge_report_write=true`.",
                    "7. Run read-only `aegis.doctor` after closeout writes a passing report.",
                    "8. If Taskmaster is in use, mark Taskmaster done only after closeout and doctor pass; then refresh generated task files with the project helper when present, otherwise run `task-master generate` deliberately.",
                    "9. Only report completion after closeout passes and doctor reports the completed state.",
                ]
            ),
        )

    @server.prompt(name="aegis.bootstrap_new_project")
    def bootstrap_new_project(target_dir: str = ".") -> str:
        return workflow_prompt(
            "Bootstrap New Aegis Project",
            "\n".join(
                [
                    f"Target: `{target_dir}`",
                    "1. Run `aegis.inspect` and read `aegis://limitations`.",
                    f"2. For the normal public path, call `aegis.init apply=true` with the MCP server default agent selection (`primary_agent={config.default_primary_agent}`, `agents={list(config.default_agents)}`).",
                    "3. Use `aegis.plan_install` and `aegis.install` only when you need an advanced dry-run/conflict review path.",
                    "4. If `aegis.init` returns `client_reload.required=true` or `next_action=restart_claude_before_mutation`, ask the user to restart Claude before source mutations.",
                    "5. After reload, follow the returned `next_action`; it should direct you to `aegis.start apply=true` or Taskmaster-backed `aegis.kickoff apply=true` before source mutations.",
                    "6. Run or cite the verification report produced by init, then continue with `aegis.next`.",
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
    def prepare_agent_session(
        agent: str = config.default_primary_agent, target_dir: str = "."
    ) -> str:
        return workflow_prompt(
            "Prepare Agent Session",
            "\n".join(
                [
                    f"Agent: `{agent}`",
                    f"Target: `{target_dir}`",
                    "1. Read `aegis://contract/current`, `aegis://managed-files`, and `aegis://limitations`.",
                    "2. Run readiness; if BLOCKED because no current work exists, request or run `aegis.kickoff apply=true`.",
                    "3. Confirm the agent entrypoint and gates from the compatibility notes.",
                    "4. Use the agent-specific readiness/workflow gate before any persistent mutation.",
                    "5. Treat memory as continuity only; tracked reports and workflow files are evidence.",
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
        "--primary-agent",
        choices=sorted(_aegis_installer.PRIMARY_AGENT_CHOICES),
        help="Default primary agent used in public MCP guidance and aegis.init when omitted.",
    )
    parser.add_argument(
        "--agent",
        choices=sorted(_aegis_installer.AGENT_CHOICES),
        action="append",
        help="Default enabled agent adapter for public MCP guidance; repeat for multi-agent defaults.",
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
        default_primary_agent=args.primary_agent,
        default_agents=args.agent,
    )
    if args.describe_config:
        print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
        return 0
    create_server(config).run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
