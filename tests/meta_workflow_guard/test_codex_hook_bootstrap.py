"""Task 252 regressions for target-local, failure-bounded Codex hook bootstrap."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import _aegis_installer as installer


REPO_ROOT = Path(__file__).resolve().parents[2]


def _install_codex_target(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    target.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=target, check=True)
    report = installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    assert report["status"] == "applied"
    enforcement = target / installer.AEGIS_ENFORCEMENT_REL
    enforcement.parent.mkdir(parents=True, exist_ok=True)
    enforcement.write_text(
        json.dumps(
            {
                "mode": "advisory",
                "set_at": "2026-07-14T00:00:00Z",
                "set_by": "task-252-test",
                "reason": "exercise passive target-local hooks",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def _run_local_hook(
    target: Path,
    phase: str,
    payload: dict[str, object] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(target / installer.AEGIS_LOCAL_BIN_REL), "hook", phase],
        cwd=target,
        input=json.dumps(payload or {}),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            "AEGIS_INVOKING_AGENT": "codex",
            "XDG_STATE_HOME": str(target / ".test-xdg-state"),
        },
        check=False,
    )


def _managed_record(target: Path, rel_path: str) -> dict[str, object]:
    manifest = json.loads(
        (target / installer.AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    )
    return next(
        record
        for record in manifest["managed_files"]
        if isinstance(record, dict) and record.get("path") == rel_path
    )


def _write_recorded_managed_bytes(target: Path, rel_path: str, content: bytes) -> None:
    path = target / rel_path
    path.write_bytes(content)
    manifest_path = target / installer.AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["managed_files"]
        if isinstance(item, dict) and item.get("path") == rel_path
    )
    record["checksum"] = "sha256:" + hashlib.sha256(content).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _pre_adapter_manifest(target: Path) -> None:
    manifest_path = target / installer.AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["managed_files"] = [
        record
        for record in manifest["managed_files"]
        if record.get("path") != installer.CODEX_HOOKS_REL
    ]
    codex = manifest["agents"]["codex"]
    codex["managed_files"] = [
        path for path in codex["managed_files"] if path != installer.CODEX_HOOKS_REL
    ]
    codex["gate_ids"] = [
        gate_id
        for gate_id in codex["gate_ids"]
        if gate_id not in set(installer.CODEX_GATE_IDS)
        or gate_id in {"codex.guard", "codex.work_tracking_audit"}
    ]
    manifest["gates"] = [
        gate
        for gate in manifest["gates"]
        if gate["id"] not in set(installer.CODEX_GATE_IDS)
        or gate["id"] in {"codex.guard", "codex.work_tracking_audit"}
    ]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_generated_codex_hooks_dispatch_all_phases_through_target_local_shim() -> None:
    payload = json.loads(installer._render_codex_hooks())
    commands = [
        handler["command"]
        for groups in payload["hooks"].values()
        for group in groups
        for handler in group["hooks"]
    ]

    assert commands
    assert all("$(git rev-parse --show-toplevel)/.aegis/bin/aegis" in command for command in commands)
    assert all(" hook " in command for command in commands)
    assert all("/.claude/scripts/" not in command for command in commands)
    assert all("AEGIS_INVOKING_AGENT=codex" in command for command in commands)


def test_two_targets_run_hooks_without_their_recorded_source_root(tmp_path: Path) -> None:
    targets = [
        _install_codex_target(tmp_path, "first"),
        _install_codex_target(tmp_path, "second"),
    ]
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n*** Add File: probe.txt\n+probe\n*** End Patch"
        },
    }

    for target in targets:
        (target / installer.AEGIS_RUNTIME_ENV_REL).write_text(
            "AEGIS_SOURCE_ROOT=/definitely/missing/aegis-source\n",
            encoding="utf-8",
        )
        result = _run_local_hook(target, "pretooluse", payload)
        assert result.returncode == 0, result.stderr
        assert "Aegis CLI is unavailable" not in result.stderr
        assert (target / installer.AEGIS_GATE_DECISIONS_REL).is_file()


def test_missing_target_runtime_fails_closed_once_and_passive_hooks_degrade_once(
    tmp_path: Path,
) -> None:
    target = _install_codex_target(tmp_path, "missing-runtime")
    (target / ".claude/scripts/gate_lib.py").unlink()
    mutation = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": "*** Begin Patch\n*** Add File: denied.txt\n+denied\n*** End Patch"
        },
    }

    first_pre = _run_local_hook(target, "pretooluse", mutation)
    second_pre = _run_local_hook(target, "pretooluse", mutation)
    first_stop = _run_local_hook(target, "stop")
    second_stop = _run_local_hook(target, "stop")

    assert first_pre.returncode == 2
    assert second_pre.returncode == 2
    assert first_pre.stderr.count("target-local Aegis hook runtime is unavailable") == 1
    assert second_pre.stderr == ""
    assert first_stop.returncode == 0
    assert second_stop.returncode == 0
    assert first_stop.stderr.count("target-local Aegis hook runtime is unavailable") == 1
    assert second_stop.stderr == ""
    assert len(first_pre.stderr.splitlines()) == 1
    assert len(first_stop.stderr.splitlines()) == 1


def test_cli_hook_dispatch_prefers_explicit_target_runtime(tmp_path: Path) -> None:
    target = _install_codex_target(tmp_path, "cli-target")
    marker = target / "local-hook-ran.txt"
    local_gate = target / ".claude/scripts/gate_lib.py"
    local_gate.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path('local-hook-ran.txt').write_text(sys.argv[1], encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            "/definitely/missing/aegis-source",
            "hook",
            "stop",
        ],
        cwd=target,
        input="{}",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            "AEGIS_TARGET_ROOT": str(target),
            "PYTHONPATH": str(REPO_ROOT),
        },
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert marker.read_text(encoding="utf-8") == "stop"


def test_exact_legacy_absolute_hooks_migrate_but_unknown_aegis_like_hooks_refuse(
    tmp_path: Path,
) -> None:
    target = _install_codex_target(tmp_path, "legacy-hooks")
    _pre_adapter_manifest(target)
    legacy = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "^(Bash|apply_patch)$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash /opt/aegis/.claude/scripts/pretooluse-gate.sh",
                        },
                        {"type": "command", "command": "./project-owned-hook"},
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash /opt/aegis/.claude/scripts/handoff-nudge.sh",
                        }
                    ]
                }
            ],
        }
    }
    hooks_path = target / installer.CODEX_HOOKS_REL
    hooks_path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

    preview = installer.project_update(target, source_root=REPO_ROOT, apply=False)
    operation = next(
        item
        for item in preview["install"]["plan"]["operations"]
        if item["path"] == installer.CODEX_HOOKS_REL
    )
    assert operation["classification"] == "modify"
    assert operation["safe_to_apply"] is True

    report = installer.project_update(target, source_root=REPO_ROOT, apply=True)
    assert report["status"] == "applied"
    rendered = hooks_path.read_text(encoding="utf-8")
    assert "/opt/aegis/.claude/scripts/" not in rendered
    assert "./project-owned-hook" in rendered

    unknown_target = _install_codex_target(tmp_path, "unknown-hooks")
    _pre_adapter_manifest(unknown_target)
    unknown_path = unknown_target / installer.CODEX_HOOKS_REL
    unknown_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "bash /opt/aegis/.claude/scripts/custom-stop.sh",
                                }
                            ]
                        }
                    ]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    refused = installer.project_update(unknown_target, source_root=REPO_ROOT, apply=True)
    assert refused["status"] == "refused"
    assert refused["product_file_safety"]["manual_review_paths"] == [installer.CODEX_HOOKS_REL]


def test_install_restores_modified_runtime_bytes_after_mid_apply_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _install_codex_target(tmp_path, "transaction")
    stale_gate = b"# recorded old gate runtime\n"
    stale_shim = b"#!/usr/bin/env bash\n# recorded old shim\n"
    _write_recorded_managed_bytes(target, ".claude/scripts/gate_lib.py", stale_gate)
    _write_recorded_managed_bytes(target, installer.AEGIS_LOCAL_BIN_REL, stale_shim)
    manifest_before = (target / installer.AEGIS_MANIFEST_REL).read_bytes()
    real_write = installer._write_asset
    raised = False

    def fail_once(root: Path, asset: installer.Asset) -> None:
        nonlocal raised
        if asset.path == installer.AEGIS_LOCAL_BIN_REL and not raised:
            raised = True
            raise OSError("injected Task 252 activation failure")
        real_write(root, asset)

    monkeypatch.setattr(installer, "_write_asset", fail_once)
    report = installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )

    assert report["status"] == "failed"
    assert report["rollback"]["status"] == "completed"
    assert (target / ".claude/scripts/gate_lib.py").read_bytes() == stale_gate
    assert (target / installer.AEGIS_LOCAL_BIN_REL).read_bytes() == stale_shim
    assert (target / installer.AEGIS_MANIFEST_REL).read_bytes() == manifest_before
    assert _managed_record(target, ".claude/scripts/gate_lib.py")["checksum"] == (
        "sha256:" + hashlib.sha256(stale_gate).hexdigest()
    )


def test_runtime_activation_order_places_dependencies_before_entrypoints() -> None:
    assets = installer._managed_assets(REPO_ROOT, "codex", ("codex",))
    ordered = installer._ordered_install_assets(assets)
    positions = {asset.path: index for index, asset in enumerate(ordered)}

    assert positions[".claude/scripts/gate_lib.py"] < positions[installer.AEGIS_LOCAL_BIN_REL]
    assert positions[installer.AEGIS_LOCAL_BIN_REL] < positions[".claude/scripts/pretooluse-gate.sh"]
    assert positions[".claude/scripts/pretooluse-gate.sh"] < positions[installer.CODEX_HOOKS_REL]
