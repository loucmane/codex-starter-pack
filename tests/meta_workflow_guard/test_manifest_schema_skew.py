"""TM #215: schema-skew self-diagnosis for the manifest_schema gate.

HP-Coach 2026-06-12: a stale MCP bundle rejected the manifest `runtime` field with a
bare jsonschema error ("Additional properties are not allowed"), reading like target
corruption when the validator itself was the stale party. When the target's installed
schema mirror is newer than the validator's packaged copy AND accepts the manifest,
the failure must name the skew and the source root used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _aegis_installer as installer  # noqa: E402

CURRENT_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "aegis" / "foundation-manifest.schema.json").read_text(encoding="utf-8")
)


def make_stale_source(tmp_path: Path) -> Path:
    """A source root whose schema predates the `runtime` field (additionalProperties
    stays false, so a runtime-bearing manifest is rejected — the incident shape)."""

    stale = json.loads(json.dumps(CURRENT_SCHEMA))
    stale["properties"].pop("runtime", None)
    stale.get("$defs", {}).pop("runtime", None)
    root = tmp_path / "stale-source"
    (root / "schemas" / "aegis").mkdir(parents=True)
    (root / "schemas" / "aegis" / "foundation-manifest.schema.json").write_text(
        json.dumps(stale), encoding="utf-8"
    )
    return root


def make_target(tmp_path: Path, *, mirror: dict | None) -> Path:
    target = tmp_path / "target"
    (target / "schemas" / "aegis").mkdir(parents=True)
    if mirror is not None:
        (target / "schemas" / "aegis" / "foundation-manifest.schema.json").write_text(
            json.dumps(mirror), encoding="utf-8"
        )
    return target


def runtime_manifest() -> dict:
    manifest = json.loads(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "runtime": {
                    "mode": "source-root",
                    "source_root": "/home/u/codex",
                    "source_commit": None,
                    "source_dirty": False,
                    "source_dirty_paths": [],
                    "pointer": ".aegis/runtime.env",
                    "updated_at": "2026-06-12T00:00:00Z",
                    "update_command": "aegis runtime update",
                    "reinstall_required_for": [],
                },
            }
        )
    )
    return manifest


def validation_error(source: Path, manifest: dict) -> ValidationError:
    try:
        installer._validate_with_schema(source, "foundation-manifest.schema.json", manifest)
    except ValidationError as exc:
        return exc
    raise AssertionError("stale schema should have rejected the runtime manifest")


def test_stale_validator_with_newer_mirror_names_the_skew(tmp_path: Path) -> None:
    source = make_stale_source(tmp_path)
    # The mirror only needs to be newer than the validator's copy and to accept the
    # manifest — a permissive runtime-aware schema stands in for the real one.
    mirror = {"type": "object", "properties": {"runtime": {"type": "object"}}}
    target = make_target(tmp_path, mirror=mirror)
    manifest = runtime_manifest()
    exc = validation_error(source, manifest)
    message = installer._manifest_schema_failure_message(source, target, manifest, exc)
    assert "validator runtime is STALE" in message
    assert source.as_posix() in message
    assert "repoint the MCP server" in message


def test_genuine_manifest_corruption_stays_a_plain_failure(tmp_path: Path) -> None:
    """When the mirror ALSO rejects the manifest, the manifest is the problem — no
    skew claim, but the source root is still named for diagnosability."""

    source = make_stale_source(tmp_path)
    target = make_target(tmp_path, mirror=json.loads(json.dumps(CURRENT_SCHEMA)))
    manifest = {"schema_version": "1.0.0", "runtime": {"mode": "wrong-shape"}}
    exc = validation_error(source, manifest)
    message = installer._manifest_schema_failure_message(source, target, manifest, exc)
    assert "STALE" not in message
    assert "[validated with schemas from" in message


def test_missing_mirror_stays_a_plain_failure(tmp_path: Path) -> None:
    source = make_stale_source(tmp_path)
    target = make_target(tmp_path, mirror=None)
    manifest = runtime_manifest()
    exc = validation_error(source, manifest)
    message = installer._manifest_schema_failure_message(source, target, manifest, exc)
    assert "STALE" not in message
    assert "[validated with schemas from" in message


def test_identical_schemas_never_claim_skew(tmp_path: Path) -> None:
    """Mirror == validator copy means no skew exists even if the mirror would accept
    a permissive read — the failure is real."""

    source = make_stale_source(tmp_path)
    stale_copy = json.loads(
        (source / "schemas" / "aegis" / "foundation-manifest.schema.json").read_text(encoding="utf-8")
    )
    target = make_target(tmp_path, mirror=stale_copy)
    manifest = runtime_manifest()
    exc = validation_error(source, manifest)
    message = installer._manifest_schema_failure_message(source, target, manifest, exc)
    assert "STALE" not in message


def test_current_schema_accepts_runtime_block_round_trip() -> None:
    """The incident's round-trip claim: the runtime block `aegis runtime update`
    writes must validate against the CURRENT schema's runtime definition."""

    from jsonschema import Draft202012Validator

    assert "runtime" in CURRENT_SCHEMA["properties"], "current schema must support runtime"
    runtime_def = {**CURRENT_SCHEMA["$defs"]["runtime"], "$defs": CURRENT_SCHEMA["$defs"]}
    Draft202012Validator(runtime_def).validate(runtime_manifest()["runtime"])
