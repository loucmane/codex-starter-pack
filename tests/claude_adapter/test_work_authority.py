from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_foundation import work_authority


def _taskmaster(root: Path) -> None:
    path = root / ".taskmaster" / "tasks" / "tasks.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 7,
                            "title": "Legacy task",
                            "status": "done",
                            "priority": "high",
                            "dependencies": [],
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )


def _beads(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "ga-zbmk",
                    "title": "Aegis beads-first authority",
                    "description": "Durable projection work",
                    "status": "in_progress",
                    "priority": 2,
                    "issue_type": "feature",
                    "assignee": "loucmane",
                    "updated_at": "2026-08-27T10:20:26Z",
                    "labels": ["obsidian", "aegis"],
                    "metadata": {
                        "gc.branch": "codex/ga-zbmk-aegis-beads-obsidian",
                        "gc.secret_token": "must-not-project",
                        "unreviewed": "must-not-project",
                    },
                    "dependencies": [{"depends_on_id": "ga-946b", "type": "discovered-from"}],
                }
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_explicit_beads_replace_legacy_taskmaster_and_default_to_structured_only(
    tmp_path: Path,
) -> None:
    _taskmaster(tmp_path)
    source = tmp_path / "beads.json"
    _beads(source)

    snapshot = work_authority.collect_work_authority(tmp_path, bead_snapshot=source)

    assert snapshot["authority"] == "beads"
    assert snapshot["source_kind"] == "explicit-bead-snapshot"
    assert snapshot["content_policy"]["bead_titles_labels_descriptions"] is False
    assert [item["id"] for item in snapshot["items"]] == ["ga-zbmk"]
    item = snapshot["items"][0]
    assert item["title"] == ""
    assert item["description"] == ""
    assert item["labels"] == []
    assert item["assignee"] == ""
    assert item["priority"] == "P2"
    assert item["metadata"] == {"gc.branch": "codex/ga-zbmk-aegis-beads-obsidian"}
    assert item["dependencies"] == [{"id": "ga-946b", "type": "discovered-from"}]
    assert "must-not-project" not in json.dumps(snapshot)


def test_bead_content_requires_explicit_opt_in(tmp_path: Path) -> None:
    source = tmp_path / "beads.json"
    _beads(source)

    snapshot = work_authority.collect_work_authority(
        tmp_path,
        bead_snapshot=source,
        include_bead_content=True,
    )

    item = snapshot["items"][0]
    assert item["title"] == "Aegis beads-first authority"
    assert item["description"] == "Durable projection work"
    assert item["labels"] == ["aegis", "obsidian"]
    assert item["assignee"] == "loucmane"


def test_taskmaster_remains_read_only_compatibility_source(tmp_path: Path) -> None:
    _taskmaster(tmp_path)

    snapshot = work_authority.collect_work_authority(tmp_path)

    assert snapshot["authority"] == "taskmaster"
    assert snapshot["source_kind"] == "legacy-taskmaster"
    assert snapshot["items"][0]["id"] == "7"
    assert snapshot["items"][0]["title"] == "Legacy task"
    assert snapshot["items"][0]["authority"] == "taskmaster"


def test_bead_snapshot_refuses_symlinks_duplicates_and_unsafe_ids(tmp_path: Path) -> None:
    source = tmp_path / "beads.json"
    _beads(source)
    link = tmp_path / "link.json"
    link.symlink_to(source)
    with pytest.raises(work_authority.WorkAuthorityError, match="non-symlink"):
        work_authority.collect_work_authority(tmp_path, bead_snapshot=link)

    source.write_text(
        json.dumps([{"id": "ga-one"}, {"id": "ga-one"}]),
        encoding="utf-8",
    )
    with pytest.raises(work_authority.WorkAuthorityError, match="duplicate bead id"):
        work_authority.collect_work_authority(tmp_path, bead_snapshot=source)

    source.write_text(json.dumps([{"id": "../../unsafe"}]), encoding="utf-8")
    with pytest.raises(work_authority.WorkAuthorityError, match="unsafe bead id"):
        work_authority.collect_work_authority(tmp_path, bead_snapshot=source)


def test_accepts_beads_jsonl_export(tmp_path: Path) -> None:
    source = tmp_path / "beads.jsonl"
    source.write_text(
        json.dumps({"_type": "issue", "id": "ga-one", "status": "open"})
        + "\n"
        + json.dumps({"_type": "issue", "id": "ga-two", "status": "closed"})
        + "\n",
        encoding="utf-8",
    )

    snapshot = work_authority.collect_work_authority(tmp_path, bead_snapshot=source)

    assert [item["id"] for item in snapshot["items"]] == ["ga-one", "ga-two"]


def test_accepts_one_record_beads_jsonl_export(tmp_path: Path) -> None:
    source = tmp_path / "beads.jsonl"
    source.write_text(
        json.dumps({"_type": "issue", "id": "ga-one", "status": "open"}) + "\n",
        encoding="utf-8",
    )

    snapshot = work_authority.collect_work_authority(tmp_path, bead_snapshot=source)

    assert [item["id"] for item in snapshot["items"]] == ["ga-one"]


def test_accepts_native_hierarchical_bead_ids_and_dependencies(tmp_path: Path) -> None:
    source = tmp_path / "beads.json"
    source.write_text(
        json.dumps(
            [
                {"id": "ga-parent", "status": "open"},
                {
                    "id": "ga-parent.3",
                    "parent_id": "ga-parent",
                    "status": "open",
                    "dependencies": [{"depends_on_id": "ga-parent.2", "type": "blocks"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    snapshot = work_authority.collect_work_authority(tmp_path, bead_snapshot=source)

    assert [item["id"] for item in snapshot["items"]] == ["ga-parent", "ga-parent.3"]
    assert snapshot["items"][1]["parent_id"] == "ga-parent"
    assert snapshot["items"][1]["dependencies"] == [{"id": "ga-parent.2", "type": "blocks"}]
