#!/usr/bin/env python3
"""Audit one lane's closed blind bundle and exact report-only output surface."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from validate_evidence_run import EvidenceError, validate_manifest


def _lane(manifest: dict[str, object], lane_id: str) -> dict[str, object]:
    matches = [lane for lane in manifest["lanes"] if lane["id"] == lane_id]  # type: ignore[index]
    if len(matches) != 1:
        raise EvidenceError(f"manifest does not contain exactly one lane {lane_id}")
    return matches[0]


def _files(root: Path) -> list[str]:
    if not root.is_dir() or root.is_symlink():
        raise EvidenceError(f"lane directory must be a non-symlink directory: {root}")
    result: list[str] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs.sort()
        files.sort()
        for name in dirs:
            entry = current_path / name
            if name == ".git" or stat.S_ISLNK(entry.lstat().st_mode):
                raise EvidenceError(f"bundle contains Git metadata or a symlink: {entry}")
            if not stat.S_ISDIR(entry.lstat().st_mode):
                raise EvidenceError(f"bundle contains a special directory entry: {entry}")
        for name in files:
            entry = current_path / name
            mode = entry.lstat().st_mode
            if name == ".git" or ".git" in entry.relative_to(root).parts:
                raise EvidenceError(f"bundle contains Git metadata: {entry}")
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise EvidenceError(f"bundle contains a link or special file: {entry}")
            result.append(entry.relative_to(root).as_posix())
    return result


def audit(manifest_path: Path, lane_id: str, stage: str) -> dict[str, object]:
    manifest = validate_manifest(manifest_path.resolve())
    lane = _lane(manifest, lane_id)
    bundle = Path(str(lane["bundle_dir"])).resolve()
    reports = Path(str(lane["report_dir"])).resolve()
    observed = _files(bundle)
    expected = sorted(str(item) for item in lane["declared_bundle_files"])
    if observed != expected:
        raise EvidenceError(f"lane {lane_id} bundle inventory mismatch: expected={expected} observed={observed}")
    forbidden = [str(item).casefold().encode("utf-8") for item in lane["forbidden_patterns"]]
    for relative in observed:
        path = bundle / relative
        data = path.read_bytes().lower()
        hit = next((pattern.decode("utf-8") for pattern in forbidden if pattern in data), None)
        if hit is not None:
            raise EvidenceError(f"lane {lane_id} bundle contains forbidden pattern {hit!r}: {relative}")
    if stage == "pre-dispatch":
        if reports.exists() or reports.is_symlink():
            raise EvidenceError(f"lane {lane_id} report directory must not exist before dispatch")
        outputs: list[str] = []
    else:
        outputs = _files(reports)
        allowed = sorted(str(item) for item in lane["allowed_outputs"])
        if outputs != allowed:
            raise EvidenceError(
                f"lane {lane_id} output inventory mismatch: expected={allowed} observed={outputs}"
            )
    return {"ok": True, "run_id": manifest["run_id"], "lane_id": lane_id, "stage": stage, "bundle_files": observed, "outputs": outputs}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--stage", choices=("pre-dispatch", "post-collection"), required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.manifest, args.lane, args.stage)
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"audit-blind-bundle: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
