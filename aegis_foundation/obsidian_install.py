"""Deterministic user-level installation assets for Obsidian reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from typing import Sequence
import zipfile

from aegis_foundation.obsidian_registry import Registry, load_registry

RUNTIME_MODULES = (
    "obsidian_reconcile_cli.py",
    "obsidian_reconciler.py",
    "obsidian_registry.py",
    "obsidian_live_index.py",
    "obsidian_ledger_reader.py",
    "obsidian_vault.py",
    "work_authority.py",
)
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def _zip_info(name: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def build_runtime_bytes(source_root: str | Path) -> bytes:
    root = Path(source_root).resolve()
    package = root / "aegis_foundation"
    files: dict[str, bytes] = {
        "__main__.py": (
            "from aegis_foundation.obsidian_reconcile_cli import main\n"
            "raise SystemExit(main())\n"
        ).encode(),
        "aegis_foundation/__init__.py": b'"""Installed Aegis Obsidian runtime."""\n',
    }
    for name in RUNTIME_MODULES:
        source = package / name
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f"runtime source is missing or unsafe: {source}")
        files[f"aegis_foundation/{name}"] = source.read_bytes()
    buffer = io.BytesIO()
    buffer.write(b"#!/usr/bin/env python3\n")
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in sorted(files.items()):
            archive.writestr(_zip_info(name), content)
    return buffer.getvalue()


def _unit_quote(value: str | Path) -> str:
    raw = str(value)
    if any(ord(character) < 32 or ord(character) == 127 for character in raw):
        raise RuntimeError(f"systemd unit path contains a control character: {raw!r}")
    return '"' + raw.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_assets(
    *,
    home: str | Path,
    registry_path: str | Path,
    registry: Registry | None = None,
) -> dict[str, bytes]:
    resolved_home = Path(home).resolve()
    active_registry = registry or load_registry(registry_path)
    stable_registry_path = Path(registry_path).resolve()
    runtime = resolved_home / ".local" / "bin" / "aegis-obsidian-reconcile"
    state = resolved_home / ".local" / "state" / "aegis" / "obsidian-reconciler"
    writable = {
        state,
        *(item.output_dir.parent for item in active_registry.projects if item.enabled),
    }
    write_lines = "\n".join(f"ReadWritePaths={_unit_quote(path)}" for path in sorted(writable))
    service = f"""[Unit]
Description=Reconcile deterministic Aegis evidence into Obsidian
After=default.target

[Service]
Type=oneshot
ExecStart={_unit_quote(runtime)} run --registry {_unit_quote(stable_registry_path)} --state-dir {_unit_quote(state)}
Environment={_unit_quote(f"PATH={resolved_home}/gascity/bin:/usr/local/bin:/usr/bin:/bin")}
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
{write_lines}
ProtectControlGroups=true
ProtectKernelModules=true
ProtectKernelTunables=true
RestrictSUIDSGID=true
LockPersonality=true
"""
    timer = """[Unit]
Description=Keep deterministic Aegis Obsidian projections fresh

[Timer]
OnBootSec=45s
OnUnitActiveSec=60s
RandomizedDelaySec=5s
AccuracySec=1s
Persistent=true
Unit=aegis-obsidian-reconcile.service

[Install]
WantedBy=timers.target
"""
    return {
        "aegis-obsidian-reconcile.service": service.encode(),
        "aegis-obsidian-reconcile.timer": timer.encode(),
    }


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700 if mode == 0o600 else 0o755)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def _run_systemctl(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *arguments],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _unit_state(unit: str) -> dict[str, object]:
    enabled = _run_systemctl("is-enabled", unit)
    active = _run_systemctl("is-active", unit)
    return {
        "enabled": enabled.returncode == 0 and enabled.stdout.strip() == "enabled",
        "active": active.returncode == 0 and active.stdout.strip() == "active",
        "enabled_value": enabled.stdout.strip(),
        "active_value": active.stdout.strip(),
    }


def _expected_files(
    *,
    home: Path,
    source_root: Path,
    registry_source: Path,
) -> tuple[dict[Path, tuple[bytes, int]], Registry]:
    registry = load_registry(registry_source)
    registry_destination = home / ".config" / "aegis" / "obsidian-projects.json"
    assets = render_assets(
        home=home,
        registry_path=registry_destination,
        registry=registry,
    )
    files: dict[Path, tuple[bytes, int]] = {
        home
        / ".local/bin/aegis-obsidian-reconcile": (
            build_runtime_bytes(source_root),
            0o755,
        ),
        registry_destination: (registry_source.read_bytes(), 0o600),
    }
    files.update(
        {home / ".config/systemd/user" / name: (content, 0o644) for name, content in assets.items()}
    )
    return files, registry


def _manifest_path(home: Path) -> Path:
    return home / ".local/state/aegis/obsidian-reconciler/install-manifest.json"


def _read_manifest(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _verify_previous(
    files: dict[Path, tuple[bytes, int]], manifest: dict[str, object] | None
) -> None:
    declared = manifest.get("files") if isinstance(manifest, dict) else None
    declared_files = declared if isinstance(declared, dict) else {}
    for path, (expected, _mode) in files.items():
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"managed destination is not a regular file: {path}")
        current = _digest(path.read_bytes())
        prior = declared_files.get(path.as_posix())
        if prior is None and current != _digest(expected):
            raise RuntimeError(f"refusing unknown existing installation file: {path}")
        if isinstance(prior, str) and current != prior:
            raise RuntimeError(f"installed file drift: {path}")


def install(
    *,
    home: Path,
    source_root: Path,
    registry_source: Path,
) -> dict[str, object]:
    files, registry = _expected_files(
        home=home,
        source_root=source_root,
        registry_source=registry_source,
    )
    manifest_path = _manifest_path(home)
    previous_manifest = _read_manifest(manifest_path)
    _verify_previous(files, previous_manifest)
    output_parents = sorted(
        {project.output_dir.parent for project in registry.projects if project.enabled}
    )
    for parent in output_parents:
        if parent.is_symlink() or not parent.is_dir():
            raise RuntimeError(f"registered Obsidian output parent is missing or unsafe: {parent}")
    previous_files = {
        path: (
            path.read_bytes() if path.is_file() and not path.is_symlink() else None,
            stat.S_IMODE(path.stat().st_mode) if path.is_file() and not path.is_symlink() else None,
        )
        for path in files
    }
    timer = "aegis-obsidian-reconcile.timer"
    before_timer = _unit_state(timer)
    wrote_manifest = False
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if manifest_path.parent.is_symlink() or not manifest_path.parent.is_dir():
            raise RuntimeError(f"reconciler state directory is unsafe: {manifest_path.parent}")
        os.chmod(manifest_path.parent, 0o700)
        for path, (content, mode) in files.items():
            _atomic_write(path, content, mode)
        reload_result = _run_systemctl("daemon-reload")
        if reload_result.returncode != 0:
            raise RuntimeError(f"systemd user daemon-reload failed: {reload_result.stderr.strip()}")
        enabled = _run_systemctl("enable", "--now", timer)
        if enabled.returncode != 0:
            raise RuntimeError(f"timer enable failed: {enabled.stderr.strip()}")
        started = _run_systemctl("start", "aegis-obsidian-reconcile.service")
        if started.returncode != 0:
            raise RuntimeError(f"initial reconciliation failed: {started.stderr.strip()}")
        state = _unit_state(timer)
        if not state["enabled"] or not state["active"]:
            raise RuntimeError(f"timer did not become enabled and active: {state}")
        runtime_check = subprocess.run(
            [
                str(home / ".local/bin/aegis-obsidian-reconcile"),
                "check",
                "--registry",
                str(home / ".config/aegis/obsidian-projects.json"),
                "--state-dir",
                str(home / ".local/state/aegis/obsidian-reconciler"),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if runtime_check.returncode != 0:
            raise RuntimeError(f"installed reconciler check failed: {runtime_check.stdout.strip()}")
        manifest = {
            "schema_version": "1",
            "registry_digest": registry.digest,
            "files": {
                path.as_posix(): _digest(content) for path, (content, _mode) in files.items()
            },
            "timer": state,
        }
        _atomic_write(
            manifest_path,
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
            0o600,
        )
        wrote_manifest = True
        return {"ok": True, "status": "installed", **manifest}
    except Exception:
        _run_systemctl("disable", "--now", timer)
        for path, (content, mode) in previous_files.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, content, int(mode or 0o600))
        _run_systemctl("daemon-reload")
        if before_timer["enabled"]:
            _run_systemctl("enable", timer)
        if before_timer["active"]:
            _run_systemctl("start", timer)
        if wrote_manifest:
            manifest_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-aegis-obsidian-reconciler")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--registry-source")
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--source-root", default=str(Path(__file__).resolve().parent.parent))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    home = Path(args.home).resolve()
    source_root = Path(args.source_root).resolve()
    registry_source = (
        Path(args.registry_source).resolve()
        if args.registry_source
        else home / ".config/aegis/obsidian-projects.json"
    )
    files, registry = _expected_files(
        home=home,
        source_root=source_root,
        registry_source=registry_source,
    )
    expected = {path.as_posix(): _digest(content) for path, (content, _mode) in files.items()}
    if args.plan:
        print(
            json.dumps(
                {
                    "schema_version": "1",
                    "registry_digest": registry.digest,
                    "expected": expected,
                    "service_transition": [
                        "systemctl --user daemon-reload",
                        "enable --now aegis-obsidian-reconcile.timer",
                        "start aegis-obsidian-reconcile.service",
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.apply:
        try:
            result = install(
                home=home,
                source_root=source_root,
                registry_source=registry_source,
            )
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print(json.dumps({"ok": False, "status": "failed", "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    manifest = _read_manifest(_manifest_path(home))
    declared = manifest.get("files") if isinstance(manifest, dict) else {}
    problems = []
    for raw, digest in expected.items():
        path = Path(raw)
        if not path.is_file() or path.is_symlink():
            problems.append(f"missing or unsafe: {path}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append(f"digest drift: {path}")
        elif not isinstance(declared, dict) or declared.get(raw) != digest:
            problems.append(f"install manifest drift: {path}")
    timer = _unit_state("aegis-obsidian-reconcile.timer")
    if not timer["enabled"] or not timer["active"]:
        problems.append(f"reconciler timer is not enabled and active: {timer}")
    if problems:
        print("\n".join(problems))
        return 1
    print("Aegis Obsidian reconciler installation files match reviewed source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
