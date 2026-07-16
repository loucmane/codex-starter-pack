from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
BROKER = ROOT / "deploy/gas-city/bin/git-worktree-broker"


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    expected: int = 0,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def _git(cwd: Path, *arguments: str, environment: dict[str, str] | None = None) -> str:
    return _run(["/usr/bin/git", *arguments], cwd=cwd, environment=environment).stdout.strip()


def _fixture(tmp_path: Path) -> dict[str, object]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare", "--quiet")
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _git(repository, "config", "user.name", "Broker Test")
    _git(repository, "config", "user.email", "broker@example.invalid")
    (repository / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "--quiet", "-m", "baseline")
    _git(repository, "remote", "add", "origin", str(origin))
    _git(repository, "push", "--quiet", "-u", "origin", "main")
    _git(repository, "remote", "set-head", "origin", "main")
    _git(repository, "switch", "--quiet", "-c", "other")
    (repository / "other-only.txt").write_text("protected other branch\n", encoding="utf-8")
    _git(repository, "add", "other-only.txt")
    _git(repository, "commit", "--quiet", "-m", "protected other branch")
    other_oid = _git(repository, "rev-parse", "HEAD")
    _git(repository, "switch", "--quiet", "main")

    worktree = tmp_path / "city/.gc/worktrees/aegis/polecats/gastown.polecat_test"
    worktree.parent.mkdir(parents=True)
    _git(
        repository,
        "worktree",
        "add",
        "--quiet",
        "-b",
        "gc-polecat-test-0123456789ab",
        str(worktree),
        "origin/main",
    )
    state_parent = tmp_path / "state/git-broker/rig-aegis/agent"
    state_parent.mkdir(parents=True, mode=0o700)
    # Every parent crossed by the broker is an owner-only runtime boundary.
    for parent in (tmp_path / "state", tmp_path / "state/git-broker", tmp_path / "state/git-broker/rig-aegis", state_parent):
        parent.chmod(0o700)
    state = state_parent / "session"
    prepare = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree.resolve()),
            "--expected-common",
            str((repository / ".git").resolve()),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=tmp_path,
    )
    assert json.loads(prepare.stdout)["status"] == "prepared"
    baseline = json.loads((state / "baseline.json").read_text(encoding="utf-8"))
    receipt = json.loads((state / "broker-receipt.json").read_text(encoding="utf-8"))
    private_git = state / "private.git"
    environment = {
        **os.environ,
        "GIT_DIR": str(private_git),
        "GIT_WORK_TREE": str(worktree.resolve()),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }
    return {
        "origin": origin,
        "repository": repository,
        "other_oid": other_oid,
        "worktree": worktree.resolve(),
        "state": state,
        "baseline": baseline,
        "receipt": receipt,
        "private_git": private_git,
        "environment": environment,
    }


def _startup(
    fixture: dict[str, object],
    *,
    source_id: str = "ags-work",
    resumed: bool = False,
) -> Path:
    state = fixture["state"]
    worktree = fixture["worktree"]
    private_git = fixture["private_git"]
    receipt = fixture["receipt"]
    environment = fixture["environment"]
    assert isinstance(state, Path)
    assert isinstance(worktree, Path)
    assert isinstance(private_git, Path)
    assert isinstance(receipt, dict)
    assert isinstance(environment, dict)
    branch = f"polecat/{source_id}"
    if resumed:
        assert _git(worktree, "branch", "--show-current", environment=environment) == branch
    else:
        _git(worktree, "switch", "--quiet", "-c", branch, "refs/remotes/origin/main", environment=environment)
    head = _git(worktree, "rev-parse", "HEAD", environment=environment)
    startup = {
        "schema_version": 1,
        "kind": "aegis-polecat-pre-provider-startup",
        "status": "resumed" if resumed else "prepared",
        "rig": "aegis",
        "template": "aegis/gastown.polecat",
        "route": "aegis/gastown.polecat",
        "git_broker_receipt_sha256": hashlib.sha256(
            (state / "broker-receipt.json").read_bytes()
        ).hexdigest(),
        "git_broker_id": receipt["broker_id"],
        "git_source_branch": receipt["source_branch"],
        "git_starting_oid": receipt["starting_oid"],
        "git_source_common_dir": receipt["source_common_dir"],
        "git_private_common_dir": "/run/gas-city-git/private.git",
        "source_work_id": source_id,
        "branch": branch,
        "work_dir": str(worktree),
        "base_branch": "main",
        "git_head": head,
    }
    path = fixture["state"].parent / "startup-output.json"
    assert isinstance(path, Path)
    path.write_text(json.dumps(startup, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    frozen = _run(
        [str(BROKER), "freeze", "--state-dir", str(state), "--startup-receipt", str(path)],
        cwd=state,
    )
    assert json.loads(frozen.stdout)["authorized_branch"] == branch
    return path


def _host_model_evidence(
    fixture: dict[str, object], provider: str = "claude", exit_code: int = 0
) -> Path:
    state = fixture["state"]
    assert isinstance(state, Path)
    git_content = (state / "baseline.json").read_bytes()
    git = json.loads(git_content)
    source = git["source"]
    model = "gpt-5.6-sol" if provider == "codex" else "claude-fable-5"
    effort = "xhigh" if provider == "codex" else None
    model_state = state / "model-evidence"
    model_state.mkdir(mode=0o700)
    bindings = {
        "evidence_id": "evidence-test",
        "run_generation": 1,
        "run_id_sha256": "1" * 64,
        "session_id_sha256": git["session_id_sha256"],
        "git_broker_id": git["broker_id"],
        "git_broker_receipt_sha256": git["broker_receipt_sha256"],
        "git_startup_receipt_sha256": git["startup_receipt_sha256"],
        "git_source_starting_oid": source["starting_oid"],
        "git_authorized_ref": git["authorized_ref"],
    }

    def receipt(phase: str, preflight_sha: str | None) -> bytes:
        value = {
            "schema_version": 1,
            "kind": "host-model-evidence-receipt",
            "status": "verified",
            "phase": phase,
            "provider": provider,
            "expected_model": model,
            "expected_effort": effort,
            "observed_model": model,
            "observed_effort": effort,
            "provider_exit_code": 0 if phase == "preflight" else exit_code,
            "event_sha256": "2" * 64,
            "transcript_sha256": "3" * 64,
            "transcript_locator": (
                (
                    "in-memory:claude-stream-json"
                    if provider == "claude"
                    else "in-memory:codex-exec-jsonl+server-model-log"
                )
                if phase == "preflight"
                else f"/home/worker/.{provider}/sessions/test.jsonl"
            ),
            "tool_free": phase == "preflight",
            "challenge_sha256": "4" * 64,
            "container_name": f"{phase}-container",
            "container_image_id": "sha256:" + "5" * 64,
            "container_boundary": (
                "model-preflight" if phase == "preflight" else "isolated-worker"
            ),
            "model_source_phase": "preflight",
            "model_attestation_scope": (
                "isolated-zero-tool-invocation-preflight-gates-session"
            ),
            **bindings,
            "container_init_host_pid": 100,
            "supervisor_host_pid": 101,
            "supervisor_host_uid": os.geteuid(),
            "supervisor_host_gid": os.getegid(),
            "supervisor_starttime_ticks": 200,
            "preflight_receipt_sha256": preflight_sha,
            "recorded_at": "2026-07-16T00:00:00+00:00",
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"

    preflight_content = receipt("preflight", None)
    preflight_sha = hashlib.sha256(preflight_content).hexdigest()
    session_content = receipt("session", preflight_sha)
    for name, content in (
        ("preflight-receipt.json", preflight_content),
        ("session-receipt.json", session_content),
    ):
        path = model_state / name
        path.write_bytes(content)
        path.chmod(0o400)
    baseline = {
        "schema_version": 1,
        "kind": "host-model-evidence-baseline",
        "status": "evidence_recorded",
        "provider": provider,
        "expected_model": model,
        "expected_effort": effort,
        "model_attestation_scope": (
            "isolated-zero-tool-invocation-preflight-gates-session"
        ),
        **bindings,
        "git_baseline_sha256_at_begin": hashlib.sha256(git_content).hexdigest(),
        "preflight_container": "preflight-container",
        "session_container": "session-container",
        "worker_image_id": "sha256:" + "5" * 64,
        "preflight_receipt_sha256": preflight_sha,
        "session_receipt_sha256": hashlib.sha256(session_content).hexdigest(),
    }
    baseline_path = model_state / "baseline.json"
    baseline_path.write_text(json.dumps(baseline, sort_keys=True) + "\n", encoding="utf-8")
    baseline_path.chmod(0o600)
    return model_state


def _provider_commit(fixture: dict[str, object], content: str = "brokered change\n") -> str:
    worktree = fixture["worktree"]
    environment = fixture["environment"]
    assert isinstance(worktree, Path) and isinstance(environment, dict)
    (worktree / "tracked.txt").write_text(content, encoding="utf-8")
    _git(worktree, "add", "tracked.txt", environment=environment)
    _git(worktree, "commit", "--quiet", "-m", "brokered", environment=environment)
    return _git(worktree, "rev-parse", "HEAD", environment=environment)


def _finalize(
    fixture: dict[str, object],
    *,
    expected: int = 0,
    model_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    state = fixture["state"]
    worktree = fixture["worktree"]
    assert isinstance(state, Path) and isinstance(worktree, Path)
    model = model_path or _host_model_evidence(fixture)
    return _run(
        [
            str(BROKER),
            "finalize",
            "--state-dir",
            str(state),
            "--provider",
            "claude",
            "--provider-exit",
            "0",
            "--model-evidence-state",
            str(model),
        ],
        cwd=worktree,
        expected=expected,
    )


def test_private_git_promotes_exactly_one_authorized_branch(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    worktree = fixture["worktree"]
    repository = fixture["repository"]
    state = fixture["state"]
    environment = fixture["environment"]
    assert all(isinstance(item, Path) for item in (worktree, repository, state))
    assert isinstance(environment, dict)
    before_refs = _git(repository, "for-each-ref", "--format=%(refname) %(objectname)")
    target = _provider_commit(fixture)
    result = _finalize(fixture)
    promotion = json.loads(result.stdout)
    assert promotion["promoted_branch"] == "polecat/ags-work"
    assert promotion["promoted_oid"] == target
    assert _git(repository, "rev-parse", "refs/heads/polecat/ags-work") == target
    after_refs = _git(repository, "for-each-ref", "--format=%(refname) %(objectname)")
    before = dict(line.split(" ", 1) for line in before_refs.splitlines())
    after = dict(line.split(" ", 1) for line in after_refs.splitlines())
    assert {key: value for key, value in after.items() if key != "refs/heads/polecat/ags-work"} == before
    assert _git(worktree, "status", "--porcelain=v1", "--untracked-files=all") == ""
    receipt = fixture["receipt"]
    assert isinstance(receipt, dict)
    terminal_retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
    )
    assert json.loads(terminal_retry.stdout)["status"] == "already_promoted"


@pytest.mark.parametrize("tamper", ["main", "other", "config"])
def test_private_protected_ref_and_config_tamper_are_rejected(
    tmp_path: Path, tamper: str
) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    worktree = fixture["worktree"]
    state = fixture["state"]
    environment = fixture["environment"]
    assert isinstance(worktree, Path) and isinstance(state, Path) and isinstance(environment, dict)
    # The provider can mutate only its private copy; doing so is still rejected
    # because promotion permits no non-authorized private ref/config changes.
    target = _provider_commit(fixture)
    if tamper == "config":
        _git(
            worktree,
            "config",
            "core.hooksPath",
            str(worktree / "hooks"),
            environment=environment,
        )
    else:
        _git(
            worktree,
            "update-ref",
            f"refs/heads/{tamper}",
            target,
            environment=environment,
        )
    result = _finalize(fixture, expected=70)
    expected_message = (
        "private Git config changed"
        if tamper == "config"
        else "private Git changed a non-authorized ref"
    )
    assert expected_message in result.stderr


def test_no_work_terminal_state_is_idempotent_without_provider_restart(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    state = fixture["state"]
    worktree = fixture["worktree"]
    receipt = fixture["receipt"]
    assert isinstance(state, Path) and isinstance(worktree, Path) and isinstance(receipt, dict)
    startup = {
        "schema_version": 1,
        "kind": "aegis-polecat-pre-provider-startup",
        "status": "no_work",
        "rig": "aegis",
        "template": "aegis/gastown.polecat",
        "route": "aegis/gastown.polecat",
        "git_broker_receipt_sha256": hashlib.sha256(
            (state / "broker-receipt.json").read_bytes()
        ).hexdigest(),
        "git_broker_id": receipt["broker_id"],
        "git_source_branch": receipt["source_branch"],
        "git_starting_oid": receipt["starting_oid"],
        "git_source_common_dir": receipt["source_common_dir"],
        "git_private_common_dir": "/run/gas-city-git/private.git",
    }
    startup_path = state.parent / "no-work.json"
    startup_path.write_text(json.dumps(startup, sort_keys=True) + "\n", encoding="utf-8")
    startup_path.chmod(0o600)
    frozen = _run(
        [
            str(BROKER),
            "freeze",
            "--state-dir",
            str(state),
            "--startup-receipt",
            str(startup_path),
        ],
        cwd=state,
    )
    assert json.loads(frozen.stdout)["status"] == "no_work"
    terminal_retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
    )
    assert json.loads(terminal_retry.stdout)["status"] == "already_no_work"


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        ("config", "primary/common Git config changed"),
        ("hooks", "primary/common Git hooks changed"),
        ("worktree_config", "linked-worktree Git config changed"),
        ("ref", "protected primary/common Git ref changed"),
    ],
)
def test_primary_common_config_hooks_and_ref_tamper_fail_closed(
    tmp_path: Path, tamper: str, message: str
) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    worktree = fixture["worktree"]
    repository = fixture["repository"]
    assert isinstance(worktree, Path) and isinstance(repository, Path)
    if tamper == "config":
        config = repository / ".git/config"
        config.write_text(config.read_text(encoding="utf-8") + "\n# host tamper\n", encoding="utf-8")
    elif tamper == "hooks":
        hook = repository / ".git/hooks/pre-commit.sample"
        hook.write_text(hook.read_text(encoding="utf-8") + "\n# host tamper\n", encoding="utf-8")
    elif tamper == "worktree_config":
        git_dir = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-dir"))
        (git_dir / "config.worktree").write_text(
            "[core]\n\thooksPath = /tmp/escaped-hooks\n",
            encoding="utf-8",
        )
    else:
        _git(repository, "update-ref", "-d", "refs/heads/other")
    result = _finalize(fixture, expected=70)
    assert message in result.stderr


def test_authorized_target_ref_host_race_fails_compare_and_swap(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    repository = fixture["repository"]
    assert isinstance(repository, Path)
    _provider_commit(fixture)
    _git(repository, "update-ref", "refs/heads/polecat/ags-work", "refs/heads/other")
    result = _finalize(fixture, expected=70)
    assert "authorized branch raced before broker promotion" in result.stderr


def test_reachable_primary_object_deletion_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    repository = fixture["repository"]
    other_oid = fixture["other_oid"]
    assert isinstance(repository, Path) and isinstance(other_oid, str)
    object_path = repository / ".git/objects" / other_oid[:2] / other_oid[2:]
    assert object_path.is_file()
    object_path.unlink()
    result = _finalize(fixture, expected=70)
    assert "Git broker command failed" in result.stderr


def test_private_git_symlink_escape_is_rejected_before_git_reads(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    private_git = fixture["private_git"]
    repository = fixture["repository"]
    assert isinstance(private_git, Path) and isinstance(repository, Path)
    alternates = private_git / "objects/info/alternates"
    alternates.unlink()
    alternates.symlink_to(repository / ".git/config")
    result = _finalize(fixture, expected=70)
    assert "session-private Git state" in result.stderr


def test_non_fast_forward_authorized_history_is_rejected(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    worktree = fixture["worktree"]
    environment = fixture["environment"]
    assert isinstance(worktree, Path) and isinstance(environment, dict)
    tree = _git(worktree, "rev-parse", "HEAD^{tree}", environment=environment)
    divergent = _git(
        worktree,
        "commit-tree",
        tree,
        "-m",
        "divergent root",
        environment=environment,
    )
    _git(
        worktree,
        "update-ref",
        "refs/heads/polecat/ags-work",
        divergent,
        environment=environment,
    )
    _git(
        worktree,
        "symbolic-ref",
        "HEAD",
        "refs/heads/polecat/ags-work",
        environment=environment,
    )
    _git(worktree, "reset", "--hard", "--quiet", divergent, environment=environment)
    result = _finalize(fixture, expected=70)
    assert "not a fast-forward descendant" in result.stderr


def test_broker_receipt_and_host_baseline_tamper_are_rejected(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    state = fixture["state"]
    worktree = fixture["worktree"]
    receipt = fixture["receipt"]
    assert isinstance(state, Path) and isinstance(worktree, Path) and isinstance(receipt, dict)
    receipt_path = state / "broker-receipt.json"
    receipt_path.chmod(0o600)
    receipt_path.write_text(
        json.dumps({**receipt, "status": "tampered"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt_path.chmod(0o400)
    retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
        expected=70,
    )
    assert "Git broker receipt digest changed" in retry.stderr

    second = _fixture(tmp_path / "baseline")
    second_state = second["state"]
    assert isinstance(second_state, Path)
    baseline_path = second_state / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["broker_id"] = "tampered-baseline"
    baseline_path.write_text(json.dumps(baseline, sort_keys=True) + "\n", encoding="utf-8")
    baseline_path.chmod(0o600)
    baseline_result = _run(
        [str(BROKER), "freeze-generic", "--state-dir", str(second_state)],
        cwd=second_state,
        expected=70,
    )
    assert "receipt no longer matches its host baseline" in baseline_result.stderr


def test_frozen_startup_receipt_tamper_and_model_mismatch_promote_nothing(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    state = fixture["state"]
    repository = fixture["repository"]
    assert isinstance(state, Path) and isinstance(repository, Path)
    frozen = state / "startup-receipt.json"
    frozen.chmod(0o600)
    value = json.loads(frozen.read_text(encoding="utf-8"))
    value["branch"] = "polecat/ags-escape"
    frozen.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    frozen.chmod(0o400)
    receipt_result = _finalize(fixture, expected=70)
    assert "frozen startup receipt digest changed" in receipt_result.stderr
    _run(
        ["/usr/bin/git", "show-ref", "--verify", "--quiet", "refs/heads/polecat/ags-work"],
        cwd=repository,
        expected=1,
    )

    mismatch = _fixture(tmp_path / "model")
    _startup(mismatch)
    _provider_commit(mismatch)
    mismatch_state = mismatch["state"]
    mismatch_repository = mismatch["repository"]
    assert isinstance(mismatch_state, Path) and isinstance(mismatch_repository, Path)
    model = _host_model_evidence(mismatch)
    session_receipt = model / "session-receipt.json"
    session_receipt.chmod(0o600)
    model_value = json.loads(session_receipt.read_text(encoding="utf-8"))
    model_value["observed_model"] = "claude-fallback"
    session_receipt.write_text(
        json.dumps(model_value, sort_keys=True) + "\n", encoding="utf-8"
    )
    session_receipt.chmod(0o400)
    model_result = _finalize(mismatch, expected=70, model_path=model)
    assert "host model receipt" in model_result.stderr
    _run(
        ["/usr/bin/git", "show-ref", "--verify", "--quiet", "refs/heads/polecat/ags-work"],
        cwd=mismatch_repository,
        expected=1,
    )


def test_host_model_receipt_fields_must_be_exact(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    state = fixture["state"]
    assert isinstance(state, Path)
    model = _host_model_evidence(fixture)
    session_receipt = model / "session-receipt.json"
    session_receipt.chmod(0o600)
    value = json.loads(session_receipt.read_text(encoding="utf-8"))
    value["provider_claim"] = "untrusted-extra-field"
    session_receipt.write_text(
        json.dumps(value, sort_keys=True) + "\n", encoding="utf-8"
    )
    session_receipt.chmod(0o400)
    result = _finalize(fixture, expected=70, model_path=model)
    assert "host model receipt" in result.stderr


def test_crash_preserves_private_state_and_idempotent_retry(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    state = fixture["state"]
    worktree = fixture["worktree"]
    receipt = fixture["receipt"]
    assert isinstance(state, Path) and isinstance(worktree, Path) and isinstance(receipt, dict)
    result = _run(
        [str(BROKER), "finalize", "--state-dir", str(state), "--provider", "codex", "--provider-exit", "137", "--model-evidence-state", str(state / "model-evidence")],
        cwd=worktree,
    )
    assert json.loads(result.stdout)["status"] == "preserved"
    retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
    )
    assert json.loads(retry.stdout)["status"] == "resumed"
    assert (state / "private.git").is_dir()


def test_pre_authorization_startup_failure_resumes_without_ref_allowance(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    state = fixture["state"]
    worktree = fixture["worktree"]
    receipt = fixture["receipt"]
    assert isinstance(state, Path) and isinstance(worktree, Path) and isinstance(receipt, dict)
    preserved = _run(
        [
            str(BROKER),
            "preserve",
            "--state-dir",
            str(state),
            "--provider-exit",
            "71",
            "--reason",
            "startup_failed",
        ],
        cwd=worktree,
    )
    assert json.loads(preserved.stdout)["status"] == "preserved"
    retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
    )
    assert json.loads(retry.stdout)["status"] == "resumed"
    _startup(fixture)


def test_rejected_private_metadata_cannot_be_laundered_through_retry(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    state = fixture["state"]
    worktree = fixture["worktree"]
    receipt = fixture["receipt"]
    environment = fixture["environment"]
    assert isinstance(state, Path) and isinstance(worktree, Path)
    assert isinstance(receipt, dict) and isinstance(environment, dict)
    _git(worktree, "config", "alias.escape", "!touch /tmp/escape", environment=environment)
    assert _finalize(fixture, expected=70).returncode == 70
    _run(
        [
            str(BROKER),
            "preserve",
            "--state-dir",
            str(state),
            "--provider-exit",
            "0",
            "--reason",
            "promotion_rejected",
        ],
        cwd=worktree,
    )
    retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
        expected=70,
    )
    assert "private Git config changed before broker retry" in retry.stderr


def test_retry_recovers_exact_post_compare_and_swap_target(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _startup(fixture)
    worktree = fixture["worktree"]
    repository = fixture["repository"]
    state = fixture["state"]
    receipt = fixture["receipt"]
    environment = fixture["environment"]
    assert all(isinstance(item, Path) for item in (worktree, repository, state))
    assert isinstance(receipt, dict) and isinstance(environment, dict)
    target = _provider_commit(fixture, "post-CAS recovery\n")
    # Simulate a broker process dying after its ref CAS but before it updates
    # the linked-worktree metadata and durable promotion receipt.
    _git(
        worktree,
        "push",
        "--quiet",
        str(repository),
        f"{target}:refs/heads/polecat/ags-work",
        environment=environment,
    )
    retry = _run(
        [
            str(BROKER),
            "prepare",
            "--state-dir",
            str(state),
            "--worktree",
            str(worktree),
            "--expected-common",
            str(receipt["source_common_dir"]),
            "--base-branch",
            "main",
            "--agent",
            "polecat-test",
            "--session-id",
            "session-1",
        ],
        cwd=worktree,
    )
    assert json.loads(retry.stdout)["status"] == "resumed"
    _startup(fixture, resumed=True)
    promotion = json.loads(_finalize(fixture).stdout)
    assert promotion["promoted_oid"] == target
    assert promotion["recovered_after_cas"] is True
    assert _git(repository, "rev-parse", "refs/heads/polecat/ags-work") == target


def test_static_launcher_prevents_original_git_write_bypass() -> None:
    launcher = (ROOT / "deploy/gas-city/bin/provider-container").read_text(encoding="utf-8")
    assert 'src=$git_marker,dst=$git_marker,readonly' in launcher
    assert 'src=$git_common,dst=$git_common,readonly' in launcher
    assert 'src=$private_git,dst=/run/gas-city-git/private.git' in launcher
    assert "GIT_DIR=/run/gas-city-git/private.git" in launcher
    assert "git-worktree-broker" in launcher
    assert "already_promoted|already_no_work" in launcher
    assert "update-ref" not in launcher
    readme = (ROOT / "deploy/gas-city/README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())
    assert "does not parse or constrain an HTTPS push refspec" in normalized_readme
    assert "it withholds the write token and stops the session" in normalized_readme
