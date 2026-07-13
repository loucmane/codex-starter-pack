"""Task 248 regression coverage for the first-class Codex hook adapter."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts import _aegis_installer as installer


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_REL = Path(".codex/hooks.json")


def _hook_commands(payload: dict[str, object]) -> list[dict[str, object]]:
    hooks = payload["hooks"]
    assert isinstance(hooks, dict)
    return [
        hook
        for registrations in hooks.values()
        for registration in registrations
        for hook in registration["hooks"]
    ]


def _operation(report: dict[str, object], rel_path: str) -> dict[str, object]:
    plan = report["plan"] if "plan" in report else report
    assert isinstance(plan, dict)
    operations = plan["operations"]
    assert isinstance(operations, list)
    return next(
        operation
        for operation in operations
        if isinstance(operation, dict) and operation.get("path") == rel_path
    )


def _write_pre_adapter_codex_manifest(target: Path) -> bytes:
    """Downgrade a current install to the Blog pre-Task-248 manifest shape."""

    manifest_path = target / installer.AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    codex = manifest["agents"]["codex"]
    codex["gate_ids"] = ["codex.guard", "codex.work_tracking_audit"]
    codex["managed_files"] = [
        path
        for path in codex["managed_files"]
        if path
        not in {
            HOOKS_REL.as_posix(),
            ".claude/scripts/gate_lib.py",
            ".claude/scripts/pretooluse-gate.sh",
            ".claude/scripts/posttooluse-tracking.sh",
        }
    ]
    manifest["gates"] = [
        gate
        for gate in manifest["gates"]
        if gate["id"] not in set(installer.CODEX_GATE_IDS)
        or gate["id"] in {"codex.guard", "codex.work_tracking_audit"}
    ]
    manifest["managed_files"] = [
        record
        for record in manifest["managed_files"]
        if record["path"] != HOOKS_REL.as_posix()
    ]
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path.write_bytes(payload)
    return payload


def test_rendered_codex_hooks_use_canonical_apply_patch_and_git_root_dispatch() -> None:
    payload = json.loads(installer._render_codex_hooks())
    hooks = payload["hooks"]

    assert set(hooks) == {"PreToolUse", "PostToolUse", "SessionStart", "Stop"}
    assert hooks["PreToolUse"][0]["matcher"] == installer.CODEX_HOOK_MATCHER
    assert hooks["PostToolUse"][0]["matcher"] == installer.CODEX_HOOK_MATCHER
    assert "apply_patch" in installer.CODEX_HOOK_MATCHER

    post_commands = [hook["command"] for hook in hooks["PostToolUse"][0]["hooks"]]
    assert post_commands == [
        installer.CODEX_POSTTOOLUSE_COMMAND,
        installer.CODEX_LEDGER_RECORD_COMMAND,
    ]
    for hook in _hook_commands(payload):
        command = str(hook["command"])
        assert "AEGIS_INVOKING_AGENT=codex" in command
        assert "$(git rev-parse --show-toplevel)" in command
        assert "async" not in hook


@pytest.mark.parametrize(
    ("primary_agent", "agents"),
    [("codex", ["codex"]), ("multi", ["claude", "codex"])],
)
def test_codex_only_and_multi_agent_installs_are_managed_and_idempotent(
    tmp_path: Path,
    primary_agent: str,
    agents: list[str],
) -> None:
    target = tmp_path / primary_agent
    target.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=target,
        check=True,
    )

    report = installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
        apply=True,
    )

    assert report["status"] == "applied"
    assert (target / HOOKS_REL).is_file()
    assert (target / ".claude/scripts/gate_lib.py").is_file()
    assert (target / ".claude/scripts/pretooluse-gate.sh").is_file()
    assert (target / ".claude/scripts/posttooluse-tracking.sh").is_file()
    assert (target / "CODEX.md").is_file()
    if primary_agent == "codex":
        assert not (target / "CLAUDE.md").exists()
        assert not (target / ".claude/settings.json").exists()
    else:
        assert (target / "CLAUDE.md").is_file()
        assert (target / ".claude/settings.json").is_file()

    manifest = json.loads(
        (target / installer.AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    )
    codex = manifest["agents"]["codex"]
    assert codex["enabled"] is True
    assert manifest["entrypoints"]["codex"] == "CODEX.md"
    assert HOOKS_REL.as_posix() in codex["managed_files"]
    assert set(installer.CODEX_GATE_IDS).issubset(codex["gate_ids"])
    assert set(installer.CODEX_GATE_IDS).issubset(
        {gate["id"] for gate in manifest["gates"]}
    )

    managed_paths = [item["path"] for item in manifest["managed_files"]]
    assert len(managed_paths) == len(set(managed_paths))
    reload_report = report["client_reload"]
    assert "codex" in reload_report["agents"]
    assert reload_report["hook_trust"] == {
        "required": True,
        "settings_path": HOOKS_REL.as_posix(),
        "review_command": "/hooks",
        "hash_scope": "exact_hook_definition",
        "bypass_allowed": False,
        "instructions": (
            "Review and trust the exact project hook hashes with /hooks; changed hashes "
            "remain skipped until trusted."
        ),
    }
    init_next = installer._post_init_next_action(report)
    assert init_next["action"] == (
        "restart_codex_before_mutation"
        if primary_agent == "codex"
        else "restart_clients_before_mutation"
    )
    assert "/hooks" in init_next["suggested_cli"]
    assert init_next["details"]["agents"] == reload_report["agents"]
    assert init_next["details"]["hook_trust"]["bypass_allowed"] is False

    strict_checks = installer._strict_codex_checks(target, manifest)
    assert strict_checks
    assert all(check["status"] == "pass" for check in strict_checks), strict_checks

    second = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
    )
    assert {operation["classification"] for operation in second["operations"]} == {"skip"}


def test_semantically_identical_unowned_codex_hooks_are_adopted_byte_for_byte(
    tmp_path: Path,
) -> None:
    target = tmp_path / "semantic-adoption"
    hooks_path = target / HOOKS_REL
    hooks_path.parent.mkdir(parents=True)
    compact = json.dumps(
        json.loads(installer._render_codex_hooks()),
        separators=(",", ":"),
    ).encode("utf-8")
    hooks_path.write_bytes(compact)

    preview = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
    )
    operation = _operation(preview, HOOKS_REL.as_posix())
    assert operation["classification"] == "skip"
    assert operation["safe_to_apply"] is True
    assert preview["summary"]["manual_reviews"] == 0

    report = installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert hooks_path.read_bytes() == compact


def test_modified_managed_codex_hooks_require_manual_review_and_update_refuses(
    tmp_path: Path,
) -> None:
    target = tmp_path / "manual-review"
    target.mkdir()
    installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    hooks_path = target / HOOKS_REL
    customized = json.dumps({"hooks": {"PreToolUse": []}}, indent=2).encode("utf-8")
    hooks_path.write_bytes(customized)

    preview = installer.plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
    )
    operation = _operation(preview, HOOKS_REL.as_posix())
    assert operation["classification"] == "manual-review"
    assert operation["safe_to_apply"] is False

    report = installer.project_update(target, source_root=REPO_ROOT, apply=True)
    assert report["status"] == "refused"
    assert report["product_file_safety"]["manual_review_paths"] == [
        HOOKS_REL.as_posix()
    ]
    assert hooks_path.read_bytes() == customized


@pytest.mark.parametrize(
    ("primary_agent", "agents"),
    [("codex", ["codex"]), ("multi", ["claude", "codex"])],
)
def test_project_update_migrates_pre_adapter_codex_manifest_before_runtime_refresh(
    tmp_path: Path,
    primary_agent: str,
    agents: list[str],
) -> None:
    target = tmp_path / f"pre-adapter-{primary_agent}"
    target.mkdir()
    installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
        apply=True,
    )
    _write_pre_adapter_codex_manifest(target)
    (target / HOOKS_REL).unlink()

    current_schema = json.loads(
        (REPO_ROOT / "schemas/aegis/foundation-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    legacy_manifest = json.loads(
        (target / installer.AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    )
    with pytest.raises(ValidationError):
        Draft202012Validator(current_schema).validate(legacy_manifest)
    with pytest.raises(ValidationError):
        installer.runtime_update(target, source_root=REPO_ROOT, apply=True)

    preview = installer.project_update(target, source_root=REPO_ROOT, apply=False)
    hook_operation = _operation(preview["install"]["plan"], HOOKS_REL.as_posix())
    assert preview["status"] == "preview"
    assert hook_operation["classification"] == "create"
    assert hook_operation["safe_to_apply"] is True
    assert preview["install"]["summary"]["manual_reviews"] == 0

    report = installer.project_update(target, source_root=REPO_ROOT, apply=True)

    assert report["status"] == "applied"
    assert report["install"]["applied"]["status"] == "applied"
    assert report["runtime"]["applied"]["status"] == "applied"
    assert (target / HOOKS_REL).read_bytes() == installer._render_codex_hooks()
    migrated = json.loads(
        (target / installer.AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    )
    Draft202012Validator(current_schema).validate(migrated)
    assert HOOKS_REL.as_posix() in migrated["agents"]["codex"]["managed_files"]
    assert set(installer.CODEX_GATE_IDS).issubset(
        migrated["agents"]["codex"]["gate_ids"]
    )

    second_preview = installer.project_update(target, source_root=REPO_ROOT, apply=False)
    assert second_preview["status"] == "preview"
    assert second_preview["install"]["summary"]["creates"] == 0
    assert second_preview["install"]["summary"]["modifies"] == 0
    assert second_preview["install"]["summary"]["manual_reviews"] == 0


def test_pre_adapter_divergent_codex_hooks_refuse_before_any_update_write(
    tmp_path: Path,
) -> None:
    target = tmp_path / "pre-adapter-divergent-hooks"
    target.mkdir()
    installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )
    _write_pre_adapter_codex_manifest(target)
    hooks_path = target / HOOKS_REL
    customized = b'{"hooks":{"PreToolUse":[]}}\n'
    hooks_path.write_bytes(customized)
    manifest_path = target / installer.AEGIS_MANIFEST_REL
    runtime_path = target / installer.AEGIS_RUNTIME_ENV_REL
    manifest_before = manifest_path.read_bytes()
    runtime_before = runtime_path.read_bytes()

    report = installer.project_update(target, source_root=REPO_ROOT, apply=True)

    hook_operation = _operation(report["install"]["plan"], HOOKS_REL.as_posix())
    assert report["status"] == "refused"
    assert hook_operation["classification"] == "manual-review"
    assert hook_operation["managed"] is False
    assert report["product_file_safety"]["manual_review_paths"] == [
        HOOKS_REL.as_posix()
    ]
    assert hooks_path.read_bytes() == customized
    assert manifest_path.read_bytes() == manifest_before
    assert runtime_path.read_bytes() == runtime_before


def test_new_codex_reload_requirement_preserves_existing_claude_marker(
    tmp_path: Path,
) -> None:
    target = tmp_path / "reload-union"
    marker = target / installer.AEGIS_CLIENT_RELOAD_REL
    marker.parent.mkdir(parents=True)
    marker.write_text(
        json.dumps(
            {
                "schema_version": installer.SCHEMA_VERSION,
                "status": "required",
                "agent": "claude",
                "agents": ["claude"],
                "changed_paths": [".claude/settings.json"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    plan = {
        "operations": [
            {
                "classification": "modify",
                "path": installer.CODEX_HOOKS_REL,
            }
        ]
    }

    report = installer._client_reload_report(target, plan, ["claude", "codex"])

    assert report["agents"] == ["claude", "codex"]
    assert report["agent"] == "multi"
    assert report["changed_paths"] == [
        ".claude/settings.json",
        installer.CODEX_HOOKS_REL,
    ]
    assert report["hook_trust"]["required"] is True


def test_codex_runtime_and_schema_sources_match_packaged_assets() -> None:
    pairs = [
        (
            ".claude/scripts/gate_lib.py",
            "aegis_foundation/assets/.claude/scripts/gate_lib.py",
        ),
        (
            "scripts/_aegis_installer.py",
            "aegis_foundation/assets/scripts/_aegis_installer.py",
        ),
        (
            "schemas/aegis/profile.schema.json",
            "aegis_foundation/assets/schemas/aegis/profile.schema.json",
        ),
        (
            "schemas/aegis/foundation-manifest.schema.json",
            "aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json",
        ),
    ]
    for source, packaged in pairs:
        assert (REPO_ROOT / source).read_bytes() == (REPO_ROOT / packaged).read_bytes()


def test_schemas_reject_incomplete_first_class_codex_records(tmp_path: Path) -> None:
    target = tmp_path / "schema-contract"
    target.mkdir()
    installer.install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    manifest = json.loads(
        (target / installer.AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    )
    manifest_schema = json.loads(
        (REPO_ROOT / "schemas/aegis/foundation-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(manifest_schema).validate(manifest)

    incomplete_manifest = copy.deepcopy(manifest)
    incomplete_manifest["gates"] = [
        gate for gate in incomplete_manifest["gates"] if gate["id"] != "codex.apply_patch"
    ]
    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(incomplete_manifest)

    profile = installer.profile_payload()
    profile_schema = json.loads(
        (REPO_ROOT / "schemas/aegis/profile.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(profile_schema).validate(profile)
    incomplete_profile = copy.deepcopy(profile)
    incomplete_profile["conditional_gates"]["agents.codex.enabled"].remove(
        "codex.apply_patch"
    )
    with pytest.raises(ValidationError):
        Draft202012Validator(profile_schema).validate(incomplete_profile)
