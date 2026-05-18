from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FILE_MUTATION_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
HOOKABLE_TOOLS = FILE_MUTATION_TOOLS | {"Bash"}

PROTECTED_PREFIXES = ("templates/", ".codex/")
PROTECTED_EXACT = {"CODEX.md"}
PROTECTED_NAME_PREFIXES = ("scripts/codex-", "scripts/template-")

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
REDIRECT_RE = re.compile(r"(?<![<])(?:>>|>)(?![>&])\s*([\"']?)([^\"'\s;&|]+)\1")
PYTHON_WRITE_RE = re.compile(
    r"(?:open|Path)\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"][^'\"]*[wa+][^'\"]*['\"])?"
    r"|write_text\(\s*['\"]",
    re.IGNORECASE,
)
MCP_READ_ONLY_TOOL_RE = re.compile(
    r"^mcp__.*__(get|list|read|search|find|query|show|help|check|resolve|fetch|open|is_|has_)",
    re.IGNORECASE,
)
MCP_MUTATION_TOOL_RE = re.compile(
    r"^mcp__.*__(add|create|update|set|write|edit|delete|remove|rename|move|parse|expand|generate|archive|init|initialize)",
    re.IGNORECASE,
)
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


def load_payload() -> Payload | None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    return Payload(tool_name=str(data.get("tool_name") or ""), tool_input=tool_input)


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
    return path.as_posix().lstrip("./")


def is_protected_path(path_text: str, root: Path | None = None) -> bool:
    rel = normalize_path(path_text, root)
    if rel in PROTECTED_EXACT:
        return True
    if rel.startswith(PROTECTED_PREFIXES):
        return True
    return rel.startswith(PROTECTED_NAME_PREFIXES)


def is_mcp_tool(tool_name: str) -> bool:
    return tool_name.startswith("mcp__")


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


def bash_is_mutation(command: str) -> bool:
    if not command.strip():
        return False
    if REDIRECT_RE.search(command):
        return True
    if re.search(r"(^|[;&|]\s*)(sed\b[^;\n]*\s-i\b|sed\s+-i\b)", command):
        return True
    if re.search(r"(^|[;&|]\s*)tee\b", command):
        return True
    if re.search(r"(^|[;&|]\s*)(rm|mv|cp|install|touch|chmod|chown|mkdir|rmdir)\b", command):
        return True
    if MUTATING_GIT_RE.search(command) or MUTATING_TASKMASTER_RE.search(command):
        return True
    if re.search(r"python3?\s+-c\s+['\"][^'\"]*(open|write_text)", command):
        return True
    return False


def protected_bash_violations(command: str, root: Path | None = None) -> list[str]:
    root = root or project_root()
    violations: list[str] = []

    for match in REDIRECT_RE.finditer(command):
        target = match.group(2)
        if is_protected_path(target, root):
            violations.append(f"redirection targets protected path {normalize_path(target, root)}")

    tokens = shlex_tokens(command)
    for index, token in enumerate(tokens):
        lower = token.lower()
        if lower == "sed" and "-i" in tokens[index + 1 : index + 4]:
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-") or candidate.startswith("s/"):
                    continue
                if is_protected_path(candidate, root):
                    violations.append(f"sed -i targets protected path {normalize_path(candidate, root)}")
        if lower == "tee":
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-"):
                    continue
                if is_protected_path(candidate, root):
                    violations.append(f"tee targets protected path {normalize_path(candidate, root)}")
        if lower in {"cp", "mv"}:
            for candidate in tokens[index + 1 :]:
                if candidate.startswith("-"):
                    continue
                if is_protected_path(candidate, root):
                    violations.append(f"{lower} references protected path {normalize_path(candidate, root)}")

    for match in PYTHON_WRITE_RE.finditer(command):
        target = match.group(1)
        if target and is_protected_path(target, root):
            violations.append(f"python write targets protected path {normalize_path(target, root)}")

    return sorted(set(violations))


def block(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


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
        "Bash may not be used to bypass protected Codex-owned path boundaries."
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


def payload_is_mutation(payload: Payload) -> bool:
    if payload.tool_name in FILE_MUTATION_TOOLS:
        return True
    if payload.tool_name == "Bash":
        return bash_is_mutation(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        return mcp_is_mutation(payload)
    return False


def pretooluse_gate() -> int:
    payload = load_payload()
    if payload is None:
        return 0
    if not is_hookable_tool(payload.tool_name):
        return 0

    root = project_root()
    is_mutation = payload_is_mutation(payload)
    readiness = run_readiness(root)
    if readiness.returncode == 2 and is_mutation:
        return block(
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: Claude readiness is BLOCKED, so hookable persistent mutations are refused.\n\n"
            f"{readiness.stdout.strip()}\n\n"
            "Run the kickoff workflow or repair task/session/plan/work-tracking state before mutating files, memory, Git, Taskmaster, or other persistent surfaces."
        )
    if readiness.returncode not in {0, 2} and is_mutation:
        return block(
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            f"Reason: readiness failed with exit {readiness.returncode}.\n\n"
            f"{readiness.stdout.strip()}\n{readiness.stderr.strip()}"
        )

    if payload.tool_name in FILE_MUTATION_TOOLS:
        protected = [path for path in file_paths_from_payload(payload, root) if is_protected_path(path, root)]
        if protected:
            paths = "\n".join(f"  - {path}" for path in protected)
            return block(
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Protected path(s):\n{paths}\n\n"
                "Claude may not edit Codex-owned paths from this task."
            )

    if payload.tool_name == "Bash":
        violations = protected_bash_violations(bash_command(payload), root)
        if violations:
            details = "\n".join(f"  - {violation}" for violation in violations)
            return block(
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: Bash\nCommand: {bash_command(payload)}\n"
                f"Violation(s):\n{details}\n\n"
                "Bash may not be used to bypass protected Codex-owned path boundaries."
            )

    if is_mcp_tool(payload.tool_name):
        protected = [
            normalize_path(path, root)
            for path in mcp_path_values(payload.tool_input)
            if is_protected_path(path, root)
        ]
        if protected:
            paths = "\n".join(f"  - {path}" for path in sorted(set(protected)))
            return block(
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Protected path(s):\n{paths}\n\n"
                "MCP tools may not bypass protected Codex-owned path boundaries."
            )

    return 0


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
        print("usage: gate_lib.py <pretooluse|path|bash>", file=sys.stderr)
        return 1
    command = sys.argv[1]
    if command == "pretooluse":
        return pretooluse_gate()
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
