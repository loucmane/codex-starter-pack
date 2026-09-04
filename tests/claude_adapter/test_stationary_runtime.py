"""Executable runtime integrity, not Git-status or cache-name assumptions."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import marshal
import os
import py_compile
import stat
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis_foundation.gate.hooks.coordination_runtime import reviewed_runtime
from test_native_command_profile import event, git
from test_pretooluse_gates import PRETOOLUSE, run_gate, write
from test_stationary_orchestrator import command, stationary_fixture


@pytest.fixture(autouse=True)
def source_only_context(monkeypatch):
    # Direct verifier calls must satisfy exactly the policy established by the
    # real entrypoints. Explicit cfile paths below keep cache fixtures ordinary.
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(sys, "pycache_prefix", os.devnull)
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv("PYTHONPYCACHEPREFIX", os.devnull)


@pytest.mark.parametrize(
    "surface,name,value",
    [
        ("sys", "dont_write_bytecode", False),
        ("sys", "dont_write_bytecode", 1),
        ("sys", "pycache_prefix", None),
        ("sys", "pycache_prefix", "/tmp"),
        ("env", "PYTHONDONTWRITEBYTECODE", None),
        ("env", "PYTHONDONTWRITEBYTECODE", "0"),
        ("env", "PYTHONPYCACHEPREFIX", None),
        ("env", "PYTHONPYCACHEPREFIX", "/tmp"),
    ],
)
def test_missing_loading_isolation_refuses_before_any_runtime_inventory(
    tmp_path, monkeypatch, surface, name, value
):
    from aegis_foundation.gate.hooks import coordination_runtime

    if surface == "sys":
        monkeypatch.setattr(sys, name, value)
    elif value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)

    def unexpected_inventory(*args):
        pytest.fail("runtime inventory must not precede loading-isolation refusal")

    monkeypatch.setattr(coordination_runtime, "_git", unexpected_inventory)
    with pytest.raises(ValueError, match="source-only loading"):
        reviewed_runtime(tmp_path, tmp_path)


@pytest.mark.parametrize(
    "mode,device",
    [
        (stat.S_IFREG, 0),
        (stat.S_IFDIR, 0),
        (stat.S_IFLNK, 0),
        (stat.S_IFCHR, os.makedev(1, 5)),
    ],
)
def test_cache_sink_must_be_exact_linux_null_device(tmp_path, monkeypatch, mode, device):
    original = Path.lstat

    def fake_lstat(path):
        if path == Path(os.devnull):
            return SimpleNamespace(st_mode=mode, st_rdev=device)
        return original(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(ValueError, match="null device"):
        reviewed_runtime(tmp_path, tmp_path)


@pytest.mark.parametrize("scope", ["canonical", "target"])
@pytest.mark.parametrize(
    "relative",
    ["scripts/ignored_import.py", "aegis_foundation/ignored.so", "scripts/orphan.pyc"],
)
def test_ignored_import_inputs_are_not_reviewed(tmp_path, scope, relative):
    canonical, target, _ = stationary_fixture(tmp_path)
    write(canonical / ".git/info/exclude", relative + "\n")
    root = canonical if scope == "canonical" else target
    write(root / relative, "# unreviewed fixture\n")
    with pytest.raises(ValueError):
        reviewed_runtime(target, canonical)


@pytest.mark.parametrize("scope", ["canonical", "target"])
def test_poisoned_ignored_cache_never_executes_during_readiness(tmp_path, scope):
    canonical, target, _ = stationary_fixture(tmp_path)
    write(canonical / ".git/info/exclude", "__pycache__/\n*.pyc\n")
    root = canonical if scope == "canonical" else target
    source = root / "scripts/_source_workflow_state.py"
    marker = tmp_path / "executed-unreviewed-cache"
    code = compile(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        str(source),
        "exec",
    )
    clean = run_gate(PRETOOLUSE, canonical, event(canonical, command(canonical, target)))
    assert clean.returncode == 0, clean.stderr
    cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    cache.parent.mkdir(parents=True, exist_ok=True)
    header = importlib.util.MAGIC_NUMBER + struct.pack(
        "<III", 0, int(source.stat().st_mtime), source.stat().st_size
    )
    poisoned = header + marshal.dumps(code)
    cache.write_bytes(poisoned)
    result = run_gate(PRETOOLUSE, canonical, event(canonical, command(canonical, target)))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json.loads(clean.stdout)
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert not marker.exists(), "unreviewed bytecode executed during source-only readiness"
    assert cache.read_bytes() == poisoned, "cache must remain preserved as evidence"


@pytest.mark.parametrize("optimization", [0, 1, 2])
@pytest.mark.parametrize("mode", list(py_compile.PycInvalidationMode))
def test_legitimate_source_caches_remain_preserved(tmp_path, mode, optimization):
    canonical, target, _ = stationary_fixture(tmp_path)
    write(canonical / ".git/info/exclude", "__pycache__/\n*.pyc\n")
    caches = []
    for root in (canonical, target):
        source = root / "scripts/_source_workflow_state.py"
        cache = (
            source.parent
            / "__pycache__"
            / (
                f"{source.stem}.{sys.implementation.cache_tag}"
                + (f".opt-{optimization}" if optimization else "")
                + ".pyc"
            )
        )
        cache = Path(
            py_compile.compile(
                str(source),
                cfile=str(cache),
                doraise=True,
                optimize=optimization,
                invalidation_mode=mode,
            )
        )
        caches.append((cache, cache.read_bytes()))
    reviewed_runtime(target, canonical)
    result = run_gate(PRETOOLUSE, canonical, event(canonical, command(canonical, target)))
    assert result.returncode == 0, result.stderr
    for cache, before in caches:
        assert cache.read_bytes() == before


@pytest.mark.parametrize("tag", ["cpython-311", "cpython-312", "cpython-314.opt-2"])
def test_stale_malformed_cache_is_inert_and_not_read(tmp_path, monkeypatch, tag):
    canonical, target, _ = stationary_fixture(tmp_path)
    cache = target / "scripts/__pycache__" / f"_source_workflow_state.{tag}.pyc"
    cache.parent.mkdir()
    before = b"not even a bytecode header; preserved, not trusted"
    cache.write_bytes(before)
    original = Path.read_bytes

    def refuse_payload_read(path):
        if path == cache:
            pytest.fail("cache payload must not be parsed, hashed, compiled, or trusted")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", refuse_payload_read)
    reviewed_runtime(target, canonical)
    assert original(cache) == before


@pytest.mark.parametrize("tag", ["cpython-311", sys.implementation.cache_tag])
@pytest.mark.parametrize("optimization", [0, 1, 2])
@pytest.mark.parametrize("source_mode", [0o644, 0o755])
def test_python_named_extensionless_helper_cache_is_preserved(
    tmp_path, tag, optimization, source_mode
):
    canonical, target, _ = stationary_fixture(tmp_path)
    relative = "scripts/reviewed-helper"
    for root in (canonical, target):
        write(root / relative, "#!/usr/bin/env python3\nvalue = 'reviewed'\n")
        (root / relative).chmod(source_mode)
    git(canonical, "add", relative)
    git(canonical, "commit", "-qm", "reviewed extensionless helper")
    source = target / relative
    # Match Python's actual naming function, not a hand-invented dotted form.
    generated = Path(
        importlib.util.cache_from_source(
            str(source), optimization=str(optimization) if optimization else ""
        )
    ).name.replace(sys.implementation.cache_tag, tag)
    assert generated.startswith("reviewed-helpercpython-")
    cache = source.parent / "__pycache__" / generated
    cache.parent.mkdir()
    before = b"preserved without loading or interpreting its payload"
    cache.write_bytes(before)
    reviewed_runtime(target, canonical)
    assert cache.read_bytes() == before


@pytest.mark.parametrize("scope", ["canonical", "target"])
def test_source_file_loader_cache_for_nonexecutable_source_is_inert(tmp_path, monkeypatch, scope):
    canonical, target, _ = stationary_fixture(tmp_path)
    relative = "scripts/reviewed-loader-source"
    for root in (canonical, target):
        write(root / relative, "value = 'reviewed nonexecutable source'\n")
        (root / relative).chmod(0o644)
    git(canonical, "add", relative)
    git(canonical, "commit", "-qm", "reviewed SourceFileLoader source")
    source = (canonical if scope == "canonical" else target) / relative
    # Reproduce the repository's real interpreter-loader behavior in a disposable
    # fixture only, then restore mandatory source-only policy before verification.
    with monkeypatch.context() as generating_cache:
        generating_cache.setattr(sys, "dont_write_bytecode", False)
        generating_cache.setattr(sys, "pycache_prefix", None)
        generating_cache.delenv("PYTHONDONTWRITEBYTECODE")
        generating_cache.delenv("PYTHONPYCACHEPREFIX")
        loader = importlib.machinery.SourceFileLoader("reviewed_fixture", str(source))
        assert loader.get_code("reviewed_fixture") is not None
        cache = Path(importlib.util.cache_from_source(str(source)))
    assert cache.is_file()
    assert stat.S_IMODE(source.stat().st_mode) == 0o644
    before = cache.read_bytes()
    original = Path.read_bytes

    def refuse_payload_read(path):
        if path == cache:
            pytest.fail("inert extensionless cache payload must not be read")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", refuse_payload_read)
    reviewed_runtime(target, canonical)
    assert original(cache) == before


@pytest.mark.parametrize("source_exists", [False, True])
def test_extensionless_cache_cannot_invent_a_reviewed_source(tmp_path, source_exists):
    canonical, target, _ = stationary_fixture(tmp_path)
    relative = "scripts/unreviewed-source"
    if source_exists:
        write(target / relative, "value = 'untracked source'\n")
    cache = target / "scripts/__pycache__/unreviewed-sourcecpython-311.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"never executable authority")
    with pytest.raises(ValueError):
        reviewed_runtime(target, canonical)


@pytest.mark.parametrize("scope", ["canonical", "target"])
@pytest.mark.parametrize("source_mode", [0o644, 0o755])
@pytest.mark.parametrize("drift", ["bytes", "mode"])
def test_extensionless_cache_does_not_waive_source_bytes_or_mode(
    tmp_path, scope, source_mode, drift
):
    canonical, target, _ = stationary_fixture(tmp_path)
    relative = "scripts/reviewed-helper"
    for root in (canonical, target):
        write(root / relative, "value = 'reviewed'\n")
        (root / relative).chmod(source_mode)
    git(canonical, "add", relative)
    git(canonical, "commit", "-qm", "reviewed extensionless helper")
    source = (canonical if scope == "canonical" else target) / relative
    cache = source.parent / "__pycache__/reviewed-helpercpython-311.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"inert cache does not authorize source drift")
    if drift == "mode":
        source.chmod(0o755 if source_mode == 0o644 else 0o644)
    else:
        source.write_text("value = 'unreviewed'\n")
    with pytest.raises(ValueError, match="canonical Git objects"):
        reviewed_runtime(target, canonical)


@pytest.mark.parametrize("kind", ["orphan", "oversized", "fifo"])
def test_inert_cache_still_requires_reviewed_source_and_bounded_regular_file(tmp_path, kind):
    from aegis_foundation.gate.hooks.coordination_runtime import MAX_FILE

    canonical, target, _ = stationary_fixture(tmp_path)
    name = "orphan" if kind == "orphan" else "_source_workflow_state"
    cache = target / "scripts/__pycache__" / f"{name}.cpython-311.pyc"
    cache.parent.mkdir()
    if kind == "fifo":
        os.mkfifo(cache)
    else:
        with cache.open("wb") as handle:
            handle.truncate(MAX_FILE + 1 if kind == "oversized" else 0)
    with pytest.raises(ValueError):
        reviewed_runtime(target, canonical)


@pytest.mark.parametrize("index_flag", ["--assume-unchanged", "--skip-worktree"])
def test_index_flags_cannot_hide_changed_executable_bytes(tmp_path, index_flag):
    canonical, target, _ = stationary_fixture(tmp_path)
    relative = "scripts/_source_workflow_state.py"
    git(target, "update-index", index_flag, relative)
    write(target / relative, "# hidden executable change\n")
    with pytest.raises(ValueError, match="canonical Git objects"):
        reviewed_runtime(target, canonical)


def test_symlinked_cache_is_not_followed(tmp_path):
    canonical, target, _ = stationary_fixture(tmp_path)
    cache = target / "scripts/__pycache__"
    cache.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="aliased"):
        reviewed_runtime(target, canonical)


@pytest.mark.parametrize("relative", [".aegis/bin/aegis", ".aegis/runtime.env"])
def test_installed_runtime_needs_a_separately_reviewed_profile(tmp_path, relative):
    canonical, target, _ = stationary_fixture(tmp_path)
    write(target / relative, "# unreviewed installed runtime\n")
    with pytest.raises(ValueError, match="source-only"):
        reviewed_runtime(target, canonical)


def test_unreadable_inventory_fails_closed(tmp_path, monkeypatch):
    from aegis_foundation.gate.hooks import coordination_runtime

    canonical, target, _ = stationary_fixture(tmp_path)

    def denied_walk(path, *, followlinks, onerror):
        onerror(PermissionError("synthetic unreadable directory"))
        return iter(())

    monkeypatch.setattr(coordination_runtime.os, "walk", denied_walk)
    with pytest.raises(ValueError, match="inventory"):
        reviewed_runtime(target, canonical)
