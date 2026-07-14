from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

CODEX_APPLY_PATCH_TOOL = "apply_patch"
FILE_MUTATION_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", CODEX_APPLY_PATCH_TOOL}
HOOKABLE_TOOLS = FILE_MUTATION_TOOLS | {"Bash"}
REQUIRED_TOOL_INPUT_FIELDS = {
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path",),
    CODEX_APPLY_PATCH_TOOL: ("command",),
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
PENDING_TRACKING_SAMPLE_LIMIT = 5

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
AEGIS_WITNESS_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+witness\b",
    re.IGNORECASE,
)
AEGIS_CLOSEOUT_RE = re.compile(
    r"(^|[;&|]\s*)(aegis|(?:\./)?\.aegis/bin/aegis|python3?\s+-m\s+aegis_foundation\.cli)\s+closeout\b",
    re.IGNORECASE,
)
LOCALHOST_URL_RE = re.compile(
    r"^https?://(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?(?:/|$)", re.IGNORECASE
)
OBSERVATION_BROWSER_MCP_RE = re.compile(
    r"^mcp__(?:playwright|browser|puppeteer|chrome(?:[-_]devtools)?|chromium)__",
    re.IGNORECASE,
)
REDIRECT_RE = re.compile(r"(?<![<])(?:>>|>)(?![>&])\s*([\"']?)([^\"'\s;&|]+)\1")
APPLY_PATCH_PATH_RE = re.compile(
    r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$",
    re.MULTILINE,
)
APPLY_PATCH_MOVE_RE = re.compile(r"^\*\*\*\s+Move\s+to:\s*(.+?)\s*$", re.MULTILINE)
SHELL_CONTROL_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
HARD_POLICY_SHELL_CONTROL_TOKENS = {"&", "&&", "(", ")", ";", "|", "||"}
HARD_POLICY_SHELLS = {"bash", "dash", "ksh", "sh", "zsh"}
GITHUB_GOVERNANCE_PATH_RE = re.compile(
    r"(?:^|/|\s)repos/[^/\s]+/[^/\s]+/(?:branches/[^/\s]+/protection(?:/|\s|$)|rulesets(?:/|\s|$))",
    re.IGNORECASE,
)
GITHUB_GOVERNANCE_GRAPHQL_RE = re.compile(
    r"\b(?:create|delete|update)(?:BranchProtectionRule|RepositoryRuleset)\b",
    re.IGNORECASE,
)
UNSUPPORTED_READ_ONLY_SHELL_RE = re.compile(r"(`|\$\(|<<|<\(|>\(|\b(?:python|python3?)\s+-c\b)")
PYTHON_WRITE_RE = re.compile(
    r"(?:open|Path)\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"][^'\"]*[wa+][^'\"]*['\"])?"
    r"|write_text\(\s*['\"]",
    re.IGNORECASE,
)
# Pure inspection commands that only write to stdout. Anything here that CAN mutate
# in place (sed -i, sort -o, yq -i) is special-cased via READ_ONLY_WRITE_FLAG_GUARDS in
# bash_segment_is_read_only; file-writing via shell redirect is caught separately by
# is_persistent_redirect_target. Commands that write to a POSITIONAL output argument
# (uniq IN OUT, xxd -r IN OUT, tee) are deliberately NOT here — a flag guard cannot model
# positional-output arity, so they stay classified as mutations (TM 216 adversarial review).
READ_ONLY_SIMPLE_COMMANDS = {
    "basename",
    "cat",
    "cmp",
    "column",
    "comm",
    "cut",
    "date",
    "diff",
    "dirname",
    "echo",
    "false",
    "file",
    "fmt",
    "fold",
    "grep",
    "head",
    "jq",
    "ls",
    "nl",
    "od",
    "paste",
    "printf",
    "pwd",
    "realpath",
    "rg",
    "sed",
    "sort",
    "stat",
    "tail",
    "test",
    "tr",
    "true",
    "wc",
    "which",
    "yq",
}
# Commands in READ_ONLY_SIMPLE_COMMANDS that mutate a file when given a specific flag.
# Enumerate BOTH short and GNU long forms; command_has_write_flag matches bundled short
# clusters (sed -ni), short values (sort -ofile), and long --flag=value (sed --in-place=.bak).
READ_ONLY_WRITE_FLAG_GUARDS = {
    "sed": ("-i", "--in-place"),
    "yq": ("-i", "--inplace"),
    "sort": ("-o", "--output"),
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
    "brief",
    "replay",
    "witness",
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


class ApplyPatchParseError(ValueError):
    """Raised when a canonical Codex apply_patch payload cannot be classified safely."""


@dataclass(frozen=True)
class ApplyPatchOperation:
    operation: str
    source_path: str
    destination_path: str | None = None

    def as_event_record(self) -> dict[str, Any]:
        record = {
            "operation": "move" if self.destination_path is not None else self.operation,
            "source_path": self.source_path,
        }
        if self.destination_path is not None:
            record["destination_path"] = self.destination_path
            record["content_operation"] = self.operation
        return record


@dataclass(frozen=True)
class ParsedApplyPatch:
    operations: tuple[ApplyPatchOperation, ...]
    affected_paths: tuple[str, ...]
    patch_digest: str


@dataclass
class Payload:
    tool_name: str
    tool_input: dict[str, Any]
    # Hook-envelope attribution (capsule PR-1c): optional so every existing call site
    # and test remains valid; populated by parse_payload from the hook stdin JSON.
    session_id: str | None = None
    cwd: str | None = None
    parsed_apply_patch: ParsedApplyPatch | None = None


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
    return Payload(
        tool_name=str(data.get("tool_name") or ""),
        tool_input=tool_input,
        session_id=str(data["session_id"]) if isinstance(data.get("session_id"), str) else None,
        cwd=str(data["cwd"]) if isinstance(data.get("cwd"), str) else None,
    )


def load_payload_result(raw: str | None = None) -> Payload | PayloadLoadError:
    return parse_payload(sys.stdin.read() if raw is None else raw)


def load_payload() -> Payload | None:
    result = load_payload_result()
    return result if isinstance(result, Payload) else None


def payload_required_field_issue(payload: Payload) -> str | None:
    required_fields = REQUIRED_TOOL_INPUT_FIELDS.get(payload.tool_name)
    if not required_fields:
        return None
    if any(
        isinstance(payload.tool_input.get(field), str) and payload.tool_input.get(field)
        for field in required_fields
    ):
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
    _dual_write_gate_decision(root, record, payload)


def _dual_write_gate_decision(root: Path, record: dict[str, Any], payload: Payload | None) -> None:
    """Capsule PR-1c: mirror the advisory decision into the ledger, best-effort.

    The JSONL above stays the primary surface (aegis enforce status and existing
    tests keep reading it); the ledger twin shares the same payload_digest, which is
    the old-vs-new parity key. Any failure here is swallowed — dual-write must never
    break or delay a gate decision.
    """

    try:
        ledger_lib = _load_ledger_lib_module()
        if ledger_lib is None:
            return
        extra = {
            "hook": record.get("hook"),
            "verdict": record.get("verdict"),
            "reason": record.get("reason"),
            "mode": record.get("mode"),
            "source_commit": record.get("source_commit"),
        }
        if record.get("readiness_state"):
            extra["readiness_state"] = record.get("readiness_state")
        event = {
            "ts": record.get("ts"),
            "session_id": payload.session_id if payload is not None else None,
            "cwd": payload.cwd if payload is not None else None,
            "event_type": "gate_decision",
            "tool_name": record.get("tool_name"),
            "payload_digest": record.get("payload_digest"),
            "extra": {key: value for key, value in extra.items() if value is not None},
        }
        ledger = ledger_lib.open_ledger(cwd=root)
        try:
            ledger.append(event)
        finally:
            ledger.close()
    except Exception:  # noqa: BLE001 - dual-write is strictly best-effort.
        return


def advisory_enabled(root: Path) -> bool:
    return enforcement_mode(root) == "advisory"


def advisory_message(hook: str, reason: str) -> None:
    print(
        f"ADVISORY | {hook} would have blocked, but Aegis enforcement mode is advisory: {reason}",
        file=sys.stderr,
    )


# TM #201 recovery contract: every block reason maps to a copyable safe repair, a
# blast-radius tier, an audit destination, and an escalation path. Tier-a/b
# (workflow-state) blocks are break-glass-eligible; tier-c (protected paths, observation
# boundary, adversarial) are NEVER override-eligible — that is the line between a
# recovery valve and a generic bypass.
AEGIS_OVERRIDE_TOKEN_REL = ".aegis/state/override-token.json"
OVERRIDE_ELIGIBLE_REASONS = {"readiness_blocked", "pending_tracking"}
RECOVERY_CONTRACT: dict[str, dict[str, str]] = {
    "readiness_blocked": {
        "tier": "b",
        "repair": "./.aegis/bin/aegis repair --target-dir . --apply",
        "alt_repair": "python3 scripts/codex-task wizard kickoff --task <id> --slug <slug> --title '<title>'",
        "audit": ".aegis/reports/gate-decisions.jsonl + ledger",
        "escalation": 'If repair/kickoff cannot resolve it, break glass: aegis override --reason "<why>" (workflow-state only).',
        "override_eligible": "true",
    },
    "pending_tracking": {
        "tier": "a",
        "repair": 'aegis log --pending-id current   # or: aegis log --handler <h> --evidence <e> --note "<past-tense>"',
        "alt_repair": "",
        "audit": "sessions/current + active TRACKER.md + ledger",
        "escalation": 'If the pending event is unmatchable, break glass: aegis override --reason "<why>".',
        "override_eligible": "true",
    },
    "observation_mode_disallowed_mutation": {
        "tier": "c",
        "repair": "./.aegis/bin/aegis observe stop --target-dir . --summary '<what was observed>' --collect-artifacts",
        "alt_repair": "",
        "audit": ".aegis/reports/observation-report.json + ledger",
        "escalation": "Stop observation before implementation work. NOT override-eligible (boundary, not workflow state).",
        "override_eligible": "false",
    },
    "destructive_git_operation": {
        "tier": "c",
        "repair": "Use a normal feature branch and protected PR delivery; use `git restore --staged <path>` only for index cleanup.",
        "alt_repair": "For recovery, create a backup branch and use a reviewed revert or repair PR instead of destructive Git.",
        "audit": ".aegis/reports/gate-decisions.jsonl + ledger",
        "escalation": "Human-executed recovery outside the autonomous session. NOT override-eligible.",
        "override_eligible": "false",
    },
}
RECOVERY_CONTRACT_DEFAULT = {
    "tier": "c",
    "repair": "./.aegis/bin/aegis next --target-dir .   # inspect the prescribed next action",
    "alt_repair": "",
    "audit": ".aegis/reports/gate-decisions.jsonl + ledger",
    "escalation": "Resolve the underlying state. NOT override-eligible by default.",
    "override_eligible": "false",
}


def recovery_contract(reason: str) -> dict[str, str]:
    base = RECOVERY_CONTRACT.get(reason, RECOVERY_CONTRACT_DEFAULT)
    return {**RECOVERY_CONTRACT_DEFAULT, **base}


def recovery_block_suffix(reason: str) -> str:
    contract = recovery_contract(reason)
    lines = [
        "",
        "── Aegis recovery contract ──",
        f"blast-radius tier: {contract['tier']}",
        f"copyable safe repair: {contract['repair']}",
    ]
    if contract.get("alt_repair"):
        lines.append(f"alternative: {contract['alt_repair']}")
    lines.append(f"audit destination: {contract['audit']}")
    lines.append(f"escalation: {contract['escalation']}")
    return "\n".join(lines)


def _consume_override_token(root: Path, reason: str) -> dict[str, Any] | None:
    """One-shot, TTL-bounded break-glass token (TM #201).

    Honored ONLY for override-eligible (tier-a/b workflow-state) reasons, and consumed
    on use so it can never become a standing bypass. Returns the token record when a
    valid token is consumed, else None.
    """

    if reason not in OVERRIDE_ELIGIBLE_REASONS:
        return None
    path = root / AEGIS_OVERRIDE_TOKEN_REL
    token = _read_json_object(path)
    if not token:
        return None
    token_reason = str(token.get("reason_class") or "")
    if token_reason not in {"", "any", reason} and token_reason != reason:
        return None
    expires_at = str(token.get("expires_at") or "")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if expires_at and now > expires_at:
        try:
            path.unlink()
        except OSError:
            pass
        return None
    try:
        path.unlink()  # single use
    except OSError:
        return None
    return token


def gate_block_or_record(
    root: Path,
    payload: Payload,
    message: str,
    *,
    reason: str,
    readiness_state: str | None = None,
) -> int:
    token = _consume_override_token(root, reason)
    if token is not None:
        append_gate_decision(
            root,
            hook="pretooluse",
            payload=payload,
            verdict="allow",
            reason=f"break_glass_override:{reason}",
            readiness_state=readiness_state,
        )
        _record_override_use(root, payload, reason=reason, token=token)
        print(
            f"BREAK-GLASS: one-shot override consumed for {reason} "
            f"(reason: {token.get('note') or 'unspecified'}). Recorded to the ledger.",
            file=sys.stderr,
        )
        return 0
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
    return block(message + "\n" + recovery_block_suffix(reason))


def gate_hard_block(
    root: Path,
    payload: Payload,
    message: str,
    *,
    reason: str,
) -> int:
    """Record and deny a tier-c action regardless of ordinary enforcement mode.

    Advisory mode is intended to relax workflow ceremony, not destructive-operation
    safety. Recording is best-effort so an unavailable ledger can never turn this
    denial into an allow through the degraded-advisory fallback.
    """

    try:
        append_gate_decision(
            root,
            hook="pretooluse",
            payload=payload,
            verdict="block",
            reason=reason,
        )
    except Exception:  # noqa: BLE001 - audit failure must not weaken a hard denial.
        pass
    return block(message + "\n" + recovery_block_suffix(reason))


def _record_override_use(
    root: Path, payload: Payload, *, reason: str, token: dict[str, Any]
) -> None:
    ledger_lib = _load_ledger_lib_module()
    if ledger_lib is None:
        return
    try:
        ledger = ledger_lib.open_ledger(cwd=root)
        try:
            ledger.append(
                {
                    "event_type": "override",
                    "tool_name": payload.tool_name,
                    "payload_digest": payload_digest(payload),
                    "extra": {
                        "reason_class": reason,
                        "note": token.get("note"),
                        "minted_at": token.get("minted_at"),
                        "minted_by": token.get("minted_by"),
                    },
                }
            )
        finally:
            ledger.close()
    except Exception:  # noqa: BLE001 - audit is best-effort, never blocks recovery.
        return


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


def safe_expanduser(path_text: str) -> Path:
    """``Path.expanduser`` that survives sandboxed environments (no HOME, no passwd
    entry), where pathlib raises ``RuntimeError: Could not determine home directory``.
    The unexpanded literal is the safe fallback: a ``~``-prefixed path never matches a
    repo-relative protected/workflow path, and home-relative classification elsewhere
    checks the ``~`` prefix textually."""

    path = Path(path_text)
    try:
        return path.expanduser()
    except RuntimeError:
        return path


def normalize_path(path_text: str, root: Path | None = None) -> str:
    if not path_text:
        return ""
    path = safe_expanduser(path_text)
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


def apply_patch_command(payload: Payload) -> str:
    command = payload.tool_input.get("command")
    return command if isinstance(command, str) else ""


def _normalize_apply_patch_path(path_text: str, root: Path) -> str:
    if not path_text:
        raise ApplyPatchParseError("patch path is empty")
    if path_text != path_text.strip():
        raise ApplyPatchParseError("patch path has ambiguous leading or trailing whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in path_text):
        raise ApplyPatchParseError("patch path contains control characters")

    root_resolved = root.resolve()
    path = safe_expanduser(path_text)
    if path.is_absolute():
        raise ApplyPatchParseError("patch path must be repository-relative")
    candidate = root_resolved / path
    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(root_resolved).as_posix()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ApplyPatchParseError(f"patch path escapes the governed project: {path_text}") from exc
    if relative in {"", "."}:
        raise ApplyPatchParseError("patch path resolves to the project root")
    return relative


def parse_apply_patch(command: str, root: Path) -> ParsedApplyPatch:
    """Parse the canonical Codex apply_patch envelope without interpreting diff hunks.

    Aegis needs the operation graph and every affected path, not a second patch
    application engine. Structural directives are therefore strict while hunk bodies
    remain opaque after the operation-specific minimum checks below.
    """

    if not command:
        raise ApplyPatchParseError("apply_patch command is empty")
    lines = command.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or lines[0] != "*** Begin Patch":
        raise ApplyPatchParseError("patch must begin with an exact *** Begin Patch marker")
    if lines[-1] != "*** End Patch":
        raise ApplyPatchParseError("patch must end with an exact *** End Patch marker")
    if any(line == "*** Begin Patch" for line in lines[1:]):
        raise ApplyPatchParseError("nested or duplicate *** Begin Patch marker")
    if any(line == "*** End Patch" for line in lines[1:-1]):
        raise ApplyPatchParseError("early or duplicate *** End Patch marker")

    header_re = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
    move_re = re.compile(r"^\*\*\* Move to: (.+)$")
    operations: list[ApplyPatchOperation] = []
    current_action: str | None = None
    current_source: str | None = None
    current_destination: str | None = None
    current_body: list[str] = []

    def finalize_current() -> None:
        nonlocal current_action, current_source, current_destination, current_body
        if current_action is None or current_source is None:
            return
        body_has_content = any(line.strip() for line in current_body)
        if current_action == "add":
            if not current_body or not all(line.startswith("+") for line in current_body):
                raise ApplyPatchParseError("Add File requires one or more + content lines")
        elif current_action == "update":
            if not body_has_content and current_destination is None:
                raise ApplyPatchParseError(
                    "Update File requires a hunk body or Move to destination"
                )
        elif current_action == "delete" and body_has_content:
            raise ApplyPatchParseError("Delete File does not accept a patch body")
        operations.append(
            ApplyPatchOperation(
                operation=current_action,
                source_path=current_source,
                destination_path=current_destination,
            )
        )
        current_action = None
        current_source = None
        current_destination = None
        current_body = []

    for line in lines[1:-1]:
        header_match = header_re.fullmatch(line)
        if header_match:
            finalize_current()
            current_action = header_match.group(1).lower()
            current_source = _normalize_apply_patch_path(header_match.group(2), root)
            continue

        move_match = move_re.fullmatch(line)
        if move_match:
            if current_action != "update" or current_source is None:
                raise ApplyPatchParseError("Move to is valid only inside an Update File operation")
            if current_destination is not None:
                raise ApplyPatchParseError("Update File contains more than one Move to directive")
            if any(body_line.strip() for body_line in current_body):
                raise ApplyPatchParseError("Move to must appear before the Update File hunk body")
            current_destination = _normalize_apply_patch_path(move_match.group(1), root)
            if current_destination == current_source:
                raise ApplyPatchParseError("Move to destination must differ from its source path")
            continue

        if line.startswith("*** "):
            raise ApplyPatchParseError(f"unsupported patch directive: {line}")
        if current_action is None:
            if line.strip():
                raise ApplyPatchParseError("patch content appears outside an operation")
            continue
        current_body.append(line)

    finalize_current()
    if not operations:
        raise ApplyPatchParseError("patch contains no file operations")

    affected_paths: list[str] = []
    seen_paths: set[str] = set()
    for operation in operations:
        for path in (operation.source_path, operation.destination_path):
            if path is None:
                continue
            if path in seen_paths:
                raise ApplyPatchParseError(f"patch affects path more than once: {path}")
            seen_paths.add(path)
            affected_paths.append(path)

    return ParsedApplyPatch(
        operations=tuple(operations),
        affected_paths=tuple(affected_paths),
        patch_digest=sha256(command.encode("utf-8")).hexdigest(),
    )


def parsed_apply_patch(payload: Payload, root: Path) -> ParsedApplyPatch:
    if payload.tool_name != CODEX_APPLY_PATCH_TOOL:
        raise ApplyPatchParseError(f"tool is not {CODEX_APPLY_PATCH_TOOL}")
    if payload.parsed_apply_patch is None:
        payload.parsed_apply_patch = parse_apply_patch(apply_patch_command(payload), root)
    return payload.parsed_apply_patch


def apply_patch_event_metadata(payload: Payload, root: Path) -> dict[str, Any]:
    parsed = parsed_apply_patch(payload, root)
    return {
        "affected_paths": list(parsed.affected_paths),
        "operations": [operation.as_event_record() for operation in parsed.operations],
        "patch_digest": parsed.patch_digest,
    }


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
    return any(
        normalized.endswith(f"__{suffix}") for suffix in TASKMASTER_READ_ONLY_MCP_TOOL_SUFFIXES
    )


def is_hookable_tool(tool_name: str) -> bool:
    return tool_name in HOOKABLE_TOOLS or is_mcp_tool(tool_name)


def file_paths_from_payload(payload: Payload, root: Path | None = None) -> list[str]:
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        return list(parsed_apply_patch(payload, root or project_root()).affected_paths)
    candidates = [
        payload.tool_input.get("file_path"),
        payload.tool_input.get("notebook_path"),
    ]
    paths: list[str] = []
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            paths.append(normalize_path(candidate, root))
    if payload.tool_name == "apply_patch":
        patch = payload.tool_input.get("command")
        if isinstance(patch, str):
            for candidate in APPLY_PATCH_PATH_RE.findall(patch) + APPLY_PATCH_MOVE_RE.findall(
                patch
            ):
                paths.append(normalize_path(candidate, root))
    return list(dict.fromkeys(paths))


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
    # Browser-observation tools (chrome-devtools / playwright) drive a live browser, not the
    # project tree (TM 191). They are read-only w.r.t. the repo UNLESS the call writes a repo
    # path (e.g. take_screenshot/save with a path field) — so observation churn (snapshot,
    # click, navigate, console, evaluate) stops arming pending-tracking while a path-bearing
    # write still tracks. Conservative: any repo path field present => treat as a mutation.
    if "__chrome_devtools__" in normalized or "__playwright__" in normalized:
        return bool(mcp_path_values(payload.tool_input))
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


def target_dir_confinement_violation(
    target_dir: str | None, root: Path | None = None
) -> str | None:
    if not target_dir:
        return None
    root = (root or project_root()).resolve()
    raw = safe_expanduser(target_dir)
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


def hard_policy_shell_segments(command: str) -> list[list[str]]:
    """Tokenize shell control flow without splitting control characters inside quotes."""

    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        raw_tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = []
    current: list[str] = []
    for token in raw_tokens:
        if token in HARD_POLICY_SHELL_CONTROL_TOKENS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def strip_hard_policy_prefixes(tokens: list[str]) -> list[str]:
    stripped = list(tokens)
    while stripped and is_shell_assignment(stripped[0]):
        stripped = stripped[1:]
    if stripped and command_name(stripped[0]) == "env":
        stripped = stripped[1:]
        while stripped:
            token = stripped[0]
            if is_shell_assignment(token) or token in {"-i", "--ignore-environment"}:
                stripped = stripped[1:]
                continue
            if token in {"-u", "--unset", "-C", "--chdir"} and len(stripped) >= 2:
                stripped = stripped[2:]
                continue
            break
    while stripped and command_name(stripped[0]) in {"command", "builtin", "nohup"}:
        stripped = stripped[1:]
        while stripped and stripped[0].startswith("-"):
            stripped = stripped[1:]
    return stripped


def nested_shell_command(tokens: list[str]) -> str | None:
    if not tokens or command_name(tokens[0]) not in HARD_POLICY_SHELLS:
        return None
    for index, token in enumerate(tokens[1:], start=1):
        if token == "--command" or (
            token.startswith("-") and not token.startswith("--") and "c" in token[1:]
        ):
            return tokens[index + 1] if index + 1 < len(tokens) else None
        if not token.startswith("-"):
            break
    return None


def git_invocation(tokens: list[str], root: Path) -> tuple[Path, str, list[str]] | None:
    tokens = strip_hard_policy_prefixes(tokens)
    if not tokens or command_name(tokens[0]) != "git":
        return None
    index = 1
    git_root = root
    options_with_values = {
        "-c",
        "--config-env",
        "--exec-path",
        "--git-dir",
        "--namespace",
        "--super-prefix",
        "--work-tree",
    }
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token == "-C" and index + 1 < len(tokens):
            candidate = safe_expanduser(tokens[index + 1])
            try:
                git_root = (
                    (git_root / candidate).resolve()
                    if not candidate.is_absolute()
                    else candidate.resolve()
                )
            except (OSError, RuntimeError, ValueError):
                pass
            index += 2
            continue
        if token.startswith("-C") and token != "-C":
            candidate = safe_expanduser(token[2:])
            try:
                git_root = (
                    (git_root / candidate).resolve()
                    if not candidate.is_absolute()
                    else candidate.resolve()
                )
            except (OSError, RuntimeError, ValueError):
                pass
            index += 1
            continue
        if token in options_with_values:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in options_with_values
            if option.startswith("--")
        ):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return git_root, token.lower(), tokens[index + 1 :]
    return None


def delivery_default_branch(root: Path) -> str:
    policy = _read_json_object(root / "aegis.delivery-policy.json")
    repository = policy.get("repository") if isinstance(policy.get("repository"), dict) else {}
    configured = str(repository.get("default_branch") or "").strip()
    if configured:
        return configured
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0 and "/" in result.stdout.strip():
        return result.stdout.strip().split("/", 1)[1]
    return "main"


def short_option_enabled(args: list[str], option: str) -> bool:
    for token in args:
        if token == "--":
            break
        if token.startswith("-") and not token.startswith("--") and option in token[1:]:
            return True
    return False


def option_positionals(args: list[str], value_options: set[str]) -> list[str]:
    positionals: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            positionals.extend(args[index + 1 :])
            break
        if token in value_options:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=") for option in value_options if option.startswith("--")
        ):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        positionals.append(token)
        index += 1
    return positionals


def refspec_targets_branch(refspec: str, branch: str, current_branch: str) -> bool:
    if refspec.startswith("+"):
        return True
    clean = refspec
    destination = clean.split(":", 1)[1] if ":" in clean else clean
    destination = destination.removeprefix("refs/heads/")
    if "*" in destination:
        return True
    if destination == branch:
        return True
    return destination in {"@", "HEAD"} and current_branch == branch


def git_push_violation(git_root: Path, args: list[str], protected_branch: str) -> str | None:
    force_flags = {"--force", "--force-if-includes"}
    destructive_flags = {"--all", "--delete", "--mirror", "--prune"}
    if short_option_enabled(args, "f") or any(
        token in force_flags or token.startswith("--force-with-lease") for token in args
    ):
        return "force-pushing is prohibited"
    if any(token in destructive_flags for token in args):
        return "broad or deleting pushes are prohibited"
    positionals = option_positionals(
        args,
        {"--exec", "--push-option", "--receive-pack", "--repo", "-o"},
    )
    current_branch = current_git_branch(git_root)
    refspecs = positionals[1:] if positionals else []
    if not refspecs:
        if current_branch == protected_branch:
            return f"implicit push from protected branch {protected_branch!r} is prohibited"
        return None
    for refspec in refspecs:
        if refspec_targets_branch(refspec, protected_branch, current_branch):
            return f"direct push to protected branch {protected_branch!r} is prohibited"
    return None


def git_config_remote_violation(args: list[str]) -> str | None:
    mutation_flags = {
        "--add",
        "--remove-section",
        "--rename-section",
        "--replace-all",
        "--unset",
        "--unset-all",
    }
    positionals = option_positionals(
        args,
        {"--file", "--fixed-value", "--type", "--value", "--worktree"},
    )
    sensitive_indexes = [
        index
        for index, token in enumerate(positionals)
        if re.fullmatch(
            r"(?:remote\.[^.]+\.(?:pushurl|url)|url\..+\.insteadof)", token, re.IGNORECASE
        )
    ]
    if not sensitive_indexes:
        return None
    if any(token in mutation_flags for token in args):
        return "mutating remote URL configuration is prohibited"
    if any(index + 1 < len(positionals) for index in sensitive_indexes):
        return "replacing a remote URL is prohibited"
    return None


def destructive_git_violation(tokens: list[str], root: Path) -> str | None:
    invocation = git_invocation(tokens, root)
    if invocation is None:
        return None
    git_root, subcommand, args = invocation
    protected_branch = delivery_default_branch(git_root)
    if subcommand == "reset" and any(mode in args for mode in {"--hard", "--keep", "--merge"}):
        return "git reset with a worktree-discarding mode is prohibited"
    if subcommand == "clean" and not ("--dry-run" in args or short_option_enabled(args, "n")):
        return "git clean is prohibited unless it is a dry run"
    if subcommand == "push":
        return git_push_violation(git_root, args, protected_branch)
    if subcommand == "checkout":
        if "--force" in args or short_option_enabled(args, "f"):
            return "forced checkout is prohibited"
        if "--" in args and args.index("--") + 1 < len(args):
            return "checkout-based worktree restoration is prohibited"
    if subcommand == "switch" and (
        "--discard-changes" in args or "--force" in args or short_option_enabled(args, "f")
    ):
        return "forced branch switching is prohibited"
    if subcommand == "restore":
        staged_only = ("--staged" in args or short_option_enabled(args, "S")) and not (
            "--worktree" in args or short_option_enabled(args, "W")
        )
        if not staged_only:
            return "worktree restoration is prohibited; index-only `git restore --staged` remains allowed"
    if subcommand == "branch" and ("-D" in args or ("--delete" in args and "--force" in args)):
        return "forced local branch deletion is prohibited"
    if subcommand == "remote" and args and args[0] in {"remove", "rename", "rm", "set-url"}:
        return "remote replacement or removal is prohibited"
    if subcommand == "config":
        return git_config_remote_violation(args)
    return None


def option_argument(tokens: list[str], *options: str) -> str | None:
    for index, token in enumerate(tokens):
        if token in options and index + 1 < len(tokens):
            return tokens[index + 1]
        for option in options:
            if token.startswith(f"{option}="):
                return token[len(option) + 1 :]
            if (
                option.startswith("-")
                and not option.startswith("--")
                and token.startswith(option)
                and token != option
            ):
                return token[len(option) :]
    return None


def github_governance_violation(tokens: list[str]) -> str | None:
    tokens = strip_hard_policy_prefixes(tokens)
    if not tokens:
        return None
    name = command_name(tokens[0])
    joined = " ".join(tokens)
    if name not in {"curl", "gh"}:
        return None
    if GITHUB_GOVERNANCE_GRAPHQL_RE.search(joined):
        return "GitHub branch-protection or ruleset GraphQL mutation is prohibited"
    if not GITHUB_GOVERNANCE_PATH_RE.search(joined):
        return None
    if name == "gh" and len(tokens) >= 2 and tokens[1] == "api":
        method = (option_argument(tokens[2:], "--method", "-X") or "").upper()
        has_data = any(
            token in {"--field", "--input", "--raw-field", "-F", "-f"}
            or token.startswith(("--field=", "--input=", "--raw-field=", "-F", "-f"))
            for token in tokens[2:]
        )
        effective_method = method or ("POST" if has_data else "GET")
        if effective_method not in {"GET", "HEAD"}:
            return "GitHub branch-protection or ruleset mutation is prohibited"
    if name == "curl":
        method = (option_argument(tokens[1:], "--request", "-X") or "").upper()
        has_data = any(
            token
            in {
                "--data",
                "--data-binary",
                "--data-raw",
                "--form",
                "--json",
                "--upload-file",
                "-d",
                "-F",
                "-T",
            }
            or token.startswith(
                ("--data=", "--data-binary=", "--data-raw=", "--form=", "--json=", "-d", "-F", "-T")
            )
            for token in tokens[1:]
        )
        effective_method = method or ("POST" if has_data else "GET")
        if effective_method not in {"GET", "HEAD"}:
            return "GitHub branch-protection or ruleset mutation is prohibited"
    return None


def hard_policy_violations(command: str, root: Path, *, depth: int = 0) -> list[str]:
    if depth > 2:
        return ["nested shell command exceeds the destructive-operation inspection limit"]
    violations: list[str] = []
    for raw_tokens in hard_policy_shell_segments(command):
        tokens = strip_hard_policy_prefixes(raw_tokens)
        if not tokens:
            continue
        nested = nested_shell_command(tokens)
        if nested is not None:
            violations.extend(hard_policy_violations(nested, root, depth=depth + 1))
            continue
        git_violation = destructive_git_violation(tokens, root)
        if git_violation:
            violations.append(git_violation)
        governance_violation = github_governance_violation(tokens)
        if governance_violation:
            violations.append(governance_violation)
    return sorted(set(violations))


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


def aegis_cli_remainder(
    tokens: list[str], root: Path | None = None, *, allow_bare: bool = False
) -> list[str] | None:
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
    if (
        len(tokens) >= 4
        and command_name(executable) in {"python", "python3"}
        and tokens[1:3]
        == [
            "-m",
            "aegis_foundation.cli",
        ]
    ):
        return tokens[3:]
    return None


def read_only_aegis_remainder(remainder: list[str]) -> bool:
    return bool(remainder) and (
        remainder[0] in READ_ONLY_AEGIS_SUBCOMMANDS
        or (len(remainder) >= 2 and remainder[0] == "ledger" and remainder[1] == "path")
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
    for segment in [
        segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()
    ]:
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
    return read_only_aegis_remainder(
        remainder
    ) and not aegis_cli_target_dir_violation_from_remainder(remainder)


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
        return (
            len(tokens) >= 3
            and tokens[1:3] == ["-m", "pytest"]
            and not has_read_only_test_output_option(tokens)
        )
    if tokens[0] == "uv" and len(tokens) >= 3 and tokens[1] == "run":
        return read_only_python_test_segment(tokens[2:])
    return False


def read_only_find_segment(tokens: list[str]) -> bool:
    return (
        tokens[0] == "find"
        and "-delete" not in tokens
        and "-exec" not in tokens
        and "-execdir" not in tokens
    )


def command_has_write_flag(arg_tokens: list[str], write_flags: tuple[str, ...]) -> bool:
    """Detect a file-mutating flag among a command's args, robust to bundled short
    clusters. A short flag like ``-i`` mutates whether written ``-i``, ``-i.bak``,
    ``-ni`` (bundled with another boolean), or ``-uo`` (cluster ending in a value flag);
    a long flag like ``--inplace`` must match a whole token. Scanning stops at a literal
    ``--`` end-of-options terminator, after which tokens are operands, not flags."""

    short_letters = {
        flag[1:]
        for flag in write_flags
        if flag.startswith("-") and not flag.startswith("--") and len(flag) == 2
    }
    long_flags = {flag for flag in write_flags if flag.startswith("--")}
    for token in arg_tokens:
        if token == "--":
            break
        # Long form, bare or with attached value: --output, --in-place=.bak.
        if token in long_flags or any(token.startswith(flag + "=") for flag in long_flags):
            return True
        if token.startswith("-") and not token.startswith("--"):
            # Alpha prefix of the short cluster, e.g. "-ni"->"ni", "-i.bak"->"i", "-uo"->"uo".
            cluster = ""
            for char in token[1:]:
                if char.isalpha():
                    cluster += char
                else:
                    break
            if any(letter in cluster for letter in short_letters):
                return True
    return False


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
        write_flags = READ_ONLY_WRITE_FLAG_GUARDS.get(name)
        if write_flags and command_has_write_flag(tokens[1:], write_flags):
            return False
        return True
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
            if (
                token.startswith("-D")
                or token.startswith("-K")
                or token.startswith("-o")
                or token.startswith("-c")
            ):
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
    return bool(segments) and all(
        bash_segment_is_observation_tooling(segment) for segment in segments
    )


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
    return bash_has_trusted_aegis_subcommand(
        command, {"start", "kickoff"}
    ) or bash_is_aegis_observe_start(command)


def bash_is_aegis_log(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"log"})


# codex-task evidence/workflow subcommands are this repo's analog of `aegis log`:
# sanctioned self-writes to the tracking surfaces (or read-only validation). They must
# not arm pending-tracking against themselves (TM 216 — fix-creates-failure loop).
CODEX_TASK_LOGGING_SUBCOMMANDS = {
    ("work-tracking", "update"),
    ("work-tracking", "audit"),
    ("sessions", "update"),
    ("plan", "sync"),
    ("scanner", "run"),
}


def codex_task_remainder(tokens: list[str], root: Path | None = None) -> list[str] | None:
    """Return the subcommand tokens after a `scripts/codex-task` invocation, else None."""

    if len(tokens) < 2:
        return None
    root = root or project_root()
    if command_name(tokens[0]) not in {"python", "python3"}:
        return None
    if normalize_path(tokens[1], root) == "scripts/codex-task":
        return tokens[2:]
    return None


def _segment_is_codex_task_logging(segment: str) -> bool:
    tokens = strip_shell_prefixes(shlex_tokens(segment))
    remainder = codex_task_remainder(tokens)
    return (
        bool(remainder)
        and len(remainder) >= 2
        and (remainder[0], remainder[1]) in CODEX_TASK_LOGGING_SUBCOMMANDS
    )


def bash_is_codex_task_logging(command: str) -> bool:
    """Whole-payload-AND: a codex-task logging command excludes the payload from
    pending-tracking only when every other segment is read-only. Without this,
    ``codex-task plan sync; rm -rf src`` would exclude the whole payload and let the
    mutation escape (TM 216 adversarial review)."""

    saw_logging = False
    for segment in [
        segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()
    ]:
        if _segment_is_codex_task_logging(segment):
            saw_logging = True
        elif not bash_is_read_only(segment):
            return False
    return saw_logging


def payload_is_codex_task_logging(payload: Payload) -> bool:
    return payload.tool_name == "Bash" and bash_is_codex_task_logging(bash_command(payload))


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


def bash_is_aegis_override(command: str) -> bool:
    segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    if len(segments) != 1:
        return False
    tokens = strip_shell_prefixes(shlex_tokens(segments[0]))
    remainder = aegis_cli_remainder(tokens, project_root(), allow_bare=False)
    return bool(remainder) and remainder[0] == "override"


def payload_is_aegis_override(payload: Payload) -> bool:
    """Minting a break-glass token must itself run while BLOCKED (TM #201).

    It writes only `.aegis/state/override-token.json` and is rate-limited + audited; it
    does not perform the user's mutation, so sanctioning it is not a bypass.
    """

    if payload.tool_name == "Bash":
        return bash_is_aegis_override(bash_command(payload))
    if is_mcp_tool(payload.tool_name):
        normalized = payload.tool_name.lower().replace(".", "_").replace("-", "_")
        return "aegis" in normalized and normalized.endswith("override")
    return False


def mcp_tool_is_aegis_verify(tool_name: str) -> bool:
    if not is_mcp_tool(tool_name):
        return False
    normalized = tool_name.lower().replace(".", "_").replace("-", "_")
    return "aegis" in normalized and normalized.endswith("verify")


def bash_is_aegis_closeout(command: str) -> bool:
    return bash_has_trusted_aegis_subcommand(command, {"closeout"})


def _segment_is_trusted_aegis(
    segment: str,
    subcommands: set[str],
    root: Path,
    *,
    require_apply: bool,
    required_option: str | None,
    handoff_repair: bool,
) -> bool:
    tokens = strip_shell_prefixes(shlex_tokens(segment))
    remainder = aegis_cli_remainder(tokens, root, allow_bare=False)
    if not remainder:
        return False
    if handoff_repair:
        return len(remainder) >= 2 and remainder[0] == "handoff" and remainder[1] == "repair"
    if remainder[0] not in subcommands:
        return False
    if require_apply and "--apply" not in remainder[1:]:
        return False
    if required_option and required_option not in remainder[1:]:
        return False
    return True


def bash_has_trusted_aegis_subcommand(
    command: str,
    subcommands: set[str],
    *,
    require_apply: bool = False,
    required_option: str | None = None,
    handoff_repair: bool = False,
) -> bool:
    """A compound command is a trusted aegis invocation only when at least one segment
    is the trusted subcommand AND every other segment is itself read-only. Otherwise a
    real mutation chained with a sanctioned command (``aegis log && rm -rf src``) would
    be wrongly trusted — escaping both the readiness gate and pending-tracking (TM 216
    adversarial review)."""

    root = project_root()
    saw_trusted = False
    for segment in [
        segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()
    ]:
        if _segment_is_trusted_aegis(
            segment,
            subcommands,
            root,
            require_apply=require_apply,
            required_option=required_option,
            handoff_repair=handoff_repair,
        ):
            saw_trusted = True
        elif not bash_is_read_only(segment):
            return False
    return saw_trusted


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
    """Whole-payload-AND, like bash_has_trusted_aegis_subcommand: a trusted nested
    invocation only when every non-trusted segment is read-only."""

    root = project_root()
    saw_trusted = False
    for segment in [
        segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()
    ]:
        tokens = strip_shell_prefixes(shlex_tokens(segment))
        remainder = aegis_cli_remainder(tokens, root, allow_bare=False)
        if len(remainder or []) >= 2 and remainder[0] == first and remainder[1] in seconds:
            saw_trusted = True
        elif not bash_is_read_only(segment):
            return False
    return saw_trusted


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
    protected = [
        path for path in file_paths_from_payload(payload, root) if is_protected_path(path, root)
    ]
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
    if not readiness.is_file():
        return subprocess.CompletedProcess(
            ["bash", str(readiness), "--quick", "--root", str(root)],
            2,
            stdout="BLOCKED | readiness runtime is missing\n",
            stderr="",
        )
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
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


def degraded_event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def write_degraded_event(
    root: Path,
    payload: Payload,
    reason: str,
    raw_payload: str,
    *,
    mode: str = "degraded_allow",
    action_class: str = "non_destructive",
    trace: str = "",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    existing_events = degraded_events(root)
    previous_hash = str(existing_events[-1].get("event_hash") or "") if existing_events else ""
    event = {
        "id": sha1(
            f"{now}|{payload.tool_name}|{reason}|{raw_payload_preview(raw_payload)}".encode("utf-8")
        ).hexdigest()[:12],
        "created_at": now,
        "gate": "pretooluse",
        "mode": mode,
        "action_class": action_class,
        "tool": payload.tool_name,
        "reason": reason,
        "raw_preview": raw_payload_preview(raw_payload),
        "previous_event_hash": previous_hash,
    }
    if trace:
        event["traceback"] = trace
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
    return (
        isinstance(work, dict)
        and work.get("mode") == "observation"
        and work.get("status") == "in-progress"
    )


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


def hook_invoking_agent(payload: Payload) -> str | None:
    explicit = str(os.environ.get("AEGIS_INVOKING_AGENT") or "").strip().lower()
    if explicit in {"claude", "codex", "gemini"}:
        return explicit
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        return "codex"
    if os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_CI") == "1":
        return "codex"
    return None


def clear_client_reload_marker(
    root: Path,
    invoking_agent: str | None = None,
    *,
    agent: str | None = None,
) -> None:
    marker = root / AEGIS_CLIENT_RELOAD_REL
    if not marker.exists():
        return
    state = _read_json_object(marker)
    normalized_agent = str(agent or invoking_agent or "").strip().lower()
    raw_agents = state.get("agents")
    pending_agents = (
        [
            str(value).strip().lower()
            for value in raw_agents
            if str(value).strip().lower() in {"claude", "codex", "gemini"}
        ]
        if isinstance(raw_agents, list)
        else []
    )
    legacy_agent = str(state.get("agent") or "").strip().lower()
    if legacy_agent in {"claude", "codex", "gemini"}:
        pending_agents.append(legacy_agent)
    pending_agents = list(dict.fromkeys(pending_agents))
    if not pending_agents:
        # Backward-compatible marker written before per-agent reload tracking.
        marker.unlink()
        return
    if normalized_agent not in pending_agents:
        return
    remaining = [value for value in pending_agents if value != normalized_agent]
    if not remaining:
        marker.unlink()
        return
    state["agents"] = remaining
    state["agent"] = remaining[0] if len(remaining) == 1 else "multi"
    changed_by_agent = state.get("changed_paths_by_agent")
    if isinstance(changed_by_agent, dict):
        changed_by_agent = {
            key: value for key, value in changed_by_agent.items() if key in remaining
        }
        state["changed_paths_by_agent"] = changed_by_agent
        state["changed_paths"] = sorted(
            {
                str(path)
                for paths in changed_by_agent.values()
                if isinstance(paths, list)
                for path in paths
                if isinstance(path, str) and path
            }
        )
    clearance_by_agent = state.get("clearance_by_agent")
    if isinstance(clearance_by_agent, dict):
        clearance_by_agent = {
            key: value for key, value in clearance_by_agent.items() if key in remaining
        }
        state["clearance_by_agent"] = clearance_by_agent
        state["clearance"] = clearance_by_agent.get(remaining[0], {})
    write_json(marker, state)


def pending_tracking_path(root: Path) -> Path:
    return root / AEGIS_PENDING_TRACKING_REL


def pending_tracking_events(root: Path) -> list[dict[str, Any]]:
    payload = read_json(pending_tracking_path(root))
    if not payload:
        return []
    events = payload.get("events")
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


def required_pending_tracking_events(root: Path) -> list[dict[str, Any]]:
    """Return events that still require strict-mode reconciliation.

    Advisory events are retained audit evidence. Missing or unknown provenance remains
    required so strict enforcement never infers that an untrusted event is safe.
    """

    return [
        event
        for event in pending_tracking_events(root)
        if str(event.get("mode") or "").strip().lower() != "advisory"
    ]


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
            "updated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
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
    candidate = safe_expanduser(evidence)
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
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        return _file_snapshot_location(root, evidence, source="codex_apply_patch_file_snapshot")
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
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        return "codex:apply_patch"
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
        return (
            "aegis" in normalized
            and normalized.endswith("uninstall")
            and payload.tool_input.get("apply") is True
        )
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
    if work is None or required_pending_tracking_events(root):
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
    if work is None or required_pending_tracking_events(root):
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
        or payload_is_codex_task_logging(payload)
    ):
        return
    handler = payload_handler(payload)
    patch_metadata: dict[str, Any] | None = None
    patch_parse_error: str | None = None
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        try:
            patch_metadata = apply_patch_event_metadata(payload, root)
            evidence = str(patch_metadata["affected_paths"][0])
            evidence_location = payload_evidence_location(payload, root, evidence)
        except ApplyPatchParseError as exc:
            patch_parse_error = str(exc)
            digest = sha256(apply_patch_command(payload).encode("utf-8")).hexdigest()
            patch_metadata = {
                "affected_paths": [],
                "operations": [],
                "patch_digest": digest,
            }
            evidence = f"apply_patch:{digest[:12]}"
            evidence_location = None
    else:
        evidence = payload_evidence(payload, root)
        evidence_location = payload_evidence_location(payload, root, evidence)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    task = work.get("task") if isinstance(work.get("task"), dict) else {}
    task_id = str(task.get("id") or "")
    slug = str(task.get("slug") or "")
    identity_suffix = str(patch_metadata.get("patch_digest")) if patch_metadata else evidence
    event_id = sha1(
        f"{now}|{payload.tool_name}|{handler}|{identity_suffix}".encode("utf-8")
    ).hexdigest()[:12]
    events = pending_tracking_events(root)
    for event in events:
        same_event = event.get("evidence") == evidence and event.get("handler") == handler
        if patch_metadata is not None:
            same_event = event.get("handler") == handler and event.get(
                "patch_digest"
            ) == patch_metadata.get("patch_digest")
        if same_event:
            event["updated_at"] = now
            if enforcement_mode(root) == "strict":
                event["mode"] = "strict"
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
    if patch_metadata is not None:
        event.update(patch_metadata)
    if patch_parse_error is not None:
        event["parse_error"] = patch_parse_error
    events.append(event)
    write_pending_tracking_events(root, events)


def format_pending_tracking(events: list[dict[str, Any]]) -> str:
    lines = []
    for event in events[:PENDING_TRACKING_SAMPLE_LIMIT]:
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
            f'{event_id} --note "<past-tense note>" '
            "--plan-step <plan-step-id> --plan-status completed"
        )
    omitted = len(events) - min(len(events), PENDING_TRACKING_SAMPLE_LIMIT)
    if omitted:
        lines.append(
            f"  ... {omitted} more pending events; inspect {AEGIS_PENDING_TRACKING_REL} "
            f"for all {len(events)}."
        )
    return "\n".join(lines)


def degraded_pretooluse_fallback(raw_payload: str, exc: BaseException) -> int:
    loaded = parse_payload(raw_payload)
    reason = f"{type(exc).__name__}: {exc}"
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-4000:]
    if isinstance(loaded, PayloadLoadError):
        return block_unclassifiable_payload(
            f"gate infrastructure failed after an unclassifiable payload: {reason}",
            loaded.raw_preview,
        )
    root = project_root()
    if degraded_payload_is_non_destructive(loaded):
        event = write_degraded_event(root, loaded, reason, raw_payload, trace=trace)
        print(
            "DEGRADED | pretooluse gate infrastructure failed; allowed conservative non-destructive action "
            f"and wrote {AEGIS_DEGRADED_EVENTS_REL} event {event['id']}",
            file=sys.stderr,
        )
        return 0
    # Advisory contract: enforcement mode advisory NEVER hard-blocks — an infra
    # failure records a degraded event (with traceback) and allows, loudly. Strict
    # mode keeps failing closed below. The advisory check itself is best-effort:
    # if it crashes too, fail closed.
    try:
        if advisory_enabled(root):
            event = write_degraded_event(
                root,
                loaded,
                reason,
                raw_payload,
                mode="degraded_advisory_allow",
                action_class="mutation_or_unsafe",
                trace=trace,
            )
            print(
                "DEGRADED-ADVISORY | pretooluse gate infrastructure failed while evaluating a mutation; "
                f"enforcement mode is advisory so the action is allowed and recorded as "
                f"{AEGIS_DEGRADED_EVENTS_REL} event {event['id']}. Details: {reason}",
                file=sys.stderr,
            )
            return 0
    except Exception:  # noqa: BLE001 - double infra failure falls through to fail-closed.
        pass
    return block(
        "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
        f"Tool: {loaded.tool_name}\n"
        "Reason: PreToolUse gate infrastructure failed while evaluating a mutation or unsafe action.\n\n"
        f"Details: {reason}\n\n"
        f"Traceback (for diagnosis):\n{trace}\n"
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

    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        try:
            parsed_apply_patch(payload, root)
        except ApplyPatchParseError as exc:
            reason = f"invalid_apply_patch: {exc}"
            if advisory_enabled(root):
                append_gate_decision(
                    root,
                    hook="pretooluse",
                    payload=payload,
                    verdict="would_block",
                    reason=reason,
                )
                advisory_message("pretooluse", reason)
                return 0
            return block_unclassifiable_payload(
                reason, raw_payload_preview(apply_patch_command(payload))
            )

    if payload.tool_name == "Bash":
        try:
            hard_violations = hard_policy_violations(bash_command(payload), root)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - safety classifier failures deny, even in advisory mode.
            hard_violations = [
                f"destructive-operation classifier failed closed ({type(exc).__name__}: {exc})"
            ]
        if hard_violations:
            details = "\n".join(f"  - {violation}" for violation in hard_violations)
            return gate_hard_block(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: Bash\nCommand: {bash_command(payload)}\n"
                f"Non-overridable violation(s):\n{details}\n\n"
                "Aegis advisory mode relaxes workflow ceremony, not destructive Git or repository-governance safety.",
                reason="destructive_git_operation",
            )

    clear_client_reload_marker(root, hook_invoking_agent(payload))
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
    post_closeout_taskmaster_completion = payload_is_post_closeout_taskmaster_completion(
        root, payload
    )
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
            'Stop observation with `./.aegis/bin/aegis observe stop --target-dir . --summary "<summary>"` before implementation work.',
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
        and not payload_is_aegis_override(payload)
        and not payload_is_aegis_uninstall_apply(payload)
        and not post_closeout_taskmaster_completion
        and not post_closeout_delivery
    ):
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: Aegis readiness is BLOCKED, so hookable persistent mutations are refused.\n\n"
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

    pending_events = required_pending_tracking_events(root)
    if pending_events and is_mutation and not payload_is_aegis_log(payload):
        return gate_block_or_record(
            root,
            payload,
            "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
            f"Tool: {payload.tool_name}\n"
            "Reason: pending S:W:H:E tracking must be logged before another persistent mutation.\n\n"
            f"Pending tracking:\n{format_pending_tracking(pending_events)}\n\n"
            "Run the pending-id repair command above, or use the explicit fallback "
            '`aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"`, '
            "so the active session, tracker, plan, implementation log, changelog, "
            "and handoff all contain the required S:W:H:E entry.",
            reason="pending_tracking",
            readiness_state=readiness.stdout.strip(),
        )

    if payload.tool_name in FILE_MUTATION_TOOLS:
        protected = [
            path for path in file_paths_from_payload(payload, root) if is_protected_path(path, root)
        ]
        if protected:
            paths = "\n".join(f"  - {path}" for path in protected)
            return gate_block_or_record(
                root,
                payload,
                "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
                f"Tool: {payload.tool_name}\n"
                f"Protected path(s):\n{paths}\n\n"
                "Task-scoped agents may not edit protected Aegis-owned or agent-owned paths.",
                reason="protected_path",
            )
        workflow_owned = [
            path
            for path in file_paths_from_payload(payload, root)
            if is_workflow_owned_path(path, root)
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
    _maybe_emit_scope_nudge(root, payload)
    return 0


def _maybe_emit_scope_nudge(root: Path, payload: Payload) -> None:
    """Capsule PR-1d (spec section 2.1): ONE non-blocking additionalContext nudge per
    branch when scope inference was ambiguous. Fully failure-proof — this runs on the
    synchronous hook path and must never gain a failure mode."""

    try:
        ledger_lib = _load_ledger_lib_module()
        if ledger_lib is None:
            return
        store = ledger_lib.store_path(cwd=root)
        if not store.is_file():
            return
        branch = _record_branch(payload.cwd or str(root))
        if not branch:
            return
        ledger = ledger_lib.open_ledger(cwd=root)
        try:
            events = _scope_events_for_branch(ledger, branch)
            needs = any(
                event.get("extra", {}).get("needs_confirmation")
                and not event.get("extra", {}).get("confirmed")
                for event in events
            )
            confirmed = any(event.get("extra", {}).get("confirmed") for event in events)
            nudged = any(event.get("extra", {}).get("nudge") for event in events)
            if not needs or confirmed or nudged:
                return
            ledger.append(
                {
                    "session_id": payload.session_id,
                    "branch": branch,
                    "event_type": "scope",
                    "extra": {"nudge": True},
                }
            )
        finally:
            ledger.close()
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            f"Aegis scope note: branch '{branch}' has no inferable task id. "
                            "If this work belongs to a task, run "
                            "`aegis scope set <task-id> [path-globs...]` once to record its scope "
                            "(used by the delivery witness). This is advisory and will not be asked again."
                        ),
                    }
                }
            )
        )
    except Exception:  # noqa: BLE001 - nudge is strictly best-effort.
        return


DELIVERY_COMMAND_RE = re.compile(
    r"(^|[;&|]\s*)(git\s+push\b|gh\s+pr\s+(create|merge|ready)\b)",
    re.IGNORECASE,
)
TASKMASTER_TASKS_JSON_SUFFIX = ".taskmaster/tasks/tasks.json"
CAPSULE_RISK_SEED_SUFFIX = ".aegis/capsule/risk-seed.json"
AEGIS_BRIEF_REL = ".aegis/brief.json"
TASK_BRANCH_RE = re.compile(r"task-?(\d+)", re.IGNORECASE)
BARE_REDIRECT_OP_RE = re.compile(r"^(?:\d?>{1,2}|<|&>{1,2})$")
REDIRECT_TOKEN_RE = re.compile(r"^(?:\d?>{1,2}\S+|\d?>>?&\d|<\S+|&>{1,2}\S+)$")


def load_brief(root: Path) -> dict[str, Any]:
    """Read `.aegis/brief.json` (capsule PR-1d gate registry); {} on any failure."""

    data = _read_json_object(root / AEGIS_BRIEF_REL)
    return data if isinstance(data, dict) else {}


def _normalize_command_text(text: str) -> str:
    tokens = strip_shell_prefixes(shlex_tokens(text))
    kept: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if BARE_REDIRECT_OP_RE.match(token):
            # A bare redirect operator consumes the following target token too.
            skip_next = True
            continue
        if REDIRECT_TOKEN_RE.match(token):
            continue
        kept.append(token)
    return " ".join(kept)


def normalized_command_segments(command: str) -> list[str]:
    """Normalized candidate forms of a Bash command for gate-registry matching.

    Splits on shell control operators, strips env-assignment prefixes and redirect
    tokens, collapses whitespace, and joins adjacent `cd X` + command pairs back into
    `cd X && command` so cd-prefix patterns match alongside `-C`/`--dir` variants.
    """

    raw_segments = [segment for segment in SHELL_CONTROL_SPLIT_RE.split(command) if segment.strip()]
    normalized = [
        form for form in (_normalize_command_text(segment) for segment in raw_segments) if form
    ]
    candidates = list(normalized)
    for index in range(len(normalized) - 1):
        if normalized[index].startswith("cd "):
            candidates.append(f"{normalized[index]} && {normalized[index + 1]}")
    return candidates


def match_gate_command(command: str, gates: dict[str, Any]) -> tuple[str, str] | None:
    """Return (package, gate) when the command matches a registered gate pattern.

    Matching is exact equality on normalized forms; pattern VALUES are per-repo
    configuration from `.aegis/brief.json`, never hardcoded here.
    """

    if not gates or not command:
        return None
    candidates = set(normalized_command_segments(command))
    if not candidates:
        return None
    for package, package_gates in gates.items():
        if not isinstance(package_gates, dict):
            continue
        for gate, patterns in package_gates.items():
            if not isinstance(patterns, (list, tuple)):
                continue
            for pattern in patterns:
                if isinstance(pattern, str) and _normalize_command_text(pattern) in candidates:
                    return str(package), str(gate)
    return None


def _record_head_commit(cwd: str | None) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = result.stdout.strip()
    return commit or None


def _scope_events_for_branch(ledger: Any, branch: str) -> list[dict[str, Any]]:
    return [event for event in ledger.read(event_type="scope") if event.get("branch") == branch]


def _ensure_scope_record(
    ledger: Any,
    *,
    branch: str | None,
    session_id: Any,
    cwd: Any,
    agent_id: str | None,
    agent_type: str | None,
    parent_agent_id: str | None,
    brief: dict[str, Any],
) -> None:
    """Capsule PR-1d (spec section 2.1): infer a scope record at the first recorded
    mutation on a new branch. One record per branch; never blocks, never re-asks."""

    if not branch:
        return
    existing = _scope_events_for_branch(ledger, branch)
    if any(not event.get("extra", {}).get("nudge") for event in existing):
        return
    match = TASK_BRANCH_RE.search(branch)
    task_id = match.group(1) if match else None
    gates = brief.get("gates") if isinstance(brief.get("gates"), dict) else {}
    source_roots = brief.get("source_roots") if isinstance(brief.get("source_roots"), list) else []
    ledger.append(
        {
            "session_id": session_id,
            "branch": branch,
            "cwd": cwd,
            "event_type": "scope",
            "agent_id": agent_id,
            "agent_type": agent_type,
            "parent_agent_id": parent_agent_id,
            "extra": {
                "task_id": task_id,
                "path_globs": list(source_roots),
                "gates": sorted(
                    f"{package}:{gate}"
                    for package, package_gates in gates.items()
                    if isinstance(package_gates, dict)
                    for gate in package_gates
                ),
                "inferred": True,
                "needs_confirmation": task_id is None,
            },
        }
    )


def _load_ledger_lib_module():
    script = Path(__file__).resolve().parent / "ledger_lib.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_gate_ledger_lib", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record_branch(cwd: str | None) -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    branch = result.stdout.strip()
    return branch or None


def _hook_adapter(data: dict[str, Any]) -> str:
    return "codex" if data.get("model") or data.get("turn_id") else "claude"


def _response_mappings(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _response_mappings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _response_mappings(nested)


def _hook_outcome(data: dict[str, Any]) -> str:
    hook_event = str(data.get("hook_event_name") or "")
    if hook_event == "PostToolUseFailure":
        return "fail"
    if data.get("is_interrupt") is True:
        return "interrupted"
    response = data.get("tool_response")
    for mapping in _response_mappings(response):
        if mapping.get("interrupted") is True or mapping.get("is_interrupt") is True:
            return "interrupted"
        if mapping.get("is_error") is True or mapping.get("isError") is True:
            return "fail"
        if mapping.get("success") is False or mapping.get("ok") is False:
            return "fail"
        status = str(mapping.get("status") or "").strip().lower()
        if status in {"cancelled", "canceled", "interrupted"}:
            return "interrupted"
        if status in {"error", "failed", "failure"}:
            return "fail"
        for key in ("exit_code", "exitCode", "returncode", "return_code"):
            value = mapping.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value != 0:
                return "fail"
            if isinstance(value, str) and value.strip().lstrip("-").isdigit() and int(value) != 0:
                return "fail"
    return "pass" if hook_event == "PostToolUse" else "unknown"


def _hook_agent_identity(data: dict[str, Any]) -> tuple[str | None, str | None, str | None, str]:
    adapter = _hook_adapter(data)
    session_id = str(data.get("session_id") or os.environ.get("AEGIS_SESSION_ID") or "").strip()
    payload_agent = str(data.get("agent_id") or "").strip()
    env_agent = str(os.environ.get("AEGIS_AGENT_ID") or "").strip()
    agent_id = payload_agent or env_agent or (f"session:{session_id}" if session_id else None)
    payload_parent = str(data.get("parent_agent_id") or "").strip()
    env_parent = str(os.environ.get("AEGIS_PARENT_AGENT_ID") or "").strip()
    root_agent = f"session:{session_id}" if session_id else None
    parent_agent_id = payload_parent or env_parent or None
    if parent_agent_id is None and agent_id is not None and root_agent and agent_id != root_agent:
        parent_agent_id = root_agent
    agent_type = (
        str(
            data.get("agent_type")
            or os.environ.get("AEGIS_AGENT_TYPE")
            or (f"{adapter}-session" if agent_id == root_agent else "")
        ).strip()
        or None
    )
    if payload_parent:
        source = "payload-parent"
    elif env_parent:
        source = "environment-parent"
    elif parent_agent_id:
        source = "session-root-parent"
    elif agent_id == root_agent:
        source = "session-root"
    elif payload_agent:
        source = "payload-agent"
    elif env_agent:
        source = "environment-agent"
    else:
        source = "unavailable"
    return agent_id, agent_type, parent_agent_id, source


def _record_handler(data: dict[str, Any], payload: Payload | None) -> str:
    adapter = _hook_adapter(data)
    if payload is None:
        hook_event = str(data.get("hook_event_name") or "unknown").lower()
        return f"{adapter}:{hook_event}"
    handler = payload_handler(payload)
    if adapter == "codex" and handler.startswith("claude:"):
        return "codex:" + handler.split(":", 1)[1]
    return handler


def _classify_record_event(
    data: dict[str, Any],
    payload: Payload | None,
    paths: list[str],
    outcome: str,
) -> str:
    hook_event = str(data.get("hook_event_name") or "")
    if hook_event == "PostToolUseFailure":
        return "tool_failure"
    if hook_event == "SessionStart":
        return "session_begin"
    if hook_event == "SessionEnd":
        return "session_end"
    if hook_event == "SubagentStart":
        return "subagent_begin"
    if hook_event == "SubagentStop":
        return "subagent_end"
    if payload is not None and payload.tool_name == "Bash":
        command = bash_command(payload)
        if DELIVERY_COMMAND_RE.search(command):
            return "delivery"
        if MUTATING_TASKMASTER_RE.search(command):
            return "task_truth"
    if any(path.endswith(TASKMASTER_TASKS_JSON_SUFFIX) for path in paths):
        return "task_truth"
    if hook_event == "PostToolUse":
        return "tool_failure" if outcome in {"fail", "interrupted"} else "mutation"
    return "unknown"


def _bash_segment_is_any_pr_merge(segment: str) -> bool:
    tokens = cleaned_shell_tokens(segment)
    if len(tokens) < 3:
        return False
    if command_name(tokens[0]) != "gh" or tokens[1:3] != ["pr", "merge"]:
        return False
    args = tokens[3:]
    if "--admin" in args or "--web" in args or option_value(tokens, "--repo") or "-R" in args:
        return False
    return any(method in args for method in {"--merge", "--squash", "--rebase"})


def _capsule_compile_reason_for_event(
    payload: Payload | None,
    paths: list[str],
    event_type: str,
) -> str | None:
    if any(path.endswith(CAPSULE_RISK_SEED_SUFFIX) for path in paths):
        return "risk-register-change"
    if any(path.endswith(TASKMASTER_TASKS_JSON_SUFFIX) for path in paths):
        return "task-status-change"
    if event_type == "verification":
        return "verification"
    if event_type == "task_truth":
        return "task-status-change"
    if payload is None or payload.tool_name != "Bash":
        return None
    command = bash_command(payload)
    if AEGIS_WITNESS_RE.search(command):
        return "pre-delivery"
    if AEGIS_VERIFY_RE.search(command):
        return "verification"
    if TASKMASTER_SET_STATUS_RE.search(command):
        return "task-status-change"
    if any(_bash_segment_is_any_pr_merge(segment) for segment in command_segments(command)):
        return "post-merge"
    return None


def ledger_record() -> int:
    """Append one passive ledger event for a hook payload (capsule PR-1b).

    The recorder must NEVER block, fail, or slow the session: every error path
    degrades to exit 0. It runs as an async hook, so nothing it prints or returns
    can influence tool behavior by design.
    """

    try:
        raw = sys.stdin.read()
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            return 0
        ledger_lib = _load_ledger_lib_module()
        if ledger_lib is None:
            return 0
        root = project_root()
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input")
        payload = (
            Payload(str(tool_name), dict(tool_input))
            if isinstance(tool_name, str) and isinstance(tool_input, dict)
            else None
        )
        patch_metadata: dict[str, Any] | None = None
        patch_parse_error: str | None = None
        if payload is not None and payload.tool_name == CODEX_APPLY_PATCH_TOOL:
            try:
                patch_metadata = apply_patch_event_metadata(payload, root)
                paths = list(patch_metadata["affected_paths"])
            except ApplyPatchParseError as exc:
                patch_parse_error = str(exc)
                paths = []
                patch_metadata = {
                    "affected_paths": [],
                    "operations": [],
                    "patch_digest": sha256(
                        apply_patch_command(payload).encode("utf-8")
                    ).hexdigest(),
                }
        else:
            paths = file_paths_from_payload(payload, root) if payload is not None else []
        hook_event = str(data.get("hook_event_name") or "")
        outcome = _hook_outcome(data)
        agent_id, agent_type, parent_agent_id, attribution_source = _hook_agent_identity(data)
        extra: dict[str, Any] = {
            "hook_event_name": hook_event or None,
            "tool_use_id": data.get("tool_use_id"),
            "turn_id": data.get("turn_id"),
            "model": data.get("model"),
            "permission_mode": data.get("permission_mode"),
            "transcript_path": data.get("transcript_path"),
            "agent_transcript_path": data.get("agent_transcript_path"),
            "agent_attribution_source": attribution_source,
            "adapter": _hook_adapter(data),
            "error": data.get("error"),
            "source": data.get("source"),
            "reason": data.get("reason"),
        }
        if payload is not None:
            extra["is_mutation"] = payload_is_mutation(payload)
            if payload.tool_name == "Bash":
                extra["command"] = bash_command(payload)
            if patch_metadata is not None:
                extra.update(patch_metadata)
                if paths:
                    extra["primary_evidence_path"] = paths[0]
            if patch_parse_error is not None:
                extra["parse_error"] = patch_parse_error
        brief = load_brief(root)
        gates = brief.get("gates") if isinstance(brief.get("gates"), dict) else {}
        redact_extra = (
            brief.get("redact_extra") if isinstance(brief.get("redact_extra"), list) else []
        )
        cwd_value = data.get("cwd") if isinstance(data.get("cwd"), str) else None
        branch = _record_branch(cwd_value)
        event_type = _classify_record_event(data, payload, paths, outcome)
        if (
            payload is not None
            and payload.tool_name == "Bash"
            and hook_event in {"PostToolUse", "PostToolUseFailure"}
        ):
            matched = match_gate_command(bash_command(payload), gates)
            if matched is not None:
                event_type = "verification"
                extra["package"], extra["gate"] = matched
                extra["commit"] = _record_head_commit(cwd_value)
        capsule_reason = _capsule_compile_reason_for_event(payload, paths, event_type)
        if capsule_reason:
            extra["capsule_refresh_reason"] = capsule_reason
        event = {
            "session_id": data.get("session_id"),
            "branch": branch,
            "cwd": data.get("cwd"),
            "event_type": event_type,
            "tool_name": tool_name if isinstance(tool_name, str) else None,
            "handler": _record_handler(data, payload),
            "paths": paths,
            "outcome": outcome,
            "exit_class": outcome,
            "duration_ms": data.get("duration_ms"),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "parent_agent_id": parent_agent_id,
            "payload_digest": payload_digest(payload) if payload is not None else None,
            "extra": {key: value for key, value in extra.items() if value is not None},
        }
        ledger = ledger_lib.open_ledger(
            cwd=root, redact_patterns=[p for p in redact_extra if isinstance(p, str)]
        )
        try:
            ledger.append(event)
            if hook_event == "PostToolUse" and extra.get("is_mutation"):
                _ensure_scope_record(
                    ledger,
                    branch=branch,
                    session_id=data.get("session_id"),
                    cwd=cwd_value,
                    agent_id=agent_id,
                    agent_type=agent_type,
                    parent_agent_id=parent_agent_id,
                    brief=brief,
                )
            if capsule_reason:
                _refresh_capsule_if_stale(root, reason=capsule_reason)
        finally:
            ledger.close()
    except Exception:  # noqa: BLE001 - the recorder must never break a session.
        return 0
    return 0


def _load_brief_lib_module():
    script = Path(__file__).resolve().parent / "brief_lib.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_gate_brief_lib", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _refresh_capsule_if_stale(root: Path, *, reason: str) -> None:
    """Best-effort boundary refresh; never block hook execution."""

    try:
        brief_lib = _load_brief_lib_module()
        if brief_lib is None:
            return
        status = brief_lib.capsule_status(root)
        if status.get("fresh"):
            return
        capsule = brief_lib.compile_capsule(root, reason=reason)
        brief_lib.write_capsule(root, capsule, brief_lib.render_markdown(capsule))
    except Exception:  # noqa: BLE001 - capsule freshness must never break hooks.
        return


def session_start_hook() -> int:
    """Capsule PR-2b: stamp session_begin with the capsule on/off flag (falsifier
    instrumentation) and, when on, inject the computed capsule via stdout.

    SessionStart is synchronous on purpose — stdout enters model context. The stamp
    and the injection are independent best-effort paths; nothing here may fail the
    hook or block a session start.
    """

    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001
        raw = ""
    root = project_root()
    brief_lib = _load_brief_lib_module()
    try:
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            data = {}
    except Exception:  # noqa: BLE001 - a malformed payload must not block a session.
        data = {}
    clear_client_reload_marker(root, agent=_hook_adapter(data))
    if brief_lib is not None and hasattr(brief_lib, "capsule_assignment"):
        assignment = brief_lib.capsule_assignment(root, session_id=data.get("session_id"))
    elif brief_lib is not None:
        assignment = {"injected": brief_lib.injection_enabled(root), "mode": "static-on"}
    else:
        assignment = {"injected": False, "mode": "no-brief-lib"}
    injected = bool(assignment.get("injected"))
    try:
        ledger_lib = _load_ledger_lib_module()
        if ledger_lib is not None:
            agent_id, agent_type, parent_agent_id, attribution_source = _hook_agent_identity(data)
            ledger = ledger_lib.open_ledger(cwd=root)
            try:
                ledger.append(
                    {
                        "session_id": data.get("session_id"),
                        "branch": _record_branch(str(root)),
                        "cwd": data.get("cwd"),
                        "event_type": "session_begin",
                        "handler": f"{_hook_adapter(data)}:sessionstart",
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "parent_agent_id": parent_agent_id,
                        "extra": {
                            "hook_event_name": "SessionStart",
                            "source": data.get("source"),
                            "turn_id": data.get("turn_id"),
                            "model": data.get("model"),
                            "adapter": _hook_adapter(data),
                            "agent_attribution_source": attribution_source,
                            "capsule_injected": injected,
                            "assignment": assignment.get("mode"),
                        },
                    }
                )
            finally:
                ledger.close()
    except Exception:  # noqa: BLE001 - the falsifier stamp is best-effort.
        pass
    if not injected or brief_lib is None:
        return 0
    try:
        source = str(data.get("source") or "")
        reason = "session-start" if source == "startup" else "session-resume"
        capsule = brief_lib.compile_capsule(root, reason=reason)
        text, _dropped = brief_lib.render_injection(capsule)
        brief_lib.write_capsule(root, capsule, brief_lib.render_markdown(capsule))
        print(text)
    except Exception:  # noqa: BLE001 - injection must never block a session start.
        return 0
    return 0


def stop_gate() -> int:
    root = project_root()
    pending_events = required_pending_tracking_events(root)
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
        '`aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"`, '
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
            and hook.get("command")
            == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh"
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
            and hook.get("command")
            == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh"
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
    path = safe_expanduser(file_path)
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
        print(
            "usage: gate_lib.py <pretooluse|posttooluse|stop|path|bash|record|recordjson>",
            file=sys.stderr,
        )
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
    if command == "sessionstart":
        return session_start_hook()
    if command in {"record", "posttoolusefailure", "sessionend", "subagentstart"}:
        return ledger_record()
    if command == "recordjson":
        result = ledger_record()
        print("{}")
        return result
    print(f"unknown gate command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
