#!/usr/bin/env python3
"""Read-only collectors for a frozen Gas City continuity snapshot."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from continuity_model import (  # noqa: E402
    BEAD_ID_PATTERN,
    SNAPSHOT_SCHEMA,
    ContinuityError,
)
from project_context import CITY, GC, build_context  # noqa: E402

OBSIDIAN_REGISTRY = Path.home() / ".config" / "aegis" / "obsidian-projects.json"
OBSIDIAN_STATE = Path.home() / ".local" / "state" / "aegis" / "obsidian-reconciler"
SIGNING_POLICIES = Path("/etc/gas-city-signing/signing-policies.json")
RESIDUE_DISPOSITIONS = (
    SCRIPT_DIR.parent / "config" / "continuity-residue-dispositions.json"
)
OPERATOR_PATH = "/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin"
FOLLOWUP_SCHEMA = "gas-city-workflow.followups.v1"
RESIDUE_DISPOSITIONS_SCHEMA = "gas-city-workflow.residue-dispositions.v1"
BRANCH_PREFIX = "refs/heads/"
TRACKER_TITLE = re.compile(r"^# Bead (?P<bead>\S+)\b", re.MULTILINE)
LEGACY_TRACKER_FOLDER = re.compile(r"^\d{8}-(?P<legacy>[A-Za-z0-9_.]+)-")
MANAGED_BRANCH = re.compile(
    r"^(?:refs/heads/)?codex/(?P<bead>[a-z][a-z0-9]*-[a-z0-9]+"
    r"(?:\.[1-9][0-9]*)*)(?:-|$)"
)
DISPOSITION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ReadOnlyRunner:
    """Small injectable runner; every live command is a read-only query."""

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd is not None else None,
            env={**os.environ, "PATH": OPERATOR_PATH},
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ContinuityError(
                f"read-only command failed ({result.returncode}): {' '.join(argv)}"
                + (f": {detail}" if detail else "")
            )
        return result


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ContinuityError(f"{label} must be a regular file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContinuityError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContinuityError(f"{label} must contain an object")
    return payload


def _json_list(text: str, label: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContinuityError(f"{label} returned invalid JSON: {exc}") from exc
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ContinuityError(f"{label} must return a JSON list of objects")
    return payload


def _project_bead(raw: Mapping[str, Any]) -> dict[str, Any]:
    bead_id = raw.get("id")
    title = raw.get("title")
    status = raw.get("status")
    if not isinstance(bead_id, str) or not BEAD_ID_PATTERN.fullmatch(bead_id):
        raise ContinuityError("Bead list contains an invalid id")
    if not isinstance(title, str) or not title:
        raise ContinuityError(f"Bead {bead_id} has no title")
    if not isinstance(status, str) or not status:
        raise ContinuityError(f"Bead {bead_id} has no status")
    labels = raw.get("labels", [])
    if not isinstance(labels, list) or not all(isinstance(value, str) for value in labels):
        raise ContinuityError(f"Bead {bead_id} labels are invalid")
    metadata = raw.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ContinuityError(f"Bead {bead_id} metadata is invalid")
    projected_metadata: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ContinuityError(f"Bead {bead_id} metadata key is invalid")
        if key.startswith(("gc.formula_", "gc.graphv2_", "gc.drain_")):
            projected_metadata[key] = True
        elif key == "gc.legacy":
            projected_metadata[key] = value in {True, "true", "1"}
        elif key == "workflow.authority" and isinstance(value, str):
            projected_metadata[key] = value
    dependencies = raw.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ContinuityError(f"Bead {bead_id} dependencies are invalid")
    projected_dependencies = []
    for value in dependencies:
        if not isinstance(value, Mapping):
            raise ContinuityError(f"Bead {bead_id} dependency is invalid")
        dependency_id = value.get("depends_on_id") or value.get("id")
        relation = value.get("type") or value.get("dependency_type") or "blocks"
        if (
            not isinstance(dependency_id, str)
            or not BEAD_ID_PATTERN.fullmatch(dependency_id)
            or not isinstance(relation, str)
            or not relation
        ):
            raise ContinuityError(f"Bead {bead_id} dependency identity is invalid")
        projected_dependencies.append(
            {"depends_on_id": dependency_id, "type": relation}
        )
    projected = {
        "id": bead_id,
        "title": title,
        "status": status,
        "issue_type": str(raw.get("issue_type") or "task"),
        "labels": sorted(set(labels)),
        "metadata": projected_metadata,
        "dependencies": sorted(
            projected_dependencies,
            key=lambda item: (item["depends_on_id"], item["type"]),
        ),
    }
    for key in ("parent", "started_at"):
        value = raw.get(key)
        if isinstance(value, str) and value:
            projected[key] = value
    return projected


def _load_registry(path: Path) -> list[dict[str, Any]]:
    payload = _read_object(path, "project registry")
    if payload.get("schema") != "gas-city-workflow.project-registry.v1":
        raise ContinuityError("project registry schema is invalid")
    projects = payload.get("projects")
    if not isinstance(projects, list) or not all(isinstance(item, dict) for item in projects):
        raise ContinuityError("project registry projects are invalid")
    return projects


def _bead_for_branch(branch: str, bead_ids: set[str]) -> str | None:
    short = branch.removeprefix(BRANCH_PREFIX)
    if not short.startswith("codex/"):
        return None
    tail = short.removeprefix("codex/")
    matches = [bead_id for bead_id in bead_ids if tail == bead_id or tail.startswith(f"{bead_id}-")]
    if matches:
        return max(matches, key=len)
    fallback = MANAGED_BRANCH.match(branch)
    return fallback.group("bead") if fallback else None


def _parse_worktrees(text: str, bead_ids: set[str]) -> list[dict[str, Any]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in [*text.splitlines(), ""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    result = []
    for record in records:
        branch = record.get("branch", "")
        bead_id = _bead_for_branch(branch, bead_ids)
        if bead_id is None:
            continue
        result.append(
            {
                "bead_id": bead_id,
                "path": record.get("worktree", ""),
                "branch": branch.removeprefix(BRANCH_PREFIX),
                "head": record.get("HEAD"),
            }
        )
    return sorted(result, key=lambda item: (item["bead_id"], item["path"]))


def _capture_worktree_cleanliness(
    worktrees: list[dict[str, Any]],
    runner: ReadOnlyRunner,
    *,
    required_paths: set[str],
) -> list[dict[str, Any]]:
    captured = []
    for item in worktrees:
        path = item.get("path")
        head = item.get("head")
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ContinuityError("managed worktree path must be absolute")
        if not isinstance(head, str) or not GIT_COMMIT_PATTERN.fullmatch(head):
            raise ContinuityError(f"managed worktree HEAD is invalid: {path}")
        if path not in required_paths:
            captured.append(item)
            continue
        status = runner.run(
            ["git", "-C", path, "status", "--porcelain=v1", "--untracked-files=normal"]
        ).stdout
        captured.append({**item, "clean": not bool(status.strip())})
    return captured


def _active_trackers(root: Path) -> list[dict[str, Any]]:
    active = root / "docs" / "ai" / "work-tracking" / "active"
    if not active.is_dir():
        return []
    result = []
    for folder in sorted(active.iterdir(), key=lambda path: path.name):
        if not folder.is_dir() or not folder.name.endswith("-ACTIVE"):
            continue
        tracker = folder / "TRACKER.md"
        match = TRACKER_TITLE.search(tracker.read_text(encoding="utf-8")) if tracker.is_file() else None
        bead_id = match.group("bead") if match else None
        if bead_id is not None and BEAD_ID_PATTERN.fullmatch(bead_id):
            result.append(
                {"bead_id": bead_id, "authority": "beads", "path": folder.as_posix()}
            )
            continue
        legacy = LEGACY_TRACKER_FOLDER.match(folder.name)
        if legacy is None:
            raise ContinuityError(f"active tracker has no safe work identity: {folder}")
        result.append(
            {
                "bead_id": None,
                "legacy_id": legacy.group("legacy"),
                "authority": "taskmaster",
                "path": folder.as_posix(),
            }
        )
    return result


def _transactions(root: Path) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ContinuityError(f"cannot resolve Git common directory for {root}")
    transaction_root = Path(result.stdout.strip()) / "gas-city-workflow" / "transactions"
    records = []
    if not transaction_root.is_dir():
        return records
    for path in sorted(transaction_root.glob("*.json")):
        payload = _read_object(path, "workflow transaction")
        spec = payload.get("spec")
        if not isinstance(spec, Mapping):
            raise ContinuityError(f"workflow transaction has no spec: {path}")
        bead_id = spec.get("bead_id")
        if not isinstance(bead_id, str) or not BEAD_ID_PATTERN.fullmatch(bead_id):
            raise ContinuityError(f"workflow transaction has invalid Bead: {path}")
        records.append(
            {
                "bead_id": bead_id,
                "phase": payload.get("phase"),
                "branch": spec.get("branch"),
                "worktree": spec.get("worktree"),
                "path": path.as_posix(),
            }
        )
    return records


def _followups(root: Path) -> list[dict[str, Any]]:
    path = root / ".gas-city-workflow" / "followups.json"
    if not path.exists():
        return []
    payload = _read_object(path, "structured followups")
    if payload.get("schema") != FOLLOWUP_SCHEMA or set(payload) != {"schema", "followups"}:
        raise ContinuityError("structured followups schema is invalid")
    followups = payload.get("followups")
    if not isinstance(followups, list) or not all(isinstance(item, dict) for item in followups):
        raise ContinuityError("structured followups must be a list of objects")
    return followups


def _systemd_properties(text: str) -> dict[str, str]:
    return {
        key: value
        for line in text.splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }


def _obsidian_process(runner: ReadOnlyRunner) -> dict[str, Any]:
    """Observe the WSL Obsidian scope without treating visibility failure as absence."""

    authority = "systemd-user-manager"
    try:
        listing = runner.run(
            [
                "systemctl",
                "--user",
                "list-units",
                "--type=scope",
                "--all",
                "--no-legend",
                "--plain",
                "--no-pager",
            ]
        ).stdout
        unit_names = sorted(
            {
                line.split()[0]
                for line in listing.splitlines()
                if line.split()
                and line.split()[0].endswith(".scope")
                and "obsidian" in line.split()[0].casefold()
            }
        )
        units = []
        for unit_name in unit_names:
            properties = _systemd_properties(
                runner.run(
                    [
                        "systemctl",
                        "--user",
                        "show",
                        unit_name,
                        "--property=Id",
                        "--property=ActiveState",
                        "--property=SubState",
                        "--property=ControlGroup",
                        "--property=InvocationID",
                        "--no-pager",
                    ]
                ).stdout
            )
            units.append(
                {
                    "id": properties.get("Id", unit_name),
                    "active_state": properties.get("ActiveState", "unknown"),
                    "sub_state": properties.get("SubState", "unknown"),
                    "control_group": properties.get("ControlGroup", ""),
                    "invocation_id": properties.get("InvocationID", ""),
                }
            )
    except ContinuityError:
        return {"status": "unknown", "authority": authority, "units": []}
    if not units:
        status = "absent"
    elif any(unit["active_state"] == "active" for unit in units):
        status = "active"
    else:
        status = "inactive"
    return {"status": status, "authority": authority, "units": units}


def _obsidian_cycle_status(state_root: Path) -> str:
    """Probe the registry-wide flock without creating or mutating its lock file."""

    lock_path = state_root / "registry-cycle.lock"
    if not lock_path.is_file() or lock_path.is_symlink():
        return "idle"
    try:
        with lock_path.open("rb") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return "running"
            finally:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
    except OSError:
        return "unknown"
    return "idle"


def _obsidian_index(
    registry_path: Path,
    state_root: Path,
    *,
    process: Mapping[str, Any],
    registry_cycle_status: str,
) -> dict[str, dict[str, Any]]:
    if not registry_path.exists():
        return {}
    registry = _read_object(registry_path, "Obsidian registry")
    projects = registry.get("projects")
    if not isinstance(projects, list):
        raise ContinuityError("Obsidian registry projects are invalid")
    result: dict[str, dict[str, Any]] = {}
    for raw in projects:
        project = _read_object_value(raw, "Obsidian project")
        target = project.get("target_dir")
        project_id = project.get("id")
        if not isinstance(target, str) or not isinstance(project_id, str):
            raise ContinuityError("Obsidian project identity is invalid")
        state_path = state_root / f"{project_id}.json"
        state = _read_object(state_path, "Obsidian state") if state_path.is_file() else {}
        success = state.get("last_success") if isinstance(state.get("last_success"), Mapping) else {}
        live = success.get("live_index") if isinstance(success.get("live_index"), Mapping) else {}
        pending = isinstance(state.get("pending_success"), Mapping)
        if pending and registry_cycle_status == "idle":
            project_cycle_status = "interrupted"
        elif pending and registry_cycle_status == "unknown":
            project_cycle_status = "unknown"
        else:
            project_cycle_status = registry_cycle_status
        completed_at = success.get("completed_at")
        observed_at = live.get("observed_at") or completed_at
        result[Path(target).resolve().as_posix()] = {
            "registered": True,
            "registry_project_id": project_id,
            "vault_status": success.get("vault_status"),
            "live_index_status": live.get("status"),
            "filesystem": {
                "status": success.get("vault_status"),
                "completed_at": completed_at,
            },
            "live_index": {
                "status": live.get("status"),
                "authority": live.get("authority"),
                "observed_at": observed_at,
            },
            "cycle": {
                "status": project_cycle_status,
                "attempted_at": state.get("last_attempt_at"),
                "pending_candidate": pending,
            },
            "process": dict(process),
            "state_path": state_path.as_posix(),
        }
    return result


def _read_object_value(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContinuityError(f"{label} must be an object")
    return value


def _receipt_index(signing_policies: Path) -> dict[str, list[dict[str, Any]]]:
    if not signing_policies.exists():
        return {}
    payload = _read_object(signing_policies, "signing policies")
    policies = payload.get("policies")
    if not isinstance(policies, Mapping):
        raise ContinuityError("signing policies are invalid")
    result: dict[str, list[dict[str, Any]]] = {}
    for policy_name, raw in sorted(policies.items()):
        policy = _read_object_value(raw, "signing policy")
        expected_common = policy.get("expected_common_dir")
        audit_dir = policy.get("audit_dir")
        if not isinstance(expected_common, str) or not isinstance(audit_dir, str):
            raise ContinuityError(f"signing policy {policy_name} paths are invalid")
        receipts = []
        root = Path(audit_dir)
        if root.is_dir():
            for path in sorted(root.glob("*.json")):
                receipt = _read_object(path, "managed signing receipt")
                receipt_payload = receipt.get("payload")
                if not isinstance(receipt_payload, Mapping):
                    raise ContinuityError(f"managed signing receipt payload is invalid: {path}")
                bead_id = receipt_payload.get("bead")
                if not isinstance(bead_id, str) or not BEAD_ID_PATTERN.fullmatch(bead_id):
                    raise ContinuityError(f"managed signing receipt Bead is invalid: {path}")
                receipts.append(
                    {
                        "bead_id": bead_id,
                        "commit": receipt_payload.get("commit"),
                        "path": path.as_posix(),
                        "policy": policy_name,
                    }
                )
        result[Path(expected_common).resolve().as_posix()] = receipts
    return result


def _verify_disposition_evidence(
    evidence: Mapping[str, Any],
    *,
    disposition_head: str,
    project: Mapping[str, Any],
    runner: ReadOnlyRunner,
) -> None:
    kind = evidence.get("kind")
    if kind == "git-merge":
        expected_keys = {"kind", "ref", "merge_commit", "merged_head"}
        if set(evidence) != expected_keys:
            raise ContinuityError("git-merge disposition evidence fields are invalid")
        merged_head = evidence.get("merged_head")
        merge_commit = evidence.get("merge_commit")
        ref = evidence.get("ref")
        if (
            not isinstance(merged_head, str)
            or not GIT_COMMIT_PATTERN.fullmatch(merged_head)
            or merged_head != disposition_head
            or not isinstance(merge_commit, str)
            or not GIT_COMMIT_PATTERN.fullmatch(merge_commit)
            or not isinstance(ref, str)
            or not ref.startswith("refs/")
        ):
            raise ContinuityError("git-merge disposition evidence identity is invalid")
        root = Path(str(project.get("root"))).resolve()
        parents = runner.run(
            ["git", "-C", str(root), "show", "-s", "--format=%H %P", merge_commit]
        ).stdout.strip().split()
        if not parents or parents[0] != merge_commit or merged_head not in parents[1:]:
            raise ContinuityError("git-merge disposition does not bind the preserved HEAD")
        runner.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", merge_commit, ref],
            cwd=root,
        )
        return
    if kind == "sha256-file":
        expected_keys = {"kind", "path", "sha256"}
        if set(evidence) != expected_keys:
            raise ContinuityError("sha256-file disposition evidence fields are invalid")
        raw_path = evidence.get("path")
        digest = evidence.get("sha256")
        if (
            not isinstance(raw_path, str)
            or not Path(raw_path).is_absolute()
            or not isinstance(digest, str)
            or not DIGEST_PATTERN.fullmatch(digest)
        ):
            raise ContinuityError("sha256-file disposition evidence identity is invalid")
        path = Path(raw_path)
        if not path.is_file() or path.is_symlink():
            raise ContinuityError(f"disposition evidence is not a regular file: {path}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != digest:
            raise ContinuityError(f"disposition evidence digest drift: {path}")
        return
    raise ContinuityError("residue disposition evidence kind is invalid")


def _load_residue_dispositions(
    path: Path | None,
    projects: Sequence[Mapping[str, Any]],
    runner: ReadOnlyRunner,
) -> dict[str, list[dict[str, Any]]]:
    if path is None:
        return {}
    payload = _read_object(path, "residue dispositions")
    if set(payload) != {"schema", "dispositions"}:
        raise ContinuityError("residue dispositions top-level fields are invalid")
    if payload.get("schema") != RESIDUE_DISPOSITIONS_SCHEMA:
        raise ContinuityError("residue dispositions schema is invalid")
    raw_dispositions = payload.get("dispositions")
    if not isinstance(raw_dispositions, list):
        raise ContinuityError("residue dispositions must be a list")
    project_index = {str(project.get("id")): project for project in projects}
    result: dict[str, list[dict[str, Any]]] = {}
    targets: set[tuple[str, str, str]] = set()
    ids: set[str] = set()
    for raw in raw_dispositions:
        disposition = dict(_read_object_value(raw, "residue disposition"))
        surface = disposition.get("surface")
        expected_keys = {
            "id",
            "project_id",
            "surface",
            "identity",
            "bead_id",
            "head",
            "reason",
            "evidence",
        }
        if surface == "worktree":
            expected_keys.add("required_clean")
        if set(disposition) != expected_keys:
            raise ContinuityError("residue disposition fields are invalid")
        disposition_id = disposition.get("id")
        project_id = disposition.get("project_id")
        identity = disposition.get("identity")
        bead_id = disposition.get("bead_id")
        head = disposition.get("head")
        reason = disposition.get("reason")
        evidence = disposition.get("evidence")
        if (
            not isinstance(disposition_id, str)
            or not DISPOSITION_ID_PATTERN.fullmatch(disposition_id)
            or disposition_id in ids
        ):
            raise ContinuityError("residue disposition id is invalid or duplicated")
        if project_id not in project_index:
            raise ContinuityError(f"residue disposition project is not registered: {project_id}")
        if surface not in {"branch", "worktree"}:
            raise ContinuityError("residue disposition surface is invalid")
        if not isinstance(identity, str) or not identity:
            raise ContinuityError("residue disposition identity is invalid")
        if surface == "branch" and not identity.startswith("codex/"):
            raise ContinuityError("branch residue identity must be a codex/* branch")
        if surface == "worktree" and not Path(identity).is_absolute():
            raise ContinuityError("worktree residue identity must be absolute")
        if not isinstance(bead_id, str) or not BEAD_ID_PATTERN.fullmatch(bead_id):
            raise ContinuityError("residue disposition Bead identity is invalid")
        if not isinstance(head, str) or not GIT_COMMIT_PATTERN.fullmatch(head):
            raise ContinuityError("residue disposition HEAD is invalid")
        if not isinstance(reason, str) or not reason.strip():
            raise ContinuityError("residue disposition reason is invalid")
        if surface == "worktree" and disposition.get("required_clean") is not True:
            raise ContinuityError("worktree residue dispositions must require clean state")
        if not isinstance(evidence, Mapping):
            raise ContinuityError("residue disposition evidence must be an object")
        target = (str(project_id), str(surface), identity)
        if target in targets:
            raise ContinuityError("residue disposition target is duplicated")
        _verify_disposition_evidence(
            evidence,
            disposition_head=head,
            project=project_index[str(project_id)],
            runner=runner,
        )
        ids.add(disposition_id)
        targets.add(target)
        result.setdefault(str(project_id), []).append(disposition)
    for project_id in result:
        result[project_id].sort(key=lambda item: str(item["id"]))
    return result


def capture_snapshot(
    registry_path: Path,
    *,
    extra_roots: Sequence[Path] = (),
    obsidian_registry: Path = OBSIDIAN_REGISTRY,
    obsidian_state: Path = OBSIDIAN_STATE,
    signing_policies: Path = SIGNING_POLICIES,
    residue_dispositions: Path | None = None,
    runner: ReadOnlyRunner | None = None,
) -> dict[str, Any]:
    runner = runner or ReadOnlyRunner()
    registry_bytes = registry_path.read_bytes()
    projects = _load_registry(registry_path)
    registered_ids = {str(project.get("id")) for project in projects}
    registered_roots = {Path(str(project.get("root"))).resolve() for project in projects}
    for requested in extra_roots:
        context = build_context(requested.resolve(), registry_path)
        project = context["project"]
        canonical_root = Path(str(context["workspace"]["canonical_root"])).resolve()
        project_id = str(project["id"])
        if canonical_root in registered_roots and project_id in registered_ids:
            continue
        if canonical_root in registered_roots or project_id in registered_ids:
            raise ContinuityError("descriptor-only project collides with a registered identity")
        projects.append(
            {
                **{
                    key: value
                    for key, value in project.items()
                    if key != "identity_source"
                },
                "root": canonical_root.as_posix(),
                "worktree_root": context["workspace"]["worktree_root"],
            }
        )
        registered_roots.add(canonical_root)
        registered_ids.add(project_id)
    obsidian_process = _obsidian_process(runner)
    obsidian_cycle_status = _obsidian_cycle_status(obsidian_state)
    obsidian = _obsidian_index(
        obsidian_registry,
        obsidian_state,
        process=obsidian_process,
        registry_cycle_status=obsidian_cycle_status,
    )
    receipts = _receipt_index(signing_policies)
    dispositions = _load_residue_dispositions(residue_dispositions, projects, runner)
    captured = []
    beads_by_rig: dict[str, list[dict[str, Any]]] = {}
    for registered in sorted(projects, key=lambda item: str(item.get("id"))):
        root = Path(str(registered.get("root"))).resolve()
        context = build_context(root, registry_path)
        project = context["project"]
        project_id = str(project["id"])
        rig = str(project["rig"])
        if rig not in beads_by_rig:
            raw_beads = _json_list(
                runner.run(
                    [
                        GC,
                        "--city",
                        CITY,
                        "--rig",
                        rig,
                        "bd",
                        "list",
                        "--all",
                        "--limit",
                        "0",
                        "--json",
                    ]
                ).stdout,
                f"{project_id} Bead list",
            )
            beads_by_rig[rig] = sorted(
                (_project_bead(bead) for bead in raw_beads),
                key=lambda bead: bead["id"],
            )
        beads = beads_by_rig[rig]
        bead_ids = {
            str(bead["id"])
            for bead in beads
            if isinstance(bead.get("id"), str) and BEAD_ID_PATTERN.fullmatch(str(bead["id"]))
        }
        worktrees = _capture_worktree_cleanliness(
            _parse_worktrees(
                runner.run(
                    ["git", "-C", str(root), "worktree", "list", "--porcelain"]
                ).stdout,
                bead_ids,
            ),
            runner,
            required_paths={
                str(disposition["identity"])
                for disposition in dispositions.get(project_id, [])
                if disposition.get("surface") == "worktree"
            },
        )
        branch_lines = runner.run(
            [
                "git",
                "-C",
                str(root),
                "for-each-ref",
                "--format=%(refname)%00%(objectname)",
                "refs/heads/codex",
            ]
        ).stdout.splitlines()
        branches = []
        for line in sorted(line for line in branch_lines if line):
            branch, separator, head = line.partition("\0")
            if not separator or not GIT_COMMIT_PATTERN.fullmatch(head):
                raise ContinuityError("managed branch ref output is invalid")
            bead_id = _bead_for_branch(branch, bead_ids)
            if bead_id is not None:
                branches.append(
                    {
                        "bead_id": bead_id,
                        "branch": branch.removeprefix(BRANCH_PREFIX),
                        "head": head,
                    }
                )
        prs = _json_list(
            runner.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    str(project["repository"]),
                    "--state",
                    "open",
                    "--limit",
                    "1000",
                    "--json",
                    "number,headRefName,isDraft,mergeStateStatus,title,url",
                ]
            ).stdout,
            f"{project_id} open PR list",
        )
        open_prs = []
        for pr in prs:
            head = pr.get("headRefName")
            bead_id = _bead_for_branch(str(head or ""), bead_ids)
            if bead_id is not None:
                open_prs.append(
                    {
                        "bead_id": bead_id,
                        "number": pr.get("number"),
                        "head": head,
                        "draft": pr.get("isDraft"),
                        "merge_state": pr.get("mergeStateStatus"),
                        "url": pr.get("url"),
                    }
                )
        common = Path(
            runner.run(
                ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"]
            ).stdout.strip()
        ).resolve()
        captured.append(
            {
                "id": project_id,
                "root": context["workspace"]["canonical_root"],
                "repository": project["repository"],
                "rig": rig,
                "workflow_profile": project["workflow_profile"],
                "aegis": {"active_trackers": _active_trackers(root)},
                "git": {
                    "branches": branches,
                    "worktrees": worktrees,
                    "open_prs": sorted(open_prs, key=lambda item: int(item["number"])),
                },
                "runtime": {
                    "transactions": _transactions(root),
                    "receipts": receipts.get(common.as_posix(), []),
                },
                "obsidian": obsidian.get(
                    root.as_posix(),
                    {
                        "registered": False,
                        "vault_status": None,
                        "live_index_status": None,
                        "filesystem": {"status": None, "completed_at": None},
                        "live_index": {
                            "status": None,
                            "authority": None,
                            "observed_at": None,
                        },
                        "cycle": {
                            "status": obsidian_cycle_status,
                            "attempted_at": None,
                            "pending_candidate": False,
                        },
                        "process": dict(obsidian_process),
                    },
                ),
                "followups": _followups(root),
                "residue_dispositions": dispositions.get(project_id, []),
            }
        )
    return {
        "schema": SNAPSHOT_SCHEMA,
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "ledgers": [
            {"rig": rig, "beads": beads_by_rig[rig]}
            for rig in sorted(beads_by_rig)
        ],
        "projects": captured,
    }
