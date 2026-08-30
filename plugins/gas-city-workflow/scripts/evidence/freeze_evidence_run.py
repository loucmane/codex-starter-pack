#!/usr/bin/env python3
"""Freeze one immutable, report-only evidence run from a reviewed request."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_SCRIPTS = SCRIPT_DIR.parent
for candidate in (SCRIPT_DIR, PARENT_SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from project_context import DEFAULT_REGISTRY, build_context  # noqa: E402
from validate_evidence_run import (  # noqa: E402
    EvidenceError,
    RUN_SCHEMA,
    absolute_path,
    asset_inventory,
    atomic_write_json,
    canonical_sha256,
    git_value,
    load_json_object,
    path_binding,
    sha256_file,
    validate_envelope,
    validate_manifest,
    validate_profile,
    validate_request,
)
from workflow_common import CommandRunner, load_bead  # noqa: E402


def _tracked(subject: Path, path: Path, label: str) -> None:
    try:
        relative = path.relative_to(subject)
    except ValueError as exc:
        raise EvidenceError(f"{label} must live inside the subject worktree") from exc
    result = __import__("subprocess").run(
        ["git", "-C", str(subject), "ls-files", "--error-unmatch", "--", relative.as_posix()],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceError(f"{label} must be tracked at the frozen commit: {relative}")


def freeze(
    request_path: Path,
    profile_path: Path,
    manifest_path: Path,
    *,
    registry: Path = DEFAULT_REGISTRY,
) -> dict[str, object]:
    request_path = request_path.resolve()
    profile_path = profile_path.resolve()
    manifest_path = manifest_path.resolve()
    request = load_json_object(request_path, "freeze request")
    profile = load_json_object(profile_path, "evidence profile")
    validate_request(request)
    validate_profile(profile)
    envelope_path = absolute_path(request["authorization_envelope"], "authorization envelope")
    envelope = load_json_object(envelope_path, "authorization envelope")
    validate_envelope(envelope, request)

    subject = absolute_path(request["subject_root"], "subject root")
    run_root = absolute_path(request["run_root"], "run root")
    if subject == run_root or subject in run_root.parents or run_root in subject.parents:
        raise EvidenceError("run root must be outside the subject worktree hierarchy")
    if manifest_path.parent != run_root:
        raise EvidenceError("manifest must be written directly inside the declared run root")
    if run_root.name != request["run_id"]:
        raise EvidenceError("run root basename must equal the immutable run id")
    if manifest_path.exists() or manifest_path.is_symlink():
        raise EvidenceError("run manifest already exists; append-forward with a new run id")
    if manifest_path.name != "manifest.json":
        raise EvidenceError("frozen manifest filename must be manifest.json")
    existing = {item.resolve(strict=False) for item in run_root.iterdir()}
    allowed_pre_freeze = {request_path, envelope_path}
    if existing != allowed_pre_freeze:
        raise EvidenceError(
            "fresh run root must contain only the freeze request and authorization envelope"
        )
    if request["repair"]:
        prior = absolute_path(request["supersedes_manifest"], "supersedes manifest")
        if not prior.is_file() or prior.is_symlink():
            raise EvidenceError("repair supersedes manifest is missing")
        prior_payload = load_json_object(prior, "superseded manifest")
        if prior_payload.get("run_id") != request["supersedes"]:
            raise EvidenceError("repair supersedes manifest identity mismatch")

    context = build_context(subject, registry)
    project = {"id": context["project"]["id"], "rig": context["workflow"]["rig"]}
    if profile["project"] != project:
        raise EvidenceError("profile project/rig does not match the subject context")
    if (
        envelope["scope"]["project_id"] != project["id"]
        or envelope["scope"]["rig"] != project["rig"]
    ):
        raise EvidenceError("authorization scope project/rig mismatch")
    bead = load_bead(CommandRunner(), context, request["parent_bead"])
    status = str(bead.get("status") or "")
    if status not in {"open", "in_progress"}:
        raise EvidenceError(f"parent bead is not live: status={status or 'unknown'}")

    branch = git_value(subject, "branch", "--show-current")
    commit = git_value(subject, "rev-parse", "HEAD")
    tree = git_value(subject, "rev-parse", "HEAD^{tree}")
    if not branch.startswith(f"codex/{request['parent_bead']}-"):
        raise EvidenceError("subject branch is not bound to the parent bead")
    if git_value(subject, "status", "--porcelain=v1", "--untracked-files=all"):
        raise EvidenceError("subject worktree must be clean before freeze")
    _tracked(subject, profile_path, "profile")
    assets = asset_inventory(profile, subject)
    for asset in assets:
        _tracked(subject, Path(asset["path"]), f"lane asset {asset['kind']}")

    external_inputs = []
    for item in request["external_inputs"]:
        external_inputs.append(
            {
                **path_binding(absolute_path(item["path"], "external input")),
                "reason": item["reason"],
            }
        )
    external_inputs.sort(key=lambda item: item["path"])
    fable_inputs = sorted(
        (path_binding(absolute_path(value, "Fable input")) for value in request["fable_inputs"]),
        key=lambda item: item["path"],
    )
    authoritative_outputs = sorted(
        (
            path_binding(absolute_path(value, "authoritative output"))
            for value in request["authoritative_outputs"]
        ),
        key=lambda item: item["path"],
    )
    profile_lanes = {lane["id"]: lane for lane in profile["lanes"]}
    if set(profile_lanes) != set(request["lane_io"]):
        raise EvidenceError("request lane ids do not match the profile")
    lanes = []
    for lane_id in sorted(profile_lanes):
        lane = profile_lanes[lane_id]
        io = request["lane_io"][lane_id]
        bundle_dir = absolute_path(io["bundle_dir"], f"lane {lane_id} bundle_dir")
        report_dir = absolute_path(io["report_dir"], f"lane {lane_id} report_dir")
        for output in (bundle_dir, report_dir):
            if run_root != output and run_root not in output.parents:
                raise EvidenceError(f"lane {lane_id} path escapes run root")
            if output.exists() or output.is_symlink():
                raise EvidenceError(f"lane {lane_id} path must not exist at freeze: {output}")
        lanes.append(
            {
                "id": lane_id,
                "bundle_dir": bundle_dir.as_posix(),
                "report_dir": report_dir.as_posix(),
                "declared_bundle_files": lane["declared_bundle_files"],
                "allowed_outputs": lane["allowed_outputs"],
                "forbidden_patterns": lane["forbidden_patterns"],
            }
        )

    frozen_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest: dict[str, object] = {
        "schema": RUN_SCHEMA,
        "run_id": request["run_id"],
        "phase": "frozen",
        "mode": "shadow",
        "repair": request["repair"],
        "supersedes": request["supersedes"],
        "created_at": request["created_at"],
        "frozen_at": frozen_at,
        "parent_bead": {"id": request["parent_bead"], "status": status},
        "project": project,
        "subject": {
            "repository": context["project"]["repository"],
            "root": subject.as_posix(),
            "branch": branch,
            "commit": commit,
            "tree": tree,
            "clean": True,
        },
        "profile": {
            "id": profile["id"],
            "path": profile_path.as_posix(),
            "sha256": sha256_file(profile_path),
        },
        "freeze_request": {"path": request_path.as_posix(), "sha256": sha256_file(request_path)},
        "authorization": {
            "path": envelope_path.as_posix(),
            "sha256": sha256_file(envelope_path),
            "request_sha256": canonical_sha256(request),
            "scope_sha256": canonical_sha256(envelope["scope"]),
            "expires_at": envelope["expires_at"],
        },
        "run_root": run_root.as_posix(),
        "candidates": request["candidates"],
        "assets": assets,
        "external_inputs": external_inputs,
        "external_inventory_sha256": canonical_sha256(external_inputs),
        "fable_inputs": fable_inputs,
        "lanes": lanes,
        "authoritative_outputs": authoritative_outputs,
    }
    if request["repair"]:
        prior = absolute_path(request["supersedes_manifest"], "supersedes manifest")
        manifest["supersedes_manifest"] = {
            "path": prior.as_posix(),
            "sha256": sha256_file(prior),
        }
    atomic_write_json(manifest_path, manifest)
    try:
        validate_manifest(manifest_path, registry=registry)
    except Exception:
        manifest_path.unlink(missing_ok=True)
        raise
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)
    try:
        manifest = freeze(
            args.request, args.profile, args.manifest, registry=args.registry.resolve()
        )
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"freeze-evidence-run: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "run_id": manifest["run_id"],
                "manifest": args.manifest.resolve().as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
