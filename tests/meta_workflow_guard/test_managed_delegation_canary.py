"""Regressions for transactional Codex managed-delegation proof."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "plugins/gas-city-workflow/scripts/managed_delegation_canary.py"
SPEC = importlib.util.spec_from_file_location("managed_delegation_canary", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _installer():
    return module._load_installer(REPO_ROOT)


def _listed_hooks(
    root: Path,
    expected: tuple[module.HookDefinition, ...],
    *,
    trust_status: str,
) -> dict[str, object]:
    hooks = []
    for index, definition in enumerate(expected):
        hooks.append(
            {
                "key": f"{root / '.codex/hooks.json'}:managed:{index}",
                "eventName": definition.event_name,
                "handlerType": "command",
                "command": definition.command,
                "async": False,
                "matcher": definition.matcher,
                "timeoutSec": definition.timeout_seconds,
                "sourcePath": (root / ".codex/hooks.json").as_posix(),
                "source": "project",
                "pluginId": None,
                "enabled": True,
                "isManaged": False,
                "currentHash": "sha256:" + sha256(str(index).encode()).hexdigest(),
                "trustStatus": trust_status,
            }
        )
    return {"data": [{"cwd": root.as_posix(), "errors": [], "warnings": [], "hooks": hooks}]}


def test_expected_managed_hooks_cover_exact_installer_contract(tmp_path: Path) -> None:
    installer = _installer()
    expected = module.expected_managed_hooks(installer)

    assert len(expected) == 7
    assert {item.command for item in expected} == set(installer.CODEX_MANAGED_HOOK_COMMANDS)
    assert {item.event_name for item in expected} == {
        "preToolUse",
        "postToolUse",
        "sessionStart",
        "stop",
        "subagentStart",
        "subagentStop",
    }

    hooks = tmp_path / ".codex/hooks.json"
    hooks.parent.mkdir()
    hooks.write_bytes(installer._render_codex_hooks())
    assert (
        module.validate_installed_manifest(hooks, expected)
        == sha256(hooks.read_bytes()).hexdigest()
    )


def test_hooks_list_validation_rejects_metadata_drift(tmp_path: Path) -> None:
    expected = module.expected_managed_hooks(_installer())
    listing = _listed_hooks(tmp_path, expected, trust_status="untrusted")

    records = module._listing_records(listing, tmp_path, expected)
    assert len(records) == len(expected)

    listing["data"][0]["hooks"][0]["timeoutSec"] = 31  # type: ignore[index]
    with pytest.raises(module.CanaryError, match="omitted or duplicated"):
        module._listing_records(listing, tmp_path, expected)


def test_installed_fixture_denies_without_launch_and_allows_local_read(tmp_path: Path) -> None:
    installer = _installer()
    project, report = module._create_fixture(tmp_path / "run", REPO_ROOT, installer)
    expected = module.expected_managed_hooks(installer)
    module.validate_installed_manifest(project / ".codex/hooks.json", expected)

    denied = module._run_installed_gate(
        project,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "fixture-session",
            "cwd": project.as_posix(),
            "tool_name": "collaboration.spawn_agent",
            "tool_input": {"task_name": "never-launched", "message": "canary"},
        },
    )
    assert denied.returncode == 2
    decision = module._decision(project)
    assert decision["reason"] == "native_delegation_requires_gas_city"
    assert decision["verdict"] == "block"

    allowed = module._run_installed_gate(
        project,
        {
            "hook_event_name": "PreToolUse",
            "session_id": "fixture-session",
            "cwd": project.as_posix(),
            "tool_name": "Read",
            "tool_input": {"file_path": (project / "README.md").as_posix()},
        },
    )
    assert allowed.returncode == 0
    assert report["status"] == "applied"


def test_trust_transaction_writes_only_exact_keys_and_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    installer = _installer()
    expected = module.expected_managed_hooks(installer)
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex/hooks.json").write_bytes(installer._render_codex_hooks())
    codex = tmp_path / "codex"
    codex.write_text("fixture\n", encoding="utf-8")
    codex_config = tmp_path / ".codex/config.toml"
    codex_config.parent.mkdir()
    original = b'model = "gpt-5.6-sol"\n# unrelated bytes\n'
    codex_config.write_bytes(original)
    codex_config.chmod(0o600)
    monkeypatch.setattr(module, "DEFAULT_CODEX", codex)

    class FakeServer:
        trusted = False

        def __init__(self, _codex: Path, config: Path, root: Path) -> None:
            self.config = config
            self.root = root

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def request(self, method: str, params: dict[str, object]):
            if method == "config/read":
                return {
                    "layers": [
                        {
                            "name": {"type": "user", "file": self.config.as_posix()},
                            "version": "sha256:" + "1" * 64,
                        }
                    ]
                }
            if method == "hooks/list":
                return _listed_hooks(
                    self.root,
                    expected,
                    trust_status="trusted" if self.trusted else "untrusted",
                )
            if method == "config/batchWrite":
                rendered = self.config.read_bytes()
                for edit in params["edits"]:  # type: ignore[index]
                    key = edit["keyPath"].removeprefix("hooks.state.").removesuffix(".trusted_hash")
                    rendered += (
                        f"\n[hooks.state.{key}]\ntrusted_hash = {json.dumps(edit['value'])}\n"
                    ).encode()
                module._atomic_write(self.config, rendered, 0o600)
                type(self).trusted = True
                return {
                    "status": "ok",
                    "filePath": self.config.as_posix(),
                    "version": "sha256:" + "2" * 64,
                }
            raise AssertionError(method)

    snapshot = module._snapshot(codex_config)
    result = module.trust_managed_hooks(
        codex=codex,
        codex_config=codex_config,
        project_root=project,
        expected=expected,
        server_factory=FakeServer,
    )
    assert len(result["keys"]) == len(expected)
    assert result["mutated"] is True
    assert codex_config.read_bytes() != original

    trusted = codex_config.read_bytes()
    second = module.trust_managed_hooks(
        codex=codex,
        codex_config=codex_config,
        project_root=project,
        expected=expected,
        server_factory=FakeServer,
    )
    assert second["mutated"] is False
    assert codex_config.read_bytes() == trusted

    module._restore_snapshot(codex_config, snapshot)
    FakeServer.trusted = False
    module.verify_hooks_untrusted(
        codex=codex,
        codex_config=codex_config,
        project_root=project,
        expected=expected,
        server_factory=FakeServer,
    )
    assert codex_config.read_bytes() == original
    assert codex_config.stat().st_mode & 0o777 == 0o600


def test_trust_project_restores_config_after_post_write_verification_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    installer = _installer()
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex/hooks.json").write_bytes(installer._render_codex_hooks())
    codex_config = tmp_path / ".codex/config.toml"
    codex_config.parent.mkdir()
    original = b'model = "gpt-5.6-sol"\n# preserve exactly\n'
    codex_config.write_bytes(original)
    codex_config.chmod(0o600)

    def fake_run(argv, *, cwd, env=None):
        del env
        command = tuple(argv)
        if command == ("git", "rev-parse", "HEAD"):
            stdout = "a" * 40 + "\n"
        elif command == ("git", "rev-parse", "HEAD^{tree}"):
            stdout = "b" * 40 + "\n"
        elif command == ("git", "status", "--porcelain"):
            stdout = ""
        elif command == ("git", "rev-parse", "--show-toplevel"):
            stdout = project.as_posix() + "\n"
        else:  # pragma: no cover - makes unexpected controller calls explicit.
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def mutate_trust(**_kwargs):
        module._atomic_write(codex_config, b"mutated\n", 0o600)
        return {"mutated": True}

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "trust_managed_hooks", mutate_trust)
    monkeypatch.setattr(
        module,
        "_run_installed_gate",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", "refused"),
    )

    with pytest.raises(module.CanaryError, match="did not deny exactly"):
        module.trust_project(
            source_root=REPO_ROOT,
            project_root=project,
            codex=tmp_path / "codex",
            codex_config=codex_config,
            state_root=tmp_path / "state",
            run_id="failure-rollback",
        )

    assert codex_config.read_bytes() == original
    assert codex_config.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("argument", "message"),
    [
        ("--run-id=not-valid", "--run-id is not valid with check"),
        ("--project-root=/tmp/not-valid", "--project-root is only valid with trust-project"),
    ],
)
def test_check_rejects_mutating_mode_arguments(
    argument: str,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        module,
        "check",
        lambda *_args, **_kwargs: pytest.fail("check must not execute after argument drift"),
    )

    assert module.main(["check", argument]) == 2
    assert message in capsys.readouterr().err
