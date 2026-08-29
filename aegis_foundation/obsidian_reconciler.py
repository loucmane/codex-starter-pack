"""Automatic, failure-bounded reconciliation of Aegis Obsidian projections."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from aegis_foundation import obsidian_live_index, obsidian_vault
from aegis_foundation.obsidian_ledger_reader import read_events
from aegis_foundation.obsidian_registry import ProjectConfig, Registry

SCHEMA_VERSION = "1"
MAX_EXPORT_BYTES = 8 * 1024 * 1024
BeadExporter = Callable[[tuple[str, ...], int], bytes]
EventReader = Callable[[Path], list[dict[str, Any]]]
Clock = Callable[[], datetime]
LiveIndexRunner = obsidian_live_index.Runner


class ReconcileError(RuntimeError):
    """Raised for a bounded source, publication, or state failure."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _redact_error(value: object) -> str:
    return " ".join(str(value).split())[:1_000]


def export_beads(argv: tuple[str, ...], timeout: int) -> bytes:
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReconcileError(f"bead export failed: {_redact_error(exc)}") from exc
    if result.returncode != 0:
        detail = _redact_error((result.stderr or result.stdout).decode("utf-8", errors="replace"))
        raise ReconcileError(f"bead export refused ({result.returncode}): {detail}")
    if len(result.stdout) > MAX_EXPORT_BYTES:
        raise ReconcileError(
            f"bead export exceeds size limit ({len(result.stdout)} > {MAX_EXPORT_BYTES})"
        )
    if not result.stdout.strip():
        raise ReconcileError("bead export returned no records")
    return result.stdout


def _read_state(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _snapshot(
    project: ProjectConfig,
    *,
    state_dir: Path,
    bead_exporter: BeadExporter,
    event_reader: EventReader,
) -> tuple[dict[str, Any], bytes]:
    exported = bead_exporter(project.bead_export_argv, project.export_timeout_seconds)
    if len(exported) > MAX_EXPORT_BYTES:
        raise ReconcileError(
            f"bead export exceeds size limit ({len(exported)} > {MAX_EXPORT_BYTES})"
        )
    descriptor, raw = tempfile.mkstemp(prefix=f".{project.id}.beads.", dir=state_dir)
    temporary = Path(raw)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(exported)
        events = event_reader(project.target_dir)
        snapshot = obsidian_vault.collect_snapshot(
            project.target_dir,
            events,
            bead_snapshot=temporary,
            include_bead_content=project.include_bead_content,
        )
    except (obsidian_vault.VaultError, OSError, ValueError) as exc:
        raise ReconcileError(_redact_error(exc)) from exc
    finally:
        temporary.unlink(missing_ok=True)
    authority = snapshot.get("work_authority", {})
    if authority.get("authority") != "beads":
        raise ReconcileError("snapshot did not resolve exact bead authority")
    if not snapshot.get("work_items"):
        raise ReconcileError("snapshot contains no bead work items")
    return snapshot, exported


def _lock(state_dir: Path, project_id: str) -> tuple[Any, bool]:
    path = state_dir / f"{project_id}.lock"
    handle = path.open("a+", encoding="utf-8")
    os.chmod(path, 0o600)
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return handle, False
    return handle, True


def _attempt_state(
    previous: dict[str, Any],
    *,
    project: ProjectConfig,
    registry: Registry,
    attempted_at: str,
    last_success: dict[str, Any] | None,
    last_error: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project.id,
        "registry_digest": registry.digest,
        "target_dir": project.target_dir.as_posix(),
        "output_dir": project.output_dir.as_posix(),
        "last_attempt_at": attempted_at,
        "last_success": last_success,
        "last_error": last_error,
        "previous_attempt_at": previous.get("last_attempt_at"),
    }


def _reconcile_project(
    project: ProjectConfig,
    registry: Registry,
    *,
    state_dir: Path,
    bead_exporter: BeadExporter,
    event_reader: EventReader,
    live_index_runner: LiveIndexRunner,
    clock: Clock,
    force: bool,
) -> dict[str, Any]:
    state_path = state_dir / f"{project.id}.json"
    previous = _read_state(state_path)
    now = clock()
    previous_attempt = _parse_time(previous.get("last_attempt_at"))
    if (
        not force
        and previous_attempt is not None
        and (now - previous_attempt).total_seconds() < project.min_interval_seconds
    ):
        return {"id": project.id, "ok": True, "status": "debounced", "changed": False}
    lock_handle, acquired = _lock(state_dir, project.id)
    if not acquired:
        lock_handle.close()
        return {"id": project.id, "ok": True, "status": "already-running", "changed": False}
    attempted_at = _iso(now)
    try:
        snapshot, exported = _snapshot(
            project,
            state_dir=state_dir,
            bead_exporter=bead_exporter,
            event_reader=event_reader,
        )
        try:
            built = obsidian_vault.build_vault(
                snapshot,
                project.output_dir,
                target_dir=project.target_dir,
            )
            gates = [
                obsidian_vault.gate_vault(
                    project.output_dir,
                    phase=phase,
                    expected_source_digest=snapshot["source_digest"],
                    expected_work_authority="beads",
                )
                for phase in ("readiness", "closeout", "publication")
            ]
        except (obsidian_vault.VaultError, OSError) as exc:
            raise ReconcileError(_redact_error(exc)) from exc
        if not all(gate["ok"] for gate in gates):
            problems = [problem for gate in gates for problem in gate.get("problems", [])]
            raise ReconcileError("projection gate failed: " + "; ".join(problems))
        if project.live_index is None:
            live_index = obsidian_live_index.not_run(
                configured=False,
                status="not-configured",
            )
        elif built["changed"]:
            live_index = obsidian_live_index.observe(
                project.live_index,
                refresh=True,
                runner=live_index_runner,
            )
        else:
            live_index = obsidian_live_index.not_run(
                configured=True,
                status="not-run-no-change",
            )
        bead_digest = hashlib.sha256(exported).hexdigest()
        _atomic_bytes(state_dir / f"{project.id}-beads.json", exported)
        success = {
            "completed_at": attempted_at,
            "source_digest": snapshot["source_digest"],
            "bead_snapshot_sha256": bead_digest,
            "vault_status": built["status"],
            "file_count": built["file_count"],
            "gate_phases": [gate["phase"] for gate in gates],
            "live_index": live_index,
        }
        _atomic_json(
            state_path,
            _attempt_state(
                previous,
                project=project,
                registry=registry,
                attempted_at=attempted_at,
                last_success=success,
                last_error=None,
            ),
        )
        return {
            "id": project.id,
            "ok": True,
            "status": built["status"],
            "changed": built["changed"],
            "source_digest": snapshot["source_digest"],
            "output": project.output_dir.as_posix(),
            "file_count": built["file_count"],
            "live_index": live_index,
        }
    except ReconcileError as exc:
        message = _redact_error(exc)
        _atomic_json(
            state_path,
            _attempt_state(
                previous,
                project=project,
                registry=registry,
                attempted_at=attempted_at,
                last_success=previous.get("last_success"),
                last_error={"failed_at": attempted_at, "message": message},
            ),
        )
        return {"id": project.id, "ok": False, "status": "failed", "error": message}
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()


def reconcile_registry(
    registry: Registry,
    *,
    state_dir: str | Path,
    bead_exporter: BeadExporter = export_beads,
    event_reader: EventReader = read_events,
    live_index_runner: LiveIndexRunner = obsidian_live_index.run_command,
    clock: Clock = _now,
    force: bool = False,
) -> dict[str, Any]:
    state = Path(state_dir).expanduser().resolve()
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state, 0o700)
    projects = [
        _reconcile_project(
            project,
            registry,
            state_dir=state,
            bead_exporter=bead_exporter,
            event_reader=event_reader,
            live_index_runner=live_index_runner,
            clock=clock,
            force=force,
        )
        for project in registry.projects
        if project.enabled
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": bool(projects) and all(item["ok"] for item in projects),
        "registry": registry.path.as_posix(),
        "registry_digest": registry.digest,
        "projects": projects,
    }


def check_registry(
    registry: Registry,
    *,
    state_dir: str | Path,
    bead_exporter: BeadExporter = export_beads,
    event_reader: EventReader = read_events,
    live_index_runner: LiveIndexRunner = obsidian_live_index.run_command,
    clock: Clock = _now,
    require_live_index: bool = False,
) -> dict[str, Any]:
    state = Path(state_dir).expanduser().resolve()
    checked: list[dict[str, Any]] = []
    for project in registry.projects:
        if not project.enabled:
            continue
        filesystem_problems: list[str] = []
        state_payload = _read_state(state / f"{project.id}.json")
        last_success = state_payload.get("last_success")
        success_time = _parse_time(
            last_success.get("completed_at") if isinstance(last_success, dict) else None
        )
        age = (clock() - success_time).total_seconds() if success_time is not None else None
        if age is None or age > project.freshness_sla_seconds:
            filesystem_problems.append("last successful reconciliation exceeds freshness SLA")
        try:
            snapshot, _exported = _snapshot(
                project,
                state_dir=state,
                bead_exporter=bead_exporter,
                event_reader=event_reader,
            )
            vault = obsidian_vault.gate_vault(
                project.output_dir,
                phase="readiness",
                expected_source_digest=snapshot["source_digest"],
                expected_work_authority="beads",
            )
            filesystem_problems.extend(vault.get("problems", []))
            source_digest = snapshot["source_digest"]
        except (ReconcileError, obsidian_vault.VaultError, OSError) as exc:
            filesystem_problems.append(_redact_error(exc))
            source_digest = None
        if require_live_index and not filesystem_problems:
            if project.live_index is None:
                live_index = obsidian_live_index.not_run(
                    configured=False,
                    status="not-configured",
                )
            else:
                live_index = obsidian_live_index.observe(
                    project.live_index,
                    refresh=False,
                    runner=live_index_runner,
                )
        elif require_live_index:
            live_index = obsidian_live_index.not_run(
                configured=project.live_index is not None,
                status="skipped-filesystem-invalid",
            )
        else:
            raw_success = last_success if isinstance(last_success, dict) else {}
            saved_observation = raw_success.get("live_index")
            live_index = (
                saved_observation
                if isinstance(saved_observation, dict)
                else obsidian_live_index.not_run(
                    configured=project.live_index is not None,
                    status="not-yet-observed",
                )
            )
        problems = list(filesystem_problems)
        if require_live_index and live_index.get("status") != "confirmed":
            problems.append(
                "live Obsidian index is not confirmed: "
                + str(live_index.get("status") or "unknown")
            )
        checked.append(
            {
                "id": project.id,
                "ok": not problems,
                "fresh": not problems,
                "filesystem_ok": not filesystem_problems,
                "live_index_required": require_live_index,
                "live_index": live_index,
                "age_seconds": age,
                "source_digest": source_digest,
                "problems": problems,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": bool(checked) and all(item["ok"] for item in checked),
        "registry_digest": registry.digest,
        "live_index_required": require_live_index,
        "projects": checked,
    }


__all__ = [
    "MAX_EXPORT_BYTES",
    "ReconcileError",
    "check_registry",
    "export_beads",
    "reconcile_registry",
]
