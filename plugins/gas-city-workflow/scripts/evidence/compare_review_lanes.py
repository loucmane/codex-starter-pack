#!/usr/bin/env python3
"""Verify seal/readback/dispatch/release ordering and compare evidence-only reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_evidence_run import (
    EVENT_SCHEMA,
    EvidenceError,
    atomic_write_json,
    canonical_sha256,
    exact_keys,
    load_json_object,
    parse_timestamp,
    sha256_file,
    validate_manifest,
)
from validate_review_report import validate_report


def _event(path: Path, event: str, manifest: dict[str, Any], payload_keys: set[str]) -> dict[str, Any]:
    value = load_json_object(path, f"{event} event")
    exact_keys(value, {"schema", "event", "run_id", "parent_bead", "at", "payload"}, f"{event} event")
    if value.get("schema") != EVENT_SCHEMA or value.get("event") != event:
        raise EvidenceError(f"{event} event schema/type mismatch")
    if value.get("run_id") != manifest["run_id"] or value.get("parent_bead") != manifest["parent_bead"]["id"]:
        raise EvidenceError(f"{event} event identity mismatch")
    if not isinstance(value.get("payload"), dict):
        raise EvidenceError(f"{event} payload must be an object")
    exact_keys(value["payload"], payload_keys, f"{event} payload")
    parse_timestamp(str(value["at"]), f"{event}.at")
    return value


def compare(
    manifest_path: Path,
    fable_report_path: Path,
    seal_path: Path,
    readback_path: Path,
    dispatch_path: Path,
    release_path: Path,
    reports: list[tuple[str, Path]],
    output: Path,
) -> dict[str, Any]:
    manifest = validate_manifest(manifest_path.resolve())
    fable_report_path = fable_report_path.resolve()
    fable_report = load_json_object(fable_report_path, "Fable report")
    seal = _event(seal_path.resolve(), "seal", manifest, {"fable_report", "sha256"})
    if seal["payload"] != {"fable_report": fable_report_path.as_posix(), "sha256": sha256_file(fable_report_path)}:
        raise EvidenceError("seal event does not bind the exact Fable report")
    readback = _event(
        readback_path.resolve(),
        "fable-readback",
        manifest,
        {"seal_event_sha256", "fable_report_sha256", "confirmed_by"},
    )
    if readback["payload"]["seal_event_sha256"] != sha256_file(seal_path.resolve()) or readback["payload"]["fable_report_sha256"] != sha256_file(fable_report_path) or readback["payload"]["confirmed_by"] != "Fable":
        raise EvidenceError("Fable readback does not confirm the sealed digest")
    dispatch = _event(dispatch_path.resolve(), "dispatch", manifest, {"readback_event_sha256"})
    if dispatch["payload"]["readback_event_sha256"] != sha256_file(readback_path.resolve()):
        raise EvidenceError("dispatch event does not bind Fable readback")
    release = _event(
        release_path.resolve(),
        "release",
        manifest,
        {"dispatch_event_sha256", "policy_attestation"},
    )
    if release["payload"]["dispatch_event_sha256"] != sha256_file(dispatch_path.resolve()):
        raise EvidenceError("release event does not bind dispatch")
    expected_attestation = "Fable did not independently access worker reports before release."
    if release["payload"]["policy_attestation"] != expected_attestation:
        raise EvidenceError("release event lacks the exact pre-release nonaccess attestation")
    times = [parse_timestamp(event["at"], event["event"]) for event in (seal, readback, dispatch, release)]
    if times != sorted(times) or len(set(times)) != len(times):
        raise EvidenceError("controller events are not strictly ordered")

    validated: list[dict[str, Any]] = []
    for lane_id, report_path in reports:
        report = validate_report(manifest_path, lane_id, report_path)
        if report_path.stat().st_mtime_ns < dispatch_path.stat().st_mtime_ns:
            raise EvidenceError("worker report predates dispatch evidence")
        if report_path.stat().st_mtime_ns > release_path.stat().st_mtime_ns:
            raise EvidenceError("release evidence predates worker report collection")
        validated.append(report)
    expected_lanes = {lane["id"] for lane in manifest["lanes"]}
    if {report["lane_id"] for report in validated} != expected_lanes:
        raise EvidenceError("comparison must contain exactly one report for every frozen lane")
    if len(validated) != len(expected_lanes):
        raise EvidenceError("comparison contains duplicate lane reports")
    findings = {
        report["lane_id"]: sorted(
            str(item.get("id")) for item in report["findings"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        )
        for report in validated
    }
    comparison: dict[str, Any] = {
        "schema": "gas-city-evidence-comparison.v1",
        "run_id": manifest["run_id"],
        "parent_bead": manifest["parent_bead"]["id"],
        "status": "evidence-only",
        "fable_report": {"path": fable_report_path.as_posix(), "sha256": sha256_file(fable_report_path)},
        "event_chain": {
            "seal": sha256_file(seal_path.resolve()),
            "fable_readback": sha256_file(readback_path.resolve()),
            "dispatch": sha256_file(dispatch_path.resolve()),
            "release": sha256_file(release_path.resolve()),
        },
        "lane_findings": findings,
        "shared_finding_ids": sorted(set.intersection(*(set(value) for value in findings.values()))) if findings else [],
        "domain_verdict": None,
        "note": "This artifact compares reported evidence and does not calculate a project verdict.",
    }
    atomic_write_json(output.resolve(), comparison)
    return comparison


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--fable-report", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--fable-readback", required=True, type=Path)
    parser.add_argument("--dispatch", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--report", action="append", nargs=2, metavar=("LANE", "PATH"), required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = compare(
            args.manifest,
            args.fable_report,
            args.seal,
            args.fable_readback,
            args.dispatch,
            args.release,
            [(lane, Path(path)) for lane, path in args.report],
            args.output,
        )
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"compare-review-lanes: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "run_id": result["run_id"], "output": args.output.resolve().as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
