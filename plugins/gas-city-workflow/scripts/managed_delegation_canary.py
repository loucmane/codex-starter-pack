#!/usr/bin/env python3
"""Transactionally prove Codex managed-project delegation enforcement.

The canary creates a synthetic descriptor-managed Git project, installs the exact
Aegis Codex adapter from a supplied source tree, trusts only the generated Aegis
project hooks through Codex's supported app-server API, and executes the installed
PreToolUse gate with a synthetic ``spawn_agent`` payload.  It never asks Codex to
launch a child.  The user's Codex configuration is restored byte-for-byte before
the command returns, including on failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.as_posix() not in sys.path:
    sys.path.insert(0, SCRIPT_DIR.as_posix())

import codex_hook_trust as trust_support  # noqa: E402


SCHEMA = "gas-city.managed-delegation-canary-result.v1"
DEFAULT_SOURCE_ROOT = Path("/home/loucmane/gas-city-ops")
DEFAULT_CODEX = Path("/home/loucmane/gascity/bin/codex")
DEFAULT_CODEX_CONFIG = Path("/home/loucmane/.codex/config.toml")
DEFAULT_STATE_ROOT = Path.home() / ".local/state/gas-city-workflow/managed-delegation-canaries"
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
HOOK_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVENT_NAMES = {
    "PreToolUse": "preToolUse",
    "PostToolUse": "postToolUse",
    "SessionStart": "sessionStart",
    "Stop": "stop",
    "SubagentStart": "subagentStart",
    "SubagentStop": "subagentStop",
}


class CanaryError(RuntimeError):
    """The canary could not prove its bounded contract."""


@dataclass(frozen=True, order=True)
class HookDefinition:
    event_name: str
    matcher: str | None
    command: str
    timeout_seconds: int


@dataclass(frozen=True)
class ConfigSnapshot:
    data: bytes
    mode: int
    uid: int
    gid: int

    @property
    def digest(self) -> str:
        return sha256(self.data).hexdigest()


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_regular(path: Path) -> bytes:
    try:
        info = path.lstat()
    except OSError as exc:
        raise CanaryError(f"cannot inspect required file {path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise CanaryError(f"required path is not a regular non-symlink file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CanaryError(f"cannot read required file {path}: {exc}") from exc


def _snapshot(path: Path) -> ConfigSnapshot:
    data = _read_regular(path)
    info = path.stat()
    return ConfigSnapshot(
        data=data,
        mode=stat.S_IMODE(info.st_mode),
        uid=info.st_uid,
        gid=info.st_gid,
    )


def _atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _restore_snapshot(path: Path, snapshot: ConfigSnapshot) -> None:
    _atomic_write(path, snapshot.data, snapshot.mode)
    after = _snapshot(path)
    if after != snapshot:
        raise CanaryError("Codex user config rollback was not byte/mode/owner exact")


def _load_installer(source_root: Path) -> Any:
    path = source_root / "scripts/_aegis_installer.py"
    expected = _read_regular(path)
    module_name = f"managed_delegation_canary_installer_{sha256(expected).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CanaryError(f"could not load Aegis installer: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _flatten_managed_hooks(
    payload: Mapping[str, Any], managed_commands: Iterable[str]
) -> tuple[HookDefinition, ...]:
    managed = frozenset(managed_commands)
    hooks = payload.get("hooks")
    if not isinstance(hooks, Mapping):
        raise CanaryError("Codex hook manifest does not contain a hooks object")
    records: list[HookDefinition] = []
    for event, groups in hooks.items():
        event_name = EVENT_NAMES.get(str(event))
        if event_name is None or not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, Mapping) or not isinstance(group.get("hooks"), list):
                continue
            matcher = group.get("matcher")
            if matcher is not None and not isinstance(matcher, str):
                raise CanaryError(f"Codex hook matcher is invalid for {event}")
            for handler in group["hooks"]:
                if not isinstance(handler, Mapping):
                    continue
                command = handler.get("command")
                if command not in managed:
                    continue
                timeout = handler.get("timeout", 600)
                if (
                    handler.get("type") != "command"
                    or not isinstance(command, str)
                    or not isinstance(timeout, int)
                    or isinstance(timeout, bool)
                    or timeout <= 0
                ):
                    raise CanaryError(f"managed Codex hook definition is invalid for {event}")
                records.append(HookDefinition(event_name, matcher, command, timeout))
    result = tuple(sorted(records))
    if not result or {item.command for item in result} != managed:
        raise CanaryError("Codex hook manifest omitted or duplicated a managed Aegis command")
    if len({(item.event_name, item.matcher, item.command) for item in result}) != len(result):
        raise CanaryError("Codex hook manifest contains duplicate managed hook definitions")
    return result


def expected_managed_hooks(installer: Any) -> tuple[HookDefinition, ...]:
    return _flatten_managed_hooks(
        installer._codex_hooks_payload(),  # noqa: SLF001 - merge-bound installer contract.
        installer.CODEX_MANAGED_HOOK_COMMANDS,
    )


def validate_installed_manifest(hooks_path: Path, expected: Sequence[HookDefinition]) -> str:
    raw = _read_regular(hooks_path)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanaryError("installed Codex hook manifest is invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise CanaryError("installed Codex hook manifest is not an object")
    actual = _flatten_managed_hooks(payload, [item.command for item in expected])
    if tuple(expected) != actual:
        raise CanaryError("installed managed Codex hook definitions drifted")
    return sha256(raw).hexdigest()


def _listing_records(
    payload: Mapping[str, Any], project_root: Path, expected: Sequence[HookDefinition]
) -> list[dict[str, str]]:
    hooks_path = project_root / ".codex/hooks.json"
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], Mapping):
        raise CanaryError("Codex hooks/list returned an unexpected project set")
    project = data[0]
    if project.get("cwd") != project_root.as_posix():
        raise CanaryError("Codex hooks/list returned the wrong project root")
    if project.get("errors") != [] or project.get("warnings") != []:
        raise CanaryError("Codex hooks/list reported hook diagnostics")
    hooks = project.get("hooks")
    if not isinstance(hooks, list):
        raise CanaryError("Codex hooks/list omitted hooks")

    expected_set = {
        (item.event_name, item.matcher, item.command, item.timeout_seconds) for item in expected
    }
    selected: list[dict[str, str]] = []
    identities: set[tuple[str, str | None, str, int]] = set()
    keys: set[str] = set()
    for hook in hooks:
        if not isinstance(hook, Mapping):
            raise CanaryError("Codex hooks/list returned a malformed hook")
        identity = (
            hook.get("eventName"),
            hook.get("matcher"),
            hook.get("command"),
            hook.get("timeoutSec"),
        )
        if identity not in expected_set:
            continue
        exact = {
            "handlerType": "command",
            "async": False,
            "sourcePath": hooks_path.as_posix(),
            "source": "project",
            "pluginId": None,
            "enabled": True,
            "isManaged": False,
        }
        if any(hook.get(name) != value for name, value in exact.items()):
            raise CanaryError(f"Codex managed hook metadata drifted: {identity}")
        key = hook.get("key")
        current_hash = hook.get("currentHash")
        trust_status = hook.get("trustStatus")
        if not isinstance(key, str) or not key.startswith(f"{hooks_path}:") or key in keys:
            raise CanaryError("Codex managed hook identity is invalid or duplicated")
        if not isinstance(current_hash, str) or not HOOK_HASH_PATTERN.fullmatch(current_hash):
            raise CanaryError(f"Codex managed hook hash is invalid: {key}")
        if trust_status not in {"untrusted", "modified", "trusted"}:
            raise CanaryError(f"Codex managed hook trust state is invalid: {key}")
        keys.add(key)
        identities.add(identity)  # type: ignore[arg-type]
        selected.append(
            {"key": key, "current_hash": current_hash, "trust_status": str(trust_status)}
        )
    if identities != expected_set or len(selected) != len(expected):
        raise CanaryError("Codex hooks/list omitted or duplicated a managed Aegis hook")
    return sorted(selected, key=lambda item: item["key"])


def trust_managed_hooks(
    *,
    codex: Path,
    codex_config: Path,
    project_root: Path,
    expected: Sequence[HookDefinition],
    require_fresh: bool = False,
    server_factory: Callable[[Path, Path, Path], Any] = trust_support.CodexAppServer,
) -> dict[str, Any]:
    before = _snapshot(codex_config)
    if (
        codex != DEFAULT_CODEX
        or not codex.exists()
        or codex.resolve(strict=True) != DEFAULT_CODEX.resolve(strict=True)
    ):
        raise CanaryError(f"unsupported Codex binary: {codex}")
    server_pid: int | None = None
    with server_factory(codex, codex_config, project_root) as server:
        process = getattr(server, "_process", None)
        candidate_pid = getattr(process, "pid", None)
        if isinstance(candidate_pid, int) and candidate_pid > 0:
            server_pid = candidate_pid
        config = server.request(
            "config/read", {"cwd": project_root.as_posix(), "includeLayers": True}
        )
        version = trust_support._user_config_version(config, codex_config)  # noqa: SLF001
        pre = _listing_records(
            server.request("hooks/list", {"cwds": [project_root.as_posix()]}),
            project_root,
            expected,
        )
        if require_fresh and any(item["trust_status"] != "untrusted" for item in pre):
            raise CanaryError("fresh canary hook identity was already trusted or modified")
        mutated = any(item["trust_status"] != "trusted" for item in pre)
        write_version: str | None = None
        if mutated:
            write = server.request(
                "config/batchWrite",
                {
                    "edits": [
                        {
                            "keyPath": f"hooks.state.{json.dumps(item['key'])}.trusted_hash",
                            "value": item["current_hash"],
                            "mergeStrategy": "upsert",
                        }
                        for item in pre
                    ],
                    "expectedVersion": version,
                    "filePath": codex_config.as_posix(),
                    "reloadUserConfig": True,
                },
            )
            candidate_version = write.get("version")
            if (
                write.get("status") != "ok"
                or write.get("filePath") != codex_config.as_posix()
                or not isinstance(candidate_version, str)
                or not HOOK_HASH_PATTERN.fullmatch(candidate_version)
            ):
                raise CanaryError("Codex config/batchWrite did not make an exact trust write")
            write_version = candidate_version
        post = _listing_records(
            server.request("hooks/list", {"cwds": [project_root.as_posix()]}),
            project_root,
            expected,
        )
        if any(item["trust_status"] != "trusted" for item in post):
            raise CanaryError("Codex did not trust every exact managed Aegis hook")

    if server_pid is not None and Path(f"/proc/{server_pid}").exists():
        raise CanaryError("Codex app-server process remained after trust transaction")

    if [(x["key"], x["current_hash"]) for x in pre] != [
        (x["key"], x["current_hash"]) for x in post
    ]:
        raise CanaryError("Codex hook identity changed during trust transaction")
    after = _snapshot(codex_config)
    keys = [item["key"] for item in post]
    before_unmanaged, before_keys = trust_support._strip_hook_trust_tables(  # noqa: SLF001
        before.data, keys
    )
    after_unmanaged, after_keys = trust_support._strip_hook_trust_tables(  # noqa: SLF001
        after.data, keys
    )
    if require_fresh and before_keys:
        raise CanaryError("fresh canary hook trust keys already existed in Codex config")
    if before_keys not in (set(), set(keys)):
        raise CanaryError("Codex config contained a partial managed-hook trust set")
    if before_unmanaged != after_unmanaged:
        if not trust_support._only_blank_line_changes(before_unmanaged, after_unmanaged):  # noqa: SLF001
            raise CanaryError("hook trust write changed unrelated Codex config bytes")
        if trust_support._parse_toml(  # noqa: SLF001
            before_unmanaged, label="Codex config before managed-hook trust"
        ) != trust_support._parse_toml(  # noqa: SLF001
            after_unmanaged, label="Codex config after managed-hook trust"
        ):
            raise CanaryError("hook trust write changed unrelated Codex config semantics")
    if after_keys != set(keys):
        raise CanaryError("hook trust write omitted an exact managed hook table")
    if (after.mode, after.uid, after.gid) != (before.mode, before.uid, before.gid):
        raise CanaryError("hook trust write changed Codex config mode or ownership")
    return {
        "before_config_sha256": before.digest,
        "trusted_config_sha256": after.digest,
        "keys": post,
        "mutated": mutated,
        "app_server_pid": server_pid,
        "app_server_stopped": True,
        "write_version": write_version,
    }


def verify_hooks_untrusted(
    *,
    codex: Path,
    codex_config: Path,
    project_root: Path,
    expected: Sequence[HookDefinition],
    server_factory: Callable[[Path, Path, Path], Any] = trust_support.CodexAppServer,
) -> None:
    server_pid: int | None = None
    with server_factory(codex, codex_config, project_root) as server:
        process = getattr(server, "_process", None)
        candidate_pid = getattr(process, "pid", None)
        if isinstance(candidate_pid, int) and candidate_pid > 0:
            server_pid = candidate_pid
        records = _listing_records(
            server.request("hooks/list", {"cwds": [project_root.as_posix()]}),
            project_root,
            expected,
        )
    if server_pid is not None and Path(f"/proc/{server_pid}").exists():
        raise CanaryError("Codex app-server process remained after rollback verification")
    if any(item["trust_status"] != "untrusted" for item in records):
        raise CanaryError("managed canary hooks remained trusted after config rollback")


def _run(
    argv: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(argv),
        cwd=cwd,
        env=None if env is None else dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise CanaryError(
            f"command failed ({result.returncode}): {' '.join(argv)}: {result.stderr.strip()}"
        )
    return result


def _create_fixture(
    run_root: Path, source_root: Path, installer: Any
) -> tuple[Path, dict[str, Any]]:
    if run_root.exists() or run_root.is_symlink():
        raise CanaryError(f"canary run root already exists: {run_root}")
    project = run_root / "project"
    project.mkdir(parents=True, mode=0o700)
    _run(["git", "init", "-q", "-b", "codex/ga-canary"], cwd=project)
    _run(["git", "config", "user.name", "Gas City delegation canary"], cwd=project)
    _run(["git", "config", "user.email", "canary@example.invalid"], cwd=project)
    _run(
        ["git", "remote", "add", "origin", "https://github.com/gas-city/delegation-canary.git"],
        cwd=project,
    )
    descriptor = {
        "schema": "gas-city-workflow.project.v1",
        "id": "delegation-canary",
        "repository": "gas-city/delegation-canary",
        "rig": "gascity",
        "workflow_authority": "beads",
        "workflow_profile": "beads-with-aegis-evidence",
    }
    _atomic_write(project / ".gas-city-workflow.json", _json_bytes(descriptor), 0o644)
    _atomic_write(project / ".gitignore", b".aegis/reports/\n", 0o644)
    _run(["git", "add", ".gas-city-workflow.json", ".gitignore"], cwd=project)
    _run(["git", "commit", "-q", "--no-gpg-sign", "-m", "fixture"], cwd=project)
    install_report = installer.install(
        project,
        source_root=source_root,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    if install_report.get("status") != "applied":
        raise CanaryError("Aegis Codex fixture installation did not apply")
    return project, install_report


def _run_installed_gate(
    project: Path, event: Mapping[str, Any]
) -> subprocess.CompletedProcess[str]:
    binary = project / ".aegis/bin/aegis"
    env = {
        **os.environ,
        "AEGIS_INVOKING_AGENT": "codex",
        "AEGIS_TARGET_ROOT": project.as_posix(),
        "CLAUDE_PROJECT_DIR": project.as_posix(),
        "XDG_CONFIG_HOME": (project / ".canary-config").as_posix(),
    }
    return subprocess.run(
        [binary.as_posix(), "hook", "pretooluse"],
        cwd=project,
        env=env,
        input=json.dumps(event, separators=(",", ":")),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _decision(project: Path) -> dict[str, Any]:
    path = project / ".aegis/reports/gate-decisions.jsonl"
    lines = _read_regular(path).decode("utf-8").splitlines()
    if len(lines) != 1:
        raise CanaryError("delegation canary did not record exactly one decision")
    try:
        result = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise CanaryError("delegation canary decision is invalid JSON") from exc
    if not isinstance(result, dict):
        raise CanaryError("delegation canary decision is not an object")
    return result


def _appended_decision(project: Path, before: bytes) -> dict[str, Any]:
    path = project / ".aegis/reports/gate-decisions.jsonl"
    after = _read_regular(path)
    if not after.startswith(before):
        raise CanaryError("delegation decision history was rewritten")
    appended = after[len(before) :].splitlines()
    if len(appended) != 1:
        raise CanaryError("delegation proof did not append exactly one decision")
    try:
        result = json.loads(appended[0])
    except json.JSONDecodeError as exc:
        raise CanaryError("delegation proof appended invalid JSON") from exc
    if not isinstance(result, dict):
        raise CanaryError("delegation proof decision is not an object")
    return result


def run_canary(
    *,
    source_root: Path,
    codex: Path,
    codex_config: Path,
    state_root: Path,
    run_id: str,
) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise CanaryError("run id is invalid")
    source_root = source_root.resolve(strict=True)
    run_root = state_root / run_id
    installer = _load_installer(source_root)
    expected = expected_managed_hooks(installer)
    source_head = _run(["git", "rev-parse", "HEAD"], cwd=source_root).stdout.strip()
    if _run(["git", "status", "--porcelain"], cwd=source_root).stdout:
        raise CanaryError("source root is not clean")
    snapshot = _snapshot(codex_config)
    trust_started = False
    result: dict[str, Any] = {}
    failure: BaseException | None = None
    try:
        project, install_report = _create_fixture(run_root, source_root, installer)
        hooks_sha256 = validate_installed_manifest(project / ".codex/hooks.json", expected)
        trust_started = True
        trust = trust_managed_hooks(
            codex=codex,
            codex_config=codex_config,
            project_root=project,
            expected=expected,
            require_fresh=True,
        )
        delegation_event = {
            "hook_event_name": "PreToolUse",
            "session_id": f"managed-delegation-canary-{run_id}",
            "cwd": project.as_posix(),
            "tool_name": "collaboration.spawn_agent",
            "tool_input": {
                "task_name": "must-not-launch",
                "message": "synthetic policy canary; do not launch",
                "fork_turns": "none",
            },
        }
        denied = _run_installed_gate(project, delegation_event)
        if (
            denied.returncode != 2
            or "provider-native delegation is not the work-routing authority" not in denied.stderr
        ):
            raise CanaryError("installed managed-project delegation hook did not deny exactly")
        decision = _decision(project)
        if (
            decision.get("verdict") != "block"
            or decision.get("reason") != "native_delegation_requires_gas_city"
            or decision.get("tool_name") != "collaboration.spawn_agent"
        ):
            raise CanaryError("installed delegation decision record drifted")
        local_event = {
            "hook_event_name": "PreToolUse",
            "session_id": f"managed-delegation-canary-{run_id}",
            "cwd": project.as_posix(),
            "tool_name": "Read",
            "tool_input": {"file_path": (project / ".gas-city-workflow.json").as_posix()},
        }
        allowed = _run_installed_gate(project, local_event)
        if allowed.returncode != 0:
            raise CanaryError("installed hook interfered with a coordinator-local read")
        result = {
            "schema": SCHEMA,
            "ok": True,
            "run_id": run_id,
            "source_root": source_root.as_posix(),
            "source_head": source_head,
            "source_tree": _run(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=source_root
            ).stdout.strip(),
            "fixture_root": project.as_posix(),
            "fixture_descriptor_sha256": sha256(
                _read_regular(project / ".gas-city-workflow.json")
            ).hexdigest(),
            "installed_hooks_sha256": hooks_sha256,
            "managed_hook_count": len(expected),
            "install_status": install_report.get("status"),
            "trust": trust,
            "denial": {
                "returncode": denied.returncode,
                "reason": decision["reason"],
                "request_digest": decision["payload_digest"],
                "child_launch_attempted": False,
            },
            "non_interference": {"tool_name": "Read", "returncode": allowed.returncode},
            "config_before_sha256": snapshot.digest,
        }
    except BaseException as exc:  # noqa: BLE001 - rollback must cover every failure.
        failure = exc
    finally:
        if trust_started:
            try:
                _restore_snapshot(codex_config, snapshot)
            except BaseException as rollback_exc:  # noqa: BLE001
                if failure is None:
                    failure = rollback_exc
                else:
                    failure = CanaryError(f"{failure}; rollback also failed: {rollback_exc}")
    if failure is not None:
        raise failure
    project = Path(result["fixture_root"])
    verify_hooks_untrusted(
        codex=codex,
        codex_config=codex_config,
        project_root=project,
        expected=expected,
    )
    restored = _snapshot(codex_config)
    if restored != snapshot:
        raise CanaryError("Codex config changed after rollback verification")
    result["config_after_sha256"] = restored.digest
    result["config_restored"] = True
    result_path = run_root / "result.json"
    _atomic_write(result_path, _json_bytes(result), 0o600)
    result["result_path"] = result_path.as_posix()
    result["result_sha256"] = sha256(_read_regular(result_path)).hexdigest()
    return result


def trust_project(
    *,
    source_root: Path,
    project_root: Path,
    codex: Path,
    codex_config: Path,
    state_root: Path,
    run_id: str,
) -> dict[str, Any]:
    """Persist exact managed-hook trust for one installed managed project.

    The user config is retained only after exact denial, non-interference, and a
    byte-identical idempotence pass.  Every failure restores the starting config.
    """

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise CanaryError("run id is invalid")
    source_root = source_root.resolve(strict=True)
    project_root = project_root.resolve(strict=True)
    run_root = state_root / run_id
    if run_root.exists() or run_root.is_symlink():
        raise CanaryError(f"project-trust run root already exists: {run_root}")
    run_root.mkdir(parents=True, mode=0o700)
    installer = _load_installer(source_root)
    expected = expected_managed_hooks(installer)
    hooks_sha256 = validate_installed_manifest(project_root / ".codex/hooks.json", expected)
    source_head = _run(["git", "rev-parse", "HEAD"], cwd=source_root).stdout.strip()
    source_tree = _run(["git", "rev-parse", "HEAD^{tree}"], cwd=source_root).stdout.strip()
    if _run(["git", "status", "--porcelain"], cwd=source_root).stdout:
        raise CanaryError("source root is not clean")
    top = Path(_run(["git", "rev-parse", "--show-toplevel"], cwd=project_root).stdout.strip())
    if top.resolve() != project_root:
        raise CanaryError("project root is not the exact Git worktree root")

    snapshot = _snapshot(codex_config)
    decisions_path = project_root / ".aegis/reports/gate-decisions.jsonl"
    decision_before = _read_regular(decisions_path) if decisions_path.exists() else b""
    trust_started = False
    success = False
    failure: BaseException | None = None
    result: dict[str, Any] = {}
    try:
        trust_started = True
        trust = trust_managed_hooks(
            codex=codex,
            codex_config=codex_config,
            project_root=project_root,
            expected=expected,
        )
        trusted_snapshot = _snapshot(codex_config)
        denied = _run_installed_gate(
            project_root,
            {
                "hook_event_name": "PreToolUse",
                "session_id": f"managed-delegation-trust-{run_id}",
                "cwd": project_root.as_posix(),
                "tool_name": "collaboration.spawn_agent",
                "tool_input": {
                    "task_name": "must-not-launch",
                    "message": "synthetic policy proof; do not launch",
                    "fork_turns": "none",
                },
            },
        )
        if (
            denied.returncode != 2
            or "provider-native delegation is not the work-routing authority" not in denied.stderr
        ):
            raise CanaryError("trusted managed-project hook did not deny exactly")
        decision = _appended_decision(project_root, decision_before)
        if (
            decision.get("verdict") != "block"
            or decision.get("reason") != "native_delegation_requires_gas_city"
            or decision.get("tool_name") != "collaboration.spawn_agent"
        ):
            raise CanaryError("trusted managed-project decision record drifted")
        allowed = _run_installed_gate(
            project_root,
            {
                "hook_event_name": "PreToolUse",
                "session_id": f"managed-delegation-trust-{run_id}",
                "cwd": project_root.as_posix(),
                "tool_name": "Read",
                "tool_input": {"file_path": (project_root / ".gas-city-workflow.json").as_posix()},
            },
        )
        if allowed.returncode != 0:
            raise CanaryError("trusted project hook interfered with a coordinator-local read")
        second = trust_managed_hooks(
            codex=codex,
            codex_config=codex_config,
            project_root=project_root,
            expected=expected,
        )
        if second["mutated"] or _snapshot(codex_config) != trusted_snapshot:
            raise CanaryError("managed-project hook trust was not idempotent")
        result = {
            "schema": SCHEMA,
            "ok": True,
            "mode": "trust-project",
            "run_id": run_id,
            "source_root": source_root.as_posix(),
            "source_head": source_head,
            "source_tree": source_tree,
            "project_root": project_root.as_posix(),
            "installed_hooks_sha256": hooks_sha256,
            "managed_hook_count": len(expected),
            "trust": trust,
            "idempotent_readback": second,
            "denial": {
                "returncode": denied.returncode,
                "reason": decision["reason"],
                "request_digest": decision["payload_digest"],
                "child_launch_attempted": False,
            },
            "non_interference": {"tool_name": "Read", "returncode": allowed.returncode},
            "config_before_sha256": snapshot.digest,
            "config_after_sha256": trusted_snapshot.digest,
            "config_retained": True,
        }
        result_path = run_root / "result.json"
        _atomic_write(result_path, _json_bytes(result), 0o600)
        result["result_path"] = result_path.as_posix()
        result["result_sha256"] = sha256(_read_regular(result_path)).hexdigest()
        success = True
    except BaseException as exc:  # noqa: BLE001 - rollback must cover every failure.
        failure = exc
    finally:
        if trust_started and not success:
            try:
                _restore_snapshot(codex_config, snapshot)
            except BaseException as rollback_exc:  # noqa: BLE001
                if failure is None:
                    failure = rollback_exc
                else:
                    failure = CanaryError(f"{failure}; rollback also failed: {rollback_exc}")
    if failure is not None:
        raise failure
    return result


def check(source_root: Path, codex: Path, codex_config: Path) -> dict[str, Any]:
    source_root = source_root.resolve(strict=True)
    installer = _load_installer(source_root)
    expected = expected_managed_hooks(installer)
    _snapshot(codex_config)
    if not codex.is_file():
        raise CanaryError(f"Codex binary is unavailable: {codex}")
    return {
        "schema": SCHEMA,
        "ok": True,
        "mode": "check",
        "source_root": source_root.as_posix(),
        "source_head": _run(["git", "rev-parse", "HEAD"], cwd=source_root).stdout.strip(),
        "managed_hook_count": len(expected),
        "codex": codex.as_posix(),
        "codex_config_sha256": _snapshot(codex_config).digest,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "apply", "trust-project"))
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--codex", type=Path, default=DEFAULT_CODEX)
    parser.add_argument("--codex-config", type=Path, default=DEFAULT_CODEX_CONFIG)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--run-id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.mode == "check":
            if args.run_id is not None:
                raise CanaryError("--run-id is not valid with check")
            if args.project_root is not None:
                raise CanaryError("--project-root is only valid with trust-project")
            result = check(args.source_root, args.codex, args.codex_config)
        elif args.mode == "apply":
            if args.run_id is None:
                raise CanaryError("apply requires --run-id")
            if args.project_root is not None:
                raise CanaryError("--project-root is only valid with trust-project")
            result = run_canary(
                source_root=args.source_root,
                codex=args.codex,
                codex_config=args.codex_config,
                state_root=args.state_root,
                run_id=args.run_id,
            )
        else:
            if args.run_id is None or args.project_root is None:
                raise CanaryError("trust-project requires --run-id and --project-root")
            result = trust_project(
                source_root=args.source_root,
                project_root=args.project_root,
                codex=args.codex,
                codex_config=args.codex_config,
                state_root=args.state_root,
                run_id=args.run_id,
            )
    except (CanaryError, trust_support.InstallError, OSError, ValueError) as exc:
        print(f"managed-delegation-canary: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
