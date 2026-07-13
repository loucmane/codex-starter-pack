"""Read-only diagnostics for Aegis worktree and child-agent capture.

Task 239 deliberately measures the installed recorder without changing it.  This module
collects normalized repository/asset/hook/ledger snapshots, compares event windows, and
replays secret-free fixtures.  It never appends ledger rows, installs hooks, creates or
removes worktrees, or mutates Git state.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "1.0.0"
RESULT_STATUSES = ("supported", "unsupported", "degraded", "failed")
CAUSE_CODES = (
    "pre_install_checkout",
    "tracked_assets_missing",
    "client_hooks_unloaded",
    "source_root_unresolved",
    "ledger_store_mismatch",
    "attribution_missing",
    "parent_only_traffic",
    "teardown_loss",
    "unsupported_surface",
    "capture_ok",
)
HOOK_EVENTS = ("SessionStart", "PostToolUse", "PostToolUseFailure", "Stop")
REQUIRED_ASSETS = {
    "shim": ".aegis/bin/aegis",
    "settings": ".claude/settings.json",
    "recorder": ".claude/scripts/ledger-record.sh",
    "gate_lib": ".claude/scripts/gate_lib.py",
    "ledger_lib": ".claude/scripts/ledger_lib.py",
}
ATTRIBUTION_FIELDS = (
    "repository_identity",
    "worktree_root",
    "branch",
    "head",
    "agent_id",
    "agent_type",
    "parent_agent_id",
)
SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bgho_[A-Za-z0-9]{8,}\b"),
    re.compile(r"(?<![A-Za-z0-9])sk_[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_-]+){1,2}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
)


class AuditError(RuntimeError):
    """Raised when deterministic audit input is malformed or unavailable."""


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _opaque(value: object, *, kind: str) -> str | None:
    text = str(value or "").strip()
    return f"{kind}:{_sha256_text(text)}" if text else None


def _run_git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise AuditError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def _asset_digest(path: Path) -> str | None:
    return _sha256_bytes(path.read_bytes()) if path.is_file() else None


def _hook_capabilities(settings_path: Path) -> dict[str, str]:
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {event: "unknown" for event in HOOK_EVENTS}
    hooks = payload.get("hooks") if isinstance(payload, Mapping) else None
    if not isinstance(hooks, Mapping):
        return {event: "unsupported" for event in HOOK_EVENTS}
    return {
        event: "supported" if isinstance(hooks.get(event), list) and hooks[event] else "unsupported"
        for event in HOOK_EVENTS
    }


def load_ledger_module(source_root: str | Path) -> Any:
    """Load the existing standalone ledger implementation without copying its logic."""

    script = Path(source_root).resolve() / ".claude" / "scripts" / "ledger_lib.py"
    if not script.is_file():
        raise AuditError(f"ledger library is missing: {script}")
    spec = importlib.util.spec_from_file_location("_task239_ledger_lib", script)
    if spec is None or spec.loader is None:
        raise AuditError(f"unable to load ledger library: {script}")
    module = importlib.util.module_from_spec(spec)
    previous = getattr(__import__("sys"), "dont_write_bytecode")
    try:
        __import__("sys").dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        __import__("sys").dont_write_bytecode = previous
    return module


def _normalized_ledger_path(path: Path, repository_identity: str) -> str:
    suffix = "shards" if path.name == "shards" else path.name
    return f"<state-root>/{repository_identity}/{suffix}"


def _event_summary(event: Mapping[str, Any]) -> dict[str, Any]:
    extra = event.get("extra") if isinstance(event.get("extra"), Mapping) else {}
    return {
        "event_id": str(event.get("event_id") or "") or None,
        "session_id": _opaque(event.get("session_id"), kind="session"),
        "branch": str(event.get("branch") or "") or None,
        "cwd": "<event-cwd>" if event.get("cwd") else None,
        "event_type": str(event.get("event_type") or "unknown"),
        "tool_name": str(event.get("tool_name") or "") or None,
        "outcome": str(event.get("outcome") or "unknown"),
        "agent_id": _opaque(event.get("agent_id"), kind="agent"),
        "agent_type": str(event.get("agent_type") or "") or None,
        "repository_identity": str(extra.get("repository_identity") or "") or None,
        "worktree_root": "<event-worktree>" if extra.get("worktree_root") else None,
        "head": str(extra.get("head") or extra.get("commit") or "") or None,
        "parent_agent_id": _opaque(extra.get("parent_agent_id"), kind="agent"),
        "hook_event_name": str(extra.get("hook_event_name") or "") or None,
    }


def collect_snapshot(
    repo: str | Path,
    *,
    source_root: str | Path,
    scenario_id: str,
    client_name: str,
    client_version: str,
    worktree_label: str,
    state_home: str | Path | None = None,
    parent_session_id: str | None = None,
    parent_agent_id: str | None = None,
    child_session_id: str | None = None,
    child_agent_id: str | None = None,
    parent_agent_link: str | None = None,
    hooks_loaded: bool | None = None,
    source_resolved: bool | None = None,
) -> dict[str, Any]:
    """Collect a normalized, read-only snapshot from one Git worktree."""

    root = Path(repo).resolve()
    common_dir = Path(_run_git(root, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = (root / common_dir).resolve()
    common_dir = common_dir.resolve()
    repository_identity = _sha256_text(common_dir.as_posix())
    branch = _run_git(root, "branch", "--show-current") or "<detached>"
    head = _run_git(root, "rev-parse", "HEAD")

    asset_states: dict[str, str] = {}
    checksums: dict[str, str] = {}
    for name, relative in REQUIRED_ASSETS.items():
        path = root / relative
        digest = _asset_digest(path)
        asset_states[name] = "present" if digest else "absent"
        if digest:
            checksums[name] = digest

    settings = root / REQUIRED_ASSETS["settings"]
    capabilities = _hook_capabilities(settings)
    environment = dict(os.environ)
    if state_home is not None:
        environment["XDG_STATE_HOME"] = Path(state_home).as_posix()

    events: list[dict[str, Any]] = []
    backend = "none"
    raw_ledger_path: Path | None = None
    ledger_error: str | None = None
    try:
        ledger_lib = load_ledger_module(source_root)
        selected_backend = str(environment.get("AEGIS_LEDGER_BACKEND") or "sqlite")
        if selected_backend == "jsonl":
            raw_ledger_path = Path(ledger_lib.shards_dir(cwd=root, env=environment))
        else:
            raw_ledger_path = Path(ledger_lib.store_path(cwd=root, env=environment))
        backend = selected_backend
        if selected_backend == "jsonl" or raw_ledger_path.is_file():
            ledger = ledger_lib.open_ledger(cwd=root, env=environment, read_only=True)
            try:
                events = [_event_summary(event) for event in ledger.read()]
            finally:
                ledger.close()
    except Exception as exc:  # noqa: BLE001 - diagnostic output owns the failure.
        ledger_error = f"{type(exc).__name__}: {exc}"

    return {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "client": {
            "name": client_name,
            "version": re.sub(r"\s+", " ", client_version.strip())[:160] or "unknown",
            "mode": "actual",
            "hooks_loaded": hooks_loaded,
            "source_resolved": source_resolved,
        },
        "parent": {
            "session_id": _opaque(parent_session_id, kind="session"),
            "agent_id": _opaque(parent_agent_id, kind="agent"),
            "agent_type": "orchestrator" if parent_agent_id else None,
        },
        "child": {
            "session_id": _opaque(child_session_id, kind="session"),
            "agent_id": _opaque(child_agent_id, kind="agent"),
            "parent_agent_id": _opaque(parent_agent_link, kind="agent"),
        },
        "repository": {
            "identity": repository_identity,
            "git_common_dir": "<repo-common-dir>",
        },
        "worktree": {
            "path": worktree_label,
            "branch": branch,
            "head": head,
        },
        "assets": {
            **asset_states,
            "checksums": checksums,
        },
        "hooks": {
            "session_start": capabilities["SessionStart"],
            "post_tool_use": capabilities["PostToolUse"],
            "post_tool_failure": capabilities["PostToolUseFailure"],
            "stop": capabilities["Stop"],
        },
        "ledger": {
            "backend": backend,
            "resolved_path": (
                _normalized_ledger_path(raw_ledger_path, repository_identity)
                if raw_ledger_path is not None
                else None
            ),
            "error": ledger_error,
        },
        "events": events,
        "event_window": {
            "event_ids": [event["event_id"] for event in events if event.get("event_id")],
            "event_count": len(events),
        },
    }


def _new_events(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[dict[str, Any]]:
    before_window = before.get("event_window") if isinstance(before.get("event_window"), Mapping) else {}
    before_ids = {str(item) for item in before_window.get("event_ids", [])}
    after_events = after.get("events") if isinstance(after.get("events"), list) else []
    return [
        dict(event)
        for event in after_events
        if isinstance(event, Mapping) and str(event.get("event_id") or "") not in before_ids
    ]


def _missing_attribution(events: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in ATTRIBUTION_FIELDS:
        result[field] = (
            "present" if events and all(event.get(field) not in (None, "") for event in events) else "missing"
        )
    return result


def classify_scenario(record: Mapping[str, Any]) -> dict[str, Any]:
    """Classify one before/after scenario without mutating its input."""

    before = record.get("before") if isinstance(record.get("before"), Mapping) else {}
    after = record.get("after") if isinstance(record.get("after"), Mapping) else {}
    metadata = record.get("metadata") if isinstance(record.get("metadata"), Mapping) else {}
    causes: list[str] = []

    if bool(metadata.get("pre_install_checkout")):
        causes.append("pre_install_checkout")

    assets = after.get("assets") if isinstance(after.get("assets"), Mapping) else {}
    required_asset_names = metadata.get("required_assets", tuple(REQUIRED_ASSETS))
    missing_assets = [
        str(name)
        for name in required_asset_names
        if assets.get(str(name)) != "present"
    ]
    if missing_assets and not metadata.get("pre_install_checkout"):
        causes.append("tracked_assets_missing")

    client = after.get("client") if isinstance(after.get("client"), Mapping) else {}
    if metadata.get("surface_supported") is False:
        causes.append("unsupported_surface")
    elif client.get("hooks_loaded") is False:
        causes.append("client_hooks_unloaded")
    if client.get("source_resolved") is False:
        causes.append("source_root_unresolved")

    before_ledger = before.get("ledger") if isinstance(before.get("ledger"), Mapping) else {}
    after_ledger = after.get("ledger") if isinstance(after.get("ledger"), Mapping) else {}
    parent_ledger_path = str(metadata.get("parent_ledger_path") or before_ledger.get("resolved_path") or "")
    child_ledger_path = str(after_ledger.get("resolved_path") or "")
    if parent_ledger_path and child_ledger_path and parent_ledger_path != child_ledger_path:
        causes.append("ledger_store_mismatch")

    new_events = _new_events(before, after)
    expected_agent = _opaque(metadata.get("expected_child_agent_id"), kind="agent")
    child_events = [
        event
        for event in new_events
        if expected_agent is None or event.get("agent_id") == expected_agent
    ]
    if new_events and not child_events:
        causes.append("parent_only_traffic")

    attribution = _missing_attribution(child_events)
    required_attribution = tuple(metadata.get("required_attribution", ATTRIBUTION_FIELDS))
    if child_events and any(attribution.get(str(field)) != "present" for field in required_attribution):
        causes.append("attribution_missing")

    post_teardown_ids = metadata.get("post_teardown_event_ids")
    if isinstance(post_teardown_ids, list):
        retained = {str(item) for item in post_teardown_ids}
        if any(str(event.get("event_id") or "") not in retained for event in new_events):
            causes.append("teardown_loss")

    expected_capture = bool(metadata.get("expected_capture", True))
    if (
        expected_capture
        and child_events
        and not any(
            cause
            in {
                "ledger_store_mismatch",
                "attribution_missing",
                "parent_only_traffic",
                "teardown_loss",
            }
            for cause in causes
        )
    ):
        causes.append("capture_ok")

    causes = [cause for cause in CAUSE_CODES if cause in causes]
    if "unsupported_surface" in causes or (
        "pre_install_checkout" in causes and not expected_capture
    ):
        status = "unsupported"
    elif expected_capture and not child_events:
        status = "failed"
    elif any(cause not in {"capture_ok"} for cause in causes):
        status = "degraded"
    elif "capture_ok" in causes:
        status = "supported"
    else:
        status = "failed"

    return {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": str(record.get("scenario_id") or after.get("scenario_id") or "unknown"),
        "client": after.get("client", {}),
        "parent": after.get("parent", {}),
        "child": after.get("child", {}),
        "repository": after.get("repository", {}),
        "worktree": after.get("worktree", {}),
        "assets": after.get("assets", {}),
        "hooks": after.get("hooks", {}),
        "ledger": {
            **dict(after_ledger),
            "shared_with_parent": (
                bool(parent_ledger_path and child_ledger_path)
                and parent_ledger_path == child_ledger_path
            ),
        },
        "event_window": {
            "before_count": int(
                (before.get("event_window") or {}).get("event_count", 0)
                if isinstance(before.get("event_window"), Mapping)
                else 0
            ),
            "after_count": int(
                (after.get("event_window") or {}).get("event_count", 0)
                if isinstance(after.get("event_window"), Mapping)
                else 0
            ),
            "event_ids": [event.get("event_id") for event in new_events],
            "event_count": len(new_events),
        },
        "attribution": attribution,
        "result": {
            "status": status,
            "causes": causes,
            "missing_assets": missing_assets,
        },
        "limitations": [str(item) for item in metadata.get("limitations", [])],
    }


def replay_fixture(payload: Mapping[str, Any]) -> dict[str, Any]:
    records = payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else []
    scenarios = [classify_scenario(record) for record in records if isinstance(record, Mapping)]
    status_counts = Counter(str(item["result"]["status"]) for item in scenarios)
    cause_counts = Counter(
        str(cause) for item in scenarios for cause in item["result"].get("causes", [])
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(payload.get("run_id") or "task239-replay"),
        "summary": {
            "scenario_count": len(scenarios),
            "status_counts": {status: status_counts.get(status, 0) for status in RESULT_STATUSES},
            "cause_counts": {cause: cause_counts.get(cause, 0) for cause in CAUSE_CODES},
        },
        "scenarios": scenarios,
    }


def assert_secret_free(payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    found = [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(rendered)]
    if found:
        raise AuditError(f"secret-shaped marker present in report: {', '.join(found)}")
    absolute_home = re.search(r'(?<![<a-z0-9])/(?:home|users)/[^"\s]+', rendered)
    if absolute_home:
        raise AuditError("live absolute home path present in report")
    if '"prompt"' in rendered or '"transcript"' in rendered:
        raise AuditError("raw prompt/transcript field present in report")


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"unable to read JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError(f"expected JSON object in {path}")
    return payload


def _write_or_print(payload: Mapping[str, Any], output: str | None) -> None:
    assert_secret_free(payload)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="Collect one read-only normalized snapshot")
    snapshot.add_argument("--repo", required=True)
    snapshot.add_argument("--source-root", required=True)
    snapshot.add_argument("--scenario-id", required=True)
    snapshot.add_argument("--client", required=True)
    snapshot.add_argument("--client-version", default="unknown")
    snapshot.add_argument("--worktree-label", required=True)
    snapshot.add_argument("--state-home")
    snapshot.add_argument("--hooks-loaded", choices=("true", "false", "unknown"), default="unknown")
    snapshot.add_argument("--source-resolved", choices=("true", "false", "unknown"), default="unknown")
    snapshot.add_argument("--output")

    replay = subparsers.add_parser("replay", help="Replay and classify a secret-free fixture")
    replay.add_argument("--fixture", required=True)
    replay.add_argument("--output")
    return parser


def _optional_bool(value: str) -> bool | None:
    return None if value == "unknown" else value == "true"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            payload = collect_snapshot(
                args.repo,
                source_root=args.source_root,
                scenario_id=args.scenario_id,
                client_name=args.client,
                client_version=args.client_version,
                worktree_label=args.worktree_label,
                state_home=args.state_home,
                hooks_loaded=_optional_bool(args.hooks_loaded),
                source_resolved=_optional_bool(args.source_resolved),
            )
        else:
            payload = replay_fixture(_read_json(args.fixture))
        _write_or_print(payload, args.output)
    except AuditError as exc:
        print(f"worktree capture audit failed: {exc}", file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess smoke.
    raise SystemExit(main())


__all__ = [
    "ATTRIBUTION_FIELDS",
    "AuditError",
    "CAUSE_CODES",
    "HOOK_EVENTS",
    "REQUIRED_ASSETS",
    "RESULT_STATUSES",
    "SCHEMA_VERSION",
    "assert_secret_free",
    "classify_scenario",
    "collect_snapshot",
    "load_ledger_module",
    "main",
    "replay_fixture",
]
