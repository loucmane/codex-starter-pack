from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
BROKER = ROOT / "deploy/gas-city/bin/github-app-token-broker"
NOW = dt.datetime(2026, 7, 16, 12, tzinfo=dt.timezone.utc)


def _module():
    loader = importlib.machinery.SourceFileLoader("github_app_token_broker_test", str(BROKER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _private(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    return path


def _rules() -> list[dict[str, object]]:
    return [
        {"type": "deletion", "ruleset_id": 42},
        {"type": "non_fast_forward", "ruleset_id": 42},
        {
            "type": "pull_request",
            "ruleset_id": 42,
            "parameters": {"required_approving_review_count": 0},
        },
        {
            "type": "required_status_checks",
            "ruleset_id": 42,
            "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [{"context": "test"}],
            },
        },
    ]


def _token_response(module, **updates):
    value = {
        "token": "ghs_" + "t" * 64,
        "expires_at": (NOW + dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "permissions": dict(module.REQUIRED_PERMISSIONS),
        "repositories": [
            {
                "id": 12345,
                "full_name": "loucmane/codex-starter-pack",
                "default_branch": "main",
            }
        ],
    }
    value.update(updates)
    return value


def _arguments(tmp_path: Path) -> SimpleNamespace:
    parent = tmp_path / "state"
    parent.mkdir(mode=0o700)
    parent.chmod(0o700)
    return SimpleNamespace(
        action="issue",
        state_dir=str(parent / "delivery"),
        repository="loucmane/codex-starter-pack",
        default_branch="main",
        app_id_file=str(_private(tmp_path / "secrets/app-id", "1001\n")),
        installation_id_file=str(
            _private(tmp_path / "secrets/installation-id", "2002\n")
        ),
        private_key_file=str(_private(tmp_path / "secrets/private-key.pem", "PRIVATE\n")),
    )


def _install_api(module, monkeypatch, token_response, *, rules=None, ruleset=None):
    observed: list[tuple[str, str, str, object]] = []
    effective = _rules() if rules is None else rules
    detail = (
        {"id": 42, "enforcement": "active", "bypass_actors": []}
        if ruleset is None
        else ruleset
    )

    def request(method, endpoint, *, token, body=None):
        observed.append((method, endpoint, token, body))
        if endpoint.endswith("/access_tokens"):
            value = token_response
        elif "/rules/branches/" in endpoint:
            value = effective
        elif endpoint.endswith("/rulesets/42"):
            value = detail
        else:  # pragma: no cover - an unexpected network shape must be visible.
            raise AssertionError(endpoint)
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        return raw, value

    monkeypatch.setattr(module, "_request_json", request)
    monkeypatch.setattr(module, "_jwt", lambda app_id, private_key, now: "signed.jwt")
    monkeypatch.setattr(module, "_now", lambda: NOW)
    return observed


def test_broker_issues_one_short_lived_scoped_token_without_printing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    token_response = _token_response(module)
    observed = _install_api(module, monkeypatch, token_response)
    result = module.issue(_arguments(tmp_path))

    token_path = Path(result["token_path"])
    receipt_path = Path(result["receipt_path"])
    assert token_path.read_text() == token_response["token"] + "\n"
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o400
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o400
    receipt = json.loads(receipt_path.read_text())
    assert token_response["token"] not in receipt_path.read_text()
    assert token_response["token"] not in json.dumps(result)
    assert receipt["permissions"] == module.REQUIRED_PERMISSIONS
    assert receipt["repository"] == {
        "id": 12345,
        "name_with_owner": "loucmane/codex-starter-pack",
        "default_branch": "main",
    }
    assert receipt["effective_rule_types"] == sorted(
        {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}
    )
    assert observed[0][3] == {
        "repositories": ["codex-starter-pack"],
        "permissions": module.REQUIRED_PERMISSIONS,
    }
    assert all(item[2] != token_response["token"] for item in observed[:1])
    assert all(item[2] == token_response["token"] for item in observed[1:])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda module, token: token.update(
                {"permissions": {**module.REQUIRED_PERMISSIONS, "administration": "write"}}
            ),
            "exact delivery contract",
        ),
        (
            lambda _module, token: token["repositories"].append(
                {"id": 9, "full_name": "loucmane/other", "default_branch": "main"}
            ),
            "exact delivery contract",
        ),
    ],
)
def test_broker_rejects_broader_tokens(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    message: str,
) -> None:
    module = _module()
    token = _token_response(module)
    mutation(module, token)
    _install_api(module, monkeypatch, token)
    with pytest.raises(module.BrokerError, match=message):
        module.issue(_arguments(tmp_path))


def test_broker_rejects_weak_or_bypassable_default_branch_rules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    weak = [rule for rule in _rules() if rule["type"] != "required_status_checks"]
    _install_api(module, monkeypatch, _token_response(module), rules=weak)
    with pytest.raises(module.BrokerError, match="missing required rules"):
        module.issue(_arguments(tmp_path))

    second = tmp_path / "second"
    second.mkdir()
    _install_api(
        module,
        monkeypatch,
        _token_response(module),
        ruleset={
            "id": 42,
            "enforcement": "active",
            "bypass_actors": [{"actor_id": 1001, "actor_type": "Integration"}],
        },
    )
    with pytest.raises(module.BrokerError, match="inactive or bypassable"):
        module.issue(_arguments(second))


def test_broker_refuses_reuse_and_unsafe_secret_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    _install_api(module, monkeypatch, _token_response(module))
    arguments = _arguments(tmp_path)
    module.issue(arguments)
    with pytest.raises(module.BrokerError, match="not empty"):
        module.issue(arguments)

    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    unsafe_arguments = _arguments(unsafe)
    Path(unsafe_arguments.private_key_file).chmod(0o644)
    with pytest.raises(module.BrokerError, match="unsafe file metadata"):
        module.issue(unsafe_arguments)
