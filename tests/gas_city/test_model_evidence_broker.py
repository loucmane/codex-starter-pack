from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import types

import pytest


ROOT = Path(__file__).resolve().parents[2]
BROKER = ROOT / "deploy/gas-city/bin/model-evidence-broker"
SUPERVISOR = ROOT / "deploy/gas-city/docker/provider-supervisor.py"
CLAUDE = ROOT / "deploy/gas-city/artifacts/claude"
CODEX = ROOT / "deploy/gas-city/artifacts/codex/bin/codex"
LAUNCHER = ROOT / "deploy/gas-city/bin/provider-container"


def _broker_module():
    loader = importlib.machinery.SourceFileLoader(
        "gas_city_model_evidence_broker_test", str(BROKER)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _supervisor_module():
    spec = importlib.util.spec_from_file_location(
        "gas_city_model_preflight_test", SUPERVISOR
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def _write_json(path: Path, value: dict[str, object], mode: int) -> bytes:
    content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    path.write_bytes(content)
    path.chmod(mode)
    return content


def _model_fixture(
    tmp_path: Path, module, *, provider: str = "claude"
) -> tuple[Path, Path]:
    root = _private_directory(tmp_path / "runtime")
    git_state = _private_directory(root / "git-session")
    session_sha = hashlib.sha256(b"session-1").hexdigest()
    _write_json(
        git_state / "baseline.json",
        {
            "schema_version": 1,
            "kind": "aegis-private-git-baseline",
            "status": "frozen",
            "broker_id": "broker-1",
            "broker_receipt_sha256": "a" * 64,
            "session_id_sha256": session_sha,
            "startup_receipt_sha256": "b" * 64,
            "authorized_ref": "refs/heads/polecat/ags-work",
            "source": {"starting_oid": "c" * 40},
        },
        0o600,
    )
    state = git_state / "model-evidence"
    module.begin_run(
        argparse.Namespace(
            state_dir=str(state),
            git_state_dir=str(git_state),
            provider=provider,
            session_id="session-1",
            run_id="run-1",
            preflight_container="preflight-one",
            session_container="session-one",
            image_id="sha256:" + "a" * 64,
        )
    )
    return git_state, state


def _payload(
    phase: str, challenge: str, *, provider: str = "claude"
) -> dict[str, object]:
    model, effort = {
        "claude": ("claude-fable-5", None),
        "codex": ("gpt-5.6-sol", "xhigh"),
    }[provider]
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": "supervisor-model-evidence",
        "phase": phase,
        "provider": provider,
        "challenge": challenge,
        "provider_exit_code": 0,
        "transcript_sha256": "e" * 64,
        "transcript_locator": (
            (
                "in-memory:claude-stream-json"
                if provider == "claude"
                else "in-memory:codex-exec-jsonl+server-model-log"
            )
            if phase == "preflight"
            else f"/home/worker/.{provider}/sessions/session.jsonl"
        ),
        "tool_free": phase == "preflight",
    }
    if phase == "preflight":
        payload.update(
            {
                "expected_model": model,
                "expected_effort": effort,
                "observed_model": model,
                "observed_effort": effort,
                "event_sha256": "d" * 64,
            }
        )
    return payload


def _identity() -> dict[str, int]:
    return {
        "container_init_host_pid": 100,
        "supervisor_host_pid": 101,
        "supervisor_host_uid": os.geteuid(),
        "supervisor_host_gid": os.getegid(),
        "supervisor_starttime_ticks": 200,
    }


def _record_phase(module, state: Path, phase: str) -> dict[str, object]:
    baseline, content = module._load_baseline(state)
    challenge = "f" * 64
    payload = _payload(phase, challenge, provider=baseline["provider"])
    module._validate_payload(payload, baseline, phase, challenge)
    return module._record_payload(
        state=state,
        baseline=baseline,
        baseline_content=content,
        phase=phase,
        payload=payload,
        challenge=challenge,
        identity=_identity(),
    )


def test_host_receipts_bind_preflight_session_and_are_idempotent(tmp_path: Path) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module)

    preflight = _record_phase(module, state, "preflight")
    session = _record_phase(module, state, "session")
    baseline, _ = module._load_baseline(state)

    assert baseline["status"] == "evidence_recorded"
    assert session["preflight_receipt_sha256"] == hashlib.sha256(
        (state / "preflight-receipt.json").read_bytes()
    ).hexdigest()
    assert preflight["tool_free"] is True
    assert session["tool_free"] is False
    assert session["model_source_phase"] == "preflight"
    assert session["model_attestation_scope"] == (
        "isolated-zero-tool-invocation-preflight-gates-session"
    )
    assert session["event_sha256"] == preflight["event_sha256"] == "d" * 64
    # A repeated receiver invocation returns the exact completed host receipt;
    # it does not reopen a socket or create a second attestation.
    repeated = module.receive(
        argparse.Namespace(
            state_dir=str(state),
            phase="session",
            accept_timeout=1,
            timeout=1,
        )
    )
    assert repeated == session


def test_codex_host_receipts_bind_sol_xhigh_and_server_model_log(tmp_path: Path) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module, provider="codex")
    preflight = _record_phase(module, state, "preflight")
    session = _record_phase(module, state, "session")
    assert preflight["provider"] == "codex"
    assert preflight["expected_model"] == "gpt-5.6-sol"
    assert preflight["observed_model"] == "gpt-5.6-sol"
    assert preflight["expected_effort"] == "xhigh"
    assert preflight["observed_effort"] == "xhigh"
    assert preflight["transcript_locator"] == (
        "in-memory:codex-exec-jsonl+server-model-log"
    )
    assert session["preflight_receipt_sha256"] == hashlib.sha256(
        (state / "preflight-receipt.json").read_bytes()
    ).hexdigest()


def test_session_wire_payload_cannot_make_a_positive_model_claim(tmp_path: Path) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module)
    _record_phase(module, state, "preflight")
    baseline, _ = module._load_baseline(state)
    challenge = "f" * 64
    payload = _payload("session", challenge)
    payload["observed_model"] = "claude-fable-5"

    with pytest.raises(module.EvidenceError, match="frozen host run"):
        module._validate_payload(payload, baseline, "session", challenge)


def test_changed_model_attestation_scope_is_fail_closed(tmp_path: Path) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module)
    baseline_path = state / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["model_attestation_scope"] = "authority-session-model-verified"
    _write_json(baseline_path, baseline, 0o600)

    with pytest.raises(module.EvidenceError, match="protocol identity"):
        module._load_baseline(state)


def test_changed_receipt_model_attestation_scope_is_fail_closed(tmp_path: Path) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module)
    _record_phase(module, state, "preflight")
    baseline, _ = module._load_baseline(state)
    receipt_path = state / "preflight-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["model_attestation_scope"] = "authority-session-model-verified"

    with pytest.raises(module.EvidenceError, match="stale|run baseline"):
        module._validate_receipt(receipt, baseline, "preflight")


def test_old_generation_receipt_cannot_be_replayed(tmp_path: Path) -> None:
    module = _broker_module()
    git_state, state = _model_fixture(tmp_path, module)
    old = _record_phase(module, state, "preflight")
    old_content = (state / "preflight-receipt.json").read_bytes()

    with pytest.raises(module.EvidenceError, match="already has a model run"):
        module.begin_run(
            argparse.Namespace(
                state_dir=str(state),
                git_state_dir=str(git_state),
                provider="claude",
                session_id="session-1",
                run_id="duplicate-run",
                preflight_container="preflight-duplicate",
                session_container="session-duplicate",
                image_id="sha256:" + "a" * 64,
            )
        )

    # A new run requires a newly frozen Git generation, as a real preserved
    # retry would produce.  Reusing the identical frozen authorization is
    # rejected before any receipt can be superseded.
    git_path = git_state / "baseline.json"
    git_value = json.loads(git_path.read_text(encoding="utf-8"))
    git_value["retry_count"] = 1
    _write_json(git_path, git_value, 0o600)

    module.begin_run(
        argparse.Namespace(
            state_dir=str(state),
            git_state_dir=str(git_state),
            provider="claude",
            session_id="session-1",
            run_id="run-2",
            preflight_container="preflight-two",
            session_container="session-two",
            image_id="sha256:" + "a" * 64,
        )
    )
    assert old["run_generation"] == 1
    (state / "preflight-receipt.json").write_bytes(old_content)
    (state / "preflight-receipt.json").chmod(0o400)
    with pytest.raises(module.EvidenceError, match="stale|run baseline"):
        module.receive(
            argparse.Namespace(
                state_dir=str(state),
                phase="preflight",
                accept_timeout=1,
                timeout=1,
            )
        )


def test_receipt_first_crash_is_recovered_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _broker_module()
    _, state = _model_fixture(tmp_path, module)
    baseline, content = module._load_baseline(state)
    challenge = "f" * 64
    payload = _payload("preflight", challenge)
    original_atomic_write = module._atomic_write
    failed = False

    def crash_between_receipt_and_baseline(path: Path, data: bytes, mode: int) -> None:
        nonlocal failed
        if path.name == "baseline.json" and not failed:
            failed = True
            raise module.EvidenceError("simulated host crash")
        original_atomic_write(path, data, mode)

    monkeypatch.setattr(module, "_atomic_write", crash_between_receipt_and_baseline)
    with pytest.raises(module.EvidenceError, match="simulated host crash"):
        module._record_payload(
            state=state,
            baseline=baseline,
            baseline_content=content,
            phase="preflight",
            payload=payload,
            challenge=challenge,
            identity=_identity(),
        )
    assert (state / "preflight-receipt.json").is_file()
    assert module._load_baseline(state)[0]["status"] == "awaiting_preflight"

    monkeypatch.setattr(module, "_atomic_write", original_atomic_write)
    recovered = module.receive(
        argparse.Namespace(
            state_dir=str(state),
            phase="preflight",
            accept_timeout=1,
            timeout=1,
        )
    )
    assert recovered["status"] == "verified"
    assert module._load_baseline(state)[0]["status"] == "awaiting_session"


def _proc_stat(pid: int, parent: int, started: int) -> str:
    fields = ["S", str(parent), *("0" for _ in range(17)), str(started)]
    return f"{pid} (python3) {' '.join(fields)}\n"


def _fake_process(
    proc: Path,
    interpreter: Path,
    *,
    pid: int,
    parent: int,
    started: int,
    argv: list[str],
) -> None:
    root = _private_directory(proc / str(pid))
    (root / "stat").write_text(_proc_stat(pid, parent, started), encoding="utf-8")
    (root / "cmdline").write_bytes(b"\0".join(item.encode() for item in argv) + b"\0")
    image_bin = root / "root/usr/bin"
    image_bin.mkdir(parents=True)
    os.link(interpreter, image_bin / "python3")
    os.link(interpreter, root / "exe")


def test_peer_binding_rejects_forged_writer_and_same_uid_provider(tmp_path: Path) -> None:
    module = _broker_module()
    proc = _private_directory(tmp_path / "proc")
    interpreter = tmp_path / "python3"
    interpreter.write_bytes(b"pinned interpreter")
    _fake_process(proc, interpreter, pid=100, parent=1, started=100, argv=["tini"])
    supervisor_argv = ["python3", module.SUPERVISOR_PATH, "claude"]
    _fake_process(
        proc,
        interpreter,
        pid=101,
        parent=100,
        started=200,
        argv=supervisor_argv,
    )
    _fake_process(
        proc,
        interpreter,
        pid=102,
        parent=101,
        started=300,
        argv=supervisor_argv,
    )
    _fake_process(
        proc,
        interpreter,
        pid=103,
        parent=100,
        started=400,
        argv=supervisor_argv,
    )

    accepted = module._trusted_peer_identity(
        peer_pid=101,
        peer_uid=os.geteuid(),
        peer_gid=os.getegid(),
        init_pid=100,
        phase="session",
        provider="claude",
        proc_root=proc,
    )
    assert accepted["supervisor_host_pid"] == 101
    with pytest.raises(module.EvidenceError, match="direct child"):
        module._trusted_peer_identity(
            peer_pid=102,
            peer_uid=os.geteuid(),
            peer_gid=os.getegid(),
            init_pid=100,
            phase="session",
            provider="claude",
            proc_root=proc,
        )
    with pytest.raises(module.EvidenceError, match="oldest direct child"):
        module._trusted_peer_identity(
            peer_pid=103,
            peer_uid=os.geteuid(),
            peer_gid=os.getegid(),
            init_pid=100,
            phase="session",
            provider="claude",
            proc_root=proc,
        )
    with pytest.raises(module.EvidenceError, match="credentials"):
        module._trusted_peer_identity(
            peer_pid=101,
            peer_uid=os.geteuid() + 1,
            peer_gid=os.getegid(),
            init_pid=100,
            phase="session",
            provider="claude",
            proc_root=proc,
        )


def test_docker_identity_binds_image_labels_and_running_init(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _broker_module()
    image = "sha256:" + "a" * 64

    def inspect(command: list[str], **kwargs):
        assert command[-1] == "session-one"
        output = f"100\ttrue\t{image}\tisolated-worker\tclaude\n".encode()
        return subprocess.CompletedProcess(command, 0, output, b"")

    monkeypatch.setattr(module.subprocess, "run", inspect)
    assert module._docker_init_pid(
        "session-one",
        expected_image=image,
        expected_boundary="isolated-worker",
        provider="claude",
    ) == 100
    with pytest.raises(module.EvidenceError, match="identity"):
        module._docker_init_pid(
            "session-one",
            expected_image="sha256:" + "b" * 64,
            expected_boundary="isolated-worker",
            provider="claude",
        )


def test_claude_and_codex_preflights_use_pinned_identity_only_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _supervisor_module()
    calls: list[list[str]] = []
    environments: list[dict[str, str]] = []

    class Credential:
        def __init__(self, provider: str, path: Path):
            assert provider in {"claude", "codex"}

        def initialize(self, *, session_overlays: bool = True) -> None:
            assert session_overlays is False

        def sync(self, *, final: bool = False) -> bool:
            raise AssertionError("identity preflight must not persist child credential changes")

    def run(command: list[str], **kwargs):
        calls.append(command)
        environments.append(kwargs["env"])
        if command[0] == "claude":
            event = {
                "type": "assistant",
                "message": {
                    "model": "claude-fable-5",
                    "content": [{"type": "text", "text": "READY"}],
                },
            }
            output = json.dumps(event, separators=(",", ":")).encode() + b"\n"
            return subprocess.CompletedProcess(command, 0, output, b"")
        output = b"\n".join(
            json.dumps(event, separators=(",", ":")).encode()
            for event in (
                {"type": "thread.started", "thread_id": "thread-1"},
                {"type": "turn.started"},
                {
                    "type": "item.completed",
                    "item": {"id": "item_0", "type": "agent_message", "text": "READY"},
                },
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 1,
                        "cached_input_tokens": 0,
                        "output_tokens": 1,
                        "reasoning_output_tokens": 0,
                    },
                },
            )
        ) + b"\n"
        stderr = (
            b"2026-07-16T00:00:00Z INFO codex_core::session: server reported model "
            b"gpt-5.6-sol (matches requested model)\n"
        )
        return subprocess.CompletedProcess(command, 0, output, stderr)

    class Channel:
        evidence: dict[str, object] | None = None

        def send_evidence(self, **kwargs) -> None:
            self.evidence = kwargs

    monkeypatch.setattr(module, "ProviderCredentialSync", Credential)
    monkeypatch.setattr(module, "_validate_codex_catalog", lambda: None)
    monkeypatch.setattr(module.subprocess, "run", run)
    channel = Channel()
    assert module._model_preflight("claude", channel) == 0
    [command] = calls
    assert command[command.index("--tools") + 1] == ""
    assert "--safe-mode" in command
    assert "--strict-mcp-config" in command
    assert "--disable-slash-commands" in command
    assert "--no-session-persistence" in command
    assert channel.evidence is not None and channel.evidence["tool_free"] is True
    assert "OPENAI_API_KEY" not in environments[0]

    assert module._model_preflight("codex", channel) == 0
    codex_command = calls[1]
    assert codex_command[:2] == ["codex", "exec"]
    assert "--ephemeral" in codex_command
    assert "--ignore-user-config" in codex_command
    assert "--ignore-rules" in codex_command
    assert "--strict-config" in codex_command
    assert "read-only" == codex_command[codex_command.index("--sandbox") + 1]
    assert 'model_reasoning_effort="xhigh"' in codex_command
    assert "tools.experimental_request_user_input={ enabled = false }" in codex_command
    assert "shell_tool" in codex_command
    assert "unified_exec" in codex_command
    assert channel.evidence is not None
    assert channel.evidence["observed_model"] == "gpt-5.6-sol"
    assert channel.evidence["observed_effort"] == "xhigh"
    assert channel.evidence["transcript_locator"] == (
        "in-memory:codex-exec-jsonl+server-model-log"
    )
    assert environments[1]["RUST_LOG"].endswith("session::handlers=off")
    assert "OPENAI_API_KEY" not in environments[1]


def test_capability_reports_both_pinned_preflights_as_supported() -> None:
    claude = subprocess.run(
        [str(BROKER), "capability", "--provider", "claude"],
        text=True,
        capture_output=True,
        check=False,
    )
    codex = subprocess.run(
        [str(BROKER), "capability", "--provider", "codex"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert claude.returncode == 0
    assert json.loads(claude.stdout) == {
        "advertised_tools": [],
        "boundary": "subscription-auth-only-empty-read-only-zero-tool-invocation",
        "provider": "claude",
        "status": "supported",
    }
    assert codex.returncode == 0
    assert json.loads(codex.stdout)["advertised_tools"] == ["update_plan", "view_image"]


def test_codex_preflight_rejects_reroutes_errors_and_any_tool_event() -> None:
    module = _supervisor_module()
    lifecycle = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "agent_message", "text": "READY"},
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1,
                "cached_input_tokens": 0,
                "output_tokens": 1,
                "reasoning_output_tokens": 0,
            },
        },
    ]

    def encoded(events: list[dict[str, object]]) -> bytes:
        return b"".join(
            json.dumps(event, separators=(",", ":")).encode() + b"\n"
            for event in events
        )

    match = (
        b"INFO codex_core::session: server reported model "
        b"gpt-5.6-sol (matches requested model)\n"
    )
    observed, event_sha = module._validate_codex_preflight(
        encoded(lifecycle), match, expected_model="gpt-5.6-sol"
    )
    assert observed == "gpt-5.6-sol"
    assert event_sha == hashlib.sha256(match).hexdigest()

    reroute = (
        b"WARN codex_core::session: server reported model gpt-5.2 "
        b"while requested model was gpt-5.6-sol\n"
    )
    with pytest.raises(RuntimeError, match="server-selected model signal"):
        module._validate_codex_preflight(
            encoded(lifecycle), reroute, expected_model="gpt-5.6-sol"
        )

    tool_events = list(lifecycle)
    tool_events[2] = {
        "type": "item.completed",
        "item": {"id": "item_0", "type": "todo_list", "items": []},
    }
    with pytest.raises(RuntimeError, match="tool event"):
        module._validate_codex_preflight(
            encoded(tool_events), match, expected_model="gpt-5.6-sol"
        )

    error_events = list(lifecycle)
    error_events.insert(
        2,
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "error", "message": "fallback"},
        },
    )
    with pytest.raises(RuntimeError, match="tool event"):
        module._validate_codex_preflight(
            encoded(error_events), match, expected_model="gpt-5.6-sol"
        )


def test_codex_preflight_catalog_matches_the_supervisor_digest() -> None:
    module = _supervisor_module()
    catalog = ROOT / "deploy/gas-city/config/codex-preflight-models.json"
    assert hashlib.sha256(catalog.read_bytes()).hexdigest() == (
        module.CODEX_PREFLIGHT_MODEL_CATALOG_SHA256
    )
    [model] = json.loads(catalog.read_text(encoding="utf-8"))["models"]
    assert model["slug"] == "gpt-5.6-sol"
    assert model["default_reasoning_level"] == "xhigh"
    assert model["shell_type"] == "disabled"
    assert model["apply_patch_tool_type"] is None
    assert model["supports_reasoning_summaries"] is True
    assert model["use_responses_lite"] is True
    assert model["tool_mode"] == "direct"
    assert model["multi_agent_version"] == "disabled"


def test_preflight_capability_is_anchored_to_pinned_cli_help() -> None:
    claude = subprocess.run(
        [str(CLAUDE), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    codex = subprocess.run(
        [str(CODEX), "exec", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert claude.returncode == 0
    claude_help = " ".join(claude.stdout.split())
    assert all(
        flag in claude_help
        for flag in (
            "--tools <tools...>",
            'Use "" to disable all tools',
            "--strict-mcp-config",
            "--safe-mode",
            "--disable-slash-commands",
            "--no-session-persistence",
        )
    )
    assert codex.returncode == 0
    assert "--sandbox <SANDBOX_MODE>" in codex.stdout
    assert "--ephemeral" in codex.stdout
    assert "--tools" not in codex.stdout


def test_supervisor_disables_same_uid_inspection_before_preflight_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _supervisor_module()
    order: list[str] = []

    class Channel:
        def __init__(self, provider: str, phase: str):
            assert (provider, phase) == ("claude", "preflight")
            order.append("authenticated-host-channel")

        def close(self) -> None:
            order.append("closed")

    def harden() -> None:
        order.append("non-dumpable")

    def preflight(provider: str, channel: object) -> int:
        assert provider == "claude" and isinstance(channel, Channel)
        order.append("provider-started")
        return 0

    monkeypatch.setattr(module, "TrustedModelEvidenceChannel", Channel)
    monkeypatch.setattr(module, "_disable_same_uid_process_inspection", harden)
    monkeypatch.setattr(module, "_model_preflight", preflight)
    assert module.main(["provider-supervisor", "model-preflight", "claude"]) == 0
    assert order == [
        "authenticated-host-channel",
        "non-dumpable",
        "provider-started",
        "closed",
    ]


def test_supervisor_waits_for_post_fsync_host_commit_ack() -> None:
    module = _supervisor_module()

    class Connection:
        def __init__(self, phase: str):
            self.sent = b""
            self.response = json.dumps(
                {
                    "schema_version": 1,
                    "kind": "host-model-evidence-committed",
                    "status": "committed",
                    "phase": phase,
                    "provider": "claude",
                    "challenge": "a" * 64,
                    "receipt_sha256": "b" * 64,
                },
                separators=(",", ":"),
            ).encode() + b"\n"

        def sendall(self, content: bytes) -> None:
            self.sent += content

        def shutdown(self, direction: int) -> None:
            return None

        def settimeout(self, timeout: int) -> None:
            assert timeout == 30

        def recv(self, maximum: int) -> bytes:
            content, self.response = self.response[:maximum], self.response[maximum:]
            return content

        def close(self) -> None:
            return None

    def send(phase: str, locator: str, tool_free: bool) -> dict[str, object]:
        connection = Connection(phase)
        channel = object.__new__(module.TrustedModelEvidenceChannel)
        channel.connection = connection
        channel.provider = "claude"
        channel.phase = phase
        channel.challenge = "a" * 64
        channel.send_evidence(
            expected_model="claude-fable-5",
            expected_effort=None,
            observed_model="claude-fable-5",
            observed_effort=None,
            provider_exit_code=0,
            event_sha256="c" * 64,
            transcript_sha256="d" * 64,
            transcript_locator=locator,
            tool_free=tool_free,
        )
        channel.close()
        return json.loads(connection.sent.decode("utf-8"))

    preflight = send("preflight", "in-memory:claude-stream-json", True)
    assert preflight["kind"] == "supervisor-model-evidence"
    assert preflight["observed_model"] == "claude-fable-5"

    session = send("session", "/home/worker/.claude/projects/session.jsonl", False)
    assert session["kind"] == "supervisor-model-evidence"
    assert "observed_model" not in session
    assert "expected_model" not in session
    assert "event_sha256" not in session


def test_launcher_mounts_only_socket_not_host_receipts_into_provider() -> None:
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "--model-evidence-state \"$model_evidence_state\"" in launcher
    assert "--model-receipt" not in launcher
    assert "GC_MODEL_RECEIPT_PATH=/home/worker/model-diagnostic.json" in launcher
    assert "src=$session_socket,dst=/run/gas-city-trusted/model-evidence.sock,readonly" in launcher
    assert "src=$preflight_socket,dst=/run/gas-city-trusted/model-evidence.sock,readonly" in launcher
    assert "src=$model_evidence_state,dst=" not in launcher
    assert "preflight-ready.json" in launcher
    assert "session-ready.json" in launcher
    assert "--accept-timeout 60" in launcher
