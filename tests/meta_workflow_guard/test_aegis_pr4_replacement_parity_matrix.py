"""Guard the PR-4 replacement-parity contract.

PR-4 must prove replacement parity before retiring old workflow scaffolding. This
test keeps the matrix from becoming an unstructured note or losing required
surfaces/dependency wiring.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "docs" / "aegis" / "pr-4-replacement-parity-matrix.md"
TASKS_JSON = REPO_ROOT / ".taskmaster" / "tasks" / "tasks.json"

REQUIRED_HEADERS = [
    "Old surface",
    "Current job performed",
    "Current owner",
    "Replacement surface",
    "Proof required for equal-or-better behavior",
    "Dogfood evidence",
    "Remaining unique legacy content",
    "Rollback path",
    "Retirement state",
    "PR-4 go/no-go",
]

REQUIRED_SURFACES = [
    "sessions/",
    "sessions/current",
    "sessions/state.json",
    "plans/",
    "plans/current",
    "TRACKER.md",
    "HANDOFF.md",
    "docs/ai/work-tracking/active/",
    ".aegis/state/pending-tracking.json",
    "posttooluse-tracking.sh",
    "tracking-stop-gate.sh",
    "Closeout and handoff semantic gates",
    "Strict readiness and current-work blocks",
    "aegis kickoff",
    "aegis closeout",
    "Protected workflow path rules",
    "Target-repo ceremony scaffolding",
    "Packaged workflow templates",
    "Installed ceremony guidance docs",
    "Doctor and repair of old surfaces",
]

ALLOWED_STATES = {"keep", "shadow", "demote", "retire"}


def _matrix_rows(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    header_index = next(
        index
        for index, line in enumerate(lines)
        if "Old surface" in line and "Retirement state" in line
    )
    headers = [cell.strip() for cell in lines[header_index].strip("|").split("|")]
    assert headers == REQUIRED_HEADERS
    rows: list[dict[str, str]] = []
    for line in lines[header_index + 2 :]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def test_pr4_replacement_parity_matrix_is_complete() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())
    assert "PR-4 MUST NOT remove, demote, stop validating, or stop generating" in text
    assert (
        "passive Aegis evidence and legacy S:W:H:E scaffolding complement one another"
        in normalized_text
    )
    assert "Task 210 is **NO-GO**" in text
    assert "reports/coexistence-audit.md" in text
    assert "15,463, 2,506, and 45,473 ledger rows" in text

    rows = _matrix_rows(text)
    assert rows
    surfaces = {row["Old surface"].replace("`", "") for row in rows}
    for surface in REQUIRED_SURFACES:
        assert any(surface in candidate for candidate in surfaces)

    for row in rows:
        state = row["Retirement state"].strip("`")
        assert state in ALLOWED_STATES
        for header in REQUIRED_HEADERS:
            value = row[header].strip()
            assert value
            assert "TBD" not in value
            assert "TODO" not in value
            assert "placeholder" not in value.lower()
        assert state in {"keep", "shadow"}
        assert row["PR-4 go/no-go"].startswith("NO-GO")
        assert len(row["Remaining unique legacy content"]) >= 40
        assert any(
            marker in row["Dogfood evidence"]
            for marker in (
                "Task 243",
                "Tasks 237",
                "Tasks 239",
                "Tasks 241",
                "Tasks 244",
                "Tasks 248",
                "Task 251",
                "Blog",
                "HP-Fetcher",
            )
        )


def test_pr4_task_depends_on_parity_matrix_task() -> None:
    data = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    tasks_payload = data.get("tasks")
    if tasks_payload is None:
        tasks_payload = data["master"]["tasks"]
    tasks = {str(task["id"]): task for task in tasks_payload}
    assert "229" in tasks
    assert "210" in tasks
    assert "229" in {str(dep) for dep in tasks["210"].get("dependencies", [])}
    assert "233" in tasks
    assert "233" in {str(dep) for dep in tasks["210"].get("dependencies", [])}
    assert "243" in tasks
    assert "243" in {str(dep) for dep in tasks["210"].get("dependencies", [])}
