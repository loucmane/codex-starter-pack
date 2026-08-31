"""Cross-surface contract tests for native hierarchical Bead identities."""

from __future__ import annotations

import re
from pathlib import Path

from aegis_foundation.gate import state as gate_state
from scripts import _source_workflow_state as source_state


REPO_ROOT = Path(__file__).resolve().parents[2]
HIERARCHICAL_BRANCH = "codex/ga-ur1c.1-continuity-status-auditor"
MALFORMED_BRANCHES = (
    "codex/ga-ur1c.0-continuity-status-auditor",
    "codex/ga-ur1c.01-continuity-status-auditor",
    "codex/ga-ur1c..1-continuity-status-auditor",
)


def test_source_and_installed_gate_share_hierarchical_branch_semantics() -> None:
    assert source_state.bead_id_from_branch(HIERARCHICAL_BRANCH) == "ga-ur1c.1"
    assert gate_state.bead_id_from_branch(HIERARCHICAL_BRANCH) == "ga-ur1c.1"

    for branch in MALFORMED_BRANCHES:
        assert source_state.bead_id_from_branch(branch) is None
        assert gate_state.bead_id_from_branch(branch) is None


def test_every_managed_identity_surface_contains_the_hierarchy_contract() -> None:
    policy = (REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8")
    assert re.search(r"\\\\\.\[1-9\]", policy)

    managed_sources = (
        REPO_ROOT / "scripts" / "_source_workflow_state.py",
        REPO_ROOT / "aegis_foundation" / "gate" / "state.py",
        REPO_ROOT / ".claude" / "scripts" / "witness_lib.py",
        REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "witness_lib.py",
        REPO_ROOT / "scripts" / "codex-task",
        REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "codex-task",
    )
    for path in managed_sources:
        text = path.read_text(encoding="utf-8")
        assert r"\.[1-9][0-9]*" in text, path.relative_to(REPO_ROOT).as_posix()

    assert (
        REPO_ROOT / ".claude" / "scripts" / "witness_lib.py"
    ).read_bytes() == (
        REPO_ROOT
        / "aegis_foundation"
        / "assets"
        / ".claude"
        / "scripts"
        / "witness_lib.py"
    ).read_bytes()
    assert (REPO_ROOT / "scripts" / "codex-task").read_bytes() == (
        REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "codex-task"
    ).read_bytes()
