from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_agents_guide_makes_rig_scoped_beads_authoritative() -> None:
    text = read("AGENTS.md")

    assert text.startswith("# Gas City Beads — Agent Integration Guide")
    assert "Gas City beads are the authoritative work ledger for new work" in text
    assert "--city /home/loucmane/gascity/city --rig gascity bd ready" in text
    assert "Do not create a parallel Taskmaster task for the same work" in text
    assert "Routing and Lifecycle Are Separate Gates" in text
    assert "Taskmaster Transition Policy" in text

    for forbidden in (
        "task-master add-task",
        "task-master set-status",
        "task-master parse-prd",
        "task-master generate-one",
    ):
        assert forbidden not in text


def test_codex_runtime_selects_work_from_beads_not_taskmaster() -> None:
    text = read("CODEX.md")

    assert "## 🤝 GAS CITY BEADS INTEGRATION" in text
    assert "gc bd ready" in text
    assert "do not create a duplicate Taskmaster task" in text
    assert "## 🤝 TASK MASTER INTEGRATION" not in text
    assert "task-master next" not in text


def test_claude_adapter_names_its_remaining_legacy_boundary() -> None:
    text = read("CLAUDE.md")
    normalized = " ".join(text.split())

    assert "## Beads Migration Status" in text
    assert "Gas City beads are authoritative for all new work" in text
    assert "supports bead-native work" in normalized
    assert "retains Taskmaster as a compatibility path" in normalized
    assert "Do not create or mutate a Taskmaster task to duplicate a bead" in normalized


def test_readme_describes_current_and_legacy_authorities() -> None:
    text = read("README.md")

    assert "Gas City bead-backed work authority" in text
    assert "Taskmaster remains a read-only compatibility surface" in text
