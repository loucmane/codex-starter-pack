"""Tests for the bounded report-only evidence reviewer installation."""

from __future__ import annotations

import importlib.util
import json
import stat
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "plugins"
    / "gas-city-workflow"
    / "scripts"
    / "install_evidence_reviewer.py"
)
SPEC = importlib.util.spec_from_file_location("install_evidence_reviewer", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


BASE_CITY = b'''[providers]\n[providers.codex]\nbase = "builtin:codex"\noptions_schema_merge = "by_key"\ncommand = "/home/loucmane/gascity/bin/codex"\n\n[providers.codex.option_defaults]\neffort = "xhigh"\nmodel = "gpt-5.6-sol"\npermission_mode = "fail-fast"\nworklog_access = "classified-vault"\n\n[[providers.codex.options_schema]]\nkey = "permission_mode"\nlabel = "Approval policy"\ntype = "select"\ndefault = "fail-fast"\n'''
BASE_CODEX = b'''model = "gpt-5.6-sol"\n# unrelated bytes must survive exactly\n[projects."/home/loucmane/codex"]\ntrust_level = "trusted"\n'''


class FakeRunner(module.Runner):
    def __init__(self, *, fail_prime: bool = False) -> None:
        self.fail_prime = fail_prime
        self.calls: list[list[str]] = []

    def run(self, argv, *, env=None):
        args = list(argv)
        self.calls.append(args)
        if args[-2:] == ["status", "--json"]:
            return json.dumps(
                {
                    "controller": {"pid": 42},
                    "rigs": [
                        {"name": "gascity", "suspended": True},
                        {"name": "hpfetcher", "suspended": True},
                        {"name": "blog", "suspended": True},
                    ],
                    "summary": {"running_agents": 0},
                }
            )
        if "--provider" in args:
            return json.dumps(
                {
                    "resolved": {
                        "option_defaults": {
                            "effort": "xhigh",
                            "model": "gpt-5.6-sol",
                            "permission_mode": "fail-fast",
                            "worklog_access": "isolated-workspace",
                        },
                        "resume_command": (
                            "/managed/codex resume --sandbox workspace-write -c "
                            "'sandbox_workspace_write.writable_roots=[]' {{.SessionKey}}"
                        ),
                    }
                }
            )
        if "--agent" in args:
            return "\n".join(
                (
                    "work_dir                       = /home/loucmane/gascity/evidence-runs",
                    "provider                       = codex-evidence",
                    "max_active_sessions            = 1",
                )
            )
        if "prime" in args:
            if self.fail_prime:
                raise module.InstallError("fixture prompt failure")
            return (
                "Read only those declared bundle files.\n"
                "Do not inspect a project checkout, Git metadata, another lane.\n"
                "Write only the declared report file.\n"
            )
        return ""


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    city = tmp_path / "city"
    city.mkdir()
    (city / "agents").mkdir()
    (city / "city.toml").write_bytes(BASE_CITY)
    (city / ".gc").mkdir()
    gc = tmp_path / "gc"
    gc.write_text("fixture\n", encoding="utf-8")
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    codex_config = codex_home / "config.toml"
    codex_config.write_bytes(BASE_CODEX)
    codex_config.chmod(0o600)
    evidence_root = tmp_path / "evidence-runs"
    evidence_root.mkdir()
    assets = REPO_ROOT / "plugins" / "gas-city-workflow" / "config" / "evidence-reviewer"
    monkeypatch.setattr(module, "DEFAULT_CITY", city.resolve())
    monkeypatch.setattr(module, "DEFAULT_GC", gc.resolve())
    monkeypatch.setattr(module, "DEFAULT_CODEX_CONFIG", codex_config.resolve())
    monkeypatch.setattr(module, "DEFAULT_EVIDENCE_ROOT", evidence_root.resolve())
    monkeypatch.setattr(module, "ASSET_ROOT", assets)
    return city, gc, codex_config, evidence_root


def _install_existing_assets(city: Path) -> bytes:
    source = module.ASSET_ROOT
    rendered = module.render_city_config(
        BASE_CITY, (source / "provider.toml").read_bytes()
    )
    (city / "city.toml").write_bytes(rendered)
    agent = city / "agents/evidence-reviewer"
    agent.mkdir()
    for name in ("agent.toml", "prompt.template.md"):
        (agent / name).write_bytes((source / name).read_bytes())
    return rendered


def test_assets_define_one_report_only_non_project_lane() -> None:
    assets = REPO_ROOT / "plugins" / "gas-city-workflow" / "config" / "evidence-reviewer"
    provider = tomllib.loads((assets / "provider.toml").read_text(encoding="utf-8"))
    agent = tomllib.loads((assets / "agent.toml").read_text(encoding="utf-8"))
    prompt = (assets / "prompt.template.md").read_text(encoding="utf-8")

    evidence = provider["providers"]["codex-evidence"]
    assert evidence["base"] == "provider:codex"
    assert evidence["option_defaults"]["worklog_access"] == "isolated-workspace"
    choice = evidence["options_schema"][0]["choices"][0]
    assert choice["flag_args"][-1] == "sandbox_workspace_write.writable_roots=[]"
    assert agent["provider"] == "codex-evidence"
    assert agent["scope"] == "rig"
    assert agent["work_dir"] == "/home/loucmane/gascity/evidence-runs"
    assert agent["max_active_sessions"] == 1
    assert "Do not inspect a project checkout, Git metadata" in prompt
    assert "Write only the declared report file" in prompt
    assert "Never repair project content" in prompt


def test_install_applies_exact_assets_and_preserves_controller_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, evidence_root = _fixture(tmp_path, monkeypatch)
    runner = FakeRunner()

    result = module.install(city, gc, apply=True, runner=runner)

    assert result["status"] == "pass"
    rendered = tomllib.loads((city / "city.toml").read_text(encoding="utf-8"))
    assert rendered["providers"]["codex-evidence"]["base"] == "provider:codex"
    source = module.ASSET_ROOT
    assert (city / "agents/evidence-reviewer/agent.toml").read_bytes() == (
        source / "agent.toml"
    ).read_bytes()
    assert (city / "agents/evidence-reviewer/prompt.template.md").read_bytes() == (
        source / "prompt.template.md"
    ).read_bytes()
    codex = tomllib.loads(codex_config.read_text(encoding="utf-8"))
    assert codex["projects"][evidence_root.as_posix()] == {"trust_level": "trusted"}
    assert codex_config.read_bytes().startswith(BASE_CODEX)
    assert stat.S_IMODE(codex_config.stat().st_mode) == 0o600
    assert any(call[-1:] == ["reload"] for call in runner.calls)
    evidence = Path(result["evidence"])
    assert (evidence / "city.toml.before").read_bytes() == BASE_CITY
    assert (evidence / "codex-config.toml.before").read_bytes() == BASE_CODEX
    assert json.loads((evidence / "result.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_append_forward_trust_repair_preserves_exact_installed_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, evidence_root = _fixture(tmp_path, monkeypatch)
    live_city = _install_existing_assets(city)
    runner = FakeRunner()

    result = module.install(city, gc, apply=True, runner=runner)

    assert result["status"] == "pass"
    assert result["operation"] == "trust-repair"
    assert result["agent_state"] == "exact"
    assert (city / "city.toml").read_bytes() == live_city
    for name in ("agent.toml", "prompt.template.md"):
        assert (city / "agents/evidence-reviewer" / name).read_bytes() == (
            module.ASSET_ROOT / name
        ).read_bytes()
    assert not any(call[-1:] == ["reload"] for call in runner.calls)
    parsed = tomllib.loads(codex_config.read_text(encoding="utf-8"))
    assert parsed["projects"][evidence_root.as_posix()] == {"trust_level": "trusted"}
    assert codex_config.read_bytes().startswith(BASE_CODEX)
    unmanaged, managed = module._strip_trust_block(codex_config.read_text(encoding="utf-8"))
    assert unmanaged.encode() == BASE_CODEX
    assert managed is not None


def test_append_forward_validation_failure_restores_only_codex_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, _ = _fixture(tmp_path, monkeypatch)
    live_city = _install_existing_assets(city)
    runner = FakeRunner(fail_prime=True)

    with pytest.raises(module.InstallError, match="fixture prompt failure"):
        module.install(city, gc, apply=True, runner=runner)

    assert codex_config.read_bytes() == BASE_CODEX
    assert (city / "city.toml").read_bytes() == live_city
    assert not any(call[-1:] == ["reload"] for call in runner.calls)


def test_post_mutation_validation_failure_restores_exact_prior_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, _ = _fixture(tmp_path, monkeypatch)
    runner = FakeRunner(fail_prime=True)

    with pytest.raises(module.InstallError, match="fixture prompt failure"):
        module.install(city, gc, apply=True, runner=runner)

    assert (city / "city.toml").read_bytes() == BASE_CITY
    assert not (city / "agents/evidence-reviewer").exists()
    assert codex_config.read_bytes() == BASE_CODEX
    assert stat.S_IMODE(codex_config.stat().st_mode) == 0o600
    assert any(call[-1:] == ["reload"] for call in runner.calls)
    evidence_roots = list((city / ".gc/gas-city-workflow/evidence-reviewer-install").iterdir())
    assert len(evidence_roots) == 1
    assert (evidence_roots[0] / "city.toml.before").read_bytes() == BASE_CITY
    assert (evidence_roots[0] / "codex-config.toml.before").read_bytes() == BASE_CODEX


def test_conflicting_or_aliased_trust_fails_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, evidence_root = _fixture(tmp_path, monkeypatch)
    conflict = (
        BASE_CODEX
        + f'\n[projects.{json.dumps(evidence_root.as_posix())}]\ntrust_level = "untrusted"\n'.encode()
    )
    codex_config.write_bytes(conflict)
    runner = FakeRunner()

    with pytest.raises(module.InstallError, match="conflicting exact"):
        module.install(city, gc, apply=True, runner=runner)

    assert codex_config.read_bytes() == conflict
    assert (city / "city.toml").read_bytes() == BASE_CITY
    assert runner.calls == []

    alias = evidence_root.parent / "evidence-runs-alias"
    alias.symlink_to(evidence_root, target_is_directory=True)
    alias_config = (
        BASE_CODEX
        + f'\n[projects.{json.dumps(alias.as_posix())}]\ntrust_level = "trusted"\n'.encode()
    )
    codex_config.write_bytes(alias_config)
    with pytest.raises(module.InstallError, match="alias"):
        module.install(city, gc, apply=True, runner=runner)

    assert codex_config.read_bytes() == alias_config
    assert runner.calls == []


def test_malformed_managed_trust_markers_fail_closed(tmp_path: Path) -> None:
    evidence_root = tmp_path / "evidence-runs"
    evidence_root.mkdir()
    malformed = BASE_CODEX + f"\n{module.TRUST_BEGIN}\n".encode()

    with pytest.raises(module.InstallError, match="malformed or duplicate"):
        module.render_codex_config(malformed, evidence_root)


def test_managed_trust_is_idempotent_and_refuses_owned_block_drift(tmp_path: Path) -> None:
    evidence_root = tmp_path / "evidence-runs"
    evidence_root.mkdir()
    rendered = module.render_codex_config(BASE_CODEX, evidence_root)

    assert module.render_codex_config(rendered, evidence_root) == rendered

    drifted = rendered.replace(
        module.TRUST_END.encode(),
        b'model = "unexpected"\n' + module.TRUST_END.encode(),
    )
    with pytest.raises(module.InstallError, match="managed evidence-root trust block drifted"):
        module.render_codex_config(drifted, evidence_root)
