"""Observation accepts only append-forward, well-formed gate audit output."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import _aegis_installer as installer
from tests.meta_workflow_guard.test_aegis_installer import simulate_claude_reload

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ".aegis/reports/gate-decisions.jsonl"


def record(reason: str = "observation_mode_disallowed_mutation") -> bytes:
    return (
        json.dumps(
            {
                "ts": "2026-09-03T15:39:00Z",
                "hook": "pretooluse",
                "tool_name": "Bash",
                "payload_digest": "a" * 64,
                "verdict": "block",
                "reason": reason,
                "readiness_state": None,
                "mode": "strict",
                "source_commit": "b" * 40,
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()


def start(tmp_path: Path, before: bytes | None = None, *, ignored: bool = False) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    installer.initialize_project(root, source_root=ROOT)
    simulate_claude_reload(root)
    if ignored:
        (root / ".gitignore").write_text(AUDIT + "\n")
    if before is not None:
        (root / AUDIT).write_bytes(before)
    installer.start_observation(root, title="Gate audit integration", source_root=ROOT)
    return root


@pytest.mark.parametrize("before", [None, record("historical")])
@pytest.mark.parametrize("ignored", [False, True])
def test_observation_preserves_valid_gate_audit_appends(tmp_path, before, ignored):
    root = start(tmp_path, before, ignored=ignored)
    expected = (before or b"") + record()
    (root / AUDIT).write_bytes(expected)
    result = installer.stop_observation(root, source_root=ROOT)
    assert result["status"] == "completed", result["unexpected_changes"]
    assert (root / AUDIT).read_bytes() == expected
    assert result["gate_audit"]["status"] == "verified"


@pytest.mark.parametrize(
    "mutation",
    [
        "truncate",
        "rewrite",
        "delete",
        "symlink",
        "directory",
        "malformed",
        "partial",
        "duplicate-keys",
        "extra-field",
        "bad-digest",
    ],
)
@pytest.mark.parametrize("ignored", [False, True])
def test_observation_refuses_gate_audit_tampering(tmp_path, mutation, ignored):
    original = record("historical")
    root = start(tmp_path, original, ignored=ignored)
    path = root / AUDIT
    if mutation == "truncate":
        path.write_bytes(b"")
    elif mutation == "rewrite":
        path.write_bytes(original.replace(b"historical", b"alteration") + record())
    elif mutation == "delete":
        path.unlink()
    elif mutation == "symlink":
        path.unlink()
        external = tmp_path / "other-log"
        external.write_bytes(original + record())
        path.symlink_to(external)
    elif mutation == "directory":
        path.unlink()
        path.mkdir()
    elif mutation == "malformed":
        path.write_bytes(original + b"not a decision\n")
    elif mutation == "partial":
        path.write_bytes(original + record().rstrip(b"\n"))
    elif mutation == "duplicate-keys":
        path.write_bytes(original + record().replace(b"{", b'{"mode":"strict",', 1))
    elif mutation == "extra-field":
        path.write_bytes(original + record().replace(b"{", b'{"command":"untrusted",', 1))
    else:
        path.write_bytes(original + record().replace(b"a" * 64, b"wrong"))
    result = installer.stop_observation(root, source_root=ROOT)
    assert result["status"] == "blocked"
    assert any("gate audit" in item for item in result["unexpected_changes"])


def test_gate_audit_does_not_exempt_neighboring_files(tmp_path):
    root = start(tmp_path)
    (root / AUDIT).write_bytes(record())
    (root / ".aegis/reports/unrelated-source.txt").write_text("not audit output\n")
    result = installer.stop_observation(root, source_root=ROOT)
    assert result["status"] == "blocked"
    assert any("unrelated-source.txt" in item for item in result["unexpected_changes"])


def test_legacy_observation_without_audit_baseline_gets_no_new_exemption(tmp_path):
    root = start(tmp_path)
    baseline_path = root / installer.AEGIS_OBSERVATION_BASELINE_REL
    baseline = json.loads(baseline_path.read_text())
    baseline.pop("gate_audit", None)
    baseline_path.write_text(json.dumps(baseline))
    (root / AUDIT).write_bytes(record())
    result = installer.stop_observation(root, source_root=ROOT)
    assert result["status"] == "blocked"
    assert any(AUDIT in item for item in result["unexpected_changes"])
