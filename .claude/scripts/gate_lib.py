from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any


FILE_MUTATION_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
HOOKABLE_TOOLS = FILE_MUTATION_TOOLS | {"Bash"}
REQUIRED_TOOL_INPUT_FIELDS = {
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path",),
    "Bash": ("command",),
}
AEGIS_CURRENT_WORK_REL = ".aegis/state/current-work.json"
AEGIS_CLIENT_RELOAD_REL = ".aegis/state/client-reload-required.json"
AEGIS_PENDING_TRACKING_REL = ".aegis/state/pending-tracking.json"
AEGIS_DEGRADED_EVENTS_REL = ".aegis/state/degraded-events.json"
AEGIS_ENFORCEMENT_REL = ".aegis/state/enforcement.json"
AEGIS_GATE_DECISIONS_REL = ".aegis/reports/gate-decisions.jsonl"
AEGIS_VERIFY_REPORT_REL = ".aegis/reports/verification-report.json"
AEGIS_LOCAL_BIN_REL = ".aegis/bin/aegis"

PROTECTED_PREFIXES = ("templates/", ".codex/", ".aegis/", ".claude/")
PROTECTED_EXACT = {"CODEX.md", "CLAUDE.md", "AGENTS.md"}
PROTECTED_NAME_PREFIXES = ("scripts/codex-", "scripts/template-")
WORKFLOW_LINK_PREFIXES = ("sessions/", "plans/")
WORKFLOW_TRACKING_PREFIX = "docs/ai/work-tracking/"
WORKFLOW_REPORT_SEGMENT = "/reports/"
SANCTIONED_AEGIS_MCP_MUTATION_SUFFIXES = {
    "kickoff",
    "start",
    "observe_start",
    "observe_stop",
    "runtime_update",
    "log",
    "handoff_repair",
    "closeout",
    "repair",
    "enforce",
}

MUTATING_GIT_RE = re.compile(
    r"(^|[;&|]\s*)git\s+("
    r"switch\s+-c|checkout\s+-b|branch\s+(-m|-d|-D)|commit\b|stash\b|reset\b|"
    r"merge\b|rebase\b|push\b|tag\b"
    r")",
    re.IGNORECASE,
)
MUTATING_TASKMASTER_RE = re.compile(
    r"(^|[;&|]\s*)task-master\s+("
    r"add-task|add-subtask|set-status|update|update-task|update-subtask|"
    r"expand|generate|parse-prd|move|add-dependency|remove-dependency|fix-dependencies"
    r")\b",
    re.IGNORECASE,
)
MUTATING_AEGIS_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+("
    r"install|uninstall|verify|start|kickoff|observe|log|closeout|enforce"
    r")\b",
    re.IGNORECASE,
)
AEGIS_REPAIR_APPLY_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+repair\b[^\n;&|]*\s--apply\b",
    re.IGNORECASE,
)
AEGIS_BOOTSTRAP_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+(start|kickoff)\b",
    re.IGNORECASE,
)
AEGIS_LOG_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+log\b",
    re.IGNORECASE,
)
AEGIS_VERIFY_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+verify\b",
    re.IGNORECASE,
)
AEGIS_CLOSEOUT_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+closeout\b",
    re.IGNORECASE,
)
LOCALHOST_URL_RE = re.compile(r"^https?://(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?(?:/|$)", re.IGNORECASE)
OBSERVATION_BROWSER_MCP_RE = re.compile(
    r"^mcp__(?:playwright|browser|puppeteer|chrome(?:[-_]devtools)?|chromium)__",
    re.IGNORECASE,
)
REDIRECT_RE = re.compile(r"(?<![<])(?:>>|>)(?![>&])\s*([\"']?)([^\"'\s;&|]+)\1")
SHELL_CONTROL_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
UNSUPPORTED_READ_ONLY_SHELL_RE = re.compile(r"(`|\$\(|<<|<\(|>\(|\b(?:python|python3?)\s+-c\b)")
PYTHON_WRITE_RE = re.compile(
    r"(?:open|Path)\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"][^'\"]*[wa+][^'\"]*['\"])?"
    r"|write_text\(\s*['\"]",
    re.IGNORECASE,
)
READ_ONLY_SIMPLE_COMMANDS = {
    "cat",
    "date",
    "echo",
    "false",
    "grep",
    "head",
    "ls",
    "pwd",
    "rg",
    "sed",
    "stat",
    "tail",
    "test",
    "true",
    "wc",
    "which",
}
READ_ONLY_GIT_SUBCOMMANDS = {
    "branch",
    "diff",
    "grep",
    "log",
    "ls-files",
    "rev-parse",
    "show",
    "status",
}
READ_ONLY_TASKMASTER_SUBCOMMANDS = {
    "complexity-report",
    "list",
    "next",
    "show",
    "validate-dependencies",
}
READ_ONLY_AEGIS_SUBCOMMANDS = {
    "doctor",
    "explain-profile",
    "inspect",
    "list-profiles",
    "next",
    "plan-install",
    "reconcile",
    "status",
}
READ_ONLY_NPM_SCRIPTS = {"check", "lint", "test", "typecheck", "verify"}
READ_ONLY_TEST_OUTPUT_OPTIONS = {
    "--junitxml",
    "--json-report-file",
    "--outputFile",
    "--output-file",
    "--reporter=json",
    "--reporter=json-summary",
}
MCP_READ_ONLY_TOOL_RE = re.compile(
    r"^mcp__.*__(get|list|read|search|find|query|show|help|check|resolve|fetch|open|is_|has_)",
    re.IGNORECASE,
)
MCP_MUTATION_TOOL_RE = re.compile(
    r"^mcp__.*__(add|create|update|set|write|edit|delete|remove|rename|move|parse|expand|generate|archive|init|initialize|start|kickoff)",
    re.IGNORECASE,
)
TASKMASTER_SET_STATUS_RE = re.compile(
    r"(^|[;&|]\s*)task-master\s+set-status\b(?P<args>[^;&|]*)",
    re.IGNORECASE,
)
TASKMASTER_GENERATE_RE = re.compile(r"(^|[;&|]\s*)task-master\s+generate\b", re.IGNORECASE)
SHELL_REDIRECT_TOKEN_RE = re.compile(r"^\d?>&\d$")
AEGIS_READ_ONLY_MCP_TOOL_SUFFIXES = {
    "inspect",
    "status",
    "runtime_status",
    "next",
    "doctor",
    "reconcile",
    "plan_install",
    "closeout_ready",
    "list_profiles",
    "explain_profile",
}
TASKMASTER_READ_ONLY_MCP_TOOL_SUFFIXES = {
    "help",
    "get_tasks",
    "next_task",
    "get_task",
}
PATH_FIELD_NAMES = {
    "file_path",
    "filepath",
    "path",
    "relative_path",
    "notebook_path",
    "target_path",
    "source_path",
    "old_path",
    "new_path",
    "destination",
    "dest",
}


@dataclass
class Payload:
    tool_name: str
    tool_input: dict[str, Any]


@dataclass
class PayloadLoadError:
    reason: str
    raw_preview: str


def raw_payload_preview(raw: str, *, limit: int = 160) -> str:
    preview = raw.replace("\n", "\\n").replace("\r", "\\r")
    if len(preview) > limit:
        return f"{preview[:limit]}..."
    return preview


def parse_payload(raw: str) -> Payload | PayloadLoadError:
    if not raw.strip():
        return Payload(tool_name="", tool_input={})
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return PayloadLoadError(
            reason=f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            raw_preview=raw_payload_preview(raw),
        )
    if not isinstance(data, dict):
        return PayloadLoadError(
            reason=f"hook payload JSON must be an object, got {type(data).__name__}",
            raw_preview=raw_payload_preview(raw),
        )
    tool_name = str(data.get("tool_name") or "")
    if not tool_name and data:
        return PayloadLoadError(
            reason="hook payload missing required field 'tool_name'",
            raw_preview=raw_payload_preview(raw),
        )
    raw_tool_input = data.get("tool_input")
    if raw_tool_input is None:
        tool_input: dict[str, Any] = {}
    elif isinstance(raw_tool_input, dict):
        tool_input = raw_tool_input
    else:
        return PayloadLoadError(
            reason=f"hook payload field 'tool_input' must be an object, got {type(raw_tool_input).__name__}",
            raw_preview=raw_payload_preview(raw),
        )
    return Payload(tool_name=str(data.get("tool_name") or ""), tool_input=tool_input)


def load_payload_result(raw: str | None = None) -> Payload | PayloadLoadError:
    return parse_payload(sys.stdin.read() if raw is None else raw)


def load_payload() -> Payload | None:
    result = load_payload_result()
    return result if isinstance(result, Payload) else None


def payload_required_field_issue(payload: Payload) -> str | None:
    required_fields = REQUIRED_TOOL_INPUT_FIELDS.get(payload.tool_name)
    if not required_fields:
        return None
    if any(isinstance(payload.tool_input.get(field), str) and payload.tool_input.get(field) for field in required_fields):
        return None
    fields = ", ".join(required_fields)
    return f"{payload.tool_name} payload missing required input field(s): {fields}"


def project_root() -> Path:
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_root:
        return Path(env_root).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def enforcement_state(root: Path) -> dict[str, Any]:
    state = _read_json_object(root / AEGIS_ENFORCEMENT_REL)
    mode = str(state.get("mode") or "strict").strip().lower()
    if mode not in {"strict", "advisory"}:
        mode = "strict"
    return {
        "mode": mode,
        "set_at": state.get("set_at"),
        "set_by": state.get("set_by"),
        "reason": state.get("reason"),
        "path": AEGIS_ENFORCEMENT_REL,
        "configured": (root / AEGIS_ENFORCEMENT_REL).is_file(),
    }


def enforcement_mode(root: Path) -> str:
    return str(enforcement_state(root).get("mode") or "strict")


def source_commit(root: Path) -> str | None:
    manifest = _read_json_object(root / ".aegis" / "foundation-manifest.json")
    runtime = manifest.get("runtime") if isinstance(manifest.get("runtime"), dict) else {}
    commit = runtime.get("source_commit") or manifest.get("source_commit")
    return str(commit) if commit else None


def payload_digest(payload: Payload | None, raw_preview: str | None = None) -> str:
    if payload is None:
        data: dict[str, Any] = {"raw_preview": raw_preview or ""}
    else:
        data = {"tool_name": payload.tool_name, "tool_input": payload.tool_input}
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def append_gate_decision(
    root: Path,
    *,
    hook: str,
    payload: Payload | None,
    verdict: str,
    reason: str,
    readiness_state: str | None = None,
    raw_preview: str | None = None,
) -> None:
    mode = enforcement_mode(root)
    report_path = root / AEGIS_GATE_DECISIONS_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "hook": hook,
        "tool_name": payload.tool_name if payload is not None else "unclassifiable",
        "payload_digest": payload_digest(payload, raw_preview),
        "verdict": verdict,
        "reason": reason,
        "readiness_state": readiness_state,
        "mode": mode,
        "source_commit": source_commit(root),
    }
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def advisory_enabled(root: Path) -> bool:
    return enforcement_mode(root) == "advisory"


def advisory_message(hook: str, reason: str) -> None:
    print(
        f"ADVISORY | {hook} would have blocked, but Aegis enforcement mode is advisory: {reason}",
        file=sys.stderr,
    )


def gate_block_or_record(
    root: Path,
    payload: Payload,
    message: str,
    *,
    reason: str,
    readiness_state: str | None = None,
) -> int:
    if advisory_enabled(root):
        append_gate_decision(
            root,
            hook="pretooluse",
            payload=payload,
            verdict="would_block",
            reason=reason,
            readiness_state=readiness_state,
        )
        advisory_message("pretooluse", reason)
        return 0
    return block(message)


def gate_allow_or_record(root: Path, payload: Payload, *, reason: str) -> int:
    if advisory_enabled(root):
        append_gate_decision(
            root,
            hook="pretooluse",
            payload=payload,
            verdict="allow",
            reason=reason,
        )
    return 0


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def normalize_path(path_text: str, root: Path | None = None) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    root = root or project_root()
    if path.is_absolute():
        try:
            return path.resolve().relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()
    rel = path.as_posix()
    if rel.startswith("./"):
        return rel[2:]
    return rel


def is_protected_path(path_text: str, root: Path | None = None) -> bool:
    rel = normalize_path(path_text, root)
    if rel in PROTECTED_EXACT:
        return True
    if rel.startswith(PROTECTED_PREFIXES):
        return True
    return rel.startswith(PROTECTED_NAME_PREFIXES)


def is_workflow_report_path(path_text: str, root: Path | None = None) -> bool:
    rel = normalize_path(path_text, root)
    return rel.startswith(WORKFLOW_TRACKING_PREFIX) and WORKFLOW_REPORT_SEGMENT in f"/{rel}/"


def is_workflow_owned_path(path_text: str, root: Path | None = None) -> bool:
    rel = normalize_path(path_text, root)
    if rel.startswith(WORKFLOW_LINK_PREFIXES):
        return True
    if rel.startswith(WORKFLOW_TRACKING_PREFIX):
        return not is_workflow_report_path(rel, root)
    return False


def is_guarded_mutation_path(path_text: str, root: Path | None = None) -> bool:
    return is_protected_path(path_text, root) or is_workflow_owned_path(path_text, root)


def is_mcp_tool(tool_name: str) -> bool:
    return tool_name.startswith("mcp__")


def normalized_mcp_tool_name(tool_name: str) -> str:
    return tool_name.lower().replace(".", "_").replace("-", "_")


def mcp_is_taskmaster_tool(tool_name: str) -> bool:
    normalized = normalized_mcp_tool_name(tool_name)
    return "taskmaster" in normalized or "task_master" in normalized


def mcp_is_read_only_taskmaster_discovery(payload: Payload) -> bool:
    if not is_mcp_tool(payload.tool_name) or not mcp_is_taskmaster_tool(payload.tool_name):
        return False
    normalized = normalized_mcp_tool_name(payload.tool_name)
    return any(normalized.endswith(f"__{suffix}") for suffix in TASKMASTER_READ_ONLY_MCP_TOOL_SUFFIXES)


def is_hookable_tool(tool_name: str) -> bool:
    return tool_name in HOOKABLE_TOOLS or is_mcp_tool(tool_name)


def file_paths_from_payload(payload: Payload, root: Path | None = None) -> list[str]:
    candidates = [
        payload.tool_input.get("file_path"),
        payload.tool_input.get("notebook_path"),
    ]
    paths: list[str] = []
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            paths.append(normalize_path(candidate, root))
    return paths


def mcp_path_values(value: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in PATH_FIELD_NAMES and isinstance(nested, str):
                paths.append(nested)
            else:
                paths.extend(mcp_path_values(nested))
    elif isinstance(value, list):
        for nested in value:
            paths.extend(mcp_path_values(nested))
    return paths


def mcp_is_mutation(payload: Payload) -> bool:
    if not is_mcp_tool(payload.tool_name):
        return False
    normalized = normalized_mcp_tool_name(payload.tool_name)
    if "aegis" in normalized and normalized.endswith("runtime_update"):
        return payload.tool_input.get("apply") is True
    if "aegis" in normalized and normalized.endswith("repair"):
        return payload.tool_input.get("apply") is True
    if "aegis" in normalized and normalized.endswith("handoff_repair"):
        return payload.tool_input.get("apply") is True
    if "aegis" in normalized and any(
        normalized.endswith(suffix) for suffix in AEGIS_READ_ONLY_MCP_TOOL_SUFFIXES
    ):
        return mcp_aegis_target_dir_violation(payload) is not None
    if mcp_is_taskmaster_tool(payload.tool_name):
        return not mcp_is_read_only_taskmaster_discovery(payload)
    if MCP_MUTATION_TOOL_RE.search(payload.tool_name):
        return True
    if MCP_READ_ONLY_TOOL_RE.search(payload.tool_name):
        return False
    # Unknown MCP tools are treated as persistent by default. This is intentionally
    # conservative because MCP tools can mutate remote systems, local files, or memory.
    return True


def bash_command(payload: Payload) -> str:
    command = payload.tool_input.get("command")
    return command if isinstance(command, str) else ""


def shlex_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def option_value(tokens: list[str], option: str) -> str | None:
    for index, token in enumerate(tokens):
        if token == option and index + 1 < len(tokens):
            return tokens[index + 1]
        prefix = f"{option}="
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def target_dir_confinement_violation(target_dir: str | None, root: Path | None = None) -> str | None:
    if not target_dir:
        return None
    root = (root or project_root()).resolve()
    raw = Path(target_dir).expanduser()
    try:
        resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    except (OSError, ValueError) as exc:
        return f"target_dir {target_dir!r} could not be resolved safely: {exc}"
    if resolved == root or root in resolved.parents:
        return None
    return (
        "target_dir escapes governed project root "
        f"(target_dir={target_dir!r}, resolved={resolved.as_posix()}, root={root.as_posix()})"
    )


def mcp_aegis_target_dir_violation(payload: Payload, root: Path | None = None) -> str | None:
    if not is_mcp_tool(payload.tool_name):
        return None
    normalized = normalized_mcp_tool_name(payload.tool_name)
    if "aegis" not in normalized:
        return None
    target_dir = payload.tool_input.get("target_dir")
    if not isinstance(target_dir, str):
        return None
    return target_dir_confinement_violation(target_dir, root)


def is_shell_assignment(token: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token))


def command_name(token: str) -> str:
    return Path(token).name


def strip_shell_prefixes(tokens: list[str]) -> list[str]:
    stripped = list(tokens)
    while stripped and is_shell_assignment(stripped[0]):
        stripped = stripped[1:]
    if stripped and stripped[0] == "env":
        stripped = stripped[1:]
        while stripped and (is_shell_assignment(stripped[0]) or stripped[0] in {"-i", "-u"}):
            if stripped[0] == "-u" and len(stripped) >= 2:
                stripped = stripped[2:]
            else:
                stripped = stripped[1:]
    return stripped


def has_read_only_test_output_option(tokens: list[str]) -> bool:
    for token in tokens:
        if token in READ_ONLY_TEST_OUTPUT_OPTIONS:
            return True
        if any(token.startswith(f"{option}=") for option in READ_ONLY_TEST_OUTPUT_OPTIONS):
            return True
        if token.startswith("--cov-report=") and token != "--cov-report=term":
            return True
    return False


def redirect_targets(command: str) -> list[str]:
    return [match.group(2) for match in REDIRECT_RE.finditer(command)]


def is_persistent_redirect_target(target: str) -> bool:
    return target not in {"/dev/null", "NUL", "nul"}


def bash_is_mutation(command: str) -> bool:
    if not command.strip():
        return False
    if bash_is_read_only(command):
        return False
    if any(is_persistent_redirect_target(target) for target in redirect_targets(command)):
        return True
    if re.search(r"(^|[;&|]\s*)(sed\b[^;\n]*\s-i\b|sed\s+-i\b)", command):
        return True
    if re.search(r"(^|[;&|]\s*)tee\b", command):
        return True
    if re.search(r"(^|[;&|]\s*)(rm|mv|cp|install|touch|chmod|chown|mkdir|rmdir)\b", command):
        return True
    if (
        MUTATING_GIT_RE.search(command)
        or MUTATING_TASKMASTER_RE.search(command)
        or MUTATING_AEGIS_RE.search(command)
        or AEGIS_REPAIR_APPLY_RE.search(command)
    ):
        return True
    if re.search(r"python3?\s+-c\s+['\"][^'\"]*(open|write_text)", command):
        return True
    return True


def read_only_git_segment(tokens: list[str]) -> bool:
    remainder = tokens[1:]
    while remainder and remainder[0].startswith("-"):
        if remainder[0] == "-C" and len(remainder) >= 2:
            remainder = remainder[2:]
        else:
            remainder = remainder[1:]
    if not remainder:
        return False
    if remainder[0] == "branch":
        return "--show-current" in remainder[1:]
    return remainder[0] in READ_ONLY_GIT_SUBCOMMANDS


def read_only_taskmaster_segment(tokens: list[str]) -> bool:
    return len(tokens) >= 2 and tokens[1] in READ_ONLY_TASKMASTER_SUBCOMMANDS


def aegis_cli_remainder(tokens: list[str], root: Path | None = None, *, allow_bare: bool = False) -> list[str] | None:
    if not tokens:
        return None
    root = root or project_root()
    executable = tokens[0]
    if normalize_path(executable, root) == AEGIS_LOCAL_BIN_REL:
        return tokens[1:]
    if executable == "aegis":
        resolved = shutil.which("aegis")
        if resolved and normalize_path(resolved, root) == AEGIS_LOCAL_BIN_REL:
            return tokens[1:]
        return tokens[1:] if allow_bare else None
    if len(tokens) >= 4 and command_name(executable) in {"python", "python3"} and tokens[1:3] == [
        "-m",
        "aegis_foundation.cli",
    ]:
        return tokens[3:]
    return None


def read_only_aegis_remainder(remainder: list[str]) -> bool:
    return bool(remainder) and (
        remainder[0] in READ_ONLY_AEGIS_SUBCOMMANDS
        or (len(remainder) >= 2 and remainder[0] == "runtime" and remainder[1] == "status")
        or (
            len(remainder) >= 2
            and remainder[0] == "runtime"
            and remainder[1] == "update"
            and "--apply" not in remainder[2:]
        )
        or (remainder[0] == "closeout" and "--dry-run" in remainder[1:])
        or (remainder[0] == "uninstall" and "--apply" not in remainder[1:])
        or (remainder[0] == "enforce" and "--mode" not in remainder[1:])
    )


def aegis_cli_target_dir_violation_from_remainder(
    remainder: list[str],
    root: Path | None = None,
) -> str | None:
    target_dir = option_value(remainder, "--target-dir")
    return target_dir_confinement_violation(target_dir, root)


def aegis_cli_target_dir_violations(command: str, root: Path | None = None) -> list[str]:
    root = root or project_root()
    violations: list[str] = []
    for segment in [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]:
        tokens = strip_shell_prefixes(shlex_tokens(segment))
        remainder = aegis_cli_remainder(tokens, root, allow_bare=True)
        if remainder is None:
            continue
        violation = aegis_cli_target_dir_violation_from_remainder(remainder, root)
        if violation:
            violations.append(violation)
    return sorted(set(violations))


def read_only_aegis_segment(tokens: list[str]) -> bool:
    remainder = aegis_cli_remainder(tokens, allow_bare=True)
    if remainder is None:
        return False
    return read_only_aegis_remainder(remainder) and not aegis_cli_target_dir_violation_from_remainder(remainder)


def read_only_node_segment(tokens: list[str]) -> bool:
    if len(tokens) >= 2 and tokens[0] in {"npm", "pnpm", "yarn"}:
        if tokens[1] in {"test", "verify"}:
            return not has_read_only_test_output_option(tokens)
        if len(tokens) >= 3 and tokens[1] == "run" and tokens[2] in READ_ONLY_NPM_SCRIPTS:
            return not has_read_only_test_output_option(tokens)
    if tokens[0] == "npx" and len(tokens) >= 2:
        return read_only_node_segment(tokens[1:])
    if tokens[0] == "vitest":
        return not has_read_only_test_output_option(tokens)
    if tokens[0] == "tsc":
        return "--noEmit" in tokens and not has_read_only_test_output_option(tokens)
    return False


def read_only_python_test_segment(tokens: list[str]) -> bool:
    if tokens[0] == "pytest":
        return not has_read_only_test_output_option(tokens)
    if command_name(tokens[0]) in {"python", "python3"}:
        return len(tokens) >= 3 and tokens[1:3] == ["-m", "pytest"] and not has_read_only_test_output_option(tokens)
    if tokens[0] == "uv" and len(tokens) >= 3 and tokens[1] == "run":
        return read_only_python_test_segment(tokens[2:])
    return False


def read_only_find_segment(tokens: list[str]) -> bool:
    return tokens[0] == "find" and "-delete" not in tokens and "-exec" not in tokens and "-execdir" not in tokens


def bash_segment_is_read_only(segment: str) -> bool:
    tokens = strip_shell_prefixes(shlex_tokens(segment))
    if not tokens:
        return True
    name = command_name(tokens[0])
    tokens[0] = name
    if name == "cd":
        return True
    if name == "git":
        return read_only_git_segment(tokens)
    if name == "task-master":
        return read_only_taskmaster_segment(tokens)
    if read_only_aegis_segment(tokens):
        return True
    if name in READ_ONLY_SIMPLE_COMMANDS:
        return name != "sed" or "-i" not in tokens
    if read_only_find_segment(tokens):
        return True
    if read_only_node_segment(tokens):
        return True
    if read_only_python_test_segment(tokens):
        return True
    return False


def bash_is_read_only(command: str) -> bool:
    if not command.strip():
        return True
    if UNSUPPORTED_READ_ONLY_SHELL_RE.search(command):
        return False
    if any(is_persistent_redirect_target(target) for target in redirect_targets(command)):
        return False
    segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    return bool(segments) and all(bash_segment_is_read_only(segment) for segment in segments)


def npm_command_words(tokens: list[str]) -> list[str]:
    words: list[str] = []
    skip_next = False
    for token in tokens[1:]:
        if skip_next:
            skip_next = False
            continue
        if token in {"-C", "--prefix", "--cwd", "--dir", "--filter", "--workspace"}:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        words.append(token)
    return words


def localhost_probe_segment(tokens: list[str]) -> bool:
    if tokens[0] == "curl":
        curl_file_output_flags = {
            "--cookie-jar",
            "--config",
            "--dump-header",
            "--etag-save",
            "--output",
            "--output-dir",
            "--remote-header-name",
            "--remote-name",
            "--remote-name-all",
            "--trace",
            "--trace-ascii",
        }
        for token in tokens[1:]:
            if token in curl_file_output_flags or any(
                token.startswith(f"{flag}=") for flag in curl_file_output_flags
            ):
                return False
            if token in {"-D", "-J", "-K", "-O", "-o", "-c"}:
                return False
            if token.startswith("-D") or token.startswith("-K") or token.startswith("-o") or token.startswith("-c"):
                return False
            if token.startswith("-") and "O" in token[1:]:
                return False
        return any(LOCALHOST_URL_RE.match(token) for token in tokens[1:])
    if tokens[0] == "wget":
        stdout = False
        for index, token in enumerate(tokens[1:], start=1):
            if token == "-O" and index + 1 < len(tokens) and tokens[index + 1] == "-":
                stdout = True
            elif token == "-O-":
                stdout = True
            elif token == "--output-document=-":
                stdout = True
            elif token.startswith("--output-document="):
                return False
            elif token == "--output-document":
                return False
            elif token in {"-e", "--config"} or token.startswith("--config="):
                return False
            elif token.startswith("-O") and token != "-O-":
                return False
        return stdout and any(LOCALHOST_URL_RE.match(token) for token in tokens[1:])
    if tokens[0] not in {"curl", "wget"}:
        return False
    return False


def dev_server_segment(tokens: list[str]) -> bool:
    name = tokens[0]
    if name in {"npm", "pnpm", "yarn", "bun"}:
        words = npm_command_words(tokens)
        if not words:
            return False
        if words[0] in {"dev", "start"}:
            return True
        return len(words) >= 2 and words[0] == "run" and words[1] in {"dev", "start"}
    if name in {"vite", "next", "astro", "wrangler"}:
        return len(tokens) >= 2 and tokens[1] in {"dev", "start"}
    return False


def bash_segment_is_observation_tooling(segment: str) -> bool:
    tokens = strip_shell_prefixes(shlex_tokens(segment))
    if not tokens:
        return True
    name = command_name(tokens[0])
    tokens[0] = name
    if bash_segment_is_read_only(segment):
        return True
    return dev_server_segment(tokens) or localhost_probe_segment(tokens)


def bash_is_observation_tooling(command: str) -> bool:
    if not command.strip():
        return True
    if any(is_persistent_redirect_target(target) for target in redirect_targets(command)):
        return False
    segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    return bool(segments) and all(bash_segment_is_observation_tooling(segment) for segment in segments)


def degraded_bash_segment_is_non_destructive(segment: str) -> bool:
    return bash_segment_is_read_only(segment)


def degraded_bash_is_non_destructive(command: str) -> bool:
    return bash_is_read_only(command)


def degraded_payload_is_non_destructive(payload: Payload) -> bool:
    try:
        if payload.tool_name in FILE_MUTATION_TOOLS:
            return False
        if payload.tool_name == "Bash":
            return degraded_bash_is_non_destructive(bash_command(payload))
        if is_mcp_tool(payload.tool_name):
            return not mcp_is_mutation(payload)
        return not payload.tool_name
    except Exception:  # noqa: BLE001 - degraded mode must fail closed on classifier faults.
        return False


def bash_is_aegis_bootstrap(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"start", "kickoff"}) or bash_is_aegis_observe_start(command)


def bash_is_aegis_log(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"log"})


def bash_is_aegis_pending_log(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"log"}, required_option="--pending-id")


def bash_is_aegis_uninstall_apply(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"uninstall"}, require_apply=True)


def bash_is_aegis_verify(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"verify"})


def bash_is_aegis_observe_start(command: str) -> bool:
    return bash_has_trusted_aegis_nested_subcommand(command, "observe", {"start"})


def bash_is_aegis_observe_stop(command: str) -> bool:
    return bash_has_trusted_aegis_nested_subcommand(command, "observe", {"stop"})


def bash_is_aegis_runtime_update(command: str) -> bool:
    return bash_has_trusted_aegis_nested_subcommand(command, "runtime", {"update"})


def bash_is_aegis_enforce(command: str) -> bool:
    segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    if len(segments) != 1:
        return False
    tokens = strip_shell_prefixes(shlex_tokens(segments[0]))
    remainder = aegis_cli_remainder(tokens, project_root(), allow_bare=False)
    return bool(remainder) and remainder[0] == "enforce"


def mcp_tool_is_aegis_verify(tool_name: str) -> bool:
    if not is_mcp_tool(tool_name):
        return False
    normalized = tool_name.lower().replace(".", "_").replace("-", "_")
    return "aegis" in normalized and normalized.endswith("verify")


def bash_is_aegis_closeout(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"closeout"})


def bash_has_trusted_aegis_subcommand(
    command: str,
    subcommands: set[str],
    *,
    require_apply: bool = False,
    required_option: str | None = None,
    handoff_repair: bool = False,
) -> bool:
    root = project_root()
    for segment in [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]:
        tokens = strip_shell_prefixes(shlex_tokens(segment))
        remainder = aegis_cli_remainder(tokens, root, allow_bare=False)
        if not remainder:
            continue
        if handoff_repair:
            if len(remainder) >= 2 and remainder[0] == "handoff" and remainder[1] == "repair":
                return True
            continue
        if remainder[0] not in subcommands:
            continue
        if require_apply and "--apply" not in remainder[1:]:
            continue
        if required_option and required_option not in remainder[1:]:
            continue
        return True
    return False


def bash_is_aegis_repair_apply(command: str) -> bool:
    segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    if len(segments) != 1:
        return False
    tokens = strip_shell_prefixes(shlex_tokens(segments[0]))
    remainder = aegis_cli_remainder(tokens, project_root(), allow_bare=False)
    return bool(remainder) and remainder[0] == "repair" and "--apply" in remainder[1:]


def bash_has_trusted_aegis_nested_subcommand(
    command: str,
    first: str,
    seconds: set[str],
) -> bool:
    root = project_root()
    for segment in [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]:
        tokens = strip_shell_prefixes(shlex_tokens(segment))
        remainder = aegis_cli_remainder(tokens, root, allow_bare=False)
        if len(remainder or []) >= 2 and remainder[0] == first and remainder[1] in seconds:
            return True
    return False


def payload_is_sanctioned_aegis_workflow_mutation(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        command = bash_command(payload)
        return (
            bash_is_aegis_bootstrap(command)
            or bash_is_aegis_log(command)
            or bash_is_aegis_verify(command)
            or bash_is_aegis_closeout(command)
            or bash_is_aegis_runtime_update(command)
            or bash_is_aegis_enforce(command)
            or bash_has_trusted_aegis_subcommand(command, {"repair"}, require_apply=True)
            or bash_has_trusted_aegis_subcommand(command, set(), handoff_repair=True)
        )
    if is_mcp_tool(payload.tool_name):
        normalized = normalized_mcp_tool_name(payload.tool_name)
        return "aegis" in normalized and any(
            normalized.endswith(suffix) for suffix in SANCTIONED_AEGIS_MCP_MUTATION_SUFFIXES
        )
    return False


def guarded_bash_path_violation(action: str, target: str, root: Path) -> str | None:
    normalized = normalize_path(target, root)
    if is_protected_path(target, root):
        return f"{action} protected path {normalized}"
    if is_workflow_owned_path(target, root):
        return f"{action} workflow-owned path {normalized}"
    return None


def protected_bash_violations(command: str, root: Path | None = None) -> list[str]:
    root = root or project_root()
    violations: list[str] = []
    violations.extend(aegis_cli_target_dir_violations(command, root))

    for match in REDIRECT_RE.finditer(command):
        target = match.group(2)
        if not is_persistent_redirect_target(target):
            continue
        violation = guarded_bash_path_violation("redirection targets", target, root)
        if violation:
            violations.append(violation)

    tokens = shlex_tokens(command)
    for index, token in enumerate(tokens):
        lower = token.lower()
        if lower == "sed" and "-i" in tokens[index + 1 : index + 4]:
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-") or candidate.startswith("s/"):
                    continue
                violation = guarded_bash_path_violation("sed -i targets", candidate, root)
                if violation:
                    violations.append(violation)
        if lower == "tee":
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-"):
                    continue
                violation = guarded_bash_path_violation("tee targets", candidate, root)
                if violation:
                    violations.append(violation)
        if lower in {"rm", "mv", "cp", "install", "touch", "chmod", "chown", "mkdir", "rmdir"}:
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-"):
                    continue
                violation = guarded_bash_path_violation(f"{lower} references", candidate, root)
                if violation:
                    violations.append(violation)

    for match in PYTHON_WRITE_RE.finditer(command):
        target = match.group(1)
        if target:
            violation = guarded_bash_path_violation("python write targets", target, root)
            if violation:
                violations.append(violation)

    return sorted(set(violations))


def block(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def block_unclassifiable_payload(reason: str, raw_preview: str | None = None) -> int:
    details = f"Details: {reason}"
    if raw_preview:
        details = f"{details}\nPayload preview: {raw_preview}"
    return block(
        "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
        "Reason: PreToolUse hook payload could not be parsed or classified safely.\n\n"
        f"{details}\n\n"
        "Aegis fails closed for non-empty or incomplete hook payloads so autonomous agents cannot mutate "
        "a project when the gate cannot render a verdict."
    )


def path_guard() -> int:
    payload = load_payload()
    if payload is None:
        return 0
    root = project_root()
    protected = [path for path in file_paths_from_payload(payload, root) if is_protected_path(path, root)]
    if not protected:
        return 0
    paths = "\n".join(f"  - {path}" for path in protected)
    return block(
        "BLOCKED by .claude/scripts/codex-path-guard.sh\n\n"
        f"Tool: {payload.tool_name}\n"
        f"Protected path(s):\n{paths}\n\n"
        "Claude-owned work must not modify CODEX.md, templates/**, scripts/codex-*, "
        "scripts/template-*, or .codex/**. Use a Codex-led follow-up for shared changes."
    )


def bash_guard() -> int:
    payload = load_payload()
    if payload is None:
        return 0
    command = bash_command(payload)
    violations = protected_bash_violations(command)
    if not violations:
        return 0
    details = "\n".join(f"  - {violation}" for violation in violations)
    return block(
        "BLOCKED by .claude/scripts/bash-command-guard.sh\n\n"
        f"Command: {command}\n"
        f"Violation(s):\n{details}\n\n"
        "Bash may not be used to bypass protected Aegis/Codex-owned path boundaries."
    )


def run_readiness(root: Path) -> subprocess.CompletedProcess[str]:
    readiness = script_dir() / "readiness.sh"
    return subprocess.run(
        ["bash", str(readiness), "--quick", "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def degraded_events_path(root: Path) -> Path:
    return root / AEGIS_DEGRADED_EVENTS_REL


def degraded_events(root: Path) -> list[dict[str, Any]]:
    payload = read_json(degraded_events_path(root))
    if not payload:
        return []
    events = payload.get("events")
    return [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []


def degraded_event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def write_degraded_event(root: Path, payload: Payload, reason: str, raw_payload: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    existing_events = degraded_events(root)
    previous_hash = str(existing_events[-1].get("event_hash") or "") if existing_events else ""
    event = {
        "id": sha1(f"{now}|{payload.tool_name}|{reason}|{raw_payload_preview(raw_payload)}".encode("utf-8")).hexdigest()[:12],
        "created_at": now,
        "gate": "pretooluse",
        "mode": "degraded_allow",
        "action_class": "non_destructive",
        "tool": payload.tool_name,
        "reason": reason,
        "raw_preview": raw_payload_preview(raw_payload),
        "previous_event_hash": previous_hash,
    }
    event["event_hash"] = degraded_event_hash(event)
    existing_events.append(event)
    write_json(
        degraded_events_path(root),
        {
            "schema_version": "1.0.0",
            "updated_at": now,
            "events": existing_events,
        },
    )
    return event


def current_work(root: Path) -> dict[str, Any] | None:
    return read_json(root / AEGIS_CURRENT_WORK_REL)


def current_work_is_observation(root: Path) -> bool:
    work = current_work(root)
    return isinstance(work, dict) and work.get("mode") == "observation" and work.get("status") == "in-progress"


def current_work_closeout_completed(root: Path) -> dict[str, Any] | None:
    work = current_work(root)
    if not isinstance(work, dict):
        return None
    if work.get("status") == "completed" and work.get("closeout_passed_at"):
        return work
    return None


def current_git_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "branch", "--show-current"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_work_branch_name(work: dict[str, Any]) -> str:
    branch = work.get("branch")
    if isinstance(branch, dict):
        return str(branch.get("current") or branch.get("name") or "").strip()
    if isinstance(branch, str):
        return branch.strip()
    return ""


def clear_client_reload_marker(root: Path) -> None:
    marker = root / AEGIS_CLIENT_RELOAD_REL
    if marker.exists():
        marker.unlink()


def pending_tracking_path(root: Path) -> Path:
    return root / AEGIS_PENDING_TRACKING_REL


def pending_tracking_events(root: Path) -> list[dict[str, Any]]:
    payload = read_json(pending_tracking_path(root))
    if not payload:
        return []
    events = payload.get("events")
    return [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []


def write_pending_tracking_events(root: Path, events: list[dict[str, Any]]) -> None:
    path = pending_tracking_path(root)
    if not events:
        if path.exists():
            path.unlink()
        return
    write_json(
        path,
        {
            "schema_version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "events": events,
        },
    )


def first_redirect_target(command: str, root: Path) -> str | None:
    for target in redirect_targets(command):
        if is_persistent_redirect_target(target):
            return normalize_path(target, root)
    return None


def payload_evidence(payload: Payload, root: Path) -> str:
    if payload.tool_name in FILE_MUTATION_TOOLS:
        paths = file_paths_from_payload(payload, root)
        if paths:
            return paths[0]
    if payload.tool_name == "Bash":
        command = bash_command(payload)
        if bash_is_aegis_verify(command):
            return AEGIS_VERIFY_REPORT_REL
        redirect_target = first_redirect_target(command, root)
        if redirect_target:
            return redirect_target
        return f"cmd`{command}`"
    if is_mcp_tool(payload.tool_name):
        if mcp_tool_is_aegis_verify(payload.tool_name):
            return AEGIS_VERIFY_REPORT_REL
        paths = mcp_path_values(payload.tool_input)
        if paths:
            return normalize_path(paths[0], root)
        return payload.tool_name
    return payload.tool_name or "unknown"


def _path_for_evidence(root: Path, evidence: str) -> Path | None:
    if not evidence or evidence.startswith("cmd`"):
        return None
    candidate = Path(evidence).expanduser()
    if candidate.is_absolute():
        return candidate
    return root / evidence


def _line_count(path: Path) -> int | None:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None


def _display_location(path_text: str, line_start: int | None, line_end: int | None) -> str:
    if line_start is None:
        return path_text
    if line_end is None or line_end == line_start:
        return f"{path_text}:{line_start}"
    return f"{path_text}:{line_start}-{line_end}"


def _snippet_line_range(path: Path, snippet: str) -> tuple[int, int] | None:
    if not snippet:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None
    offset = text.find(snippet)
    if offset < 0:
        return None
    line_start = text[:offset].count("\n") + 1
    line_span = max(1, len(snippet.splitlines()) or 1)
    return line_start, line_start + line_span - 1


def _file_snapshot_location(root: Path, evidence: str, *, source: str) -> dict[str, Any] | None:
    path = _path_for_evidence(root, evidence)
    if path is None:
        return None
    count = _line_count(path)
    if count is None:
        return {
            "path": evidence,
            "source": source,
            "confidence": "unavailable",
            "display": evidence,
        }
    line_start = 1 if count > 0 else None
    line_end = count if count > 0 else None
    return {
        "path": evidence,
        "line_start": line_start,
        "line_end": line_end,
        "line_count": count,
        "source": source,
        "confidence": "file_snapshot",
        "display": _display_location(evidence, line_start, line_end),
    }


def payload_evidence_location(payload: Payload, root: Path, evidence: str) -> dict[str, Any] | None:
    path = _path_for_evidence(root, evidence)
    if payload.tool_name == "Edit" and path is not None:
        new_string = payload.tool_input.get("new_string")
        if isinstance(new_string, str):
            found = _snippet_line_range(path, new_string)
            if found:
                line_start, line_end = found
                return {
                    "path": evidence,
                    "line_start": line_start,
                    "line_end": line_end,
                    "source": "tool_input.new_string",
                    "confidence": "best_effort",
                    "display": _display_location(evidence, line_start, line_end),
                }
        return _file_snapshot_location(root, evidence, source="edit_file_snapshot")

    if payload.tool_name == "MultiEdit" and path is not None:
        edits = payload.tool_input.get("edits")
        ranges: list[dict[str, int]] = []
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                new_string = edit.get("new_string")
                if not isinstance(new_string, str):
                    continue
                found = _snippet_line_range(path, new_string)
                if found:
                    ranges.append({"line_start": found[0], "line_end": found[1]})
        if ranges:
            line_start = min(item["line_start"] for item in ranges)
            line_end = max(item["line_end"] for item in ranges)
            return {
                "path": evidence,
                "line_start": line_start,
                "line_end": line_end,
                "ranges": ranges,
                "source": "tool_input.edits.new_string",
                "confidence": "best_effort",
                "display": _display_location(evidence, line_start, line_end),
            }
        return _file_snapshot_location(root, evidence, source="multiedit_file_snapshot")

    if payload.tool_name == "Write":
        return _file_snapshot_location(root, evidence, source="write_file_snapshot")

    if payload.tool_name == "NotebookEdit":
        return _file_snapshot_location(root, evidence, source="notebook_file_snapshot")

    if payload.tool_name == "Bash" and not evidence.startswith("cmd`"):
        return _file_snapshot_location(root, evidence, source="bash_file_snapshot")

    if is_mcp_tool(payload.tool_name) and not evidence.startswith("cmd`"):
        return _file_snapshot_location(root, evidence, source="mcp_file_snapshot")

    return None


def payload_handler(payload: Payload) -> str:
    if payload.tool_name == "Bash":
        if bash_is_aegis_verify(bash_command(payload)):
            return "aegis:verify"
        tokens = shlex_tokens(bash_command(payload))
        for token in tokens:
            if is_shell_assignment(token):
                continue
            return f"bash:{token}"
        return "bash"
    if mcp_tool_is_aegis_verify(payload.tool_name):
        return "aegis:verify"
    return f"claude:{payload.tool_name}" if payload.tool_name else "claude:unknown"


def payload_is_aegis_log(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_log(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("log")
    return False


def payload_is_aegis_observe_start(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_observe_start(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("observe_start")
    return False


def payload_is_aegis_observe_stop(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_observe_stop(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("observe_stop")
    return False


def payload_is_aegis_runtime_update(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_runtime_update(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("runtime_update")
    return False


def payload_is_aegis_repair_apply(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_repair_apply(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = normalized_mcp_tool_name(payload.tool_name)
        return (
            "aegis" in normalized
            and normalized.endswith("aegis_repair")
            and payload.tool_input.get("apply") is True
        )
    return False


def payload_is_aegis_pending_log(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_pending_log(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return (
            "aegis" in normalized
            and normalized.endswith("log")
            and bool(
                payload.tool_input.get("pending_id")
                or payload.tool_input.get("pending-id")
                or payload.tool_input.get("pendingEventId")
            )
        )
    return False


def payload_is_aegis_uninstall_apply(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_uninstall_apply(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("uninstall") and payload.tool_input.get("apply") is True
    return False


def payload_is_aegis_enforce(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_enforce(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("enforce")
    return False


def payload_is_mutation(payload: Payload) -> bool:
    if payload.tool_name in FILE_MUTATION_TOOLS:
        return True
    if payload.tool_name == "Bash":
        return bash_is_mutation(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        return mcp_is_mutation(payload)
    return False


def payload_is_read_only(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_read_only(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        return not mcp_is_mutation(payload)
    return False


def payload_is_observation_allowed(payload: Payload) -> bool:
    if payload.tool_name in FILE_MUTATION_TOOLS:
        return False
    if payload_is_read_only(payload):
        return True
    if payload_is_aegis_log(payload) or payload_is_aegis_observe_stop(payload):
        return True
    if payload.tool_name == "Bash":
        command = bash_command(payload)
        return bash_is_observation_tooling(command)
    if is_mcp_tool(payload.tool_name):
        return bool(OBSERVATION_BROWSER_MCP_RE.match(payload.tool_name))
    return False


def payload_is_aegis_bootstrap(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_bootstrap(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith(("start", "kickoff", "observe_start"))
    return False


def payload_is_aegis_closeout(payload: Payload) -> bool:
    if payload.tool_name == "Bash":
        return bash_is_aegis_closeout(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("closeout")
    return False


def bash_is_post_closeout_taskmaster_completion(command: str, task_id: str) -> bool:
    if TASKMASTER_GENERATE_RE.search(command):
        return True
    for match in TASKMASTER_SET_STATUS_RE.finditer(command):
        tokens = shlex_tokens(f"task-master set-status {match.group('args')}")
        status = (option_value(tokens, "--status") or "").strip().lower()
        requested_id = (option_value(tokens, "--id") or "").strip()
        if status in {"done", "completed"} and requested_id == task_id:
            return True
    return False


def command_segments(command: str) -> list[str]:
    return [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]


def cleaned_shell_tokens(segment: str) -> list[str]:
    tokens = strip_shell_prefixes(shlex_tokens(segment))
    return [token for token in tokens if not SHELL_REDIRECT_TOKEN_RE.match(token)]


def shell_args_have_positional(args: list[str], value_options: set[str] | None = None) -> bool:
    value_options = value_options or set()
    skip_next = False
    for token in args:
        if skip_next:
            skip_next = False
            continue
        if token.startswith("-"):
            if token in value_options:
                skip_next = True
            continue
        return True
    return False


def bash_segment_is_current_branch_push(segment: str, branch: str) -> bool:
    tokens = cleaned_shell_tokens(segment)
    if len(tokens) < 3:
        return False
    if command_name(tokens[0]) != "git" or tokens[1] != "push":
        return False
    if any(
        token in {"-f", "--force", "--force-with-lease", "--mirror", "--all", "--tags", "--delete"}
        or token.startswith("--force-with-lease=")
        for token in tokens[2:]
    ):
        return False
    args = tokens[2:]
    if not args:
        return False
    if args[0] in {"-u", "--set-upstream"}:
        args = args[1:]
    if len(args) != 2:
        return False
    remote, ref = args
    if remote != "origin":
        return False
    return ref in {branch, "HEAD"}


def bash_segment_is_current_branch_pr_create(segment: str, branch: str) -> bool:
    tokens = cleaned_shell_tokens(segment)
    if len(tokens) < 3:
        return False
    if command_name(tokens[0]) != "gh" or tokens[1:3] != ["pr", "create"]:
        return False
    if "--web" in tokens[3:] or option_value(tokens, "--repo") or "-R" in tokens[3:]:
        return False
    head = option_value(tokens, "--head")
    if head:
        return head == branch or head.endswith(f":{branch}")
    return True


def bash_segment_is_current_branch_pr_ready(segment: str, branch: str) -> bool:
    tokens = cleaned_shell_tokens(segment)
    if len(tokens) < 3:
        return False
    if command_name(tokens[0]) != "gh" or tokens[1:3] != ["pr", "ready"]:
        return False
    args = tokens[3:]
    if "--undo" in args or "--web" in args or option_value(tokens, "--repo") or "-R" in args:
        return False
    return not shell_args_have_positional(args, {"--repo", "-R"})


def bash_segment_is_current_branch_pr_merge(segment: str, branch: str) -> bool:
    tokens = cleaned_shell_tokens(segment)
    if len(tokens) < 3:
        return False
    if command_name(tokens[0]) != "gh" or tokens[1:3] != ["pr", "merge"]:
        return False
    args = tokens[3:]
    if "--admin" in args or "--web" in args or option_value(tokens, "--repo") or "-R" in args:
        return False
    if not any(method in args for method in {"--merge", "--squash", "--rebase"}):
        return False
    value_options = {"--subject", "--body", "--body-file", "--author-email", "--match-head-commit"}
    return not shell_args_have_positional(args, value_options)


def bash_is_post_closeout_delivery(command: str, branch: str) -> bool:
    if not branch:
        return False
    if UNSUPPORTED_READ_ONLY_SHELL_RE.search(command):
        return False
    if any(is_persistent_redirect_target(target) for target in redirect_targets(command)):
        return False
    segments = command_segments(command)
    if not segments:
        return False
    first, rest = segments[0], segments[1:]
    if not (
        bash_segment_is_current_branch_push(first, branch)
        or bash_segment_is_current_branch_pr_create(first, branch)
        or bash_segment_is_current_branch_pr_ready(first, branch)
        or bash_segment_is_current_branch_pr_merge(first, branch)
    ):
        return False
    return all(bash_segment_is_read_only(segment) for segment in rest)


def mcp_is_post_closeout_taskmaster_completion(payload: Payload, task_id: str) -> bool:
    normalized = normalized_mcp_tool_name(payload.tool_name)
    if not mcp_is_taskmaster_tool(payload.tool_name):
        return False
    if normalized.endswith("generate"):
        return True
    if not normalized.endswith("set_task_status"):
        return False
    requested_id = str(
        payload.tool_input.get("id")
        or payload.tool_input.get("task_id")
        or payload.tool_input.get("taskId")
        or ""
    ).strip()
    status = str(payload.tool_input.get("status") or "").strip().lower()
    return requested_id == task_id and status in {"done", "completed"}


def payload_is_post_closeout_taskmaster_completion(root: Path, payload: Payload) -> bool:
    work = current_work_closeout_completed(root)
    if work is None or pending_tracking_events(root):
        return False
    task = work.get("task") if isinstance(work.get("task"), dict) else {}
    task_id = str(task.get("id") or "").strip()
    if not task_id:
        return False
    if payload.tool_name == "Bash":
        return bash_is_post_closeout_taskmaster_completion(bash_command(payload), task_id)
    if is_mcp_tool(payload.tool_name):
        return mcp_is_post_closeout_taskmaster_completion(payload, task_id)
    return False


def payload_is_post_closeout_delivery(root: Path, payload: Payload) -> bool:
    work = current_work_closeout_completed(root)
    if work is None or pending_tracking_events(root):
        return False
    if payload.tool_name != "Bash":
        return False
    branch = current_git_branch(root)
    if not branch:
        return False
    recorded_branch = current_work_branch_name(work)
    if recorded_branch and recorded_branch != branch:
        return False
    return bash_is_post_closeout_delivery(bash_command(payload), branch)


def record_pending_tracking_event(root: Path, payload: Payload) -> None:
    work = current_work(root)
    if not work:
        return
    if work.get("status") != "in-progress":
        return
    if work.get("mode") == "observation":
        return
    if (
        not payload_is_mutation(payload)
        or payload_is_aegis_bootstrap(payload)
        or payload_is_aegis_runtime_update(payload)
        or payload_is_aegis_log(payload)
        or payload_is_aegis_closeout(payload)
    ):
        return
    evidence = payload_evidence(payload, root)
    handler = payload_handler(payload)
    evidence_location = payload_evidence_location(payload, root, evidence)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    task = work.get("task") if isinstance(work.get("task"), dict) else {}
    task_id = str(task.get("id") or "")
    slug = str(task.get("slug") or "")
    event_id = sha1(f"{now}|{payload.tool_name}|{handler}|{evidence}".encode("utf-8")).hexdigest()[:12]
    events = pending_tracking_events(root)
    for event in events:
        if event.get("evidence") == evidence and event.get("handler") == handler:
            event["updated_at"] = now
            if evidence_location:
                event["evidence_location"] = evidence_location
            write_pending_tracking_events(root, events)
            return
    event = {
        "id": event_id,
        "created_at": now,
        "updated_at": now,
        "tool": payload.tool_name,
        "handler": handler,
        "evidence": evidence,
        "task": {
            "id": task_id,
            "slug": slug,
        },
        "mode": enforcement_mode(root),
        "reason": "Mutation requires S:W:H:E entries in sessions/current and active TRACKER.md.",
    }
    if evidence_location:
        event["evidence_location"] = evidence_location
    events.append(event)
    write_pending_tracking_events(root, events)


def format_pending_tracking(events: list[dict[str, Any]]) -> str:
    lines = []
    for event in events:
        event_id = event.get("id", "<unknown>")
        lines.append(
            f"  - {event_id}: H={event.get('handler', '<unknown>')} E={event.get('evidence', '<unknown>')}"
        )
        location = event.get("evidence_location")
        if isinstance(location, dict) and location.get("display"):
            confidence = str(location.get("confidence") or "unknown")
            lines.append(f"    location: {location['display']} ({confidence})")
        lines.append(
            "    repair: ./.aegis/bin/aegis log --pending-id "
            f"{event_id} --note \"<past-tense note>\" "
            "--plan-step <plan-step-id> --plan-status completed"
        )
    return "\n".join(lines)


def degraded_pretooluse_fallback(raw_payload: str, exc: BaseException) -> int:
    loaded = parse_payload(raw_payload)
    reason = f"{type(exc).__name__}: {exc}"
    if isinstance(loaded, PayloadLoadError):
        return block_unclassifiable_payload(f"gate infrastructure failed after an unclassifiable payload: {reason}", loaded.raw_preview)
    root = project_root()
    if degraded_payload_is_non_destructive(loaded):
        event = write_degraded_event(root, loaded, reason, raw_payload)
        print(
            "DEGRADED | pretooluse gate infrastructure failed; allowed conservative non-destructive action "
            f"and wrote {AEGIS_DEGRADED_EVENTS_REL} event {event['id']}",
            file=sys.stderr,
        )
        return 0
    return block(
        "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
        f"Tool: {loaded.tool_name}\n"
        "Reason: PreToolUse gate infrastructure failed while evaluating a mutation or unsafe action.\n\n"
        f"Details: {reason}\n\n"
        "Aegis fails closed for destructive, protected, workflow-state, and unclassified actions when the gate cannot render a verdict."
    )


def pretooluse_gate(raw_payload: str | None = None) -> int:
    root = project_root()
    loaded = load_payload_result(raw_payload)
    if isinstance(loaded, PayloadLoadError):
        if advisory_enabled(root):
            append_gate_decision(
                root,
                hook="pretooluse",
                payload=None,
                verdict="would_block",
                reason=f"unclassifiable_payload: {loaded.reason}",
                raw_preview=loaded.raw_preview,
            )
            advisory_message("pretooluse", "unclassifiable_payload")
            return 0
        return block_unclassifiable_payload(loaded.reason, loaded.raw_preview)
    payload = loaded
    if not is_hookable_tool(payload.tool_name):
        return 0
    required_field_issue = payload_required_field_issue(payload)
    if required_field_issue:
        if advisory_enabled(root):
            append_gate_decision(
                root,
                hook="pretooluse",
                payload=payload,
                verdict="would_block",
                reason=f"invalid_payload: {required_field_issue}",
            )
            advisory_message("pretooluse", "invalid_payload")
            return 0
        return block_unclassifiable_payload(required_field_issue)

    clear_client_reload_marker(root)
    aegis_target_violations: list[str] = []
    if payload.tool_name == "Bash":
        aegis_target_violations = aegis_cli_target_dir_violations(bash_command(payload), root)
    elif is_mcp_tool(payload.tool_name):
        violation = mcp_aegis_target_dir_violation(payload, root)
        if violation:
            aegis_target_violations = [violation]
    if aegis_target_violations:
        details = "\n".join(f"  - {violation}" for violation in aegis_target_violations)
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            f"Violation(s):\n{details}\n\n"
            "Aegis read-only target selection is confined to the governed project root.",
            reason="aegis_target_dir_violation",
        )
    if payload_is_read_only(payload):
        return gate_allow_or_record(root, payload, reason="read_only")
    is_mutation = payload_is_mutation(payload)
    readiness = run_readiness(root)
    post_closeout_taskmaster_completion = payload_is_post_closeout_taskmaster_completion(root, payload)
    post_closeout_delivery = payload_is_post_closeout_delivery(root, payload)
    if current_work_is_observation(root) and is_mutation:
        if payload_is_observation_allowed(payload):
            return gate_allow_or_record(root, payload, reason="observation_allowed")
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: Aegis observation mode only permits observation tooling.\n\n"
            "Allowed while observing: read-only inspection, dev servers, localhost probes, browser/screenshot MCP tools, aegis log, and aegis observe stop.\n"
            "Blocked while observing: source edits, Taskmaster mutations, git mutations, Aegis closeout/apply paths, and unclassified persistent mutations.\n\n"
            "Stop observation with `./.aegis/bin/aegis observe stop --target-dir . --summary \"<summary>\"` before implementation work.",
            reason="observation_mode_disallowed_mutation",
        )
    if (
        readiness.returncode == 2
        and is_mutation
        and not payload_is_aegis_bootstrap(payload)
        and not payload_is_aegis_pending_log(payload)
        and not payload_is_aegis_runtime_update(payload)
        and not payload_is_aegis_repair_apply(payload)
        and not payload_is_aegis_enforce(payload)
        and not payload_is_aegis_uninstall_apply(payload)
        and not post_closeout_taskmaster_completion
        and not post_closeout_delivery
    ):
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: Claude readiness is BLOCKED, so hookable persistent mutations are refused.\n\n"
            f"{readiness.stdout.strip()}\n\n"
            "Run the kickoff workflow or repair task/session/plan/work-tracking state before mutating files, memory, Git, Taskmaster, or other persistent surfaces.",
            reason="readiness_blocked",
            readiness_state=readiness.stdout.strip(),
        )
    if readiness.returncode not in {0, 2} and is_mutation:
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            f"Reason: readiness failed with exit {readiness.returncode}.\n\n"
            f"{readiness.stdout.strip()}\n{readiness.stderr.strip()}",
            reason=f"readiness_error:{readiness.returncode}",
            readiness_state=readiness.stdout.strip(),
        )

    pending_events = pending_tracking_events(root)
    if pending_events and is_mutation and not payload_is_aegis_log(payload):
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: pending S:W:H:E tracking must be logged before another persistent mutation.\n\n"
            f"Pending tracking:\n{format_pending_tracking(pending_events)}\n\n"
            "Run the pending-id repair command above, or use the explicit fallback "
            "`aegis log --handler <handler> --evidence <path-or-command> --note \"<past-tense note>\"`, "
            "so the active session, tracker, plan, implementation log, changelog, "
            "and handoff all contain the required S:W:H:E entry.",
            reason="pending_tracking",
            readiness_state=readiness.stdout.strip(),
        )

    if payload.tool_name in FILE_MUTATION_TOOLS:
        protected = [path for path in file_paths_from_payload(payload, root) if is_protected_path(path, root)]
        if protected:
            paths = "\n".join(f"  - {path}" for path in protected)
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Protected path(s):\n{paths}\n\n"
                "Claude may not edit protected Aegis/Codex-owned paths from this task.",
                reason="protected_path",
            )
        workflow_owned = [
            path for path in file_paths_from_payload(payload, root) if is_workflow_owned_path(path, root)
        ]
        if workflow_owned:
            paths = "\n".join(f"  - {path}" for path in workflow_owned)
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Workflow-owned path(s):\n{paths}\n\n"
                "Agents may not directly edit Aegis authority surfaces. Use sanctioned Aegis commands "
                "such as kickoff, log, handoff repair, or closeout so workflow evidence stays structured.",
                reason="workflow_owned_path",
            )

    if payload.tool_name == "Bash":
        violations = protected_bash_violations(bash_command(payload), root)
        if violations:
            details = "\n".join(f"  - {violation}" for violation in violations)
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: Bash\nCommand: {bash_command(payload)}\n"
                f"Violation(s):\n{details}\n\n"
                "Bash may not be used to bypass protected Aegis/Codex-owned path boundaries.",
                reason="protected_bash_violation",
            )

    if is_mcp_tool(payload.tool_name):
        sanctioned_aegis = payload_is_sanctioned_aegis_workflow_mutation(payload)
        protected = [
            normalize_path(path, root)
            for path in mcp_path_values(payload.tool_input)
            if is_protected_path(path, root)
        ]
        if protected:
            paths = "\n".join(f"  - {path}" for path in sorted(set(protected)))
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Protected path(s):\n{paths}\n\n"
                "MCP tools may not bypass protected Aegis/Codex-owned path boundaries.",
                reason="mcp_protected_path",
            )
        workflow_owned = [
            normalize_path(path, root)
            for path in mcp_path_values(payload.tool_input)
            if is_workflow_owned_path(path, root)
        ]
        if workflow_owned and not sanctioned_aegis:
            paths = "\n".join(f"  - {path}" for path in sorted(set(workflow_owned)))
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Workflow-owned path(s):\n{paths}\n\n"
                "MCP tools may not directly mutate Aegis authority surfaces. Use sanctioned Aegis MCP "
                "handlers so workflow evidence stays structured.",
                reason="mcp_workflow_owned_path",
            )

    return gate_allow_or_record(root, payload, reason="allow")


def pretooluse_gate_with_degraded_fallback(raw_payload: str) -> int:
    try:
        return pretooluse_gate(raw_payload)
    except Exception as exc:
        return degraded_pretooluse_fallback(raw_payload, exc)


def posttooluse_tracking() -> int:
    payload = load_payload()
    if payload is None:
        return 0
    root = project_root()
    record_pending_tracking_event(root, payload)
    return 0


def stop_gate() -> int:
    root = project_root()
    pending_events = pending_tracking_events(root)
    if not pending_events:
        if advisory_enabled(root):
            append_gate_decision(
                root,
                hook="stop",
                payload=Payload("Stop", {}),
                verdict="allow",
                reason="no_pending_tracking",
            )
        return 0
    message = (
        "BLOCKED by .claude/scripts/tracking-stop-gate.sh\n\n"
        "Reason: pending S:W:H:E tracking remains before session stop.\n\n"
        f"Pending tracking:\n{format_pending_tracking(pending_events)}\n\n"
        "Run the pending-id repair command above, or use the explicit fallback "
        "`aegis log --handler <handler> --evidence <path-or-command> --note \"<past-tense note>\"`, "
        "before ending the session."
    )
    if advisory_enabled(root):
        append_gate_decision(
            root,
            hook="stop",
            payload=Payload("Stop", {}),
            verdict="would_block",
            reason="pending_tracking",
        )
        advisory_message("stop", "pending_tracking")
        return 0
    return block(message)


def settings_has_required_hooks(settings_path: Path) -> tuple[bool, list[str]]:
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced in hook feedback.
        return False, [f"could not parse {settings_path}: {exc}"]
    if not isinstance(data, dict):
        return False, [f"{settings_path} is not a JSON object"]

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False, ["settings missing hooks object"]

    issues: list[str] = []
    pretool = hooks.get("PreToolUse")
    if not isinstance(pretool, list) or not any(
        isinstance(group, dict)
        and str(group.get("matcher") or "") == "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$"
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in pretool
    ):
        issues.append("required PreToolUse dispatcher hook missing or changed")

    posttool = hooks.get("PostToolUse")
    if not isinstance(posttool, list) or not any(
        isinstance(group, dict)
        and str(group.get("matcher") or "") == "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$"
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in posttool
    ):
        issues.append("required PostToolUse S:W:H:E tracking hook missing or changed")

    stop = hooks.get("Stop")
    if not isinstance(stop, list) or not any(
        isinstance(group, dict)
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/handoff-nudge.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in stop
    ):
        issues.append("required Stop handoff hook missing or changed")

    if not isinstance(stop, list) or not any(
        isinstance(group, dict)
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in stop
    ):
        issues.append("required Stop S:W:H:E tracking gate missing or changed")

    return not issues, issues


def config_change_guard() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return 0
    if not isinstance(data, dict):
        return 0

    source = str(data.get("source") or "")
    if source == "policy_settings":
        return 0

    file_path = data.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    root = project_root()
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    project_settings = (root / ".claude" / "settings.json").resolve()
    if path != project_settings:
        return 0

    ok, issues = settings_has_required_hooks(path)
    if ok:
        return 0
    details = "\n".join(f"  - {issue}" for issue in issues)
    return block(
        "BLOCKED by .claude/scripts/config-change-guard.sh\n\n"
        f"Settings file: {path}\n"
        f"Violation(s):\n{details}\n\n"
        "Project settings must keep the Claude runtime gate registered. Restore the PreToolUse dispatcher and Stop handoff hook before continuing."
    )


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: gate_lib.py <pretooluse|posttooluse|stop|path|bash>", file=sys.stderr)
        return 1
    command = sys.argv[1]
    if command == "pretooluse":
        return pretooluse_gate_with_degraded_fallback(sys.stdin.read())
    if command == "posttooluse":
        return posttooluse_tracking()
    if command == "stop":
        return stop_gate()
    if command == "path":
        return path_guard()
    if command == "bash":
        return bash_guard()
    if command == "configchange":
        return config_change_guard()
    print(f"unknown gate command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
