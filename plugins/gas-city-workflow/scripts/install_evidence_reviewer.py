#!/usr/bin/env python3
"""Transactionally install the generic report-only Gas City evidence reviewer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

SCHEMA = "gas-city-workflow.evidence-reviewer-install.v1"
OPERATOR_PATH = "/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin"
DEFAULT_CITY = Path("/home/loucmane/gascity/city")
DEFAULT_GC = Path("/home/loucmane/gascity/bin/gc")
ASSET_ROOT = Path(__file__).resolve().parent.parent / "config" / "evidence-reviewer"
AGENT_RELATIVE = Path("agents/evidence-reviewer")
ANCHOR = """[providers.codex.option_defaults]
effort = "xhigh"
model = "gpt-5.6-sol"
permission_mode = "fail-fast"
worklog_access = "classified-vault"
"""


class InstallError(RuntimeError):
    """Raised when the bounded install cannot be proven safe."""


class Runner:
    def run(self, argv: Sequence[str], *, env: dict[str, str] | None = None) -> str:
        result = subprocess.run(
            list(argv), check=False, capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise InstallError(
                f"command failed ({result.returncode}): {' '.join(argv)}"
                + (f": {detail}" if detail else "")
            )
        return result.stdout


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise InstallError(f"expected regular file: {path}")
    return path.read_bytes()


def _asset(name: str) -> bytes:
    return _read_regular(ASSET_ROOT / name)


def render_city_config(before: bytes, provider: bytes) -> bytes:
    text = before.decode("utf-8")
    fragment = provider.decode("utf-8").strip() + "\n"
    if "[providers.codex-evidence]" in text:
        raise InstallError("codex-evidence provider already exists but is not install-bound")
    if text.count(ANCHOR) != 1:
        raise InstallError("city.toml Codex provider anchor is missing or ambiguous")
    rendered = text.replace(ANCHOR, ANCHOR + "\n" + fragment, 1).encode("utf-8")
    try:
        parsed = tomllib.loads(rendered.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise InstallError("rendered city.toml is invalid TOML") from exc
    evidence = parsed.get("providers", {}).get("codex-evidence", {})
    if evidence.get("base") != "provider:codex":
        raise InstallError("rendered provider base mismatch")
    return rendered


def _atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            os.chmod(temporary, mode)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _env() -> dict[str, str]:
    return {**os.environ, "PATH": OPERATOR_PATH}


def _status(runner: Runner, gc: Path, city: Path) -> dict[str, Any]:
    raw = runner.run([str(gc), "--city", str(city), "status", "--json"], env=_env())
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallError("gc status returned invalid JSON") from exc
    rigs = payload.get("rigs") if isinstance(payload, dict) else None
    if not isinstance(rigs, list) or not rigs or any(not item.get("suspended") for item in rigs):
        raise InstallError("every registered rig must be suspended")
    summary = payload.get("summary") if isinstance(payload, dict) else None
    if not isinstance(summary, dict) or summary.get("running_agents") != 0:
        raise InstallError("city must have zero running agent sessions")
    controller = payload.get("controller") if isinstance(payload, dict) else None
    if not isinstance(controller, dict) or not isinstance(controller.get("pid"), int):
        raise InstallError("gc status did not identify the controller epoch")
    return payload


def _validate_resolved(runner: Runner, gc: Path, city: Path) -> dict[str, Any]:
    runner.run([str(gc), "start", str(city), "--dry-run"], env=_env())
    raw = runner.run(
        [str(gc), "--city", str(city), "config", "explain", "--provider", "codex-evidence", "--json"],
        env=_env(),
    )
    try:
        provider = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallError("provider explanation returned invalid JSON") from exc
    resolved = provider.get("resolved") if isinstance(provider, dict) else None
    defaults = resolved.get("option_defaults") if isinstance(resolved, dict) else None
    resume = resolved.get("resume_command") if isinstance(resolved, dict) else None
    expected_defaults = {
        "effort": "xhigh",
        "model": "gpt-5.6-sol",
        "permission_mode": "fail-fast",
        "worklog_access": "isolated-workspace",
    }
    if defaults != expected_defaults:
        raise InstallError("resolved provider defaults mismatch")
    if not isinstance(resume, str) or "sandbox_workspace_write.writable_roots=[]" not in resume:
        raise InstallError("resolved provider does not clear additional writable roots")
    agent = runner.run(
        [str(gc), "--city", str(city), "config", "explain", "--agent", "evidence-reviewer"],
        env=_env(),
    )
    required_agent_facts = (
        "work_dir                       = /home/loucmane/gascity/evidence-runs",
        "provider                       = codex-evidence",
        "max_active_sessions            = 1",
    )
    if any(item not in agent for item in required_agent_facts):
        raise InstallError("resolved evidence-reviewer agent mismatch")
    prompt = runner.run(
        [str(gc), "--city", str(city), "--rig", "gascity", "prime", "evidence-reviewer"],
        env=_env(),
    )
    for sentence in (
        "Read only those declared bundle files.",
        "Do not inspect a project checkout, Git metadata",
        "Write only the declared report file",
    ):
        if sentence not in prompt:
            raise InstallError("resolved evidence-reviewer prompt mismatch")
    return provider


def install(city: Path, gc: Path, *, apply: bool, runner: Runner | None = None) -> dict[str, Any]:
    runner = runner or Runner()
    city = city.resolve()
    gc = gc.resolve()
    if city != DEFAULT_CITY:
        raise InstallError(f"unsupported city root: {city}")
    if gc != DEFAULT_GC or not gc.is_file():
        raise InstallError(f"unsupported gc binary: {gc}")
    city_toml = city / "city.toml"
    agent_dir = city / AGENT_RELATIVE
    if not agent_dir.parent.is_dir() or agent_dir.parent.is_symlink():
        raise InstallError("city agents root is missing or unsafe")
    targets = {
        "city.toml": city_toml,
        "agent.toml": agent_dir / "agent.toml",
        "prompt.template.md": agent_dir / "prompt.template.md",
    }
    assets = {
        "provider.toml": _asset("provider.toml"),
        "agent.toml": _asset("agent.toml"),
        "prompt.template.md": _asset("prompt.template.md"),
    }
    before = _read_regular(city_toml)
    expected_city = render_city_config(before, assets["provider.toml"])
    pre = _status(runner, gc, city)
    plan = {
        "schema": SCHEMA,
        "status": "planned",
        "city": city.as_posix(),
        "before_city_sha256": _sha256(before),
        "after_city_sha256": _sha256(expected_city),
        "asset_sha256": {name: _sha256(data) for name, data in assets.items()},
        "controller_pid": pre["controller"]["pid"],
        "targets": {name: path.as_posix() for name, path in targets.items()},
    }
    if not apply:
        return plan
    if agent_dir.exists():
        raise InstallError("evidence-reviewer agent path already exists")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    evidence = city / ".gc" / "gas-city-workflow" / "evidence-reviewer-install" / stamp
    if evidence.exists():
        raise InstallError("install evidence path already exists")
    evidence.mkdir(parents=True, mode=0o700)
    _atomic_write(evidence / "city.toml.before", before, 0o600)
    _atomic_write(
        evidence / "plan.json",
        (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode(),
        0o600,
    )
    mutated = False
    try:
        _atomic_write(city_toml, expected_city, 0o644)
        mutated = True
        agent_dir.mkdir(mode=0o755)
        _atomic_write(targets["agent.toml"], assets["agent.toml"], 0o644)
        _atomic_write(targets["prompt.template.md"], assets["prompt.template.md"], 0o644)
        provider = _validate_resolved(runner, gc, city)
        runner.run([str(gc), "--city", str(city), "reload"], env=_env())
        post = _status(runner, gc, city)
        if post["controller"]["pid"] != pre["controller"]["pid"]:
            raise InstallError("controller epoch changed during config-only install")
        result = {**plan, "status": "pass", "evidence": evidence.as_posix(), "provider": provider}
        _atomic_write(
            evidence / "result.json",
            (json.dumps(result, indent=2, sort_keys=True) + "\n").encode(),
            0o600,
        )
        return result
    except Exception:
        if mutated:
            _atomic_write(city_toml, before, 0o644)
            if agent_dir.exists():
                shutil.rmtree(agent_dir, ignore_errors=False)
            runner.run([str(gc), "--city", str(city), "reload"], env=_env())
            restored = _status(runner, gc, city)
            if restored["controller"]["pid"] != pre["controller"]["pid"]:
                raise InstallError("rollback restored bytes but controller epoch changed")
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default=str(DEFAULT_CITY))
    parser.add_argument("--gc", default=str(DEFAULT_GC))
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = install(Path(args.city), Path(args.gc), apply=args.apply)
    except Exception as exc:  # noqa: BLE001 - stable fail-closed CLI boundary.
        print(f"evidence-reviewer-install: BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
