#!/usr/bin/env python3
"""Validate every byte and identity bound by a frozen evidence-run manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent
PARENT_SCRIPTS = PLUGIN_ROOT / "scripts"
if str(PARENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PARENT_SCRIPTS))

from project_context import DEFAULT_REGISTRY, build_context  # noqa: E402

RUN_SCHEMA = "gas-city-evidence-run.v1"
PROFILE_SCHEMA = "gas-city-evidence-profile.v1"
REQUEST_SCHEMA = "gas-city-evidence-freeze-request.v1"
ENVELOPE_SCHEMA = "gas-city-evidence-authorization-envelope.v1"
REPORT_SCHEMA = "gas-city-evidence-report.v1"
EVENT_SCHEMA = "gas-city-evidence-controller-event.v1"
MANIFEST_SCHEMA_PATH = PLUGIN_ROOT / "config" / "evidence-run.schema.json"
REQUIRED_EXCLUSIONS = frozenset(
    {"push", "merge", "deploy", "publish", "rig-lifecycle", "authoritative-output-write"}
)


class EvidenceError(RuntimeError):
    """Raised when evidence cannot be accepted without guessing."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"expected a regular non-symlink file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"{label} must be a regular non-symlink file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"{label} is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be a JSON object: {path}")
    return value


def atomic_write_json(path: Path, value: Mapping[str, Any], *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    if path.exists() or path.is_symlink():
        raise EvidenceError(f"refusing to overwrite evidence: {path}")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, mode)
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise EvidenceError(f"{label} must be a normalized relative path: {value}")
    return path


def absolute_path(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise EvidenceError(f"{label} must be absolute: {value}")
    return path.resolve(strict=False)


def exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    expected_set = set(expected)
    if set(value) != expected_set:
        raise EvidenceError(
            f"{label} keys mismatch: expected={sorted(expected_set)} observed={sorted(value)}"
        )


def tree_inventory(path: Path) -> list[dict[str, str]]:
    """Return a deterministic byte inventory; reject links and special files."""
    if not path.is_dir() or path.is_symlink():
        raise EvidenceError(f"expected a non-symlink directory: {path}")
    result: list[dict[str, str]] = []
    for current, dirs, files in os.walk(path, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs.sort()
        files.sort()
        for name in dirs:
            entry = current_path / name
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise EvidenceError(f"directory tree contains a link or special entry: {entry}")
            result.append({"path": entry.relative_to(path).as_posix() + "/", "kind": "directory"})
        for name in files:
            entry = current_path / name
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise EvidenceError(f"directory tree contains a link or special entry: {entry}")
            result.append(
                {"path": entry.relative_to(path).as_posix(), "kind": "file", "sha256": sha256_file(entry)}
            )
    return result


def path_binding(path: Path) -> dict[str, str]:
    if path.is_file() and not path.is_symlink():
        return {"path": path.as_posix(), "kind": "file", "sha256": sha256_file(path)}
    if path.is_dir() and not path.is_symlink():
        return {
            "path": path.as_posix(),
            "kind": "directory",
            "sha256": canonical_sha256(tree_inventory(path)),
        }
    raise EvidenceError(f"cannot bind missing, linked, or special path: {path}")


def require_binding(binding: Mapping[str, Any], label: str) -> None:
    exact_keys(binding, {"path", "kind", "sha256"}, label)
    observed = path_binding(absolute_path(str(binding["path"]), f"{label}.path"))
    if observed != dict(binding):
        raise EvidenceError(f"{label} digest or type drift: {binding['path']}")


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{label} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{label} must include a timezone")
    return parsed.astimezone(UTC)


def validate_profile(profile: Mapping[str, Any]) -> None:
    exact_keys(profile, {"schema", "id", "project", "lanes"}, "profile")
    if profile.get("schema") != PROFILE_SCHEMA:
        raise EvidenceError("profile schema mismatch")
    if not isinstance(profile.get("id"), str) or not profile["id"]:
        raise EvidenceError("profile id is missing")
    project = profile.get("project")
    if not isinstance(project, dict):
        raise EvidenceError("profile project must be an object")
    exact_keys(project, {"id", "rig"}, "profile.project")
    if not all(isinstance(project.get(key), str) and project[key] for key in ("id", "rig")):
        raise EvidenceError("profile project id and rig are required")
    lanes = profile.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise EvidenceError("profile must declare at least one lane")
    lane_ids: list[str] = []
    for index, lane in enumerate(lanes):
        if not isinstance(lane, dict):
            raise EvidenceError(f"profile lane {index} must be an object")
        exact_keys(
            lane,
            {
                "id", "bundle_builder", "prompt", "rubric", "report_schema",
                "declared_bundle_files", "allowed_outputs", "forbidden_patterns",
            },
            f"profile.lanes[{index}]",
        )
        lane_id = lane.get("id")
        if not isinstance(lane_id, str) or not lane_id:
            raise EvidenceError(f"profile lane {index} id is missing")
        lane_ids.append(lane_id)
        for key in ("bundle_builder", "prompt", "rubric", "report_schema"):
            if not isinstance(lane.get(key), str):
                raise EvidenceError(f"profile lane {lane_id} {key} is missing")
            safe_relative(lane[key], f"profile lane {lane_id} {key}")
        for key in ("declared_bundle_files", "allowed_outputs", "forbidden_patterns"):
            values = lane.get(key)
            if not isinstance(values, list) or not values or not all(
                isinstance(item, str) and item for item in values
            ):
                raise EvidenceError(f"profile lane {lane_id} {key} must be non-empty strings")
            if len(values) != len(set(values)):
                raise EvidenceError(f"profile lane {lane_id} {key} contains duplicates")
        for item in lane["declared_bundle_files"] + lane["allowed_outputs"]:
            safe_relative(item, f"profile lane {lane_id} file")
    if len(lane_ids) != len(set(lane_ids)):
        raise EvidenceError("profile lane ids must be unique")


def validate_request(request: Mapping[str, Any]) -> None:
    exact_keys(
        request,
        {
            "schema", "run_id", "created_at", "parent_bead", "mode", "repair", "supersedes",
            "subject_root", "candidates", "external_inputs", "fable_inputs",
            "authoritative_outputs", "lane_io", "authorization_envelope", "run_root",
        },
        "freeze request",
    )
    if request.get("schema") != REQUEST_SCHEMA:
        raise EvidenceError("freeze request schema mismatch")
    if request.get("mode") != "shadow":
        raise EvidenceError("mode=authoritative is forbidden; v1 accepts only shadow")
    repair = request.get("repair")
    supersedes = request.get("supersedes")
    if not isinstance(repair, bool) or (repair and not isinstance(supersedes, str)) or (
        not repair and supersedes is not None
    ):
        raise EvidenceError("repair runs require supersedes; non-repairs require null")
    parse_timestamp(str(request.get("created_at") or ""), "freeze request created_at")
    for key in ("run_id", "parent_bead", "subject_root", "authorization_envelope", "run_root"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise EvidenceError(f"freeze request {key} is missing")
    absolute_path(request["subject_root"], "freeze request subject_root")
    absolute_path(request["authorization_envelope"], "freeze request authorization_envelope")
    absolute_path(request["run_root"], "freeze request run_root")
    candidates = request.get("candidates")
    if not isinstance(candidates, list) or not candidates or not all(
        isinstance(value, str) and value for value in candidates
    ) or len(candidates) != len(set(candidates)):
        raise EvidenceError("freeze request candidates must be unique non-empty strings")
    for key in ("fable_inputs", "authoritative_outputs"):
        values = request.get(key)
        if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
            raise EvidenceError(f"freeze request {key} must contain paths")
        for value in values:
            absolute_path(value, f"freeze request {key}")
    external = request.get("external_inputs")
    if not isinstance(external, list):
        raise EvidenceError("freeze request external_inputs must be a list")
    for index, item in enumerate(external):
        if not isinstance(item, dict):
            raise EvidenceError(f"external input {index} must be an object")
        exact_keys(item, {"path", "reason"}, f"external input {index}")
        absolute_path(str(item.get("path") or ""), f"external input {index} path")
        if not isinstance(item.get("reason"), str) or not item["reason"]:
            raise EvidenceError(f"external input {index} reason is missing")
    lane_io = request.get("lane_io")
    if not isinstance(lane_io, dict) or not lane_io:
        raise EvidenceError("freeze request lane_io must be an object")
    for lane_id, value in lane_io.items():
        if not isinstance(lane_id, str) or not isinstance(value, dict):
            raise EvidenceError("freeze request lane_io is invalid")
        exact_keys(value, {"bundle_dir", "report_dir"}, f"lane_io.{lane_id}")
        absolute_path(str(value["bundle_dir"]), f"lane_io.{lane_id}.bundle_dir")
        absolute_path(str(value["report_dir"]), f"lane_io.{lane_id}.report_dir")


def validate_envelope(envelope: Mapping[str, Any], request: Mapping[str, Any]) -> None:
    exact_keys(
        envelope,
        {"schema", "request_sha256", "authorized_at", "expires_at", "scope", "verbatim_authorization"},
        "authorization envelope",
    )
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise EvidenceError("authorization envelope schema mismatch")
    if envelope.get("request_sha256") != canonical_sha256(request):
        raise EvidenceError("authorization envelope does not bind the freeze request")
    authorized = parse_timestamp(str(envelope.get("authorized_at") or ""), "authorized_at")
    expires = parse_timestamp(str(envelope.get("expires_at") or ""), "expires_at")
    if expires <= authorized or expires <= datetime.now(UTC):
        raise EvidenceError("authorization envelope is expired or has an invalid interval")
    scope = envelope.get("scope")
    if not isinstance(scope, dict):
        raise EvidenceError("authorization envelope scope must be an object")
    exact_keys(
        scope,
        {"project_id", "rig", "parent_bead", "run_id", "mode", "max_workers", "allowed_write_roots", "excluded_actions"},
        "authorization scope",
    )
    if scope.get("parent_bead") != request.get("parent_bead") or scope.get("run_id") != request.get("run_id") or scope.get("mode") != "shadow":
        raise EvidenceError("authorization scope identity mismatch")
    if not isinstance(scope.get("max_workers"), int) or not 1 <= scope["max_workers"] <= 128:
        raise EvidenceError("authorization scope max_workers is invalid")
    roots = scope.get("allowed_write_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(v, str) for v in roots):
        raise EvidenceError("authorization scope allowed_write_roots is invalid")
    resolved_roots = {absolute_path(v, "allowed_write_root").as_posix() for v in roots}
    lane_roots = {
        absolute_path(str(value["report_dir"]), "lane report directory").as_posix()
        for value in request["lane_io"].values()
    }
    if resolved_roots != lane_roots:
        raise EvidenceError("authorization write roots must equal the lane report directories")
    exclusions = scope.get("excluded_actions")
    if not isinstance(exclusions, list) or not REQUIRED_EXCLUSIONS.issubset(exclusions):
        raise EvidenceError("authorization scope lacks mandatory exclusions")
    if not isinstance(envelope.get("verbatim_authorization"), str) or not envelope["verbatim_authorization"].strip():
        raise EvidenceError("authorization envelope must preserve verbatim authorization")


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise EvidenceError(f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def asset_inventory(profile: Mapping[str, Any], subject: Path) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    for lane in profile["lanes"]:
        for kind in ("bundle_builder", "prompt", "rubric", "report_schema"):
            relative = safe_relative(lane[kind], f"lane {lane['id']} {kind}")
            path = (subject / relative).resolve()
            if subject not in path.parents:
                raise EvidenceError(f"lane asset escapes the subject: {relative}")
            assets.append(
                {"kind": kind, "lane_id": lane["id"], "path": path.as_posix(), "sha256": sha256_file(path)}
            )
    return sorted(assets, key=lambda item: (item["lane_id"], item["kind"], item["path"]))


def validate_manifest(path: Path, *, registry: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    manifest = load_json_object(path, "evidence manifest")
    schema = load_json_object(MANIFEST_SCHEMA_PATH, "evidence manifest schema")
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.absolute_path) or "<root>"
        raise EvidenceError(f"manifest schema error at {location}: {first.message}")
    if manifest.get("schema") != RUN_SCHEMA or manifest.get("mode") != "shadow":
        raise EvidenceError("only frozen shadow manifests are accepted")

    subject = absolute_path(manifest["subject"]["root"], "manifest subject root")
    profile_path = absolute_path(manifest["profile"]["path"], "manifest profile path")
    request_path = absolute_path(manifest["freeze_request"]["path"], "manifest request path")
    envelope_path = absolute_path(manifest["authorization"]["path"], "manifest envelope path")
    if sha256_file(profile_path) != manifest["profile"]["sha256"]:
        raise EvidenceError("profile digest drift")
    if sha256_file(request_path) != manifest["freeze_request"]["sha256"]:
        raise EvidenceError("freeze request digest drift")
    if sha256_file(envelope_path) != manifest["authorization"]["sha256"]:
        raise EvidenceError("authorization envelope digest drift")
    profile = load_json_object(profile_path, "evidence profile")
    request = load_json_object(request_path, "freeze request")
    envelope = load_json_object(envelope_path, "authorization envelope")
    validate_profile(profile)
    validate_request(request)
    validate_envelope(envelope, request)
    if profile["id"] != manifest["profile"]["id"]:
        raise EvidenceError("manifest profile id mismatch")
    if manifest["authorization"]["request_sha256"] != canonical_sha256(request):
        raise EvidenceError("manifest authorization request digest mismatch")
    if manifest["authorization"]["scope_sha256"] != canonical_sha256(envelope["scope"]):
        raise EvidenceError("manifest authorization scope digest mismatch")
    if manifest["authorization"]["expires_at"] != envelope["expires_at"]:
        raise EvidenceError("manifest authorization expiry mismatch")
    if request["run_id"] != manifest["run_id"] or request["parent_bead"] != manifest["parent_bead"]["id"]:
        raise EvidenceError("manifest and request identities disagree")
    if (
        request["created_at"] != manifest["created_at"]
        or request["repair"] != manifest["repair"]
        or request["supersedes"] != manifest["supersedes"]
        or request["candidates"] != manifest["candidates"]
    ):
        raise EvidenceError("manifest and request frozen fields disagree")
    if request["run_root"] != manifest["run_root"]:
        raise EvidenceError("manifest run root mismatch")
    context = build_context(subject, registry)
    if context["project"]["id"] != manifest["project"]["id"] or context["workflow"]["rig"] != manifest["project"]["rig"]:
        raise EvidenceError("manifest project or rig does not match project context")
    if profile["project"] != manifest["project"] or envelope["scope"]["project_id"] != manifest["project"]["id"] or envelope["scope"]["rig"] != manifest["project"]["rig"]:
        raise EvidenceError("profile or authorization project identity mismatch")
    observed_subject = {
        "repository": context["project"]["repository"],
        "root": subject.as_posix(),
        "branch": git_value(subject, "branch", "--show-current"),
        "commit": git_value(subject, "rev-parse", "HEAD"),
        "tree": git_value(subject, "rev-parse", "HEAD^{tree}"),
        "clean": git_value(subject, "status", "--porcelain=v1", "--untracked-files=all") == "",
    }
    if observed_subject != manifest["subject"]:
        raise EvidenceError("subject Git identity or clean-state drift")
    if asset_inventory(profile, subject) != manifest["assets"]:
        raise EvidenceError("workflow asset drift")
    for binding in manifest["fable_inputs"]:
        require_binding(binding, "Fable input")
    for binding in manifest["authoritative_outputs"]:
        require_binding(binding, "authoritative output")
    if sorted(item["path"] for item in manifest["fable_inputs"]) != sorted(request["fable_inputs"]):
        raise EvidenceError("manifest Fable inputs disagree with the request")
    if sorted(item["path"] for item in manifest["authoritative_outputs"]) != sorted(
        request["authoritative_outputs"]
    ):
        raise EvidenceError("manifest authoritative outputs disagree with the request")
    external: list[dict[str, str]] = []
    for item in request["external_inputs"]:
        bound = path_binding(absolute_path(item["path"], "external input path"))
        external.append({**bound, "reason": item["reason"]})
    external.sort(key=lambda item: item["path"])
    if external != manifest["external_inputs"] or canonical_sha256(external) != manifest["external_inventory_sha256"]:
        raise EvidenceError("external input inventory drift")
    profile_lanes = {lane["id"]: lane for lane in profile["lanes"]}
    manifest_lanes = {lane["id"]: lane for lane in manifest["lanes"]}
    if set(profile_lanes) != set(manifest_lanes) or set(request["lane_io"]) != set(profile_lanes):
        raise EvidenceError("lane identities disagree")
    run_root = absolute_path(manifest["run_root"], "manifest run root")
    for lane_id, lane in manifest_lanes.items():
        profile_lane = profile_lanes[lane_id]
        expected = {
            "id": lane_id,
            "bundle_dir": request["lane_io"][lane_id]["bundle_dir"],
            "report_dir": request["lane_io"][lane_id]["report_dir"],
            "declared_bundle_files": profile_lane["declared_bundle_files"],
            "allowed_outputs": profile_lane["allowed_outputs"],
            "forbidden_patterns": profile_lane["forbidden_patterns"],
        }
        if lane != expected:
            raise EvidenceError(f"lane binding drift: {lane_id}")
        for key in ("bundle_dir", "report_dir"):
            lane_path = absolute_path(lane[key], f"lane {lane_id} {key}")
            if run_root != lane_path and run_root not in lane_path.parents:
                raise EvidenceError(f"lane {lane_id} {key} escapes run root")
        if Path(lane["bundle_dir"]).resolve() == Path(lane["report_dir"]).resolve():
            raise EvidenceError(f"lane {lane_id} input and output directories overlap")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)
    try:
        manifest = validate_manifest(args.manifest.resolve(), registry=args.registry.resolve())
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"validate-evidence-run: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "schema": RUN_SCHEMA, "run_id": manifest["run_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
