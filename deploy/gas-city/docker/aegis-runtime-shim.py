#!/usr/bin/env python3
"""Offline launcher for the immutable Aegis runtime in Gas City workers.

The Aegis source repository intentionally is not foundation-installed into
itself.  A worker therefore receives a private tmpfs at ``.aegis/bin`` and the
supervisor writes a tiny target-local ``aegis`` entrypoint into that tmpfs.
This image-owned shim loads the pinned wheel extracted at image-build time.

For every invocation, a process lock in the same tmpfs serializes access.  If
the repository has no real foundation manifest, the shim creates the minimum
manifest needed by the existing Aegis command implementation, retains an open
descriptor to that exact inode, and removes only that inode after the command.
No installed assets are written into the source checkout.
"""

from __future__ import annotations

from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Sequence


RUNTIME_ROOT = Path("/opt/gas-city/aegis-runtime")
RUNTIME_SOURCE_ROOT = RUNTIME_ROOT / "aegis_foundation/assets"
SHIM_PATH = Path("/opt/gas-city/aegis-runtime-shim.py")
CITY_ROOT = Path("/home/loucmane/gas-city")
RIG_ROOT = Path("/home/loucmane/codex")
GIT_COMMON_DIR = RIG_ROOT / ".git"
WORKTREE_ROOT = CITY_ROOT / ".gc/worktrees/aegis/polecats"
GIT_PATH = Path("/usr/bin/git")
LOCAL_ENTRYPOINT_REL = Path(".aegis/bin/aegis")
LOCK_NAME = ".runtime.lock"
MANIFEST_REL = Path(".aegis/foundation-manifest.json")
BOOTSTRAP_MANIFEST = b'{"capabilities":{}}\n'
SELF_HOST_INSTALL_COMMANDS = frozenset(
    {"init", "install", "repair", "setup", "uninstall", "update"}
)


class RuntimeShimError(RuntimeError):
    """The immutable Aegis runtime cannot be used without guessing."""


@dataclass(frozen=True)
class RuntimePaths:
    runtime_root: Path = RUNTIME_ROOT
    runtime_source_root: Path = RUNTIME_SOURCE_ROOT
    shim: Path = SHIM_PATH
    city_root: Path = CITY_ROOT
    rig_root: Path = RIG_ROOT
    git_common_dir: Path = GIT_COMMON_DIR
    worktree_root: Path = WORKTREE_ROOT
    git: Path = GIT_PATH
    require_tmpfs: bool = True


def _target_from_arguments(arguments: Sequence[str]) -> Path:
    values: list[str] = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "--source-root" or value.startswith("--source-root="):
            raise RuntimeShimError("Aegis runtime source-root overrides are forbidden")
        if value == "--target-dir":
            if index + 1 >= len(arguments):
                raise RuntimeShimError("--target-dir is missing its value")
            values.append(arguments[index + 1])
            index += 2
            continue
        if value.startswith("--target-dir="):
            values.append(value.split("=", 1)[1])
        index += 1
    if len(values) > 1:
        raise RuntimeShimError("Aegis runtime received more than one --target-dir")
    raw = values[0] if values else "."
    try:
        return Path(raw).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RuntimeShimError("Aegis target directory does not exist") from exc


def _git_text(paths: RuntimePaths, target: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            [str(paths.git), "-C", str(target), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeShimError("could not validate the target git boundary") from exc
    if result.returncode != 0:
        raise RuntimeShimError("target is not the exact Aegis Gas City worktree")
    return result.stdout.strip()


def _require_environment(name: str, expected: str) -> None:
    if os.environ.get(name) != expected:
        raise RuntimeShimError(f"immutable Aegis runtime identity mismatch for {name}")


def _require_target(paths: RuntimePaths, target: Path) -> Path:
    _require_environment("GC_CITY_ROOT", str(paths.city_root))
    _require_environment("GC_RIG", "aegis")
    _require_environment("GC_RIG_ROOT", str(paths.rig_root))
    _require_environment("GC_BEADS_PREFIX", "ags")
    _require_environment("GC_TEMPLATE", "aegis/gastown.polecat")
    try:
        target.relative_to(paths.worktree_root)
    except ValueError as exc:
        raise RuntimeShimError("Aegis runtime target escaped the polecat worktree root") from exc
    top = Path(_git_text(paths, target, "rev-parse", "--show-toplevel"))
    common = Path(
        _git_text(
            paths,
            target,
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        )
    )
    try:
        top = top.resolve(strict=True)
        common = common.resolve(strict=True)
        expected_common = paths.git_common_dir.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RuntimeShimError("could not canonicalize the Aegis git boundary") from exc
    if top != target or common != expected_common:
        raise RuntimeShimError("Aegis runtime target has the wrong git boundary")
    return target / ".aegis/bin"


def _mount_type(path: Path) -> str | None:
    """Return the exact mount type for *path* from Linux mountinfo."""

    try:
        lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
    except OSError as exc:  # pragma: no cover - production workers are Linux.
        raise RuntimeShimError("cannot inspect the local launcher mount") from exc
    encoded = str(path).replace(" ", "\\040")
    matches: list[str] = []
    for line in lines:
        fields = line.split()
        if len(fields) < 10 or fields[4] != encoded or "-" not in fields:
            continue
        separator = fields.index("-")
        if separator + 1 < len(fields):
            matches.append(fields[separator + 1])
    if len(matches) > 1:
        raise RuntimeShimError("local launcher has an ambiguous mount identity")
    return matches[0] if matches else None


def _require_private_bin(paths: RuntimePaths, bin_dir: Path) -> None:
    try:
        metadata = bin_dir.lstat()
    except OSError as exc:
        raise RuntimeShimError("target-local Aegis bin directory is missing") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise RuntimeShimError("target-local Aegis bin directory is not private")
    if paths.require_tmpfs and _mount_type(bin_dir) != "tmpfs":
        raise RuntimeShimError("target-local Aegis bin directory is not the nested tmpfs")


def _open_lock(bin_dir: Path) -> int:
    path = bin_dir / LOCK_NAME
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RuntimeShimError("cannot open the Aegis runtime lock") from exc
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_nlink != 1
    ):
        os.close(descriptor)
        raise RuntimeShimError("Aegis runtime lock has unsafe metadata")
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    return descriptor


def _open_temporary_manifest(target: Path) -> tuple[int | None, tuple[int, int] | None]:
    path = target / MANIFEST_REL
    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise RuntimeShimError("cannot inspect the Aegis foundation manifest") from exc
    if existing is not None:
        if (
            stat.S_ISLNK(existing.st_mode)
            or not stat.S_ISREG(existing.st_mode)
            or existing.st_uid != os.geteuid()
            or existing.st_nlink != 1
            or stat.S_IMODE(existing.st_mode) & 0o022
            or existing.st_size <= 0
            or existing.st_size > 1024 * 1024
        ):
            raise RuntimeShimError("existing Aegis foundation manifest is unsafe")
        return None, None

    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
        offset = 0
        while offset < len(BOOTSTRAP_MANIFEST):
            written = os.write(descriptor, BOOTSTRAP_MANIFEST[offset:])
            if written <= 0:
                raise OSError("short temporary manifest write")
            offset += written
        os.fsync(descriptor)
    except OSError as exc:
        try:
            os.close(descriptor)  # type: ignore[possibly-undefined]
        except (OSError, UnboundLocalError):
            pass
        raise RuntimeShimError("cannot create the temporary Aegis foundation manifest") from exc
    metadata = os.fstat(descriptor)
    return descriptor, (metadata.st_dev, metadata.st_ino)


def _remove_temporary_manifest(
    target: Path,
    descriptor: int | None,
    identity: tuple[int, int] | None,
) -> None:
    if descriptor is None or identity is None:
        return
    path = target / MANIFEST_REL
    try:
        current = path.lstat()
        opened = os.fstat(descriptor)
        current_identity = (current.st_dev, current.st_ino)
        opened_identity = (opened.st_dev, opened.st_ino)
        if (
            current_identity != identity
            or opened_identity != identity
            or not stat.S_ISREG(current.st_mode)
            or current.st_nlink != 1
        ):
            raise RuntimeShimError(
                "temporary Aegis foundation manifest changed identity; refusing removal"
            )
        path.unlink()
        if os.fstat(descriptor).st_nlink != 0:
            raise RuntimeShimError("temporary Aegis foundation manifest was not unlinked")
    except OSError as exc:
        raise RuntimeShimError("could not remove the temporary Aegis foundation manifest") from exc
    finally:
        os.close(descriptor)


def _load_cli(paths: RuntimePaths):
    runtime = paths.runtime_root.resolve(strict=True)
    source = paths.runtime_source_root.resolve(strict=True)
    if source.parent.parent != runtime:
        raise RuntimeShimError("immutable Aegis packaged assets escaped the runtime root")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(runtime))
    try:
        from aegis_foundation import cli  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 - immutable runtime import fails closed.
        raise RuntimeShimError("immutable Aegis runtime could not be imported") from exc
    try:
        module_path = Path(cli.__file__).resolve(strict=True)
        module_path.relative_to(runtime)
    except (AttributeError, OSError, RuntimeError, ValueError) as exc:
        raise RuntimeShimError("Aegis CLI was not loaded from the immutable runtime") from exc
    configured_source = os.environ.get("AEGIS_SOURCE_ROOT")
    if configured_source not in {None, "", str(source)}:
        raise RuntimeShimError("inherited AEGIS_SOURCE_ROOT conflicts with the image runtime")
    os.environ["AEGIS_SOURCE_ROOT"] = str(source)
    return cli


def _subcommand(arguments: Sequence[str]) -> str:
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "--version":
            return "--version"
        if value == "--target-dir":
            index += 2
            continue
        if value.startswith("--target-dir="):
            index += 1
            continue
        if not value.startswith("-"):
            return value
        index += 1
    raise RuntimeShimError("Aegis runtime command is missing its subcommand")


def run(
    arguments: Sequence[str],
    *,
    paths: RuntimePaths = RuntimePaths(),
) -> int:
    if not arguments:
        raise RuntimeShimError("Aegis runtime requires one command")
    target = _target_from_arguments(arguments)
    bin_dir = _require_target(paths, target)
    _require_private_bin(paths, bin_dir)
    lock = _open_lock(bin_dir)
    manifest_descriptor: int | None = None
    manifest_identity: tuple[int, int] | None = None
    command_error: BaseException | None = None
    result = 1
    try:
        manifest_descriptor, manifest_identity = _open_temporary_manifest(target)
        if (
            manifest_descriptor is not None
            and _subcommand(arguments) in SELF_HOST_INSTALL_COMMANDS
        ):
            raise RuntimeShimError(
                "foundation install/update commands are forbidden in the Aegis self-host worktree"
            )
        cli = _load_cli(paths)
        result = int(cli.main(list(arguments)))
    except BaseException as exc:  # preserve cleanup before propagating.
        command_error = exc
    cleanup_error: BaseException | None = None
    try:
        _remove_temporary_manifest(target, manifest_descriptor, manifest_identity)
    except BaseException as exc:
        cleanup_error = exc
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)
    if cleanup_error is not None:
        raise cleanup_error
    if command_error is not None:
        raise command_error
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        return run(arguments)
    except Exception as exc:  # noqa: BLE001 - the image entrypoint fails closed.
        print(f"immutable Aegis runtime rejected invocation: {exc}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
