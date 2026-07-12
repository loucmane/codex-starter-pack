"""Task 238: universal context budgets preserve truth while bounding stdout."""

from __future__ import annotations

from contextlib import nullcontext
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis_foundation import output_budget, replay
from aegis_foundation import cli as aegis_cli
from aegis_foundation.cli import build_arg_parser

REPO_ROOT = Path(__file__).resolve().parents[2]


def payload_with_events(size: int) -> dict[str, object]:
    return {
        "status": "failed",
        "installed": True,
        "summary": f"fixture with {size} events",
        "events": [
            {
                "id": index,
                "verdict": "would_block" if index % 4 == 0 else "allow",
                "tool_name": "Bash" if index % 2 == 0 else "Edit",
                "reason": "fixture reason",
            }
            for index in range(size)
        ],
        "next_action": {"command": "aegis repair --dry-run --target-dir ."},
    }


def collection_record(metadata: dict[str, object], path: str) -> dict[str, object]:
    records = metadata["collection_counts"]
    assert isinstance(records, list)
    return next(record for record in records if record["path"] == path)


@pytest.mark.parametrize("size", [0, 10, 3_500, 100_000])
def test_default_json_is_valid_bounded_and_exact(size: int) -> None:
    payload = payload_with_events(size)
    rendered = output_budget.render_json(
        payload,
        command="status",
        artifact_paths=[".aegis/state/pending-tracking.json"],
    )
    projected = json.loads(rendered)
    metadata = projected["_aegis_output"]

    assert len(rendered.splitlines()) <= output_budget.DEFAULT_MAX_LINES
    assert len(rendered.encode("utf-8")) <= output_budget.DEFAULT_MAX_BYTES
    assert metadata["actual"] == {"lines": 1, "bytes": len(rendered.encode("utf-8"))}
    assert projected["status"] == payload["status"]
    assert projected["installed"] is True
    assert len(projected["events"]) == min(size, output_budget.DEFAULT_SAMPLE_SIZE)
    assert collection_record(metadata, "$.events")["items"] == size
    assert metadata["category_counts"].get("verdict", {}).get("total", 0) == size
    assert metadata["next_action"] == "aegis repair --dry-run --target-dir ."
    assert metadata["artifact_paths"] == [".aegis/state/pending-tracking.json"]
    if size > output_budget.DEFAULT_SAMPLE_SIZE:
        truncation = next(item for item in metadata["truncations"] if item["path"] == "$.events")
        assert truncation == {
            "kind": "array",
            "omitted": size - output_budget.DEFAULT_SAMPLE_SIZE,
            "path": "$.events",
            "shown": output_budget.DEFAULT_SAMPLE_SIZE,
            "total": size,
        }


def test_verbose_is_bounded_and_samples_twenty() -> None:
    rendered = output_budget.render_json(
        payload_with_events(3_500),
        command="doctor",
        mode=output_budget.VERBOSE_MODE,
    )
    projected = json.loads(rendered)
    assert len(projected["events"]) == output_budget.VERBOSE_SAMPLE_SIZE
    assert len(rendered.splitlines()) <= output_budget.VERBOSE_MAX_LINES
    assert len(rendered.encode("utf-8")) <= output_budget.VERBOSE_MAX_BYTES
    assert projected["_aegis_output"]["detail_mode"] == "verbose"


def test_all_json_is_the_complete_legacy_payload() -> None:
    payload = payload_with_events(3_500)
    rendered = output_budget.render_json(payload, command="verify", mode=output_budget.ALL_MODE)
    assert json.loads(rendered) == payload
    assert "_aegis_output" not in json.loads(rendered)
    assert len(json.loads(rendered)["events"]) == 3_500


def test_high_cardinality_categories_cannot_expand_stdout_unboundedly() -> None:
    payload = {
        "status": "failed",
        "events": [
            {"reason": f"unique-{index}-" + ("x" * 500), "verdict": "allow"}
            for index in range(100_000)
        ],
    }
    rendered = output_budget.render_json(payload, command="next")
    metadata = json.loads(rendered)["_aegis_output"]
    assert len(rendered.encode("utf-8")) <= output_budget.DEFAULT_MAX_BYTES
    assert metadata["category_counts"]["reason"]["total"] == 100_000
    assert metadata["category_counts"]["reason"]["other"] > 0


def test_hpfetcher_pending_cardinality_fixture_is_one_screen_without_losing_count() -> None:
    fixture = json.loads(
        (REPO_ROOT / "tests/fixtures/aegis/hpfetcher-status-pending-budget.json").read_text(
            encoding="utf-8"
        )
    )
    pending_count = fixture["pending_event_count"]
    payload = {
        "status": "current",
        "installed": True,
        "workflow_guidance": {
            "status": "blocked",
            "details": {"pending_event_ids": [f"event-{index}" for index in range(pending_count)]},
        },
    }
    rendered = output_budget.render_json(
        payload,
        command="status",
        artifact_paths=[fixture["expected_artifact"]],
    )
    projected = json.loads(rendered)
    metadata = projected["_aegis_output"]
    pending = collection_record(metadata, "$.workflow_guidance.details.pending_event_ids")
    assert pending["items"] == pending_count
    assert len(rendered.splitlines()) <= fixture["expected_default_max_lines"]
    assert len(rendered.encode("utf-8")) <= fixture["expected_default_max_bytes"]
    assert fixture["expected_artifact"] in metadata["artifact_paths"]


def test_text_preserves_primary_verdict_and_discloses_truncation() -> None:
    payload = payload_with_events(100_000)
    source = "Result: FAIL\n" + "detail " + ("x" * 40_000) + "\n" + ("more\n" * 500)
    rendered = output_budget.render_text(
        source,
        payload,
        command="witness",
        artifact_paths=[".aegis/reports/witness-report.json"],
    )
    assert rendered.startswith("Result: FAIL\n")
    assert "Truncated: yes" in rendered
    assert "Artifacts: .aegis/reports/witness-report.json" in rendered
    assert "Full stdout: rerun the same command with --all." in rendered
    assert len(rendered.splitlines()) <= output_budget.DEFAULT_MAX_LINES
    assert len(rendered.encode("utf-8")) <= output_budget.DEFAULT_MAX_BYTES


def test_text_does_not_repeat_an_existing_copyable_next_action() -> None:
    command = "./.aegis/bin/aegis repair --target-dir ."
    source = f"Aegis next: repair\nSuggested: {command}\n"
    rendered = output_budget.render_text(
        source,
        {"status": "blocked", "suggested_cli": command},
        command="next",
    )
    assert rendered.count(command) == 1


def test_failure_stdout_is_bounded_while_ci_artifact_remains_complete(tmp_path: Path) -> None:
    payload = {
        "status": "failed",
        "passed": False,
        "failures": [
            {"status": "fail", "path": f"src/generated/failure-{index}.py"}
            for index in range(3_500)
        ],
    }
    artifact = tmp_path / "verification-report.json"
    artifact.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    rendered = output_budget.render_json(
        payload,
        command="verify",
        artifact_paths=[artifact.as_posix()],
    )
    projected = json.loads(rendered)
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert len(projected["failures"]) == output_budget.DEFAULT_SAMPLE_SIZE
    assert len(stored["failures"]) == 3_500
    assert len(rendered.encode("utf-8")) <= output_budget.DEFAULT_MAX_BYTES
    assert collection_record(projected["_aegis_output"], "$.failures")["items"] == 3_500


def test_detail_flags_are_uniform_and_mutually_exclusive() -> None:
    parser = build_arg_parser()
    for command in ("status", "update", "next", "doctor", "verify", "closeout"):
        args = parser.parse_args([command, "--verbose"])
        assert args.verbose is True
        args = parser.parse_args([command, "--all"])
        assert args.all_output is True
        with pytest.raises(SystemExit):
            parser.parse_args([command, "--verbose", "--all"])


def test_standalone_readiness_source_and_packaged_asset_remain_identical() -> None:
    source = REPO_ROOT / ".claude/scripts/readiness.sh"
    packaged = REPO_ROOT / "aegis_foundation/assets/.claude/scripts/readiness.sh"
    assert source.read_bytes() == packaged.read_bytes()


def test_replay_artifact_retains_every_result_when_stdout_can_sample(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    entries = [
        {
            "id": f"ALLOW-{index}",
            "label": "must_allow",
            "state": "ready_advisory",
            "hook": "pretooluse",
            "payload": {"tool_name": "Bash", "tool_input": {"command": "git status --short"}},
            "notes": "read-only fixture",
        }
        for index in range(10)
    ]
    corpus.write_text("".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
    report = replay.run_corpus(
        [corpus], source_root=Path(__file__).resolve().parents[2], work_dir=tmp_path / "work"
    )
    artifact = Path(report["report_path"])
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert len(stored["results"]) == 10
    projected = json.loads(
        output_budget.render_json(
            report,
            command="replay",
            artifact_paths=[artifact.as_posix()],
        )
    )
    assert len(projected["results"]) == output_budget.DEFAULT_SAMPLE_SIZE
    assert collection_record(projected["_aegis_output"], "$.results")["items"] == 10


def test_all_eight_cli_surfaces_route_json_through_the_shared_renderer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    commands: list[str] = []

    def render_json_spy(_payload: object, *, command: str, **_kwargs: object) -> str:
        commands.append(command)
        return "{}\n"

    monkeypatch.setattr(output_budget, "render_json", render_json_spy)
    monkeypatch.setattr(aegis_cli, "_resolve_source_root", lambda _source: nullcontext(REPO_ROOT))
    monkeypatch.setattr(aegis_cli, "_refresh_capsule_if_stale", lambda *_args, **_kwargs: None)

    payload = {
        "status": "passed",
        "passed": True,
        "events": list(range(3_500)),
    }
    monkeypatch.setattr(aegis_cli._aegis_installer, "status", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "project_update", lambda *_args, **_kwargs: payload
    )
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "next_action", lambda *_args, **_kwargs: payload
    )
    monkeypatch.setattr(aegis_cli._aegis_installer, "doctor", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(aegis_cli._aegis_installer, "verify", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(aegis_cli._aegis_installer, "closeout", lambda *_args, **_kwargs: payload)

    common = {
        "target_dir": ".",
        "source_root": None,
        "json": True,
        "verbose": False,
        "all_output": False,
    }
    assert aegis_cli.handle_status(SimpleNamespace(**common)) == 0
    assert aegis_cli.handle_update(SimpleNamespace(**common, apply=False)) == 0
    assert aegis_cli.handle_next(SimpleNamespace(**common)) == 0
    assert aegis_cli.handle_doctor(SimpleNamespace(**common)) == 0
    assert aegis_cli.handle_verify(SimpleNamespace(**common, strict=False)) == 0
    assert (
        aegis_cli.handle_closeout(
            SimpleNamespace(
                **common,
                update_handoff=False,
                require_clean_git=False,
                no_git_guidance=False,
                dry_run=True,
            )
        )
        == 0
    )

    class WitnessStub:
        WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"

        @staticmethod
        def run_witness(*_args: object, **_kwargs: object) -> dict[str, object]:
            return dict(payload)

    monkeypatch.setattr(aegis_cli, "_load_witness_lib", lambda _source: WitnessStub)
    assert aegis_cli.handle_witness(SimpleNamespace(**common, base=None, ci=True)) == 0

    report_path = tmp_path / "replay" / "aegis-replay-report.json"
    monkeypatch.setattr(
        replay,
        "run_corpus",
        lambda *_args, **_kwargs: {**payload, "report_path": report_path.as_posix()},
    )
    assert (
        aegis_cli.handle_replay(
            SimpleNamespace(
                source_root=None,
                corpus=["fixture.jsonl"],
                work_dir=(tmp_path / "replay").as_posix(),
                json=True,
                verbose=False,
                all_output=False,
            )
        )
        == 0
    )
    capsys.readouterr()
    assert commands == [
        "status",
        "update",
        "next",
        "doctor",
        "verify",
        "closeout",
        "witness",
        "replay",
    ]


def test_human_facing_cli_summaries_route_through_the_shared_text_renderer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    commands: list[str] = []

    def render_text_spy(_text: str, _payload: object, *, command: str, **_kwargs: object) -> str:
        commands.append(command)
        return "bounded\n"

    monkeypatch.setattr(output_budget, "render_text", render_text_spy)
    monkeypatch.setattr(aegis_cli, "_resolve_source_root", lambda _source: nullcontext(REPO_ROOT))
    monkeypatch.setattr(aegis_cli, "_refresh_capsule_if_stale", lambda *_args, **_kwargs: None)
    payload = {"status": "passed", "passed": True, "events": list(range(3_500))}
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "next_action", lambda *_args, **_kwargs: payload
    )
    monkeypatch.setattr(aegis_cli._aegis_installer, "doctor", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(aegis_cli._aegis_installer, "closeout", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "format_next_summary", lambda _payload: "next\n"
    )
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "format_doctor_summary", lambda _payload: "doctor\n"
    )
    monkeypatch.setattr(
        aegis_cli._aegis_installer, "format_closeout_summary", lambda _payload: "closeout\n"
    )
    common = {
        "target_dir": ".",
        "source_root": None,
        "json": False,
        "verbose": False,
        "all_output": False,
    }
    assert aegis_cli.handle_next(SimpleNamespace(**common)) == 0
    assert aegis_cli.handle_doctor(SimpleNamespace(**common)) == 0
    assert (
        aegis_cli.handle_closeout(
            SimpleNamespace(
                **common,
                update_handoff=False,
                require_clean_git=False,
                no_git_guidance=False,
                dry_run=True,
            )
        )
        == 0
    )

    class WitnessStub:
        WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"

        @staticmethod
        def run_witness(*_args: object, **_kwargs: object) -> dict[str, object]:
            return dict(payload)

        @staticmethod
        def render_report(_report: object) -> str:
            return "witness\n"

    monkeypatch.setattr(aegis_cli, "_load_witness_lib", lambda _source: WitnessStub)
    assert aegis_cli.handle_witness(SimpleNamespace(**common, base=None, ci=True)) == 0

    monkeypatch.setattr(
        replay,
        "run_corpus",
        lambda *_args, **_kwargs: {
            **payload,
            "report_path": (tmp_path / "aegis-replay-report.json").as_posix(),
        },
    )
    monkeypatch.setattr(replay, "render_report", lambda _report: "replay\n")
    assert (
        aegis_cli.handle_replay(
            SimpleNamespace(
                source_root=None,
                corpus=["fixture.jsonl"],
                work_dir=tmp_path.as_posix(),
                json=False,
                verbose=False,
                all_output=False,
            )
        )
        == 0
    )
    capsys.readouterr()
    assert commands == ["next", "doctor", "closeout", "witness", "replay"]
