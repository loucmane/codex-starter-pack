#!/usr/bin/env python3
"""Pure validation and classification for Gas City continuity snapshots."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

SNAPSHOT_SCHEMA = "gas-city-workflow.continuity-snapshot.v1"
REPORT_SCHEMA = "gas-city-workflow.continuity-report.v1"
PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
BEAD_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*-[a-z0-9][a-z0-9-]*(?:\.[1-9][0-9]*)*$"
)
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
NONBLOCKING_DEPENDENCIES = frozenset(
    {"parent-child", "relates-to", "tracks", "discovered-from"}
)
GENERATED_TYPES = frozenset({"convoy", "gate", "molecule"})
WORK_CATEGORIES = (
    "current",
    "next",
    "blocked",
    "deferred",
    "legacy",
    "generated",
    "orphaned",
)


class ContinuityError(RuntimeError):
    """Raised when a continuity snapshot cannot be interpreted without guessing."""


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContinuityError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContinuityError(f"{label} must be a list")
    return value


def _string(value: object, label: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ContinuityError(f"{label} must be a non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        raise ContinuityError(f"{label} is invalid")
    return value


def _surface_bead_id(item: Mapping[str, Any]) -> str | None:
    value = item.get("bead_id")
    if value is None:
        return None
    if not isinstance(value, str) or not BEAD_ID_PATTERN.fullmatch(value):
        raise ContinuityError("surface bead_id is invalid")
    return value


def _metadata(bead: Mapping[str, Any]) -> Mapping[str, Any]:
    value = bead.get("metadata", {})
    return _mapping(value, f"bead {bead.get('id')} metadata")


def _labels(bead: Mapping[str, Any]) -> set[str]:
    values = _list(bead.get("labels", []), f"bead {bead.get('id')} labels")
    if not all(isinstance(value, str) for value in values):
        raise ContinuityError(f"bead {bead.get('id')} labels must be strings")
    return {value.casefold() for value in values}


def _is_generated(bead: Mapping[str, Any]) -> bool:
    issue_type = str(bead.get("issue_type") or "")
    metadata = _metadata(bead)
    labels = _labels(bead)
    return (
        issue_type in GENERATED_TYPES
        or "generated" in labels
        or any(
            key.startswith(("gc.formula_", "gc.graphv2_", "gc.drain_"))
            for key in metadata
        )
    )


def _is_legacy(bead: Mapping[str, Any]) -> bool:
    metadata = _metadata(bead)
    labels = _labels(bead)
    return bool(
        labels.intersection({"legacy", "taskmaster", "authority:taskmaster"})
        or metadata.get("gc.legacy") in {True, "true", "1"}
        or metadata.get("workflow.authority") == "taskmaster"
    )


def _blocking_dependencies(
    bead: Mapping[str, Any], bead_index: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    unresolved: set[str] = set()
    dependencies = _list(
        bead.get("dependencies", []), f"bead {bead.get('id')} dependencies"
    )
    for raw in dependencies:
        dependency = _mapping(raw, f"bead {bead.get('id')} dependency")
        relation = dependency.get("type", "blocks")
        if not isinstance(relation, str):
            raise ContinuityError(f"bead {bead.get('id')} dependency type is invalid")
        if relation in NONBLOCKING_DEPENDENCIES:
            continue
        dependency_id = dependency.get("depends_on_id") or dependency.get("id")
        if not isinstance(dependency_id, str) or not BEAD_ID_PATTERN.fullmatch(dependency_id):
            raise ContinuityError(f"bead {bead.get('id')} dependency id is invalid")
        target = bead_index.get(dependency_id)
        if target is None or target.get("status") != "closed":
            unresolved.add(dependency_id)
    return sorted(unresolved)


def _work_item(
    project_id: str,
    bead: Mapping[str, Any],
    *,
    reason: str,
    blockers: Iterable[str] = (),
) -> dict[str, Any]:
    bead_id = _string(bead.get("id"), "bead id", pattern=BEAD_ID_PATTERN)
    title = _string(bead.get("title"), f"bead {bead_id} title")
    return {
        "id": f"{project_id}:{bead_id}",
        "project_id": project_id,
        "bead_id": bead_id,
        "title": title,
        "status": str(bead.get("status") or "unknown"),
        "reason": reason,
        "blockers": sorted(set(blockers)),
    }


def _finding(
    *,
    code: str,
    project_id: str,
    surface: str,
    identity: str,
    bead_id: str | None,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "code": code,
        "project_id": project_id,
        "surface": surface,
        "identity": identity,
        "bead_id": bead_id,
        "severity": severity,
    }


def _identity(item: Mapping[str, Any], surface: str) -> str:
    for key in ("path", "head", "commit", "id", "number"):
        value = item.get(key)
        if value is not None:
            return str(value)
    return surface


def _obsidian_status(obsidian: Mapping[str, Any], surface: str, legacy_field: str) -> object:
    nested = obsidian.get(surface)
    if isinstance(nested, Mapping):
        return nested.get("status")
    return obsidian.get(legacy_field)


def _validate_snapshot(
    snapshot: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[str, list[Any]]]:
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ContinuityError("snapshot schema is invalid")
    registry_sha256 = snapshot.get("registry_sha256")
    if not isinstance(registry_sha256, str) or not DIGEST_PATTERN.fullmatch(registry_sha256):
        raise ContinuityError("registry_sha256 is invalid")
    projects = [
        _mapping(project, "snapshot project")
        for project in _list(snapshot.get("projects"), "snapshot projects")
    ]
    ids = [
        _string(project.get("id"), "project id", pattern=PROJECT_ID_PATTERN)
        for project in projects
    ]
    if len(set(ids)) != len(ids):
        raise ContinuityError("project ids must be unique")
    ledgers: dict[str, list[Any]] = {}
    for raw in _list(snapshot.get("ledgers"), "snapshot ledgers"):
        ledger = _mapping(raw, "snapshot ledger")
        rig = _string(ledger.get("rig"), "ledger rig", pattern=PROJECT_ID_PATTERN)
        if rig in ledgers:
            raise ContinuityError("ledger rigs must be unique")
        ledgers[rig] = _list(ledger.get("beads"), f"ledger {rig} beads")
    project_rigs = {
        _string(project.get("rig"), f"project {project.get('id')} rig", pattern=PROJECT_ID_PATTERN)
        for project in projects
    }
    if project_rigs != set(ledgers):
        raise ContinuityError("project rigs and ledger rigs must match exactly")
    return projects, ledgers


def _classify_project(
    project: Mapping[str, Any],
    *,
    scope_ids: set[str] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    project_id = _string(project.get("id"), "project or ledger id")
    beads = [
        _mapping(bead, f"project {project_id} bead")
        for bead in _list(project.get("beads"), f"project {project_id} beads")
    ]
    bead_ids = [
        _string(bead.get("id"), f"project {project_id} bead id", pattern=BEAD_ID_PATTERN)
        for bead in beads
    ]
    if len(set(bead_ids)) != len(bead_ids):
        raise ContinuityError(f"project {project_id} bead ids must be unique")
    bead_index = dict(zip(bead_ids, beads, strict=True))
    work = {category: [] for category in WORK_CATEGORIES}
    findings: list[dict[str, Any]] = []

    for bead in beads:
        bead_id = str(bead["id"])
        status = bead.get("status")
        if status not in {"open", "in_progress", "blocked", "deferred", "closed"}:
            raise ContinuityError(f"bead {bead_id} status is invalid")
        blockers = _blocking_dependencies(bead, bead_index)
        if scope_ids is not None and bead_id not in scope_ids:
            continue
        if _is_generated(bead):
            work["generated"].append(
                _work_item(project_id, bead, reason="generated-work", blockers=blockers)
            )
        elif _is_legacy(bead):
            work["legacy"].append(
                _work_item(project_id, bead, reason="legacy-authority", blockers=blockers)
            )
        elif status == "deferred":
            work["deferred"].append(
                _work_item(project_id, bead, reason="explicitly-deferred", blockers=blockers)
            )
        elif status == "blocked" or blockers:
            work["blocked"].append(
                _work_item(project_id, bead, reason="unresolved-blocker", blockers=blockers)
            )
        elif (
            status == "in_progress"
            or bead.get("started_at") is not None
            or (
                bead.get("issue_type") == "epic"
                and "initiative:active" in _labels(bead)
            )
        ):
            work["current"].append(
                _work_item(
                    project_id,
                    bead,
                    reason="active-initiative" if status != "in_progress" else "in-progress",
                    blockers=blockers,
                )
            )
        elif status == "open":
            work["next"].append(
                _work_item(project_id, bead, reason="ready-open-work", blockers=blockers)
            )

    surfaces = (
        ("active-tracker", _mapping(project.get("aegis"), "aegis").get("active_trackers", [])),
        ("branch", _mapping(project.get("git"), "git").get("branches", [])),
        ("worktree", _mapping(project.get("git"), "git").get("worktrees", [])),
        ("open-pr", _mapping(project.get("git"), "git").get("open_prs", [])),
        ("transaction", _mapping(project.get("runtime"), "runtime").get("transactions", [])),
        ("runtime-receipt", _mapping(project.get("runtime"), "runtime").get("receipts", [])),
    )
    for surface, raw_items in surfaces:
        for raw in _list(raw_items, f"project {project_id} {surface} entries"):
            item = _mapping(raw, f"project {project_id} {surface} entry")
            surface_project_id = str(item.get("project_id") or project_id)
            bead_id = _surface_bead_id(item)
            if bead_id is None:
                if surface == "active-tracker" and item.get("authority") == "taskmaster":
                    legacy_id = _string(item.get("legacy_id"), "legacy tracker id")
                    identity = _identity(item, surface)
                    work["legacy"].append(
                        {
                            "id": f"{project_id}:legacy:{legacy_id}",
                            "project_id": project_id,
                            "bead_id": None,
                            "title": legacy_id,
                            "status": "legacy",
                            "reason": "legacy-active-tracker",
                            "blockers": [],
                        }
                    )
                    findings.append(
                        _finding(
                            code="legacy-active-tracker",
                            project_id=surface_project_id,
                            surface=surface,
                            identity=identity,
                            bead_id=None,
                            severity="warning",
                        )
                    )
                continue
            bead = bead_index.get(bead_id)
            identity = _identity(item, surface)
            finding: dict[str, Any] | None = None
            if bead is None:
                finding = _finding(
                    code=f"unbound-{surface}",
                    project_id=surface_project_id,
                    surface=surface,
                    identity=identity,
                    bead_id=bead_id,
                )
            elif (
                surface in {"branch", "worktree"}
                and bead.get("status") == "closed"
                and _is_generated(bead)
            ):
                finding = _finding(
                    code=f"terminal-generated-{surface}",
                    project_id=surface_project_id,
                    surface=surface,
                    identity=identity,
                    bead_id=bead_id,
                )
            elif surface == "active-tracker" and bead.get("status") == "closed":
                finding = _finding(
                    code="terminal-active-tracker",
                    project_id=surface_project_id,
                    surface=surface,
                    identity=identity,
                    bead_id=bead_id,
                )
            elif surface == "open-pr" and bead.get("status") == "closed":
                finding = _finding(
                    code="terminal-open-pr",
                    project_id=surface_project_id,
                    surface=surface,
                    identity=identity,
                    bead_id=bead_id,
                )
            if finding is not None:
                findings.append(finding)
                work["orphaned"].append(
                    {
                        "id": f"{project_id}:{surface}:{identity}",
                        "project_id": surface_project_id,
                        "bead_id": bead_id,
                        "title": finding["code"],
                        "status": "orphaned",
                        "reason": finding["code"],
                        "blockers": [],
                    }
                )

    followups = _list(project.get("followups", []), f"project {project_id} followups")
    for raw in followups:
        followup = _mapping(raw, f"project {project_id} followup")
        followup_id = _string(followup.get("id"), "followup id")
        bead_id = followup.get("bead_id")
        disposition = followup.get("disposition")
        bound = isinstance(bead_id, str) and bead_id in bead_index
        disposed = isinstance(disposition, str) and bool(disposition.strip())
        if not bound and not disposed:
            findings.append(
                _finding(
                    code="untracked-promised-followup",
                    project_id=project_id,
                    surface="followup",
                    identity=followup_id,
                    bead_id=bead_id if isinstance(bead_id, str) else None,
                )
            )

    obsidian = _mapping(project.get("obsidian"), f"project {project_id} obsidian")
    cycle_status = _obsidian_status(obsidian, "cycle", "cycle_status")
    if obsidian.get("registered") is not True:
        findings.append(
            _finding(
                code="obsidian-project-unregistered",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    elif (
        _obsidian_status(obsidian, "filesystem", "vault_status") != "current"
        and cycle_status != "running"
    ):
        findings.append(
            _finding(
                code="obsidian-filesystem-stale",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    if (
        obsidian.get("registered") is True
        and _obsidian_status(obsidian, "live_index", "live_index_status") != "confirmed"
        and cycle_status != "running"
    ):
        findings.append(
            _finding(
                code="obsidian-live-index-unconfirmed",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    return work, findings


def _initiative_scope(beads: list[Mapping[str, Any]]) -> set[str] | None:
    roots = {
        str(bead["id"])
        for bead in beads
        if (
            bead.get("issue_type") == "epic"
            and bead.get("status") != "closed"
            and "initiative:active" in _labels(bead)
        )
    }
    if not roots:
        return None
    scope = set(roots)
    changed = True
    while changed:
        changed = False
        for bead in beads:
            bead_id = str(bead["id"])
            if bead_id in scope:
                continue
            parent = bead.get("parent")
            dependencies = _list(
                bead.get("dependencies", []), f"bead {bead_id} dependencies"
            )
            parents = {
                str(dependency.get("depends_on_id") or dependency.get("id"))
                for dependency in dependencies
                if isinstance(dependency, Mapping)
                and dependency.get("type") == "parent-child"
            }
            if (isinstance(parent, str) and parent in scope) or parents.intersection(scope):
                scope.add(bead_id)
                changed = True
    return scope


def _merge_surface(
    members: list[Mapping[str, Any]], section: str, key: str
) -> list[dict[str, Any]]:
    merged: dict[bytes, dict[str, Any]] = {}
    for member in members:
        project_id = str(member["id"])
        section_value = _mapping(member.get(section), f"project {project_id} {section}")
        for raw in _list(section_value.get(key, []), f"project {project_id} {section}.{key}"):
            item = dict(_mapping(raw, f"project {project_id} {section}.{key} entry"))
            item["project_id"] = project_id
            merged[canonical_bytes(item)] = item
    return [merged[key] for key in sorted(merged)]


def _ledger_project(
    members: list[Mapping[str, Any]], beads: list[Any]
) -> tuple[dict[str, Any], set[str] | None]:
    rig = str(members[0].get("rig"))
    ledger_id = str(members[0]["id"]) if len(members) == 1 else f"rig:{rig}"
    project = {
        "id": ledger_id,
        "root": None,
        "repository": None,
        "rig": rig,
        "workflow_profile": "shared-ledger" if len(members) > 1 else members[0].get("workflow_profile"),
        "beads": beads,
        "aegis": {"active_trackers": _merge_surface(members, "aegis", "active_trackers")},
        "git": {
            "branches": _merge_surface(members, "git", "branches"),
            "worktrees": _merge_surface(members, "git", "worktrees"),
            "open_prs": _merge_surface(members, "git", "open_prs"),
        },
        "runtime": {
            "transactions": _merge_surface(members, "runtime", "transactions"),
            "receipts": _merge_surface(members, "runtime", "receipts"),
        },
        "obsidian": {
            "registered": True,
            "vault_status": "current",
            "live_index_status": "confirmed",
        },
        "followups": [
            followup
            for member in members
            for followup in _list(
                member.get("followups", []), f"project {member.get('id')} followups"
            )
        ],
    }
    return project, _initiative_scope([_mapping(bead, "ledger bead") for bead in beads])


def _obsidian_findings(project: Mapping[str, Any]) -> list[dict[str, Any]]:
    project_id = str(project["id"])
    obsidian = _mapping(project.get("obsidian"), f"project {project_id} obsidian")
    cycle_status = _obsidian_status(obsidian, "cycle", "cycle_status")
    findings = []
    if obsidian.get("registered") is not True:
        findings.append(
            _finding(
                code="obsidian-project-unregistered",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    elif obsidian.get("registry_project_id") != project_id:
        findings.append(
            _finding(
                code="obsidian-project-id-mismatch",
                project_id=project_id,
                surface="obsidian",
                identity=str(obsidian.get("registry_project_id") or "missing"),
                bead_id=None,
            )
        )
    elif (
        _obsidian_status(obsidian, "filesystem", "vault_status") != "current"
        and cycle_status != "running"
    ):
        findings.append(
            _finding(
                code="obsidian-filesystem-stale",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    if cycle_status == "running":
        findings.append(
            _finding(
                code="obsidian-reconciliation-in-progress",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
                severity="warning",
            )
        )
    elif cycle_status == "unknown":
        findings.append(
            _finding(
                code="obsidian-cycle-observation-unknown",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
                severity="warning",
            )
        )
    elif cycle_status == "interrupted":
        findings.append(
            _finding(
                code="obsidian-reconciliation-interrupted",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    elif cycle_status not in {None, "idle"}:
        findings.append(
            _finding(
                code="obsidian-cycle-observation-invalid",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    if (
        obsidian.get("registered") is True
        and _obsidian_status(obsidian, "live_index", "live_index_status") != "confirmed"
        and cycle_status != "running"
    ):
        findings.append(
            _finding(
                code="obsidian-live-index-unconfirmed",
                project_id=project_id,
                surface="obsidian",
                identity=project_id,
                bead_id=None,
            )
        )
    live_index = obsidian.get("live_index")
    if isinstance(live_index, Mapping) and live_index.get("status") == "confirmed":
        if live_index.get("authority") != "host-obsidian-ipc":
            findings.append(
                _finding(
                    code="obsidian-live-index-authority-invalid",
                    project_id=project_id,
                    surface="obsidian",
                    identity=project_id,
                    bead_id=None,
                )
            )
        if not isinstance(live_index.get("observed_at"), str):
            findings.append(
                _finding(
                    code="obsidian-live-index-observation-time-missing",
                    project_id=project_id,
                    surface="obsidian",
                    identity=project_id,
                    bead_id=None,
                )
            )
    process = obsidian.get("process")
    if isinstance(process, Mapping):
        process_status = process.get("status")
        if process_status == "unknown":
            findings.append(
                _finding(
                    code="obsidian-process-observation-unknown",
                    project_id=project_id,
                    surface="obsidian-process",
                    identity=project_id,
                    bead_id=None,
                    severity="warning",
                )
            )
        elif process_status in {"absent", "inactive"}:
            findings.append(
                _finding(
                    code="obsidian-process-not-active",
                    project_id=project_id,
                    surface="obsidian-process",
                    identity=project_id,
                    bead_id=None,
                )
            )
        elif process_status != "active":
            findings.append(
                _finding(
                    code="obsidian-process-observation-invalid",
                    project_id=project_id,
                    surface="obsidian-process",
                    identity=project_id,
                    bead_id=None,
                )
            )
    return findings


def build_report(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    projects, beads_by_rig = _validate_snapshot(snapshot)
    work = {category: [] for category in WORK_CATEGORIES}
    findings: list[dict[str, Any]] = []
    project_summaries: list[dict[str, Any]] = []
    by_rig: dict[str, list[Mapping[str, Any]]] = {}
    for project in projects:
        rig = _string(project.get("rig"), f"project {project.get('id')} rig", pattern=PROJECT_ID_PATTERN)
        by_rig.setdefault(rig, []).append(project)
    ledgers = {
        rig: _ledger_project(
            sorted(members, key=lambda value: str(value["id"])),
            beads_by_rig[rig],
        )
        for rig, members in by_rig.items()
    }
    initiative_scoped = any(scope_ids is not None for _, scope_ids in ledgers.values())
    for rig in sorted(ledgers):
        ledger, scope_ids = ledgers[rig]
        if initiative_scoped and scope_ids is None:
            scope_ids = set()
        project_work, project_findings = _classify_project(ledger, scope_ids=scope_ids)
        for category in WORK_CATEGORIES:
            work[category].extend(project_work[category])
        findings.extend(project_findings)
    for project in sorted(projects, key=lambda value: str(value["id"])):
        findings.extend(_obsidian_findings(project))
        project_summaries.append(
            {
                "id": project["id"],
                "repository": project.get("repository"),
                "rig": project.get("rig"),
                "root": project.get("root"),
                "workflow_profile": project.get("workflow_profile"),
            }
        )
    for category in WORK_CATEGORIES:
        work[category].sort(key=lambda item: item["id"])
    findings.sort(key=lambda item: (item["code"], item["project_id"], item["identity"]))
    next_actions = [
        {
            "id": item["id"],
            "project_id": item["project_id"],
            "bead_id": item["bead_id"],
            "title": item["title"],
        }
        for item in work["next"]
    ]
    errors = [finding for finding in findings if finding["severity"] == "error"]
    return {
        "schema": REPORT_SCHEMA,
        "snapshot_sha256": canonical_sha256(snapshot),
        "registry_sha256": snapshot["registry_sha256"],
        "ok": not errors,
        "projects": project_summaries,
        "work": work,
        "findings": findings,
        "next_actions": next_actions,
        "summary": {
            "project_count": len(project_summaries),
            "finding_count": len(findings),
            "error_count": len(errors),
            "counts": {category: len(work[category]) for category in WORK_CATEGORIES},
            "next_action_ids": [item["id"] for item in next_actions],
        },
    }


def render_status(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("ok") else "BLOCKED"
    summary = _mapping(report.get("summary"), "report summary")
    lines = [
        f"continuity: {status}",
        " ".join(
            f"{category}={summary['counts'][category]}" for category in WORK_CATEGORIES
        ),
    ]
    for item in _list(report.get("next_actions"), "report next_actions"):
        action = _mapping(item, "next action")
        lines.append(f"next {action['id']} — {action['title']}")
    for raw in _list(report.get("findings"), "report findings"):
        finding = _mapping(raw, "finding")
        lines.append(
            f"{finding['severity']} {finding['code']} "
            f"project={finding['project_id']} identity={finding['identity']}"
        )
    lines.append(f"report_sha256={canonical_sha256(report)}")
    return "\n".join(lines) + "\n"
