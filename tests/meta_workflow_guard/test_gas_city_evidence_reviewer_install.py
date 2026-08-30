"""Tests for the bounded report-only evidence reviewer installation."""

from __future__ import annotations

import importlib.util
import json
import stat
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "plugins" / "gas-city-workflow" / "scripts" / "install_evidence_reviewer.py"
SPEC = importlib.util.spec_from_file_location("install_evidence_reviewer", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

import codex_hook_trust as hook_trust  # noqa: E402 - installer adds its sibling path.


BASE_CITY = b"""[providers]\n[providers.codex]\nbase = "builtin:codex"\noptions_schema_merge = "by_key"\ncommand = "/home/loucmane/gascity/bin/codex"\n\n[providers.codex.option_defaults]\neffort = "xhigh"\nmodel = "gpt-5.6-sol"\npermission_mode = "fail-fast"\nworklog_access = "classified-vault"\n\n[[providers.codex.options_schema]]\nkey = "permission_mode"\nlabel = "Approval policy"\ntype = "select"\ndefault = "fail-fast"\n"""
BASE_CODEX = b"""model = "gpt-5.6-sol"\n# unrelated bytes must survive exactly\n[projects."/home/loucmane/codex"]\ntrust_level = "trusted"\n"""
HOOK_HASHES = (
    "sha256:be269fe192c78932511fc8dc9ca2923a54cccfd311f5c4b8d9ceefcc41f6eb5a",
    "sha256:2486542babf8bd579a8794a2cb485cb0890cc76b4c79b1429270c50b20d92cee",
    "sha256:6c9160f292219bf7be62995f0fb8cf8b908b0c71c075ec7deb49acdf18a714e2",
    "sha256:10af9755784226e1d594b67b42d2b70391eeae4021b676d54992fe7dd43b8549",
)


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


def _hook_manifest_bytes() -> bytes:
    payload = {
        "hooks": {
            "PreCompact": [
                {
                    "hooks": [
                        {"command": hook_trust.EXPECTED_HOOKS[0]["command"], "type": "command"}
                    ],
                    "matcher": "",
                }
            ],
            "SessionStart": [
                {
                    "hooks": [
                        {"command": hook_trust.EXPECTED_HOOKS[1]["command"], "type": "command"}
                    ],
                    "matcher": "startup",
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {"command": hook_trust.EXPECTED_HOOKS[2]["command"], "type": "command"},
                        {"command": hook_trust.EXPECTED_HOOKS[3]["command"], "type": "command"},
                    ],
                    "matcher": "",
                }
            ],
        }
    }
    return (json.dumps(payload, indent=2) + "\n").encode()


def _fake_hook_truster(codex: Path, config: Path, evidence_root: Path):
    assert codex == module.DEFAULT_CODEX
    hooks_path = evidence_root / ".codex/hooks.json"
    keys = hook_trust._expected_hook_keys(hooks_path)
    before = config.read_bytes()
    base, _ = hook_trust._strip_hook_trust_tables(before, keys)
    rendered = base
    for key, current_hash in zip(keys, HOOK_HASHES, strict=True):
        if rendered and not rendered.endswith(b"\n"):
            rendered += b"\n"
        rendered += (
            f'\n[hooks.state.{json.dumps(key)}]\ntrusted_hash = "{current_hash}"\n'
        ).encode()
    module._atomic_write(config, rendered, stat.S_IMODE(config.stat().st_mode))
    after = [
        {"key": key, "current_hash": current_hash, "trust_status": "trusted"}
        for key, current_hash in zip(keys, HOOK_HASHES, strict=True)
    ]
    return {
        "manifest": hooks_path.as_posix(),
        "manifest_sha256": hook_trust.EVIDENCE_HOOKS_SHA256,
        "before": [dict(item, trust_status="untrusted") for item in after],
        "after": after,
        "config_write_version": "sha256:" + "a" * 64,
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    city = tmp_path / "city"
    city.mkdir()
    (city / "agents").mkdir()
    (city / "city.toml").write_bytes(BASE_CITY)
    (city / ".gc").mkdir()
    gc = tmp_path / "gc"
    gc.write_text("fixture\n", encoding="utf-8")
    codex = tmp_path / "codex"
    codex.write_text("fixture\n", encoding="utf-8")
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    codex_config = codex_home / "config.toml"
    codex_config.write_bytes(BASE_CODEX)
    codex_config.chmod(0o600)
    evidence_root = tmp_path / "evidence-runs"
    evidence_root.mkdir()
    (evidence_root / ".codex").mkdir()
    (evidence_root / ".codex/hooks.json").write_bytes(_hook_manifest_bytes())
    assets = REPO_ROOT / "plugins" / "gas-city-workflow" / "config" / "evidence-reviewer"
    monkeypatch.setattr(module, "DEFAULT_CITY", city.resolve())
    monkeypatch.setattr(module, "DEFAULT_GC", gc.resolve())
    monkeypatch.setattr(module, "DEFAULT_CODEX", codex.resolve())
    monkeypatch.setattr(module, "DEFAULT_CODEX_CONFIG", codex_config.resolve())
    monkeypatch.setattr(module, "DEFAULT_EVIDENCE_ROOT", evidence_root.resolve())
    monkeypatch.setattr(module, "ASSET_ROOT", assets)
    monkeypatch.setattr(module, "trust_codex_hooks", _fake_hook_truster)
    return city, gc, codex_config, evidence_root


def _install_existing_assets(city: Path) -> bytes:
    source = module.ASSET_ROOT
    rendered = module.render_city_config(BASE_CITY, (source / "provider.toml").read_bytes())
    (city / "city.toml").write_bytes(rendered)
    agent = city / "agents/evidence-reviewer"
    agent.mkdir()
    for name in ("agent.toml", "prompt.template.md"):
        (agent / name).write_bytes((source / name).read_bytes())
    return rendered


def _assert_exact_hook_trust(config: Path, evidence_root: Path) -> None:
    parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    state = parsed["hooks"]["state"]
    keys = hook_trust._expected_hook_keys(evidence_root / ".codex/hooks.json")
    assert {key: state[key]["trusted_hash"] for key in keys} == dict(
        zip(keys, HOOK_HASHES, strict=True)
    )


def _hook_listing(evidence_root: Path, *, status: str = "untrusted") -> dict:
    hooks_path = evidence_root / ".codex/hooks.json"
    hooks = []
    for order, (expected, current_hash) in enumerate(
        zip(hook_trust.EXPECTED_HOOKS, HOOK_HASHES, strict=True)
    ):
        hooks.append(
            {
                "key": f"{hooks_path}:{expected['key_suffix']}",
                "eventName": expected["eventName"],
                "handlerType": "command",
                "command": expected["command"],
                "async": False,
                "matcher": expected["matcher"],
                "timeoutSec": 600,
                "sourcePath": hooks_path.as_posix(),
                "source": "project",
                "pluginId": None,
                "displayOrder": order,
                "enabled": True,
                "isManaged": False,
                "currentHash": current_hash,
                "trustStatus": status,
            }
        )
    return {
        "data": [
            {
                "cwd": evidence_root.as_posix(),
                "hooks": hooks,
                "warnings": [],
                "errors": [],
            }
        ]
    }


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
    _assert_exact_hook_trust(codex_config, evidence_root)
    assert codex_config.read_bytes().startswith(BASE_CODEX)
    assert stat.S_IMODE(codex_config.stat().st_mode) == 0o600
    assert any(call[-1:] == ["reload"] for call in runner.calls)
    evidence = Path(result["evidence"])
    assert (evidence / "city.toml.before").read_bytes() == BASE_CITY
    assert (evidence / "codex-config.toml.before").read_bytes() == BASE_CODEX
    assert (evidence / "codex-config.toml.after").read_bytes() == codex_config.read_bytes()
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
    _assert_exact_hook_trust(codex_config, evidence_root)
    assert codex_config.read_bytes().startswith(BASE_CODEX)
    unmanaged, managed = module._strip_trust_block(codex_config.read_text(encoding="utf-8"))
    stripped, found = hook_trust._strip_hook_trust_tables(
        unmanaged.encode(),
        hook_trust._expected_hook_keys(evidence_root / ".codex/hooks.json"),
    )
    assert stripped == BASE_CODEX
    assert len(found) == 4
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


def test_hook_manifest_and_runtime_listing_are_exactly_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, evidence_root = _fixture(tmp_path, monkeypatch)
    listing = _hook_listing(evidence_root)

    validated = hook_trust._validate_hook_listing(
        listing, evidence_root, allowed_trust={"untrusted"}
    )

    assert len(validated) == 4
    assert {item["current_hash"] for item in validated} == set(HOOK_HASHES)

    listing["data"][0]["hooks"][2]["command"] += " --unexpected"
    with pytest.raises(module.InstallError, match="metadata drifted"):
        hook_trust._validate_hook_listing(listing, evidence_root, allowed_trust={"untrusted"})


def test_hook_listing_rejects_extra_hook_wrong_source_and_untrusted_post_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, evidence_root = _fixture(tmp_path, monkeypatch)
    extra = _hook_listing(evidence_root)
    extra["data"][0]["hooks"].append(dict(extra["data"][0]["hooks"][0]))
    with pytest.raises(module.InstallError, match="exactly four"):
        hook_trust._validate_hook_listing(extra, evidence_root, allowed_trust={"untrusted"})

    wrong_source = _hook_listing(evidence_root)
    wrong_source["data"][0]["hooks"][0]["source"] = "user"
    with pytest.raises(module.InstallError, match="metadata drifted"):
        hook_trust._validate_hook_listing(wrong_source, evidence_root, allowed_trust={"untrusted"})

    with pytest.raises(module.InstallError, match="trust state is invalid"):
        hook_trust._validate_hook_listing(
            _hook_listing(evidence_root), evidence_root, allowed_trust={"trusted"}
        )


def test_hook_manifest_drift_fails_before_city_or_config_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, gc, codex_config, evidence_root = _fixture(tmp_path, monkeypatch)
    (evidence_root / ".codex/hooks.json").write_text(
        '{"hooks":{"PreCompact":[]}}\n', encoding="utf-8"
    )
    runner = FakeRunner()

    with pytest.raises(module.InstallError, match="manifest drifted"):
        module.install(city, gc, apply=True, runner=runner)

    assert (city / "city.toml").read_bytes() == BASE_CITY
    assert codex_config.read_bytes() == BASE_CODEX
    assert runner.calls == []


def test_hook_trust_table_isolation_is_byte_exact() -> None:
    keys = ["/exact/a:0", "/exact/b:0"]
    before = BASE_CODEX
    after = (
        before
        + (
            f'\n[hooks.state.{json.dumps(keys[0])}]\ntrusted_hash = "sha256:{"a" * 64}"\n'
            f'\n[hooks.state.{json.dumps(keys[1])}]\ntrusted_hash = "sha256:{"b" * 64}"\n'
        ).encode()
    )

    stripped_before, before_found = hook_trust._strip_hook_trust_tables(before, keys)
    stripped_after, after_found = hook_trust._strip_hook_trust_tables(after, keys)

    assert stripped_before == stripped_after == before
    assert before_found == set()
    assert after_found == set(keys)
    assert hook_trust._only_blank_line_changes(b"alpha\n\nbeta\n", b"alpha\nbeta\n")
    assert not hook_trust._only_blank_line_changes(b"alpha\nbeta\n", b"alpha\ngamma\n")


def test_user_config_version_requires_the_exact_config_layer(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    payload = {
        "layers": [
            {
                "name": {"type": "user", "file": config.as_posix(), "profile": None},
                "version": "sha256:" + "c" * 64,
            }
        ]
    }

    assert hook_trust._user_config_version(payload, config) == "sha256:" + "c" * 64
    payload["layers"][0]["name"]["file"] = "/wrong/config.toml"
    with pytest.raises(module.InstallError, match="exact user config layer"):
        hook_trust._user_config_version(payload, config)
