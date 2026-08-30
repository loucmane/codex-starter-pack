"""Exact, transactional Codex hook trust for the Gas City evidence-run root."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import select
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any, Sequence

OPERATOR_PATH = "/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin"
DEFAULT_CODEX = Path("/home/loucmane/gascity/bin/codex")
EVIDENCE_HOOKS_SHA256 = "55e21a9d981805afb62da110b022bc847f7ad2b9a62bada45de95dbdfa472410"
HOOK_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
EXPECTED_HOOKS = (
    {
        "key_suffix": "pre_compact:0:0",
        "eventName": "preCompact",
        "matcher": "",
        "command": (
            "'/home/loucmane/gascity/bin/gc' --city '/home/loucmane/gascity/city' "
            'handoff --auto --hook-format codex "context cycle"'
        ),
    },
    {
        "key_suffix": "session_start:0:0",
        "eventName": "sessionStart",
        "matcher": "startup",
        "command": (
            "GC_MANAGED_SESSION_HOOK=1 GC_HOOK_EVENT_NAME=SessionStart "
            "'/home/loucmane/gascity/bin/gc' --city '/home/loucmane/gascity/city' "
            "prime --hook --hook-format codex"
        ),
    },
    {
        "key_suffix": "user_prompt_submit:0:0",
        "eventName": "userPromptSubmit",
        "matcher": None,
        "command": (
            "'/home/loucmane/gascity/bin/gc' --city '/home/loucmane/gascity/city' "
            "hook run --timeout 15s --timeout-exit-code 0 -- nudge drain --inject "
            "--hook-format codex"
        ),
    },
    {
        "key_suffix": "user_prompt_submit:0:1",
        "eventName": "userPromptSubmit",
        "matcher": None,
        "command": (
            "'/home/loucmane/gascity/bin/gc' --city '/home/loucmane/gascity/city' "
            "hook run --timeout 15s --timeout-exit-code 0 -- mail check --inject "
            "--hook-format codex"
        ),
    },
)


class InstallError(RuntimeError):
    """Raised when the bounded evidence-reviewer install cannot be proven safe."""


class CodexAppServer:
    """Small bounded JSONL client for the supported Codex app-server API."""

    def __init__(self, codex: Path, codex_config: Path, cwd: Path) -> None:
        self._stderr = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        env = {
            **os.environ,
            "CODEX_HOME": codex_config.parent.as_posix(),
            "HOME": codex_config.parent.parent.as_posix(),
            "PATH": OPERATOR_PATH,
        }
        try:
            self._process = subprocess.Popen(  # noqa: S603 - exact reviewed binary.
                [str(codex), "app-server", "--stdio"],
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._stderr,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self._stderr.close()
            raise InstallError(f"could not start Codex app-server: {exc}") from exc
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise InstallError("Codex app-server did not expose JSONL pipes")
        self._request_id = 0
        try:
            self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "gas-city-evidence-reviewer-installer",
                        "version": "1",
                    },
                    "capabilities": {},
                },
            )
            self.notify("initialized")
        except Exception:
            self.close()
            raise

    def _diagnostics(self) -> str:
        self._stderr.flush()
        self._stderr.seek(0)
        return self._stderr.read().strip()

    def _send(self, payload: dict[str, Any]) -> None:
        assert self._process.stdin is not None
        try:
            self._process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            detail = self._diagnostics()
            raise InstallError(
                "Codex app-server input closed" + (f": {detail}" if detail else "")
            ) from exc

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def request(
        self, method: str, params: dict[str, Any], *, timeout_seconds: float = 15.0
    ) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        self._send({"id": request_id, "method": method, "params": params})
        assert self._process.stdout is not None
        deadline = time.monotonic() + timeout_seconds
        while True:
            if self._process.poll() is not None:
                detail = self._diagnostics()
                raise InstallError(
                    f"Codex app-server exited during {method}" + (f": {detail}" if detail else "")
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise InstallError(f"Codex app-server timed out during {method}")
            ready, _, _ = select.select([self._process.stdout], [], [], remaining)
            if not ready:
                raise InstallError(f"Codex app-server timed out during {method}")
            line = self._process.stdout.readline()
            if not line:
                detail = self._diagnostics()
                raise InstallError(
                    f"Codex app-server closed during {method}" + (f": {detail}" if detail else "")
                )
            try:
                response = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InstallError("Codex app-server returned invalid JSON") from exc
            if not isinstance(response, dict) or response.get("id") != request_id:
                continue
            if "error" in response:
                raise InstallError(f"Codex app-server {method} failed: {response['error']}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise InstallError(f"Codex app-server {method} returned no object result")
            return result

    def close(self) -> None:
        process = getattr(self, "_process", None)
        if process is not None and process.poll() is None:
            if process.stdin is not None:
                try:
                    process.stdin.close()
                except OSError:
                    pass
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        self._stderr.close()

    def __enter__(self) -> CodexAppServer:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise InstallError(f"expected regular file: {path}")
    return path.read_bytes()


def _parse_toml(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise InstallError(f"{label} is invalid TOML") from exc
    if not isinstance(parsed, dict):
        raise InstallError(f"{label} root must be a table")
    return parsed


def _hook_manifest(evidence_root: Path) -> Path:
    path = evidence_root / ".codex" / "hooks.json"
    data = _read_regular(path)
    if _sha256(data) != EVIDENCE_HOOKS_SHA256:
        raise InstallError("evidence-root Codex hook manifest drifted")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise InstallError("evidence-root Codex hook manifest is invalid JSON") from exc
    expected = {
        "hooks": {
            "PreCompact": [
                {
                    "hooks": [{"command": EXPECTED_HOOKS[0]["command"], "type": "command"}],
                    "matcher": "",
                }
            ],
            "SessionStart": [
                {
                    "hooks": [{"command": EXPECTED_HOOKS[1]["command"], "type": "command"}],
                    "matcher": "startup",
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {"command": EXPECTED_HOOKS[2]["command"], "type": "command"},
                        {"command": EXPECTED_HOOKS[3]["command"], "type": "command"},
                    ],
                    "matcher": "",
                }
            ],
        }
    }
    if payload != expected:
        raise InstallError("evidence-root Codex hook semantics drifted")
    return path


def _expected_hook_keys(hooks_path: Path) -> list[str]:
    return [f"{hooks_path}:{item['key_suffix']}" for item in EXPECTED_HOOKS]


def _validate_hook_listing(
    payload: dict[str, Any],
    evidence_root: Path,
    *,
    allowed_trust: set[str],
) -> list[dict[str, str]]:
    hooks_path = _hook_manifest(evidence_root)
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise InstallError("Codex hooks/list returned an unexpected project set")
    entry = data[0]
    if entry.get("cwd") != evidence_root.as_posix():
        raise InstallError("Codex hooks/list returned the wrong working directory")
    if entry.get("errors") != [] or entry.get("warnings") != []:
        raise InstallError("Codex hooks/list reported hook load diagnostics")
    hooks = entry.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != len(EXPECTED_HOOKS):
        raise InstallError("Codex hooks/list did not return exactly four reviewed hooks")
    expected_by_key = {f"{hooks_path}:{item['key_suffix']}": item for item in EXPECTED_HOOKS}
    if {item.get("key") for item in hooks if isinstance(item, dict)} != set(expected_by_key):
        raise InstallError("Codex hooks/list returned an unexpected hook identity")

    result: list[dict[str, str]] = []
    for hook in hooks:
        if not isinstance(hook, dict):
            raise InstallError("Codex hooks/list returned a malformed hook")
        key = hook.get("key")
        expected = expected_by_key.get(key)
        if expected is None:
            raise InstallError("Codex hooks/list returned an unreviewed hook")
        exact = {
            "eventName": expected["eventName"],
            "handlerType": "command",
            "command": expected["command"],
            "async": False,
            "matcher": expected["matcher"],
            "timeoutSec": 600,
            "sourcePath": hooks_path.as_posix(),
            "source": "project",
            "pluginId": None,
            "enabled": True,
            "isManaged": False,
        }
        if any(hook.get(name) != value for name, value in exact.items()):
            raise InstallError(f"Codex hook metadata drifted: {key}")
        current_hash = hook.get("currentHash")
        trust_status = hook.get("trustStatus")
        if not isinstance(current_hash, str) or not HOOK_HASH_PATTERN.fullmatch(current_hash):
            raise InstallError(f"Codex hook hash is invalid: {key}")
        if trust_status not in allowed_trust:
            raise InstallError(f"Codex hook trust state is invalid: {key}")
        result.append({"key": key, "current_hash": current_hash, "trust_status": trust_status})
    return sorted(result, key=lambda item: item["key"])


def _user_config_version(payload: dict[str, Any], codex_config: Path) -> str:
    layers = payload.get("layers")
    if not isinstance(layers, list):
        raise InstallError("Codex config/read omitted configuration layers")
    matches = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        name = layer.get("name")
        if (
            isinstance(name, dict)
            and name.get("type") == "user"
            and name.get("file") == codex_config.as_posix()
        ):
            matches.append(layer.get("version"))
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise InstallError("Codex config/read did not identify the exact user config layer")
    version = matches[0]
    if not HOOK_HASH_PATTERN.fullmatch(version):
        raise InstallError("Codex user config version is invalid")
    return version


def _strip_hook_trust_tables(data: bytes, keys: Sequence[str]) -> tuple[bytes, set[str]]:
    """Remove only exact managed hook tables so all other bytes can be compared."""

    text = data.decode("utf-8")
    headers = {f"[hooks.state.{json.dumps(key)}]": key for key in keys}
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    found: set[str] = set()
    skipping = False
    for line in lines:
        stripped = line.rstrip("\r\n")
        if stripped.startswith("["):
            key = headers.get(stripped)
            if key is not None:
                if key in found:
                    raise InstallError(f"duplicate Codex hook trust table: {key}")
                found.add(key)
                if kept and not kept[-1].strip():
                    kept.pop()
                skipping = True
                continue
            skipping = False
        if not skipping:
            kept.append(line)
    return "".join(kept).encode("utf-8"), found


def _only_blank_line_changes(before: bytes, after: bytes) -> bool:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines)
    for operation, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        changed = before_lines[before_start:before_end] + after_lines[after_start:after_end]
        if any(line.strip() for line in changed):
            return False
    return True


def trust_codex_hooks(codex: Path, codex_config: Path, evidence_root: Path) -> dict[str, Any]:
    """Trust only the exact reviewed evidence-root hooks through supported Codex APIs."""

    hooks_path = _hook_manifest(evidence_root)
    if (
        codex != DEFAULT_CODEX
        or not codex.exists()
        or codex.resolve(strict=True) != DEFAULT_CODEX.resolve(strict=True)
    ):
        raise InstallError(f"unsupported Codex binary: {codex}")
    before = _read_regular(codex_config)
    keys = _expected_hook_keys(hooks_path)
    with CodexAppServer(codex, codex_config, evidence_root) as server:
        config_read = server.request(
            "config/read", {"cwd": evidence_root.as_posix(), "includeLayers": True}
        )
        version = _user_config_version(config_read, codex_config)
        pre = _validate_hook_listing(
            server.request("hooks/list", {"cwds": [evidence_root.as_posix()]}),
            evidence_root,
            allowed_trust={"untrusted", "modified", "trusted"},
        )
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
        write_version = write.get("version")
        if (
            write.get("status") != "ok"
            or write.get("filePath") != codex_config.as_posix()
            or not isinstance(write_version, str)
            or not HOOK_HASH_PATTERN.fullmatch(write_version)
        ):
            raise InstallError("Codex config/batchWrite did not make an exact user-config write")
        post = _validate_hook_listing(
            server.request("hooks/list", {"cwds": [evidence_root.as_posix()]}),
            evidence_root,
            allowed_trust={"trusted"},
        )

    pre_identity = [(item["key"], item["current_hash"]) for item in pre]
    post_identity = [(item["key"], item["current_hash"]) for item in post]
    if pre_identity != post_identity:
        raise InstallError("Codex hook identity changed during trust transaction")
    after = _read_regular(codex_config)
    before_unmanaged, _ = _strip_hook_trust_tables(before, keys)
    after_unmanaged, after_keys = _strip_hook_trust_tables(after, keys)
    if before_unmanaged != after_unmanaged:
        if not _only_blank_line_changes(before_unmanaged, after_unmanaged):
            raise InstallError("Codex hook trust write changed unrelated nonblank config bytes")
        if _parse_toml(before_unmanaged, label="Codex config before hook trust") != _parse_toml(
            after_unmanaged, label="Codex config after hook trust"
        ):
            raise InstallError("Codex hook trust write changed unrelated config semantics")
    if after_keys != set(keys):
        raise InstallError("Codex hook trust write omitted a reviewed hook table")
    parsed = _parse_toml(after, label="Codex config after hook trust write")
    state = parsed.get("hooks", {}).get("state", {})
    if not isinstance(state, dict):
        raise InstallError("Codex hook trust state is not a table")
    expected_hashes = {item["key"]: item["current_hash"] for item in post}
    for key, current_hash in expected_hashes.items():
        entry = state.get(key)
        if not isinstance(entry, dict) or entry != {"trusted_hash": current_hash}:
            raise InstallError(f"Codex hook trust config readback mismatch: {key}")
    return {
        "manifest": hooks_path.as_posix(),
        "manifest_sha256": EVIDENCE_HOOKS_SHA256,
        "before": pre,
        "after": post,
        "config_write_version": write_version,
    }
