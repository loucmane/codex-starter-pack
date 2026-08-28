"""Bounded host-Obsidian refresh and observation for managed Aegis projections."""

from __future__ import annotations

from collections.abc import Callable
import subprocess
from typing import Any

from aegis_foundation.obsidian_registry import LiveIndexConfig

MAX_OUTPUT_BYTES = 64 * 1024
Runner = Callable[[tuple[str, ...], int], subprocess.CompletedProcess[bytes]]


def run_command(argv: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _detail(stdout: bytes | None, stderr: bytes | None) -> str:
    raw = (stderr or stdout or b"").decode("utf-8", errors="replace")
    return " ".join(raw.split())[:1_000]


def _execute(
    argv: tuple[str, ...],
    *,
    timeout: int,
    runner: Runner,
) -> dict[str, Any]:
    try:
        result = runner(argv, timeout)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "status": "unavailable",
            "returncode": None,
            "detail": _detail(b"", str(exc).encode()),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "status": "timeout",
            "returncode": None,
            "detail": f"Obsidian CLI exceeded {timeout}s timeout",
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": "unavailable",
            "returncode": None,
            "detail": _detail(b"", str(exc).encode()),
        }

    stdout = result.stdout or b""
    stderr = result.stderr or b""
    if len(stdout) + len(stderr) > MAX_OUTPUT_BYTES:
        return {
            "ok": False,
            "status": "failed",
            "returncode": result.returncode,
            "detail": "Obsidian CLI output exceeded bounded size",
        }
    detail = _detail(stdout, stderr)
    if result.returncode == 0:
        return {
            "ok": True,
            "status": "passed",
            "returncode": 0,
            "detail": "",
        }
    lowered = detail.lower()
    unavailable = (
        "unable to find obsidian" in lowered
        or "make sure obsidian is running" in lowered
        or "obsidian is not running" in lowered
    )
    return {
        "ok": False,
        "status": "unavailable" if unavailable else "failed",
        "returncode": result.returncode,
        "detail": detail,
    }


def observe(
    config: LiveIndexConfig,
    *,
    refresh: bool,
    runner: Runner = run_command,
) -> dict[str, Any]:
    """Refresh when requested, then prove one managed note through live Obsidian IPC."""

    base = (config.obsidian_cli.as_posix(), f"vault={config.vault}")
    refresh_result: dict[str, Any] | None = None
    if refresh:
        refresh_result = _execute(
            (*base, "reload"),
            timeout=config.timeout_seconds,
            runner=runner,
        )
        if not refresh_result["ok"]:
            return {
                "configured": True,
                "ok": False,
                "authority": "observer-limited",
                "status": refresh_result["status"],
                "refresh_attempted": True,
                "refresh": refresh_result,
                "probe": None,
            }

    probe_result = _execute(
        (*base, "read", f"path={config.probe_path}"),
        timeout=config.timeout_seconds,
        runner=runner,
    )
    return {
        "configured": True,
        "ok": bool(probe_result["ok"]),
        "authority": "host-obsidian-ipc",
        "status": "confirmed" if probe_result["ok"] else probe_result["status"],
        "refresh_attempted": refresh,
        "refresh": refresh_result,
        "probe": probe_result,
        "vault": config.vault,
        "probe_path": config.probe_path,
    }


def not_run(*, configured: bool, status: str) -> dict[str, Any]:
    return {
        "configured": configured,
        "ok": None,
        "authority": "not-observed",
        "status": status,
        "refresh_attempted": False,
        "refresh": None,
        "probe": None,
    }


__all__ = ["MAX_OUTPUT_BYTES", "Runner", "not_run", "observe", "run_command"]
