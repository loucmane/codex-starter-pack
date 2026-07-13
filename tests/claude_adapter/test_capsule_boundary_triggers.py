"""Capsule boundary-trigger tests for CLI handlers.

The capsule should refresh at workflow boundaries, not after every mutation.
These tests pin the command-handler wiring without running the full underlying
workflow operation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from aegis_foundation import cli  # noqa: E402


def _args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    values = {
        "source_root": REPO_ROOT.as_posix(),
        "target_dir": tmp_path.as_posix(),
        "json": True,
        "base": None,
        "ci": False,
        "strict": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_cli_boundary_handlers_refresh_expected_capsule_reasons(
    tmp_path: Path, monkeypatch
) -> None:
    called: list[str] = []

    def fake_refresh(_source_root: Path, _target_dir: str, *, reason: str):
        called.append(reason)
        return {"refreshed": True, "reason": reason}

    class FakeWitnessLib:
        @staticmethod
        def run_witness(_target_dir: str, *, base: str | None, ci_mode: bool):
            return {"passed": True, "base": base, "ci_mode": ci_mode}

        @staticmethod
        def render_report(_report: dict[str, object]) -> str:
            return "witness passed\n"

    monkeypatch.setattr(cli, "_refresh_capsule_if_stale", fake_refresh)
    monkeypatch.setattr(cli, "_load_witness_lib", lambda _source_root: FakeWitnessLib)
    monkeypatch.setattr(
        cli._aegis_installer,
        "next_action",
        lambda target_dir, *, source_root, invoking_agent=None: {
            "target_dir": target_dir,
            "source_root": source_root.as_posix(),
            "invoking_agent": invoking_agent,
        },
    )
    monkeypatch.setattr(
        cli._aegis_installer, "verify", lambda *args, **kwargs: {"status": "passed"}
    )

    assert cli.handle_next(_args(tmp_path)) == 0
    assert cli.handle_witness(_args(tmp_path)) == 0
    assert cli.handle_verify(_args(tmp_path)) == 0

    assert called == ["orientation", "pre-delivery", "verification"]


def test_witness_projection_failure_does_not_change_witness_verdict(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    class FakeWitnessLib:
        WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"

        @staticmethod
        def run_witness(_target_dir: str, *, base: str | None, ci_mode: bool):
            return {
                "passed": True,
                "base": base,
                "mode": "ci" if ci_mode else "local",
                "branch": "feat/task-234-witness-delivery-projection",
                "head_commit": "abc1234",
                "checks": {},
                "escalations": [],
            }

        @staticmethod
        def render_report(_report: dict[str, object]) -> str:
            return "witness passed\n"

    monkeypatch.setattr(cli, "_refresh_capsule_if_stale", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_load_witness_lib", lambda _source_root: FakeWitnessLib)
    monkeypatch.setattr(
        cli,
        "_record_witness_boundary",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("projection unavailable")),
    )

    assert cli.handle_witness(_args(tmp_path)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["boundary_event"]["status"] == "warning"
    assert payload["boundary_event"]["reason"] == "projection unavailable"
    assert payload["legacy_projection"]["status"] == "skipped"


def test_witness_cli_preserves_semantic_process_exit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class UnsupportedWitnessLib:
        WITNESS_REPORT_REL = ".aegis/reports/witness-report.json"
        DELIVERY_REPORT_REL = ".aegis/reports/delivery-report.md"

        @staticmethod
        def run_witness(_target_dir: str, *, base: str | None, ci_mode: bool):
            return {
                "passed": False,
                "exit_class": "unsupported",
                "process_exit_code": 2,
                "base": base,
                "mode": "ci" if ci_mode else "local",
                "branch": "feat/task-241-quiet-witness",
                "head_commit": "abc1234",
                "checks": {},
                "escalations": [],
            }

        @staticmethod
        def render_report(_report: dict[str, object]) -> str:
            return "witness unsupported\n"

    monkeypatch.setattr(cli, "_refresh_capsule_if_stale", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_load_witness_lib", lambda _source_root: UnsupportedWitnessLib)

    assert cli.handle_witness(_args(tmp_path, ci=True)) == 2
