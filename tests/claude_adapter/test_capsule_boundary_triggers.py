"""Capsule boundary-trigger tests for CLI handlers.

The capsule should refresh at workflow boundaries, not after every mutation.
These tests pin the command-handler wiring without running the full underlying
workflow operation.
"""

from __future__ import annotations

import argparse
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
    monkeypatch.setattr(cli._aegis_installer, "verify", lambda *args, **kwargs: {"status": "passed"})

    assert cli.handle_next(_args(tmp_path)) == 0
    assert cli.handle_witness(_args(tmp_path)) == 0
    assert cli.handle_verify(_args(tmp_path)) == 0

    assert called == ["orientation", "pre-delivery", "verification"]
