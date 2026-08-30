#!/usr/bin/env python3
"""Transactionally install the generic report-only Gas City evidence reviewer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
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
DEFAULT_CODEX_CONFIG = Path("/home/loucmane/.codex/config.toml")
DEFAULT_EVIDENCE_ROOT = Path("/home/loucmane/gascity/evidence-runs")
ASSET_ROOT = Path(__file__).resolve().parent.parent / "config" / "evidence-reviewer"
AGENT_RELATIVE = Path("agents/evidence-reviewer")
TRUST_BEGIN = "# GAS-CITY-WORKFLOW:BEGIN evidence-reviewer-project-trust v1"
TRUST_END = "# GAS-CITY-WORKFLOW:END evidence-reviewer-project-trust v1"
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


def _parse_toml(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise InstallError(f"{label} is invalid TOML") from exc
    if not isinstance(parsed, dict):
        raise InstallError(f"{label} root must be a table")
    return parsed


def _strip_trust_block(text: str) -> tuple[str, str | None]:
    lines = text.splitlines(keepends=True)
    begin = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == TRUST_BEGIN]
    end = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == TRUST_END]
    if not begin and not end:
        return text, None
    if len(begin) != 1 or len(end) != 1 or begin[0] >= end[0]:
        raise InstallError("Codex config has malformed or duplicate evidence trust markers")
    managed = "".join(lines[begin[0] : end[0] + 1])
    return "".join(lines[: begin[0]] + lines[end[0] + 1 :]), managed


def _project_identity(value: str) -> Path | None:
    path = Path(value).expanduser()
    if not path.is_absolute():
        return None
    try:
        return path.resolve(strict=False)
    except OSError:
        return None


def render_codex_config(before: bytes, evidence_root: Path) -> bytes:
    """Render one exact attended-Codex trust entry without rewriting unrelated bytes."""

    _parse_toml(before, label="Codex config")
    before_text = before.decode("utf-8")
    base_text, managed = _strip_trust_block(before_text)
    base = _parse_toml(base_text.encode("utf-8"), label="unmanaged Codex config")
    projects = base.get("projects", {})
    if not isinstance(projects, dict):
        raise InstallError("Codex config [projects] must be a table")

    exact_path = evidence_root.as_posix()
    canonical = evidence_root.resolve(strict=True)
    expected_block = (
        f"{TRUST_BEGIN}\n"
        f"[projects.{json.dumps(exact_path)}]\n"
        'trust_level = "trusted"\n'
        f"{TRUST_END}\n"
    )
    if managed is not None and managed != expected_block:
        raise InstallError("managed evidence-root trust block drifted")
    exact = projects.get(exact_path)
    if exact is not None:
        if not isinstance(exact, dict) or exact.get("trust_level") != "trusted":
            raise InstallError("Codex config has a conflicting exact evidence-root trust entry")
        rendered = base_text
    else:
        for configured_path in projects:
            if not isinstance(configured_path, str):
                raise InstallError("Codex config project keys must be strings")
            if _project_identity(configured_path) == canonical:
                raise InstallError(
                    "Codex config has an alias for the evidence root; exact-path trust is required"
                )
        rendered = base_text
        if rendered and not rendered.endswith("\n"):
            rendered += "\n"
        rendered += expected_block

    result = rendered.encode("utf-8")
    parsed = _parse_toml(result, label="proposed Codex config")
    trusted = parsed.get("projects", {}).get(exact_path)
    if not isinstance(trusted, dict) or trusted.get("trust_level") != "trusted":
        raise InstallError("proposed Codex config does not contain exact trusted evidence root")
    return result


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


def expected_city_config(before: bytes, provider: bytes, *, agent_state: str) -> bytes:
    text = before.decode("utf-8")
    fragment = provider.decode("utf-8").strip() + "\n"
    provider_present = "[providers.codex-evidence]" in text
    if agent_state == "absent":
        if provider_present:
            raise InstallError("codex-evidence provider exists without its managed agent")
        return render_city_config(before, provider)
    if not provider_present or text.count(fragment) != 1:
        raise InstallError("installed codex-evidence provider bytes drifted")
    parsed = _parse_toml(before, label="city.toml")
    source = _parse_toml(provider, label="provider asset")
    if parsed.get("providers", {}).get("codex-evidence") != source.get("providers", {}).get(
        "codex-evidence"
    ):
        raise InstallError("installed codex-evidence provider semantics drifted")
    return before


def _agent_state(agent_dir: Path, assets: dict[str, bytes]) -> str:
    if not agent_dir.exists():
        return "absent"
    if not agent_dir.is_dir() or agent_dir.is_symlink():
        raise InstallError("evidence-reviewer agent path is unsafe")
    expected_names = {"agent.toml", "prompt.template.md"}
    actual_names = {entry.name for entry in agent_dir.iterdir()}
    if actual_names != expected_names:
        raise InstallError("installed evidence-reviewer agent file set drifted")
    for name in sorted(expected_names):
        if _read_regular(agent_dir / name) != assets[name]:
            raise InstallError(f"installed evidence-reviewer {name} drifted")
    return "exact"


def _validate_evidence_root(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise InstallError("evidence root must be an existing non-symlink directory")
    resolved = path.resolve(strict=True)
    if resolved != DEFAULT_EVIDENCE_ROOT.resolve(strict=True):
        raise InstallError(f"unsupported evidence root: {resolved}")
    return resolved


def _validate_codex_config_path(path: Path) -> tuple[Path, int]:
    if path.is_symlink() or not path.is_file():
        raise InstallError("Codex config must be an existing regular non-symlink file")
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise InstallError("Codex config parent is unsafe")
    resolved = path.resolve(strict=True)
    if resolved != DEFAULT_CODEX_CONFIG.resolve(strict=True):
        raise InstallError(f"unsupported Codex config: {resolved}")
    details = path.stat()
    mode = stat.S_IMODE(details.st_mode)
    if details.st_uid != os.getuid():
        raise InstallError("Codex config is not owned by the executing user")
    if mode & 0o022:
        raise InstallError("Codex config is group- or world-writable")
    return resolved, mode


def _validate_codex_trust(path: Path, evidence_root: Path) -> None:
    parsed = _parse_toml(_read_regular(path), label="installed Codex config")
    entry = parsed.get("projects", {}).get(evidence_root.as_posix())
    if not isinstance(entry, dict) or entry.get("trust_level") != "trusted":
        raise InstallError("installed Codex config trust readback mismatch")


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


def install(
    city: Path,
    gc: Path,
    *,
    apply: bool,
    codex_config: Path | None = None,
    evidence_root: Path | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    runner = runner or Runner()
    city = city.resolve()
    gc = gc.resolve()
    if city != DEFAULT_CITY:
        raise InstallError(f"unsupported city root: {city}")
    if gc != DEFAULT_GC or not gc.is_file():
        raise InstallError(f"unsupported gc binary: {gc}")
    codex_config, codex_mode = _validate_codex_config_path(
        codex_config or DEFAULT_CODEX_CONFIG
    )
    evidence_root = _validate_evidence_root(evidence_root or DEFAULT_EVIDENCE_ROOT)
    city_toml = city / "city.toml"
    agent_dir = city / AGENT_RELATIVE
    if not agent_dir.parent.is_dir() or agent_dir.parent.is_symlink():
        raise InstallError("city agents root is missing or unsafe")
    targets = {
        "city.toml": city_toml,
        "agent.toml": agent_dir / "agent.toml",
        "prompt.template.md": agent_dir / "prompt.template.md",
        "codex-config.toml": codex_config,
    }
    assets = {
        "provider.toml": _asset("provider.toml"),
        "agent.toml": _asset("agent.toml"),
        "prompt.template.md": _asset("prompt.template.md"),
    }
    before = _read_regular(city_toml)
    codex_before = _read_regular(codex_config)
    state = _agent_state(agent_dir, assets)
    expected_city = expected_city_config(before, assets["provider.toml"], agent_state=state)
    expected_codex = render_codex_config(codex_before, evidence_root)
    pre = _status(runner, gc, city)
    plan = {
        "schema": SCHEMA,
        "status": "planned",
        "city": city.as_posix(),
        "before_city_sha256": _sha256(before),
        "after_city_sha256": _sha256(expected_city),
        "before_codex_config_sha256": _sha256(codex_before),
        "after_codex_config_sha256": _sha256(expected_codex),
        "codex_config_mode": f"{codex_mode:04o}",
        "evidence_root": evidence_root.as_posix(),
        "agent_state": state,
        "operation": "install" if state == "absent" else "trust-repair",
        "city_changed": expected_city != before,
        "codex_config_changed": expected_codex != codex_before,
        "asset_sha256": {name: _sha256(data) for name, data in assets.items()},
        "controller_pid": pre["controller"]["pid"],
        "targets": {name: path.as_posix() for name, path in targets.items()},
    }
    if not apply:
        return plan
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    evidence = city / ".gc" / "gas-city-workflow" / "evidence-reviewer-install" / stamp
    if evidence.exists():
        raise InstallError("install evidence path already exists")
    evidence.mkdir(parents=True, mode=0o700)
    _atomic_write(evidence / "city.toml.before", before, 0o600)
    _atomic_write(evidence / "codex-config.toml.before", codex_before, 0o600)
    _atomic_write(
        evidence / "plan.json",
        (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode(),
        0o600,
    )
    city_mutated = False
    agent_created = False
    codex_mutated = False
    try:
        if expected_city != before:
            _atomic_write(city_toml, expected_city, 0o644)
            city_mutated = True
        if state == "absent":
            agent_dir.mkdir(mode=0o755)
            agent_created = True
            _atomic_write(targets["agent.toml"], assets["agent.toml"], 0o644)
            _atomic_write(targets["prompt.template.md"], assets["prompt.template.md"], 0o644)
        if expected_codex != codex_before:
            _atomic_write(codex_config, expected_codex, codex_mode)
            codex_mutated = True
        provider = _validate_resolved(runner, gc, city)
        _validate_codex_trust(codex_config, evidence_root)
        if city_mutated or agent_created:
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
    except Exception as exc:
        rollback_errors: list[str] = []
        if codex_mutated:
            try:
                _atomic_write(codex_config, codex_before, codex_mode)
            except Exception as rollback_exc:  # noqa: BLE001 - collect all rollback failures.
                rollback_errors.append(f"codex-config={rollback_exc}")
        if city_mutated or agent_created:
            try:
                _atomic_write(city_toml, before, 0o644)
                if agent_created and agent_dir.exists():
                    shutil.rmtree(agent_dir, ignore_errors=False)
                runner.run([str(gc), "--city", str(city), "reload"], env=_env())
                restored = _status(runner, gc, city)
                if restored["controller"]["pid"] != pre["controller"]["pid"]:
                    raise InstallError("rollback restored bytes but controller epoch changed")
            except Exception as rollback_exc:  # noqa: BLE001 - collect all rollback failures.
                rollback_errors.append(f"gas-city={rollback_exc}")
        try:
            if _read_regular(codex_config) != codex_before:
                raise InstallError("rollback did not restore exact Codex config bytes")
        except Exception as rollback_exc:  # noqa: BLE001 - report incomplete rollback.
            rollback_errors.append(f"codex-readback={rollback_exc}")
        if rollback_errors:
            raise InstallError(
                "evidence-reviewer transaction failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default=str(DEFAULT_CITY))
    parser.add_argument("--gc", default=str(DEFAULT_GC))
    parser.add_argument("--codex-config", default=str(DEFAULT_CODEX_CONFIG))
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = install(
            Path(args.city),
            Path(args.gc),
            apply=args.apply,
            codex_config=Path(args.codex_config),
            evidence_root=Path(args.evidence_root),
        )
    except Exception as exc:  # noqa: BLE001 - stable fail-closed CLI boundary.
        print(f"evidence-reviewer-install: BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
