"""Tests for the bounded report-only evidence reviewer installation."""

from __future__ import annotations

import importlib.util
import json
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
    assets = REPO_ROOT / "plugins" / "gas-city-workflow" / "config" / "evidence-reviewer"
    monkeypatch.setattr(module, "DEFAULT_CITY", city.resolve())
    monkeypatch.setattr(module, "DEFAULT_GC", gc.resolve())
    monkeypatch.setattr(module, "ASSET_ROOT", assets)
    return city, gc


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
    city, gc = _fixture(tmp_path, monkeypatch)
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
    assert any(call[-1:] == ["reload"] for call in runner.calls)
    evidence = Path(result["evidence"])
    assert (evidence / "city.toml.before").read_bytes() == BASE_CITY
    assert json.loads((evidence / "result.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_post_mutation_validation_failure_restores_exact_prior_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc = _fixture(tmp_path, monkeypatch)
    runner = FakeRunner(fail_prime=True)

    with pytest.raises(module.InstallError, match="fixture prompt failure"):
        module.install(city, gc, apply=True, runner=runner)

    assert (city / "city.toml").read_bytes() == BASE_CITY
    assert not (city / "agents/evidence-reviewer").exists()
    assert any(call[-1:] == ["reload"] for call in runner.calls)
    evidence_roots = list((city / ".gc/gas-city-workflow/evidence-reviewer-install").iterdir())
    assert len(evidence_roots) == 1
    assert (evidence_roots[0] / "city.toml.before").read_bytes() == BASE_CITY
