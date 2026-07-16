"""Guarded host-side transition to Gas City's external HQ Dolt endpoint.

The upstream ``gc beads city use-external`` command is the only supported
topology writer.  This module surrounds that command with a fail-closed
operator transaction: exact tool and city identity checks, a mutation-free
dry-run, append-only byte snapshots, post-state and live connection proof, and
an exact rollback journal.  Database credentials are accepted only as an
in-memory value sourced by the CLI from an owner-only file; they are never
placed in argv, receipts, or diagnostic output.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import tomllib
from typing import Any, Iterator

from aegis_foundation import gas_city_ops


PRODUCTION_CITY_ROOT = Path("/home/loucmane/gas-city")
PRODUCTION_AEGIS_ROOT = Path("/home/loucmane/codex")
HQ_HOST = "127.0.0.1"
HQ_PORT = 33070
HQ_USER = "gas_city_hq"
HQ_DATABASE = "hq"
AEGIS_HOST = "127.0.0.1"
AEGIS_PORT = 33071
AEGIS_USER = "aegis_beads"
TRANSITION_SECRET_VARIABLE = "GAS_CITY_HQ_DOLT_PASSWORD_FILE"
INTERNAL_CREDENTIAL_FD_VARIABLE = "GAS_CITY_INTERNAL_CREDENTIAL_FD"
TRANSITION_SCHEMA = "gas-city-hq-endpoint-transition/v1"
ROLLBACK_SCHEMA = "gas-city-hq-endpoint-rollback/v1"
HQ_INITIALIZATION_SCHEMA = "gas-city-hq-beads-initialization/v1"
MANIFEST_SCHEMA = "gas-city-endpoint-file-manifest/v1"
PREPARED_SCHEMA = "gas-city-hq-endpoint-prepared/v1"
SAFE_RUN_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SAFE_RIG_NAME_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
PROJECT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z"
)
HQ_BEADS_CUSTOM_TYPES = (
    "molecule,convoy,message,event,gate,merge-request,agent,role,rig,session,"
    "spec,convergence,step"
)
HQ_BEADS_INITIAL_CONFIG = (
    b"issue_prefix: gc\n"
    b"issue-prefix: gc\n"
    b"dolt.auto-start: false\n"
    b"dolt:\n"
    b"  disable-event-flush: true\n"
    b"export.auto: false\n"
    b"backup.enabled: false\n"
    b"gc.endpoint_origin: city_canonical\n"
    b"gc.endpoint_status: unverified\n"
    b"dolt.host: 127.0.0.1\n"
    b"dolt.port: 33070\n"
)
HQ_BEADS_CONFIG = (
    HQ_BEADS_INITIAL_CONFIG
    + f"types.custom: {HQ_BEADS_CUSTOM_TYPES}\n".encode("ascii")
)
HQ_BEADS_SCHEMA = (
    ("blocked_issues", "VIEW"),
    ("child_counters", "BASE TABLE"),
    ("comments", "BASE TABLE"),
    ("compaction_snapshots", "BASE TABLE"),
    ("config", "BASE TABLE"),
    ("custom_statuses", "BASE TABLE"),
    ("custom_types", "BASE TABLE"),
    ("dependencies", "BASE TABLE"),
    ("events", "BASE TABLE"),
    ("federation_peers", "BASE TABLE"),
    ("ignored_schema_migrations", "BASE TABLE"),
    ("interactions", "BASE TABLE"),
    ("issues", "BASE TABLE"),
    ("issue_counter", "BASE TABLE"),
    ("issue_snapshots", "BASE TABLE"),
    ("labels", "BASE TABLE"),
    ("local_metadata", "BASE TABLE"),
    ("metadata", "BASE TABLE"),
    ("ready_issues", "VIEW"),
    ("repo_mtimes", "BASE TABLE"),
    ("routes", "BASE TABLE"),
    ("schema_migrations", "BASE TABLE"),
    ("wisps", "BASE TABLE"),
    ("wisp_child_counters", "BASE TABLE"),
    ("wisp_comments", "BASE TABLE"),
    ("wisp_dependencies", "BASE TABLE"),
    ("wisp_events", "BASE TABLE"),
    ("wisp_labels", "BASE TABLE"),
)
HQ_BEADS_SEEDED_ROW_COUNTS = {
    "config": 11,
    "custom_types": 13,
    "ignored_schema_migrations": 11,
    "local_metadata": 1,
    "metadata": 2,
    "schema_migrations": 53,
}
HQ_BEADS_CONTENT_TABLES = tuple(
    name
    for name, kind in HQ_BEADS_SCHEMA
    if kind == "BASE TABLE" and name not in HQ_BEADS_SEEDED_ROW_COUNTS
)
HQ_BEADS_LOCAL_NAMES = frozenset(
    {
        ".gitignore",
        ".local_version",
        "README.md",
        "config.yaml",
        "dolt",
        "dolt-server.port",
        "interactions.jsonl",
        "metadata.json",
    }
)
HQ_BEADS_GITIGNORE_SHA256 = (
    "f7602e4a43fb73574acc38aa0475d03d7383956983183b87f431865663676dc1"
)
HQ_BEADS_README_SHA256 = (
    "cae1648db67c27f1d86f92ed110119445356e23bb18a5df57e73a7f476619267"
)
VERSION_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "gc": ("version",),
    "bd": ("--version",),
    "dolt": ("version",),
}
AMBIENT_ENDPOINT_KEYS = frozenset(
    {
        "BEADS_DIR",
        "BEADS_DOLT_SERVER_HOST",
        "BEADS_DOLT_SERVER_PORT",
        "BEADS_DOLT_SERVER_USER",
        "BEADS_DOLT_SERVER_DATABASE",
        "BEADS_DOLT_SERVER_TLS",
        "BEADS_DOLT_PASSWORD",
        "BEADS_CREDENTIALS_FILE",
        "DOLT_CLI_PASSWORD",
        "GC_DOLT_HOST",
        "GC_DOLT_PORT",
        "GC_DOLT_USER",
        "GC_DOLT_DATABASE",
        "GC_DOLT_PASSWORD",
        "GC_DOLT_DATA_DIR",
        "GC_DOLT_LOG_FILE",
        "GC_DOLT_STATE_FILE",
        "GC_DOLT_PID_FILE",
        "GC_DOLT_LOCK_FILE",
        "GC_DOLT_CONFIG_FILE",
        "GC_PACK_STATE_DIR",
        "GC_RIG",
        "GC_RIG_ROOT",
        "GC_STORE_ROOT",
        "GC_STORE_SCOPE",
        TRANSITION_SECRET_VARIABLE,
        INTERNAL_CREDENTIAL_FD_VARIABLE,
    }
)


class EndpointTransitionError(gas_city_ops.GasCityOpsError):
    """The HQ endpoint operation could not prove its safety contract."""


Runner = Callable[
    [Sequence[str], Path, Mapping[str, str]], subprocess.CompletedProcess[str]
]
LockLoader = Callable[[Path], Mapping[str, Any]]


@dataclasses.dataclass(frozen=True)
class TrackedPath:
    role: str
    scope: str
    path: Path


@dataclasses.dataclass(frozen=True)
class DiscoveredTopology:
    city: Path
    aegis: Path
    tracked: tuple[TrackedPath, ...]
    city_config: Mapping[str, Any]
    site_config: Mapping[str, Any]


@dataclasses.dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int

    def evidence(self) -> dict[str, Any]:
        argv_bytes = _canonical_json_bytes(list(self.argv))
        return {
            "argv": list(self.argv),
            "argv_sha256": _sha256(argv_bytes),
            "returncode": self.returncode,
            "stdout_sha256": _sha256(self.stdout.encode("utf-8")),
            "stderr_sha256": _sha256(self.stderr.encode("utf-8")),
        }


def _default_runner(
    argv: Sequence[str], cwd: Path, environment: Mapping[str, str]
) -> subprocess.CompletedProcess[str]:
    child_environment = dict(environment)
    pass_fds: tuple[int, ...] = ()
    raw_descriptor = child_environment.pop(INTERNAL_CREDENTIAL_FD_VARIABLE, None)
    if raw_descriptor is not None:
        try:
            descriptor = int(raw_descriptor)
        except ValueError as exc:
            raise EndpointTransitionError("internal credential descriptor is invalid") from exc
        child_environment["BEADS_CREDENTIALS_FILE"] = f"/proc/self/fd/{descriptor}"
        pass_fds = (descriptor,)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=child_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        pass_fds=pass_fds,
    )


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _format_utc(value: dt.datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != dt.timedelta(0):
        raise EndpointTransitionError("endpoint transition clock must return UTC")
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _strict_json_bytes(content: bytes, *, label: str) -> Any:
    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EndpointTransitionError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EndpointTransitionError(f"{label} is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                EndpointTransitionError(f"{label} contains non-finite JSON {value}")
            ),
        )
    except json.JSONDecodeError as exc:
        raise EndpointTransitionError(f"{label} is not valid JSON") from exc


def _strict_json_object(text: str, *, label: str) -> dict[str, Any]:
    value = _strict_json_bytes(text.encode("utf-8"), label=label)
    if type(value) is not dict:
        raise EndpointTransitionError(f"{label} must contain one JSON object")
    return value


def _lexical_absolute(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise EndpointTransitionError(f"{label} must be an absolute path")
    return Path(os.path.normpath(expanded.as_posix()))


def _real_directory(path: Path, *, label: str, owner_only: bool = False) -> Path:
    requested = _lexical_absolute(path, label=label)
    if requested.is_symlink():
        raise EndpointTransitionError(f"{label} must not be a symlink")
    try:
        resolved = requested.resolve(strict=True)
        metadata = requested.lstat()
    except OSError as exc:
        raise EndpointTransitionError(f"cannot inspect {label}: {requested}") from exc
    if resolved != requested or not stat.S_ISDIR(metadata.st_mode):
        raise EndpointTransitionError(f"{label} must be one canonical real directory")
    if metadata.st_uid != os.getuid():
        raise EndpointTransitionError(f"{label} must be owned by the current user")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode & 0o022:
        raise EndpointTransitionError(f"{label} must not be group/world writable")
    if owner_only and mode & 0o077:
        raise EndpointTransitionError(f"{label} must be owner-only")
    if not mode & 0o100:
        raise EndpointTransitionError(f"{label} must be owner-accessible")
    return resolved


def _regular_file(
    path: Path,
    *,
    label: str,
    exact_mode: int | None = None,
    private: bool = False,
) -> tuple[bytes, os.stat_result]:
    requested = _lexical_absolute(path, label=label)
    if requested.is_symlink():
        raise EndpointTransitionError(f"{label} must not be a symlink")
    try:
        metadata = requested.lstat()
    except OSError as exc:
        raise EndpointTransitionError(f"cannot inspect {label}: {requested}") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise EndpointTransitionError(f"{label} must be one singly-linked regular file")
    if metadata.st_uid != os.getuid():
        raise EndpointTransitionError(f"{label} must be owned by the current user")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode & 0o022:
        raise EndpointTransitionError(f"{label} must not be group/world writable")
    if private and mode & 0o077:
        raise EndpointTransitionError(f"{label} must be owner-only")
    if exact_mode is not None and mode != exact_mode:
        raise EndpointTransitionError(
            f"{label} mode must be {exact_mode:04o}, observed {mode:04o}"
        )
    try:
        return requested.read_bytes(), metadata
    except OSError as exc:
        raise EndpointTransitionError(f"cannot read {label}: {requested}") from exc


def _validate_secret(password: str) -> None:
    if (
        not isinstance(password, str)
        or not 32 <= len(password) <= 128
        or any(character.isspace() or ord(character) < 33 or ord(character) > 126 for character in password)
    ):
        raise EndpointTransitionError(
            "HQ Dolt credential must be one 32-128 character printable line"
        )


def _command_environment(
    city: Path,
    password: str,
    source: Mapping[str, str] | None,
) -> dict[str, str]:
    _validate_secret(password)
    result = dict(os.environ if source is None else source)
    for key in AMBIENT_ENDPOINT_KEYS:
        result.pop(key, None)
    result.update(
        {
            "PATH": f"{city / 'bin'}:/usr/bin:/bin",
            "NO_COLOR": "1",
            # Gas City owns attended backup/restore evidence. Suppress bd
            # 1.1.0's opportunistic auto-backup while the endpoint is still
            # being transitioned under a deliberately least-privilege account.
            "BD_BACKUP_ENABLED": "false",
            "BEADS_DOLT_PASSWORD": password,
            "DOLT_CLI_PASSWORD": password,
            "GC_DOLT_PASSWORD": password,
        }
    )
    return result


def _redacted_detail(result: subprocess.CompletedProcess[str], password: str) -> str:
    detail = (result.stderr or result.stdout or "").replace(password, "<redacted>").strip()
    return detail[-2048:]


def _run_checked(
    argv: Sequence[str],
    *,
    city: Path,
    environment: Mapping[str, str],
    password: str,
    runner: Runner,
    label: str,
) -> CommandResult:
    command = tuple(str(item) for item in argv)
    if any(password in argument for argument in command):
        raise EndpointTransitionError("secret material must never appear in argv")
    command_environment = dict(environment)
    credential_descriptor: int | None = None
    if command_environment.get("GC_DOLT_PASSWORD") == password:
        if not hasattr(os, "memfd_create"):
            raise EndpointTransitionError(
                "anonymous credential projection requires Linux memfd_create"
            )
        try:
            credential_descriptor = os.memfd_create(
                "gas-city-hq-credentials", flags=getattr(os, "MFD_CLOEXEC", 0)
            )
            os.fchmod(credential_descriptor, 0o600)
            credential_content = (
                f"[{HQ_HOST}:{HQ_PORT}]\npassword={password}\n"
            ).encode("utf-8")
            offset = 0
            while offset < len(credential_content):
                offset += os.write(credential_descriptor, credential_content[offset:])
            os.lseek(credential_descriptor, 0, os.SEEK_SET)
            command_environment[INTERNAL_CREDENTIAL_FD_VARIABLE] = str(
                credential_descriptor
            )
            # Custom runners can inspect the same anonymous file through the
            # parent procfs path.  The real runner replaces this with
            # /proc/self/fd/N and explicitly inherits only that descriptor.
            command_environment["BEADS_CREDENTIALS_FILE"] = (
                f"/proc/{os.getpid()}/fd/{credential_descriptor}"
            )
            completed = runner(command, city, command_environment)
        finally:
            if credential_descriptor is not None:
                os.close(credential_descriptor)
    else:
        completed = runner(command, city, command_environment)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if password in stdout or password in stderr:
        raise EndpointTransitionError(f"{label} exposed secret material in command output")
    result = CommandResult(command, stdout, stderr, int(completed.returncode))
    if result.returncode != 0:
        detail = _redacted_detail(completed, password)
        suffix = f": {detail}" if detail else ""
        raise EndpointTransitionError(f"{label} failed{suffix}")
    return result


def _validate_city_and_lock(
    city_root: Path,
    lock_path: Path,
    *,
    expected_city_root: Path,
) -> tuple[Path, Path, bytes]:
    city = _real_directory(city_root, label="city root", owner_only=True)
    expected = _real_directory(
        expected_city_root, label="expected city root", owner_only=True
    )
    if city != expected:
        raise EndpointTransitionError(
            f"endpoint operation is bound to exact city {expected}, not {city}"
        )
    _real_directory(city / "bin", label="city bin", owner_only=True)
    # Pinned gc 1.3.5 creates .gc as 0755 beneath the owner-only 0700 city
    # root.  Requiring a second owner-only boundary here rejects the upstream
    # scaffold without adding isolation; retain canonical ownership and the
    # no-group/world-write invariant instead.
    _real_directory(city / ".gc", label="city .gc")
    _real_directory(city / ".beads", label="city .beads", owner_only=True)
    lock = _lexical_absolute(lock_path, label="runtime lock")
    if lock != city / "runtime-lock.json":
        raise EndpointTransitionError(
            "endpoint operation requires the exact city runtime-lock.json"
        )
    content, _ = _regular_file(
        lock, label="runtime lock", exact_mode=0o600, private=True
    )
    return city, lock, content


@contextmanager
def _exclusive_runtime_lock(lock: Path) -> Iterator[None]:
    try:
        descriptor = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise EndpointTransitionError("cannot open exact runtime lock for serialization") from exc
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise EndpointTransitionError(
                "another endpoint or runtime-lock operation is in progress"
            ) from exc
        opened = os.fstat(descriptor)
        current = lock.lstat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise EndpointTransitionError("runtime lock changed during serialization")
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _assert_lock_unchanged(lock: Path, expected_sha256: str) -> None:
    content, _ = _regular_file(lock, label="runtime lock", exact_mode=0o600, private=True)
    if _sha256(content) != expected_sha256:
        raise EndpointTransitionError("runtime lock changed during endpoint operation")


def _verify_tools(
    city: Path,
    locked: Mapping[str, Any],
    *,
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    tools = locked.get("tools")
    if type(tools) is not dict or set(VERSION_ARGUMENTS) - set(tools):
        raise EndpointTransitionError("runtime lock lacks exact gc/bd/dolt records")
    records: dict[str, Any] = {}
    commands: dict[str, dict[str, Any]] = {}
    for name, version_args in VERSION_ARGUMENTS.items():
        record = tools.get(name)
        if type(record) is not dict:
            raise EndpointTransitionError(f"runtime lock {name} record is invalid")
        expected_version = record.get("version")
        expected_digest = record.get("binary_sha256")
        if (
            not isinstance(expected_version, str)
            or not expected_version
            or not isinstance(expected_digest, str)
            or SHA256_RE.fullmatch(expected_digest) is None
        ):
            raise EndpointTransitionError(f"runtime lock {name} identity is invalid")
        binary = city / "bin" / name
        content, metadata = _regular_file(binary, label=f"installed {name}")
        observed = _sha256(content)
        if observed != expected_digest:
            raise EndpointTransitionError(
                f"installed {name} does not match the exact runtime-lock digest"
            )
        if metadata.st_nlink != 1:
            raise EndpointTransitionError(f"installed {name} must not be hard-linked")
        result = _run_checked(
            (binary.as_posix(), *version_args),
            city=city,
            environment=environment,
            password=password,
            runner=runner,
            label=f"installed {name} version probe",
        )
        output = (result.stdout or result.stderr).strip()
        if re.search(
            rf"(?<![0-9A-Za-z]){re.escape(expected_version)}(?![0-9A-Za-z])",
            output,
        ) is None:
            raise EndpointTransitionError(
                f"installed {name} version output does not prove {expected_version}"
            )
        records[name] = {
            "path": binary.as_posix(),
            "version": expected_version,
            "binary_sha256": observed,
            "version_output_sha256": _sha256(output.encode("utf-8")),
        }
        commands[f"version_{name}"] = result.evidence()
    return records, commands


def _load_toml(path: Path, *, label: str, required: bool) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        if required:
            raise EndpointTransitionError(f"missing {label}: {path}")
        return {}
    content, _ = _regular_file(path, label=label)
    try:
        value = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise EndpointTransitionError(f"{label} is not valid TOML") from exc
    if type(value) is not dict:
        raise EndpointTransitionError(f"{label} must contain one TOML table")
    return value


def _rig_entries(value: Mapping[str, Any], *, label: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key in ("rigs", "rig"):
        raw = value.get(key, [])
        if raw in (None, {}):
            continue
        if type(raw) is not list or any(type(item) is not dict for item in raw):
            raise EndpointTransitionError(f"{label} {key} must be an array of tables")
        result.extend(raw)
    return result


def _active_flat_yaml(path: Path, *, label: str) -> dict[str, str]:
    if not path.exists() and not path.is_symlink():
        return {}
    content, _ = _regular_file(path, label=label)
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise EndpointTransitionError(f"{label} is not UTF-8") from exc
    result: dict[str, str] = {}
    for raw in lines:
        if not raw or raw[0].isspace() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise EndpointTransitionError(f"{label} contains unsupported active YAML")
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in result:
            raise EndpointTransitionError(f"{label} duplicates YAML key {key!r}")
        if value.startswith(('"', "'")) and value.endswith(value[:1]) and len(value) >= 2:
            value = value[1:-1]
        result[key] = value
    return result


def _discover_topology(
    city: Path,
    *,
    expected_aegis_root: Path,
) -> DiscoveredTopology:
    city_config = _load_toml(city / "city.toml", label="city.toml", required=True)
    site_path = city / ".gc" / "site.toml"
    site_config = _load_toml(site_path, label=".gc/site.toml", required=True)

    definitions: dict[str, dict[str, Any]] = {}
    for entry in _rig_entries(city_config, label="city.toml"):
        name = entry.get("name")
        if not isinstance(name, str) or SAFE_RIG_NAME_RE.fullmatch(name) is None:
            raise EndpointTransitionError("city.toml contains an invalid rig name")
        if name in definitions:
            raise EndpointTransitionError(f"city.toml duplicates rig {name!r}")
        definitions[name] = dict(entry)
    if set(definitions) != {"aegis"}:
        raise EndpointTransitionError(
            "HQ transition is allowed only while Aegis is the sole configured rig"
        )

    bindings: dict[str, str] = {}
    for entry in _rig_entries(site_config, label=".gc/site.toml"):
        name = entry.get("name")
        raw_path = entry.get("path")
        if not isinstance(name, str) or name not in definitions:
            raise EndpointTransitionError("site.toml binds an unknown rig")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise EndpointTransitionError(f"site.toml rig {name!r} lacks a path")
        if name in bindings:
            raise EndpointTransitionError(f"site.toml duplicates rig {name!r}")
        bindings[name] = raw_path
    if set(bindings) != {"aegis"}:
        raise EndpointTransitionError("site.toml must bind exactly the Aegis rig")

    raw_aegis = Path(bindings["aegis"]).expanduser()
    if not raw_aegis.is_absolute():
        raw_aegis = city / raw_aegis
    aegis = _real_directory(raw_aegis, label="Aegis rig root")
    expected_aegis = _real_directory(
        expected_aegis_root, label="expected Aegis rig root"
    )
    if aegis != expected_aegis:
        raise EndpointTransitionError(
            f"site.toml Aegis binding is {aegis}, expected {expected_aegis}"
        )
    definition = definitions["aegis"]
    if (
        definition.get("dolt_host") != AEGIS_HOST
        or str(definition.get("dolt_port", "")) != str(AEGIS_PORT)
    ):
        raise EndpointTransitionError(
            "Aegis rig compatibility endpoint must remain exact 127.0.0.1:33071"
        )

    aegis_config = _active_flat_yaml(
        aegis / ".beads" / "config.yaml", label="Aegis Beads config"
    )
    if "gc.endpoint_origin" in aegis_config:
        expected = {
            "gc.endpoint_origin": "explicit",
            "gc.endpoint_status": "verified",
            "dolt.host": AEGIS_HOST,
            "dolt.port": str(AEGIS_PORT),
            "dolt.user": AEGIS_USER,
        }
        if any(aegis_config.get(key) != value for key, value in expected.items()):
            raise EndpointTransitionError(
                "Aegis canonical endpoint is not the exact verified isolated service"
            )

    tracked = (
        TrackedPath("city_toml", "hq", city / "city.toml"),
        TrackedPath("site_toml", "hq", site_path),
        TrackedPath("hq_config", "hq", city / ".beads" / "config.yaml"),
        TrackedPath("hq_metadata", "hq", city / ".beads" / "metadata.json"),
        TrackedPath("hq_port", "hq", city / ".beads" / "dolt-server.port"),
        TrackedPath(
            "hq_managed_state",
            "hq",
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-state.json",
        ),
        TrackedPath(
            "hq_provider_state",
            "hq",
            city
            / ".gc"
            / "runtime"
            / "packs"
            / "dolt"
            / "dolt-provider-state.json",
        ),
        TrackedPath(
            "hq_provider_pid",
            "hq",
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.pid",
        ),
        TrackedPath(
            "hq_provider_lock",
            "hq",
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.lock",
        ),
        TrackedPath(
            "hq_provider_config",
            "hq",
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-config.yaml",
        ),
        TrackedPath(
            "hq_provider_log",
            "hq",
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.log",
        ),
        TrackedPath(
            "hq_provider_script",
            "hq",
            city / ".gc" / "scripts" / "gc-beads-bd.sh",
        ),
        TrackedPath("aegis_config", "aegis", aegis / ".beads" / "config.yaml"),
        TrackedPath("aegis_metadata", "aegis", aegis / ".beads" / "metadata.json"),
        TrackedPath("aegis_port", "aegis", aegis / ".beads" / "dolt-server.port"),
    )
    return DiscoveredTopology(city, aegis, tracked, city_config, site_config)


def _validate_path_ancestry(path: Path, *, roots: Sequence[Path], label: str) -> None:
    target = _lexical_absolute(path, label=label)
    root: Path | None = None
    for candidate in roots:
        try:
            target.relative_to(candidate)
        except ValueError:
            continue
        root = candidate
        break
    if root is None:
        raise EndpointTransitionError(f"{label} escaped the city and registered rig")
    cursor = root
    relative = target.relative_to(root)
    for component in relative.parts[:-1]:
        cursor = cursor / component
        if not cursor.exists() and not cursor.is_symlink():
            break
        try:
            metadata = cursor.lstat()
        except OSError as exc:
            raise EndpointTransitionError(f"cannot inspect {label} parent") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise EndpointTransitionError(f"{label} traverses a symlink")
        if not stat.S_ISDIR(metadata.st_mode):
            raise EndpointTransitionError(f"{label} parent is not a directory")
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise EndpointTransitionError(f"{label} parent is not owner-controlled")


def _snapshot_path(
    item: TrackedPath, *, roots: Sequence[Path]
) -> tuple[dict[str, Any], bytes | None]:
    path = item.path
    _validate_path_ancestry(path, roots=roots, label=item.role)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        # Distinguish a stable absence from a dangling link or an object that
        # appeared between the failed open and the absence check.
        try:
            path.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise EndpointTransitionError(f"cannot inspect {item.role}: {path}") from exc
        else:
            raise EndpointTransitionError(
                f"{item.role} changed concurrently while taking a snapshot"
            )
        return ({
            "role": item.role,
            "scope": item.scope,
            "path": path.as_posix(),
            "present": False,
            "mode": None,
            "uid": None,
            "size": 0,
            "sha256": None,
        }, None)
    except OSError as exc:
        raise EndpointTransitionError(
            f"{item.role} must be a real non-symlink file"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise EndpointTransitionError(
                f"{item.role} must be one singly-linked regular file"
            )
        if before.st_uid != os.getuid():
            raise EndpointTransitionError(f"{item.role} must be owned by the current user")
        if stat.S_IMODE(before.st_mode) & 0o022:
            raise EndpointTransitionError(
                f"{item.role} must not be group/world writable"
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_mode,
            before.st_nlink,
            before.st_uid,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_mode,
            after.st_nlink,
            after.st_uid,
        )
        if identity_before != identity_after or len(content) != after.st_size:
            raise EndpointTransitionError(
                f"{item.role} changed concurrently while taking a snapshot"
            )
        return ({
            "role": item.role,
            "scope": item.scope,
            "path": path.as_posix(),
            "present": True,
            "mode": stat.S_IMODE(after.st_mode),
            "uid": after.st_uid,
            "size": len(content),
            "sha256": _sha256(content),
        }, content)
    finally:
        os.close(descriptor)


def _entry_for_path(item: TrackedPath, *, roots: Sequence[Path]) -> dict[str, Any]:
    entry, _ = _snapshot_path(item, roots=roots)
    return entry


def _semantic_entries(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fields = ("role", "scope", "path", "present", "mode", "uid", "size", "sha256")
    return [{field: entry.get(field) for field in fields} for entry in entries]


def _manifest(
    topology: DiscoveredTopology,
    *,
    phase: str,
    evidence_root: Path | None = None,
    storage_name: str | None = None,
) -> tuple[dict[str, Any], bytes | None]:
    roots = (topology.city, topology.aegis)
    snapshots = [_snapshot_path(item, roots=roots) for item in topology.tracked]
    entries = [entry for entry, _ in snapshots]
    payloads = [payload for _, payload in snapshots]
    semantic = _semantic_entries(entries)
    result: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "phase": phase,
        "city_root": topology.city.as_posix(),
        "aegis_root": topology.aegis.as_posix(),
        "tree_sha256": _sha256(_canonical_json_bytes(semantic)),
        "entries": entries,
    }
    manifest_bytes: bytes | None = None
    if evidence_root is not None:
        phase_root = evidence_root / (phase if storage_name is None else storage_name)
        _create_private_directory(phase_root)
        files_root = phase_root / "files"
        _create_private_directory(files_root)
        for index, (entry, payload) in enumerate(zip(entries, payloads, strict=True)):
            if payload is None:
                continue
            relative = Path(phase) / "files" / f"{index:03d}.bin"
            destination = phase_root / "files" / f"{index:03d}.bin"
            _atomic_private_write(destination, payload, exclusive=True)
            entry["payload"] = relative.as_posix()
        manifest_bytes = _pretty_json_bytes(result)
        _atomic_private_write(
            phase_root / "manifest.json", manifest_bytes, exclusive=True
        )
    return result, manifest_bytes


def _persist_manifest(
    topology: DiscoveredTopology,
    *,
    phase: str,
    evidence_root: Path,
) -> tuple[dict[str, Any], bytes]:
    """Publish a complete snapshot directory with one atomic rename.

    A killed writer can leave only an owner-private dot-prefixed staging
    directory; readers never mistake it for a complete phase.  This closes the
    otherwise dangerous interval between creating ``after/`` and its final
    manifest write.
    """

    final_root = evidence_root / phase
    if final_root.exists() or final_root.is_symlink():
        raise EndpointTransitionError(f"append-only evidence already exists: {final_root}")
    storage_name = f".{phase}.{os.getpid()}.{os.urandom(8).hex()}"
    manifest, content = _manifest(
        topology,
        phase=phase,
        evidence_root=evidence_root,
        storage_name=storage_name,
    )
    assert content is not None
    staging_root = evidence_root / storage_name
    try:
        os.rename(staging_root, final_root)
        directory = os.open(evidence_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        raise EndpointTransitionError(
            f"cannot atomically publish {phase} endpoint evidence"
        ) from exc
    return manifest, content


def _manifests_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        left.get("city_root") == right.get("city_root")
        and left.get("aegis_root") == right.get("aegis_root")
        and _semantic_entries(left.get("entries", []))
        == _semantic_entries(right.get("entries", []))
    )


def _entry_semantic(entry: Mapping[str, Any]) -> dict[str, Any]:
    return _semantic_entries([entry])[0]


def _manifest_is_entrywise_mixture(
    current: Mapping[str, Any],
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> bool:
    mappings: list[dict[str, Mapping[str, Any]]] = []
    for manifest in (current, before, after):
        entries = manifest.get("entries")
        if type(entries) is not list or any(type(entry) is not dict for entry in entries):
            return False
        mapped = {str(entry.get("role")): entry for entry in entries}
        if len(mapped) != len(entries):
            return False
        mappings.append(mapped)
    current_entries, before_entries, after_entries = mappings
    if set(current_entries) != set(before_entries) or set(current_entries) != set(after_entries):
        return False
    for role, current_entry in current_entries.items():
        current_value = _entry_semantic(current_entry)
        if current_value not in (
            _entry_semantic(before_entries[role]),
            _entry_semantic(after_entries[role]),
        ):
            return False
    return True


def _entry_by_role(manifest: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    matches = [entry for entry in manifest.get("entries", []) if entry.get("role") == role]
    if len(matches) != 1:
        raise EndpointTransitionError(f"file manifest does not contain exact role {role}")
    return matches[0]


def _assert_dry_run_unchanged(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> None:
    if not _manifests_equal(before, after):
        raise EndpointTransitionError("gc endpoint dry-run mutated a topology file")


def _verify_hq_state(topology: DiscoveredTopology) -> dict[str, Any]:
    config = _active_flat_yaml(
        topology.city / ".beads" / "config.yaml", label="HQ Beads config"
    )
    expected_config = {
        "gc.endpoint_origin": "city_canonical",
        "gc.endpoint_status": "verified",
        "dolt.host": HQ_HOST,
        "dolt.port": str(HQ_PORT),
        "dolt.user": HQ_USER,
        "dolt.auto-start": "false",
    }
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise EndpointTransitionError("HQ Beads config does not prove the exact external endpoint")
    if "dolt_server_port" in config or "dolt.port-file" in config:
        raise EndpointTransitionError("HQ Beads config retains a deprecated endpoint mirror")

    city_toml = _load_toml(
        topology.city / "city.toml", label="post-transition city.toml", required=True
    )
    dolt = city_toml.get("dolt")
    if type(dolt) is not dict or dolt.get("host") != HQ_HOST or dolt.get("port") != HQ_PORT:
        raise EndpointTransitionError("city.toml does not bind exact HQ loopback endpoint")

    metadata_bytes, _ = _regular_file(
        topology.city / ".beads" / "metadata.json", label="HQ Beads metadata"
    )
    metadata = _strict_json_bytes(metadata_bytes, label="HQ Beads metadata")
    if (
        type(metadata) is not dict
        or metadata.get("backend") != "dolt"
        or metadata.get("database") != "dolt"
        or metadata.get("dolt_mode") != "server"
        or metadata.get("dolt_database") != HQ_DATABASE
        or type(metadata.get("project_id")) is not str
        or PROJECT_ID_RE.fullmatch(metadata["project_id"]) is None
    ):
        raise EndpointTransitionError("HQ metadata does not prove exact hq Dolt identity")
    if (topology.city / ".beads" / "dolt-server.port").exists():
        raise EndpointTransitionError("managed HQ port mirror survived external transition")
    if (topology.city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-state.json").exists():
        raise EndpointTransitionError("managed HQ runtime publication survived external transition")
    provider_pid = topology.city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.pid"
    if provider_pid.exists() or provider_pid.is_symlink():
        raise EndpointTransitionError("managed HQ provider pid survived external transition")
    _verify_stopped_provider_state(topology)
    return {
        "endpoint_origin": "city_canonical",
        "endpoint_status": "verified",
        "host": HQ_HOST,
        "port": HQ_PORT,
        "user": HQ_USER,
        "database": HQ_DATABASE,
    }


def _assert_aegis_isolated(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> None:
    # Pinned gc 1.3.5's provider stop canonicalizes harmless bd defaults in an
    # explicit rig config.  The rig metadata/identity must remain byte-exact,
    # while the config is validated semantically by _verify_aegis_state.
    if _semantic_entries([_entry_by_role(before, "aegis_metadata")]) != _semantic_entries(
        [_entry_by_role(after, "aegis_metadata")]
    ):
        raise EndpointTransitionError("HQ endpoint transition mutated Aegis identity metadata")
    port = _entry_by_role(after, "aegis_port")
    if port.get("present"):
        raise EndpointTransitionError("Aegis retained a managed Dolt port mirror")


def _verify_aegis_state(topology: DiscoveredTopology) -> None:
    config = _active_flat_yaml(
        topology.aegis / ".beads" / "config.yaml", label="Aegis Beads config"
    )
    expected_config = {
        "gc.endpoint_origin": "explicit",
        "gc.endpoint_status": "verified",
        "dolt.host": AEGIS_HOST,
        "dolt.port": str(AEGIS_PORT),
        "dolt.user": AEGIS_USER,
        "dolt.auto-start": "false",
    }
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise EndpointTransitionError(
            "Aegis endpoint changed while transitioning HQ"
        )
    content, _ = _regular_file(
        topology.aegis / ".beads" / "metadata.json",
        label="Aegis Beads metadata",
    )
    metadata = _strict_json_bytes(content, label="Aegis Beads metadata")
    if (
        type(metadata) is not dict
        or metadata.get("backend") != "dolt"
        or metadata.get("database") != "dolt"
        or metadata.get("dolt_mode") != "server"
        or metadata.get("dolt_database") != "aegis_beads"
    ):
        raise EndpointTransitionError(
            "Aegis database identity changed while transitioning HQ"
        )


def _verify_stopped_provider_state(topology: DiscoveredTopology) -> None:
    path = (
        topology.city
        / ".gc"
        / "runtime"
        / "packs"
        / "dolt"
        / "dolt-provider-state.json"
    )
    if not path.exists() and not path.is_symlink():
        return
    content, _ = _regular_file(path, label="HQ provider runtime state")
    value = _strict_json_bytes(content, label="HQ provider runtime state")
    if (
        type(value) is not dict
        or value.get("running") is not False
        or value.get("pid") != 0
    ):
        raise EndpointTransitionError("HQ provider runtime state does not prove stopped")


def _validate_supervisor(
    value: Mapping[str, Any], *, environment: Mapping[str, str]
) -> dict[str, Any]:
    raw_home = environment.get("HOME")
    if not raw_home:
        raise EndpointTransitionError("supervisor proof requires an explicit HOME")
    home = _lexical_absolute(Path(raw_home), label="supervisor HOME")
    raw_runtime = environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    runtime = _lexical_absolute(Path(raw_runtime), label="supervisor runtime directory")
    expected_paths = [
        (runtime / "gc" / "supervisor.sock").as_posix(),
        (home / ".gc" / "supervisor.sock").as_posix(),
    ]
    if (
        value.get("schema_version") != "1"
        or value.get("ok") is not True
        or value.get("running") is not False
        or value.get("pid") != 0
        or value.get("socket_path") != ""
        or type(value.get("checked_paths")) is not list
        or value["checked_paths"] != expected_paths
    ):
        raise EndpointTransitionError("gc supervisor status does not prove exact city stopped")
    return {
        "schema_version": "1",
        "running": False,
        "pid": 0,
        "checked_paths": list(value["checked_paths"]),
    }


def _supervisor_stopped(
    city: Path,
    *,
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    gc = city / "bin" / "gc"
    result = _run_checked(
        (gc.as_posix(), "--city", city.as_posix(), "supervisor", "status", "--json"),
        city=city,
        environment=environment,
        password=password,
        runner=runner,
        label="gc supervisor status",
    )
    value = _strict_json_object(result.stdout, label="gc supervisor status")
    return _validate_supervisor(value, environment=environment), result.evidence()


def _validate_connection_proof(
    city: Path,
    *,
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    bd = city / "bin" / "bd"
    # bd 1.1.0 removes deprecated server-user fields from metadata during the
    # official endpoint transition.  Its direct CLI does not project the
    # canonical dolt.user key the way gc does, so bind this read-only proof to
    # the exact already-validated HQ endpoint instead of allowing bd to fall
    # back to the root account.
    proof_environment = dict(environment)
    proof_environment.update(
        {
            "BEADS_DIR": (city / ".beads").as_posix(),
            "BEADS_DOLT_SERVER_HOST": HQ_HOST,
            "BEADS_DOLT_SERVER_PORT": str(HQ_PORT),
            "BEADS_DOLT_SERVER_USER": HQ_USER,
            "BEADS_DOLT_SERVER_DATABASE": HQ_DATABASE,
            "GC_DOLT_HOST": HQ_HOST,
            "GC_DOLT_PORT": str(HQ_PORT),
            "GC_DOLT_USER": HQ_USER,
            "GC_DOLT_DATABASE": HQ_DATABASE,
        }
    )
    commands = {
        "context": (
            bd.as_posix(),
            "-C",
            city.as_posix(),
            "--readonly",
            "where",
            "--json",
        ),
        "show": (
            bd.as_posix(),
            "-C",
            city.as_posix(),
            "--readonly",
            "dolt",
            "show",
            "--json",
        ),
        "test": (
            bd.as_posix(),
            "-C",
            city.as_posix(),
            "--readonly",
            "dolt",
            "test",
            "--json",
        ),
    }
    values: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    for name, argv in commands.items():
        result = _run_checked(
            argv,
            city=city,
            environment=proof_environment,
            password=password,
            runner=runner,
            label=f"bd {name} proof",
        )
        values[name] = _strict_json_object(result.stdout, label=f"bd {name} proof")
        evidence[f"proof_{name}"] = result.evidence()

    context = values["context"]
    if (
        context.get("schema_version") != 1
        or context.get("path") != (city / ".beads").as_posix()
        or context.get("database_path") != (city / ".beads" / "dolt").as_posix()
        or context.get("prefix") != "gc"
    ):
        raise EndpointTransitionError("bd where does not prove exact HQ scope identity")
    show = values["show"]
    if (
        show.get("schema_version") != 1
        or show.get("backend") != "dolt"
        or show.get("connection_ok") is not True
        or show.get("embedded") is not False
        or show.get("host") != HQ_HOST
        or show.get("port") != HQ_PORT
        or show.get("user") != HQ_USER
        or show.get("database") != HQ_DATABASE
    ):
        raise EndpointTransitionError("bd dolt show does not prove exact live HQ endpoint")
    test = values["test"]
    if (
        test.get("schema_version") != 1
        or test.get("connection_ok") is not True
        or test.get("host") != HQ_HOST
        or test.get("port") != HQ_PORT
    ):
        raise EndpointTransitionError("bd dolt test does not prove live HQ connectivity")
    return {
        "context": {
            "backend": "dolt",
            "bd_version": "1.1.0",
            "beads_dir": (city / ".beads").as_posix(),
            "database": HQ_DATABASE,
            "dolt_mode": "server",
        },
        "show": {
            "connection_ok": True,
            "host": HQ_HOST,
            "port": HQ_PORT,
            "user": HQ_USER,
            "database": HQ_DATABASE,
        },
        "test": {"connection_ok": True, "host": HQ_HOST, "port": HQ_PORT},
    }, evidence


def _create_private_directory(path: Path) -> None:
    target = _lexical_absolute(path, label="private evidence directory")
    if target.exists() or target.is_symlink():
        raise EndpointTransitionError(f"append-only evidence already exists: {target}")
    parent = target.parent
    if parent.is_symlink() or not parent.is_dir():
        raise EndpointTransitionError("evidence parent must be a real directory")
    metadata = parent.lstat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise EndpointTransitionError("evidence parent must be owner-only")
    try:
        target.mkdir(mode=0o700)
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        raise EndpointTransitionError(f"cannot create private evidence directory: {target}") from exc


def _ensure_private_parent(path: Path, *, city: Path) -> None:
    target = _lexical_absolute(path, label="evidence parent")
    try:
        target.relative_to(city)
    except ValueError as exc:
        raise EndpointTransitionError("evidence escaped the exact city") from exc
    missing: list[Path] = []
    cursor = target
    while not cursor.exists() and not cursor.is_symlink():
        missing.append(cursor)
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise EndpointTransitionError("evidence path traverses a symlink")
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    cursor = city
    for component in target.relative_to(city).parts:
        cursor = cursor / component
        metadata = cursor.lstat()
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) & 0o077
        ):
            raise EndpointTransitionError("evidence directories must be real and owner-only")


def _atomic_private_write(path: Path, content: bytes, *, exclusive: bool) -> None:
    if path.is_symlink():
        raise EndpointTransitionError("private evidence target must not be a symlink")
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise EndpointTransitionError("private evidence parent must be a real directory")
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    temporary = Path(raw_temporary)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError as exc:
                raise EndpointTransitionError(
                    f"append-only evidence already exists: {path}"
                ) from exc
            temporary.unlink()
        else:
            os.replace(temporary, path)
        os.chmod(path, 0o600)
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _evidence_directory(
    requested: Path,
    *,
    city: Path,
    category: str,
    create: bool,
) -> Path:
    path = _lexical_absolute(requested, label=f"{category} evidence directory")
    expected_parent = city / "runtime" / "evidence" / category
    if path.parent != expected_parent or SAFE_RUN_NAME_RE.fullmatch(path.name) is None:
        raise EndpointTransitionError(
            f"{category} evidence must be one safe run beneath {expected_parent}"
        )
    _ensure_private_parent(expected_parent, city=city)
    if create:
        _create_private_directory(path)
    else:
        _real_directory(path, label=f"{category} evidence directory", owner_only=True)
    return path


def _write_json(path: Path, value: Mapping[str, Any]) -> tuple[str, bytes]:
    content = _pretty_json_bytes(value)
    _atomic_private_write(path, content, exclusive=True)
    return _sha256(content), content


def _read_private_json(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    content, _ = _regular_file(path, label=label, exact_mode=0o600, private=True)
    value = _strict_json_bytes(content, label=label)
    if type(value) is not dict:
        raise EndpointTransitionError(f"{label} must contain one JSON object")
    return value, content


def _manifest_reference(
    evidence_root: Path,
    manifest: Mapping[str, Any],
    manifest_bytes: bytes,
    *,
    phase: str,
) -> dict[str, Any]:
    return {
        "path": f"{phase}/manifest.json",
        "sha256": _sha256(manifest_bytes),
        "tree_sha256": manifest["tree_sha256"],
    }


def _load_manifest_reference(
    evidence_root: Path,
    reference: Mapping[str, Any],
    *,
    phase: str,
) -> dict[str, Any]:
    expected = {"path", "sha256", "tree_sha256"}
    if set(reference) != expected or reference.get("path") != f"{phase}/manifest.json":
        raise EndpointTransitionError(f"{phase} manifest reference is invalid")
    for field in ("sha256", "tree_sha256"):
        if not isinstance(reference.get(field), str) or SHA256_RE.fullmatch(reference[field]) is None:
            raise EndpointTransitionError(f"{phase} manifest digest is invalid")
    value, content = _read_private_json(
        evidence_root / reference["path"], label=f"{phase} manifest"
    )
    if _sha256(content) != reference["sha256"]:
        raise EndpointTransitionError(f"{phase} manifest content digest mismatch")
    if (
        value.get("schema_version") != MANIFEST_SCHEMA
        or value.get("phase") != phase
        or value.get("tree_sha256") != reference["tree_sha256"]
        or value.get("tree_sha256")
        != _sha256(_canonical_json_bytes(_semantic_entries(value.get("entries", []))))
    ):
        raise EndpointTransitionError(f"{phase} manifest structure is invalid")
    roles: set[str] = set()
    paths: set[str] = set()
    for entry in value.get("entries", []):
        if type(entry) is not dict:
            raise EndpointTransitionError(f"{phase} manifest entry is invalid")
        role = entry.get("role")
        raw_path = entry.get("path")
        if not isinstance(role, str) or role in roles or not isinstance(raw_path, str) or raw_path in paths:
            raise EndpointTransitionError(f"{phase} manifest aliases a tracked file")
        roles.add(role)
        paths.add(raw_path)
        if entry.get("present"):
            payload = entry.get("payload")
            if not isinstance(payload, str) or payload != f"{phase}/files/{len(roles)-1:03d}.bin":
                raise EndpointTransitionError(f"{phase} manifest payload path is invalid")
            payload_path = evidence_root / payload
            payload_bytes, _ = _regular_file(
                payload_path, label=f"{phase} payload", exact_mode=0o600, private=True
            )
            if len(payload_bytes) != entry.get("size") or _sha256(payload_bytes) != entry.get("sha256"):
                raise EndpointTransitionError(f"{phase} snapshot payload digest mismatch")
        elif entry.get("payload") is not None:
            raise EndpointTransitionError(f"absent {phase} entry has a payload")
    required_roles = {item for item in (
        "city_toml", "site_toml", "hq_config", "hq_metadata", "hq_port",
        "hq_managed_state", "hq_provider_state", "hq_provider_pid",
        "hq_provider_lock", "hq_provider_config", "hq_provider_log",
        "hq_provider_script",
        "aegis_config", "aegis_metadata", "aegis_port"
    )}
    if roles != required_roles:
        raise EndpointTransitionError(f"{phase} manifest tracked-file set is incomplete")
    return value


def _transition_argv(city: Path, *, dry_run: bool) -> tuple[str, ...]:
    argv = (
        (city / "bin" / "gc").as_posix(),
        "--city",
        city.as_posix(),
        "beads",
        "city",
        "use-external",
        "--host",
        HQ_HOST,
        "--port",
        str(HQ_PORT),
        "--user",
        HQ_USER,
    )
    if dry_run:
        return (*argv, "--dry-run")
    return argv


def _load_transition_receipt(
    evidence_root: Path,
) -> tuple[dict[str, Any], bytes, dict[str, Any], dict[str, Any]]:
    receipt, content = _read_private_json(
        evidence_root / "transition-receipt.json", label="endpoint transition receipt"
    )
    required = {
        "schema_version", "kind", "status", "created_at", "city_root",
        "aegis_root", "runtime_lock", "endpoint", "tools", "commands",
        "supervisor", "before", "after", "connection_proof", "credential_transport",
    }
    if (
        set(receipt) != required
        or receipt.get("schema_version") != TRANSITION_SCHEMA
        or receipt.get("kind") != "hq-host-external-endpoint"
        or receipt.get("status") != "verified"
        or receipt.get("credential_transport") != "owner-only-environment-file"
    ):
        raise EndpointTransitionError("endpoint transition receipt shape is invalid")
    before = _load_manifest_reference(
        evidence_root, receipt.get("before", {}), phase="before"
    )
    after = _load_manifest_reference(
        evidence_root, receipt.get("after", {}), phase="after"
    )
    return receipt, content, before, after


def _row_value(row: Mapping[str, Any], name: str) -> Any:
    if name in row:
        return row[name]
    return row.get(name.upper())


def _nonnegative_integer(value: Any, *, label: str) -> int:
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and re.fullmatch(r"[0-9]+", value):
        return int(value)
    raise EndpointTransitionError(f"HQ database returned invalid {label}")


def _hq_sql_rows(
    city: Path,
    query: str,
    *,
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
    label: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    result = _run_checked(
        (
            (city / "bin" / "dolt").as_posix(),
            "--host",
            HQ_HOST,
            "--port",
            str(HQ_PORT),
            "--user",
            HQ_USER,
            "--use-db",
            HQ_DATABASE,
            "--no-tls",
            "sql",
            "--result-format",
            "json",
            "--query",
            query,
        ),
        city=city,
        environment=environment,
        password=password,
        runner=runner,
        label=label,
    )
    value = _strict_json_object(result.stdout, label=label)
    if value == {}:
        rows: Any = []
    elif set(value) == {"rows"}:
        rows = value["rows"]
    else:
        raise EndpointTransitionError(f"{label} returned unexpected JSON fields")
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        raise EndpointTransitionError(f"{label} did not return exact JSON rows")
    return rows, result.evidence()


def _hq_database_state(
    city: Path,
    *,
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
    allow_interrupted: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    schema_rows, schema_command = _hq_sql_rows(
        city,
        (
            "SELECT table_name, table_type FROM information_schema.tables "
            "WHERE table_schema = 'hq' ORDER BY table_name;"
        ),
        runner=runner,
        environment=environment,
        password=password,
        label="HQ Beads schema preflight",
    )
    schema: list[tuple[str, str]] = []
    for row in schema_rows:
        name = _row_value(row, "table_name")
        kind = _row_value(row, "table_type")
        if type(name) is not str or type(kind) is not str:
            raise EndpointTransitionError("HQ Beads schema row is invalid")
        schema.append((name, kind))
    expected_schema = list(HQ_BEADS_SCHEMA)
    expected_set = set(expected_schema)
    observed_set = set(schema)
    if observed_set - expected_set:
        raise EndpointTransitionError("HQ database contains a foreign table or view")
    if len(schema) != len(observed_set) or schema != [
        item for item in expected_schema if item in observed_set
    ]:
        raise EndpointTransitionError("HQ Beads schema is duplicated or unordered")
    if schema and schema != expected_schema and not allow_interrupted:
        raise EndpointTransitionError("new HQ database is not virgin")

    status_rows, status_command = _hq_sql_rows(
        city,
        "SELECT table_name, status, staged FROM dolt_status ORDER BY table_name;",
        runner=runner,
        environment=environment,
        password=password,
        label="HQ Dolt working-set preflight",
    )
    status: list[dict[str, Any]] = []
    for row in status_rows:
        table_name = _row_value(row, "table_name")
        change = _row_value(row, "status")
        staged = _row_value(row, "staged")
        if type(table_name) is not str or type(change) is not str:
            raise EndpointTransitionError("HQ Dolt working-set row is invalid")
        staged_value = _nonnegative_integer(staged, label="working-set staged flag")
        status.append(
            {"table_name": table_name, "status": change, "staged": staged_value}
        )
    if status not in ([], [{"table_name": "config", "status": "modified", "staged": 0}]):
        raise EndpointTransitionError("HQ database has an unexpected working-set change")

    branch_rows, branch_command = _hq_sql_rows(
        city,
        (
            "SELECT (SELECT COUNT(*) FROM dolt_branches) AS branch_count, "
            "(SELECT COUNT(*) FROM dolt_branches WHERE name = 'main') "
            "AS main_branch_count, (SELECT COUNT(*) FROM dolt_log) AS commit_count, "
            "HASHOF('main') AS head;"
        ),
        runner=runner,
        environment=environment,
        password=password,
        label="HQ Dolt history preflight",
    )
    if len(branch_rows) != 1:
        raise EndpointTransitionError("HQ Dolt history preflight did not return one row")
    branch = branch_rows[0]
    branch_count = _nonnegative_integer(
        _row_value(branch, "branch_count"), label="branch count"
    )
    main_branch_count = _nonnegative_integer(
        _row_value(branch, "main_branch_count"), label="main branch count"
    )
    commit_count = _nonnegative_integer(
        _row_value(branch, "commit_count"), label="commit count"
    )
    head = _row_value(branch, "head")
    if (
        branch_count != 1
        or main_branch_count != 1
        or commit_count < 1
        or type(head) is not str
        or re.fullmatch(r"[a-z0-9]{20,128}", head) is None
    ):
        raise EndpointTransitionError("HQ Dolt history is not one valid main branch")

    counts: dict[str, int] = {}
    runtime_config: list[dict[str, str]] = []
    count_command: dict[str, Any] | None = None
    runtime_config_command: dict[str, Any] | None = None
    base_tables = [name for name, kind in schema if kind == "BASE TABLE"]
    if base_tables:
        count_query = "SELECT " + ", ".join(
            f"(SELECT COUNT(*) FROM `{name}`) AS `{name}_count`"
            for name in base_tables
        ) + ";"
        count_rows, count_command = _hq_sql_rows(
            city,
            count_query,
            runner=runner,
            environment=environment,
            password=password,
            label="HQ Beads table-count preflight",
        )
        if len(count_rows) != 1:
            raise EndpointTransitionError("HQ Beads table-count preflight returned wrong rows")
        for name in base_tables:
            counts[name] = _nonnegative_integer(
                _row_value(count_rows[0], f"{name}_count"),
                label=f"{name} row count",
            )
        if any(counts.get(name, 0) != 0 for name in HQ_BEADS_CONTENT_TABLES):
            raise EndpointTransitionError("HQ Beads database contains issue or user content")
        for name, maximum in HQ_BEADS_SEEDED_ROW_COUNTS.items():
            if counts.get(name, 0) > maximum:
                raise EndpointTransitionError(
                    f"HQ Beads seeded table {name} exceeds the pinned empty shape"
                )
        if "config" in base_tables:
            runtime_rows, runtime_config_command = _hq_sql_rows(
                city,
                (
                    "SELECT `key`, value FROM config WHERE `key` IN "
                    "('issue_prefix', 'types.custom') ORDER BY `key`;"
                ),
                runner=runner,
                environment=environment,
                password=password,
                label="HQ Beads runtime-config preflight",
            )
            for row in runtime_rows:
                key = _row_value(row, "key")
                value = _row_value(row, "value")
                if type(key) is not str or type(value) is not str:
                    raise EndpointTransitionError(
                        "HQ Beads runtime-config row is invalid"
                    )
                runtime_config.append({"key": key, "value": value})
            allowed_runtime_config = (
                [{"key": "issue_prefix", "value": "gc"}],
                [
                    {"key": "issue_prefix", "value": "gc"},
                    {"key": "types.custom", "value": HQ_BEADS_CUSTOM_TYPES},
                ],
            )
            if runtime_config not in allowed_runtime_config:
                raise EndpointTransitionError(
                    "HQ Beads runtime config is not a safe Gas City subset"
                )

    if not schema:
        if status:
            raise EndpointTransitionError("virgin HQ database has a dirty working set")
        state = "virgin"
    elif schema == expected_schema:
        expected_counts = {
            **{name: 0 for name in HQ_BEADS_CONTENT_TABLES},
            **HQ_BEADS_SEEDED_ROW_COUNTS,
        }
        complete_runtime_config = [
            {"key": "issue_prefix", "value": "gc"},
            {"key": "types.custom", "value": HQ_BEADS_CUSTOM_TYPES},
        ]
        if counts == expected_counts and status == [
            {"table_name": "config", "status": "modified", "staged": 0}
        ] and runtime_config == complete_runtime_config:
            state = "initialized-empty"
        elif allow_interrupted and status == [
            {"table_name": "config", "status": "modified", "staged": 0}
        ]:
            state = "interrupted-empty"
        else:
            raise EndpointTransitionError(
                "HQ Beads database is not the exact pinned initialized-empty shape"
            )
    else:
        if not allow_interrupted:
            raise EndpointTransitionError("HQ Beads schema is only partially initialized")
        state = "interrupted-empty"

    result = {
        "state": state,
        "schema": [
            {"name": name, "type": kind} for name, kind in schema
        ],
        "row_counts": counts,
        "runtime_config": runtime_config,
        "working_set": status,
        "branch_count": branch_count,
        "main_branch_count": main_branch_count,
        "commit_count": commit_count,
        "main_head": head,
    }
    commands = {
        "schema": schema_command,
        "working_set": status_command,
        "history": branch_command,
    }
    if count_command is not None:
        commands["table_counts"] = count_command
    if runtime_config_command is not None:
        commands["runtime_config"] = runtime_config_command
    return result, commands


def _hq_local_state(
    city: Path,
    *,
    password: str,
    phase: str,
) -> dict[str, Any]:
    beads = _real_directory(city / ".beads", label="HQ .beads", owner_only=True)
    names = {path.name for path in beads.iterdir()}
    if names - HQ_BEADS_LOCAL_NAMES:
        raise EndpointTransitionError("HQ .beads contains an unexpected local entry")
    required = {"config.yaml", "metadata.json"}
    if not required <= names:
        raise EndpointTransitionError("HQ .beads is missing its canonical scaffold")
    if phase == "initial" and names != required:
        raise EndpointTransitionError("new HQ local Beads scaffold is not pristine")
    if phase == "complete" and names != HQ_BEADS_LOCAL_NAMES:
        raise EndpointTransitionError("initialized HQ local Beads files are incomplete")

    entries: list[dict[str, Any]] = []
    for name in sorted(names):
        path = beads / name
        metadata = path.lstat()
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise EndpointTransitionError("HQ .beads entry is not owner-controlled")
        if name == "dolt":
            if path.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
                raise EndpointTransitionError("HQ Dolt data root must be one real directory")
            entries.append({"name": name, "kind": "managed-data-directory"})
            continue
        content, _ = _regular_file(path, label=f"HQ .beads/{name}")
        if len(content) > 1024 * 1024:
            raise EndpointTransitionError("HQ local Beads file exceeds its size ceiling")
        if password.encode("utf-8") in content:
            raise EndpointTransitionError("bd persisted the HQ credential in local state")
        entries.append(
            {
                "name": name,
                "kind": "file",
                "size": len(content),
                "sha256": _sha256(content),
            }
        )

    config, _ = _regular_file(beads / "config.yaml", label="HQ Beads config")
    allowed_configs = (
        {HQ_BEADS_INITIAL_CONFIG}
        if phase == "initial"
        else {HQ_BEADS_CONFIG}
        if phase == "complete"
        else {HQ_BEADS_INITIAL_CONFIG, HQ_BEADS_CONFIG}
    )
    if config not in allowed_configs:
        raise EndpointTransitionError("HQ Beads config is not the exact unverified scaffold")
    metadata_bytes, _ = _regular_file(
        beads / "metadata.json", label="HQ Beads metadata"
    )
    metadata = _strict_json_bytes(metadata_bytes, label="HQ Beads metadata")
    base_metadata = {
        "backend": "dolt",
        "database": "dolt",
        "dolt_database": HQ_DATABASE,
        "dolt_mode": "server",
    }
    project_id: str | None = None
    if phase == "initial":
        if metadata != base_metadata:
            raise EndpointTransitionError("new HQ metadata is not the exact gc scaffold")
    else:
        project_id = metadata.get("project_id") if type(metadata) is dict else None
        completed_metadata = {
            "database": "dolt",
            "backend": "dolt",
            "dolt_mode": "server",
            "dolt_server_host": HQ_HOST,
            "dolt_server_port": HQ_PORT,
            "dolt_server_user": HQ_USER,
            "dolt_database": HQ_DATABASE,
            "project_id": project_id,
        }
        if (
            metadata != completed_metadata
            or type(project_id) is not str
            or PROJECT_ID_RE.fullmatch(project_id) is None
        ):
            if phase == "resume" and metadata == base_metadata:
                project_id = None
            else:
                raise EndpointTransitionError("HQ metadata is not a safe initialization state")

    generated = {
        ".gitignore": HQ_BEADS_GITIGNORE_SHA256,
        "README.md": HQ_BEADS_README_SHA256,
    }
    for name, digest in generated.items():
        if name in names and _sha256((beads / name).read_bytes()) != digest:
            raise EndpointTransitionError(f"pinned bd generated unexpected {name}")
    if ".local_version" in names and (beads / ".local_version").read_bytes() != b"1.1.0\n":
        raise EndpointTransitionError("HQ local bd version marker is invalid")
    if "interactions.jsonl" in names and (beads / "interactions.jsonl").read_bytes():
        raise EndpointTransitionError("new HQ contains interaction records")
    if "dolt-server.port" in names and (beads / "dolt-server.port").read_bytes() != b"33070":
        raise EndpointTransitionError("HQ managed port mirror is inconsistent")
    if phase == "complete" and project_id is None:
        raise EndpointTransitionError("initialized HQ lacks a project identity")
    return {
        "phase": phase,
        "project_id": project_id,
        "tree_sha256": _sha256(_canonical_json_bytes(entries)),
        "entries": entries,
    }


def _hq_initialization_argv(city: Path) -> tuple[str, ...]:
    return (
        (city / "bin" / "bd").as_posix(),
        "init",
        "--server",
        "--external",
        "--reinit-local",
        "--server-host",
        HQ_HOST,
        "--server-port",
        str(HQ_PORT),
        "--server-user",
        HQ_USER,
        "--database",
        HQ_DATABASE,
        "--prefix",
        "gc",
        "--non-interactive",
        "--skip-agents",
        "--skip-hooks",
        "--quiet",
    )


def _hq_runtime_config_argv(city: Path) -> tuple[str, ...]:
    query = (
        "INSERT INTO config (`key`, value) VALUES "
        f"('types.custom', '{HQ_BEADS_CUSTOM_TYPES}') "
        "ON DUPLICATE KEY UPDATE value = VALUES(value);"
    )
    return (
        (city / "bin" / "dolt").as_posix(),
        "--host",
        HQ_HOST,
        "--port",
        str(HQ_PORT),
        "--user",
        HQ_USER,
        "--use-db",
        HQ_DATABASE,
        "--no-tls",
        "sql",
        "--result-format",
        "json",
        "--query",
        query,
    )


def _hq_schema_migration_argv(city: Path) -> tuple[str, ...]:
    return (
        (city / "bin" / "bd").as_posix(),
        "--json",
        "--dolt-auto-commit",
        "on",
        "-C",
        city.as_posix(),
        "migrate",
        "schema",
    )


def _replace_hq_config(path: Path, expected_before: bytes) -> None:
    current, _ = _regular_file(path, label="HQ Beads config")
    if current == HQ_BEADS_CONFIG:
        return
    if current != expected_before:
        raise EndpointTransitionError("HQ Beads config drifted before custom-type binding")
    parent = path.parent
    descriptor, temporary_name = tempfile.mkstemp(prefix=".config.yaml.types.", dir=parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(HQ_BEADS_CONFIG)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _assert_hq_initialization_scope(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> None:
    allowed = {"hq_config", "hq_metadata", "hq_port"}
    before_entries = {
        str(entry.get("role")): entry for entry in before.get("entries", [])
    }
    after_entries = {
        str(entry.get("role")): entry for entry in after.get("entries", [])
    }
    if set(before_entries) != set(after_entries):
        raise EndpointTransitionError("HQ initialization changed the tracked-file set")
    for role in set(before_entries) - allowed:
        if _entry_semantic(before_entries[role]) != _entry_semantic(after_entries[role]):
            raise EndpointTransitionError(
                f"HQ initialization mutated out-of-scope topology role {role}"
            )


def initialize_hq_beads(
    city_root: Path,
    lock_path: Path,
    evidence_dir: Path,
    *,
    password: str,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    expected_city_root: Path = PRODUCTION_CITY_ROOT,
    expected_aegis_root: Path = PRODUCTION_AEGIS_ROOT,
    lock_loader: LockLoader = gas_city_ops.load_runtime_lock,
    phase_hook: Callable[[str], None] | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Initialize only a new external HQ store under an append-only journal."""

    city, lock, lock_bytes = _validate_city_and_lock(
        city_root, lock_path, expected_city_root=expected_city_root
    )
    lock_sha256 = _sha256(lock_bytes)
    env = _command_environment(city, password, environment)
    requested_evidence = _lexical_absolute(
        evidence_dir, label="HQ initialization evidence"
    )
    hook = phase_hook or (lambda _phase: None)

    with _exclusive_runtime_lock(lock):
        _assert_lock_unchanged(lock, lock_sha256)
        locked = lock_loader(lock)
        tools, version_commands = _verify_tools(
            city, locked, runner=runner, environment=env, password=password
        )
        supervisor_before, supervisor_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        topology = _discover_topology(
            city, expected_aegis_root=expected_aegis_root
        )
        current, _ = _manifest(topology, phase="current")
        exists = requested_evidence.exists() or requested_evidence.is_symlink()
        evidence_root = _evidence_directory(
            requested_evidence,
            city=city,
            category="beads-initialization",
            create=not exists,
        )
        intent_path = evidence_root / "intent.json"
        receipt_path = evidence_root / "initialization-receipt.json"
        argv = _hq_initialization_argv(city)

        if receipt_path.exists() or receipt_path.is_symlink():
            receipt, receipt_bytes = _read_private_json(
                receipt_path, label="HQ initialization receipt"
            )
            before = _load_manifest_reference(
                evidence_root, receipt.get("before", {}), phase="before"
            )
            after = _load_manifest_reference(
                evidence_root, receipt.get("after", {}), phase="after"
            )
            expected_receipt_fields = {
                "schema_version", "kind", "status", "created_at", "city_root",
                "aegis_root", "runtime_lock", "endpoint", "tools", "commands",
                "supervisor", "before", "after", "local_state", "database_state",
                "credential_transport",
            }
            local = _hq_local_state(city, password=password, phase="complete")
            database, _ = _hq_database_state(
                city,
                runner=runner,
                environment=env,
                password=password,
                allow_interrupted=False,
            )
            if (
                set(receipt) != expected_receipt_fields
                or receipt.get("schema_version") != HQ_INITIALIZATION_SCHEMA
                or receipt.get("kind") != "hq-external-beads-initialization"
                or receipt.get("status") != "verified"
                or receipt.get("city_root") != city.as_posix()
                or receipt.get("aegis_root") != topology.aegis.as_posix()
                or receipt.get("runtime_lock")
                != {"path": lock.as_posix(), "sha256": lock_sha256}
                or receipt.get("endpoint")
                != {"host": HQ_HOST, "port": HQ_PORT, "user": HQ_USER, "database": HQ_DATABASE}
                or receipt.get("local_state") != local
                or receipt.get("database_state") != database
                or not _manifests_equal(current, after)
            ):
                raise EndpointTransitionError("HQ initialization receipt is not exact")
            _assert_hq_initialization_scope(before, after)
            _assert_tools_match_receipt(tools, receipt.get("tools"))
            _assert_lock_unchanged(lock, lock_sha256)
            return {
                "status": "already-initialized",
                "action": "none",
                "project_id": local["project_id"],
                "receipt_path": receipt_path.as_posix(),
                "receipt_sha256": _sha256(receipt_bytes),
            }

        if intent_path.exists() or intent_path.is_symlink():
            intent, intent_bytes = _read_private_json(
                intent_path, label="HQ initialization intent"
            )
            expected_intent_fields = {
                "schema_version", "kind", "status", "created_at", "city_root",
                "aegis_root", "runtime_lock", "endpoint", "argv", "tools",
                "supervisor", "local_state", "database_state", "commands",
                "credential_transport",
            }
            if (
                set(intent) != expected_intent_fields
                or intent.get("schema_version") != HQ_INITIALIZATION_SCHEMA
                or intent.get("kind") != "hq-external-beads-initialization-intent"
                or intent.get("status") != "prepared"
                or intent.get("city_root") != city.as_posix()
                or intent.get("aegis_root") != topology.aegis.as_posix()
                or intent.get("runtime_lock")
                != {"path": lock.as_posix(), "sha256": lock_sha256}
                or intent.get("argv") != list(argv)
            ):
                raise EndpointTransitionError("HQ initialization intent is invalid")
            _assert_tools_match_receipt(tools, intent.get("tools"))
        else:
            local_initial = _hq_local_state(city, password=password, phase="initial")
            database_initial, database_commands = _hq_database_state(
                city,
                runner=runner,
                environment=env,
                password=password,
                allow_interrupted=False,
            )
            if database_initial["state"] != "virgin":
                raise EndpointTransitionError("new HQ database is not virgin")
            intent = {
                "schema_version": HQ_INITIALIZATION_SCHEMA,
                "kind": "hq-external-beads-initialization-intent",
                "status": "prepared",
                "created_at": _format_utc(_utc_now() if now is None else now),
                "city_root": city.as_posix(),
                "aegis_root": topology.aegis.as_posix(),
                "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
                "endpoint": {"host": HQ_HOST, "port": HQ_PORT, "user": HQ_USER, "database": HQ_DATABASE},
                "argv": list(argv),
                "tools": tools,
                "supervisor": supervisor_before,
                "local_state": local_initial,
                "database_state": database_initial,
                "commands": {**version_commands, "supervisor": supervisor_command, **{f"database_{key}": value for key, value in database_commands.items()}},
                "credential_transport": "owner-only-environment-file",
            }
            _, intent_bytes = _write_json(intent_path, intent)
            hook("intent")

        before_path = evidence_root / "before" / "manifest.json"
        prepared_path = evidence_root / "prepared.json"
        if before_path.exists() or before_path.is_symlink():
            before_value, before_bytes = _read_private_json(
                before_path, label="before manifest"
            )
            before_reference = {
                "path": "before/manifest.json",
                "sha256": _sha256(before_bytes),
                "tree_sha256": before_value.get("tree_sha256"),
            }
            before = _load_manifest_reference(
                evidence_root, before_reference, phase="before"
            )
            if not _manifests_equal(current, before) and prepared_path.exists():
                # A completed command after a crash is allowed below; every
                # out-of-scope path is still checked against this snapshot.
                _assert_hq_initialization_scope(before, current)
            elif not _manifests_equal(current, before):
                raise EndpointTransitionError(
                    "HQ topology changed before the prepared journal was committed"
                )
            if not prepared_path.exists() and not prepared_path.is_symlink():
                _write_json(
                    prepared_path,
                    {
                        "schema_version": HQ_INITIALIZATION_SCHEMA,
                        "status": "prepared",
                        "intent_sha256": _sha256(intent_bytes),
                        "before": before_reference,
                    },
                )
                hook("prepared")
        else:
            before, before_bytes = _persist_manifest(
                topology, phase="before", evidence_root=evidence_root
            )
            if not _manifests_equal(current, before):
                raise EndpointTransitionError("HQ topology changed while preparing initialization")
            before_reference = _manifest_reference(
                evidence_root, before, before_bytes, phase="before"
            )
            _write_json(
                prepared_path,
                {
                    "schema_version": HQ_INITIALIZATION_SCHEMA,
                    "status": "prepared",
                    "intent_sha256": _sha256(intent_bytes),
                    "before": before_reference,
                },
            )
            hook("prepared")

        prepared, _ = _read_private_json(
            prepared_path, label="HQ initialization prepared journal"
        )
        before = _load_manifest_reference(
            evidence_root, prepared.get("before", {}), phase="before"
        )
        if (
            set(prepared) != {"schema_version", "status", "intent_sha256", "before"}
            or prepared.get("schema_version") != HQ_INITIALIZATION_SCHEMA
            or prepared.get("status") != "prepared"
            or prepared.get("intent_sha256") != _sha256(intent_bytes)
        ):
            raise EndpointTransitionError("HQ initialization prepared journal is invalid")

        database_before, database_before_commands = _hq_database_state(
            city,
            runner=runner,
            environment=env,
            password=password,
            allow_interrupted=True,
        )
        local_before = _hq_local_state(city, password=password, phase="resume")
        init_result: CommandResult | None = None
        schema_complete = database_before["schema"] == [
            {"name": name, "type": kind} for name, kind in HQ_BEADS_SCHEMA
        ]
        if not schema_complete or local_before["project_id"] is None:
            init_result = _run_checked(
                argv,
                city=city,
                environment=env,
                password=password,
                runner=runner,
                label="pinned HQ bd initialization",
            )
        hook("after-bd-init")
        runtime_config_result: CommandResult | None = None
        if database_before["state"] != "initialized-empty":
            runtime_config_result = _run_checked(
                _hq_runtime_config_argv(city),
                city=city,
                environment=env,
                password=password,
                runner=runner,
                label="pinned HQ Gas City custom-type registration",
            )
        hook("after-runtime-config")
        schema_migration_result = _run_checked(
            _hq_schema_migration_argv(city),
            city=city,
            environment=env,
            password=password,
            runner=runner,
            label="pinned HQ Beads schema migration",
        )
        hook("after-schema-migration")
        _replace_hq_config(city / ".beads" / "config.yaml", HQ_BEADS_INITIAL_CONFIG)
        hook("after-init")
        local_after = _hq_local_state(city, password=password, phase="complete")
        database_after, database_after_commands = _hq_database_state(
            city,
            runner=runner,
            environment=env,
            password=password,
            allow_interrupted=False,
        )
        if database_after["state"] != "initialized-empty":
            raise EndpointTransitionError("HQ database did not reach initialized-empty")
        after_path = evidence_root / "after" / "manifest.json"
        if after_path.exists() or after_path.is_symlink():
            after_value, after_bytes = _read_private_json(
                after_path, label="after manifest"
            )
            after = _load_manifest_reference(
                evidence_root,
                {
                    "path": "after/manifest.json",
                    "sha256": _sha256(after_bytes),
                    "tree_sha256": after_value.get("tree_sha256"),
                },
                phase="after",
            )
        else:
            after, after_bytes = _persist_manifest(
                topology, phase="after", evidence_root=evidence_root
            )
        current_after, _ = _manifest(topology, phase="current")
        if not _manifests_equal(current_after, after):
            raise EndpointTransitionError("HQ topology changed after initialization")
        _assert_hq_initialization_scope(before, after)
        hook("after-snapshot")
        supervisor_after, supervisor_after_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        _assert_lock_unchanged(lock, lock_sha256)
        commands = {
            **version_commands,
            "supervisor_before": supervisor_command,
            **{f"preflight_{key}": value for key, value in database_before_commands.items()},
            **{f"postflight_{key}": value for key, value in database_after_commands.items()},
            "supervisor_after": supervisor_after_command,
            "init": (
                init_result.evidence()
                if init_result is not None
                else {
                    "argv": list(argv),
                    "argv_sha256": _sha256(_canonical_json_bytes(list(argv))),
                    "returncode": 0,
                    "recovered_from_verified_poststate": True,
                }
            ),
            "runtime_config": (
                runtime_config_result.evidence()
                if runtime_config_result is not None
                else {
                    "argv": list(_hq_runtime_config_argv(city)),
                    "argv_sha256": _sha256(
                        _canonical_json_bytes(list(_hq_runtime_config_argv(city)))
                    ),
                    "returncode": 0,
                    "recovered_from_verified_poststate": True,
                }
            ),
            "schema_migration": schema_migration_result.evidence(),
        }
        receipt = {
            "schema_version": HQ_INITIALIZATION_SCHEMA,
            "kind": "hq-external-beads-initialization",
            "status": "verified",
            "created_at": _format_utc(_utc_now() if now is None else now),
            "city_root": city.as_posix(),
            "aegis_root": topology.aegis.as_posix(),
            "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
            "endpoint": {"host": HQ_HOST, "port": HQ_PORT, "user": HQ_USER, "database": HQ_DATABASE},
            "tools": tools,
            "commands": commands,
            "supervisor": {"before": supervisor_before, "after": supervisor_after},
            "before": prepared["before"],
            "after": _manifest_reference(evidence_root, after, after_bytes, phase="after"),
            "local_state": local_after,
            "database_state": database_after,
            "credential_transport": "owner-only-environment-file",
        }
        receipt_sha256, _ = _write_json(receipt_path, receipt)
        return {
            "status": "verified",
            "action": "initialized",
            "project_id": local_after["project_id"],
            "receipt_path": receipt_path.as_posix(),
            "receipt_sha256": receipt_sha256,
        }


def _assert_manifest_bound_to_topology(
    manifest: Mapping[str, Any], topology: DiscoveredTopology
) -> None:
    if (
        manifest.get("city_root") != topology.city.as_posix()
        or manifest.get("aegis_root") != topology.aegis.as_posix()
    ):
        raise EndpointTransitionError("endpoint manifest is bound to another topology")
    expected = {
        item.role: (item.scope, item.path.as_posix()) for item in topology.tracked
    }
    observed: dict[str, tuple[Any, Any]] = {}
    for entry in manifest.get("entries", []):
        role = entry.get("role")
        if not isinstance(role, str) or role in observed:
            raise EndpointTransitionError("endpoint manifest has duplicate tracked roles")
        observed[role] = (entry.get("scope"), entry.get("path"))
    if observed != expected:
        raise EndpointTransitionError(
            "endpoint manifest paths do not match the exact city topology"
        )


def _load_transition_prepared(
    evidence_root: Path,
    *,
    topology: DiscoveredTopology,
    lock: Path,
    lock_sha256: str,
    tools: Mapping[str, Any],
    version_commands: Mapping[str, Any],
    supervisor_command: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    prepared, content = _read_private_json(
        evidence_root / "prepared.json", label="endpoint transition prepared journal"
    )
    required = {
        "schema_version", "status", "city_root", "aegis_root", "runtime_lock",
        "endpoint", "tools", "commands", "before", "credential_transport",
    }
    expected_endpoint = {
        "host": HQ_HOST,
        "port": HQ_PORT,
        "user": HQ_USER,
        "database": HQ_DATABASE,
    }
    if (
        set(prepared) != required
        or prepared.get("schema_version") != PREPARED_SCHEMA
        or prepared.get("status") != "prepared"
        or prepared.get("city_root") != topology.city.as_posix()
        or prepared.get("aegis_root") != topology.aegis.as_posix()
        or prepared.get("runtime_lock")
        != {"path": lock.as_posix(), "sha256": lock_sha256}
        or prepared.get("endpoint") != expected_endpoint
        or prepared.get("credential_transport") != "owner-only-environment-file"
    ):
        raise EndpointTransitionError("endpoint transition prepared journal is invalid")
    _assert_tools_match_receipt(tools, prepared.get("tools"))
    commands = prepared.get("commands")
    if type(commands) is not dict:
        raise EndpointTransitionError("endpoint transition prepared commands are invalid")
    expected_command_keys = {*version_commands, "supervisor", "dry_run"}
    if set(commands) != expected_command_keys:
        raise EndpointTransitionError("endpoint transition prepared command set drifted")
    for key, value in version_commands.items():
        if commands.get(key) != value:
            raise EndpointTransitionError(
                "endpoint transition prepared tool evidence drifted"
            )
    if commands.get("supervisor") != supervisor_command:
        raise EndpointTransitionError(
            "endpoint transition prepared supervisor evidence drifted"
        )
    dry_run = commands.get("dry_run")
    expected_argv = list(_transition_argv(topology.city, dry_run=True))
    if (
        type(dry_run) is not dict
        or set(dry_run)
        != {"argv", "argv_sha256", "returncode", "stdout_sha256", "stderr_sha256"}
        or dry_run.get("argv") != expected_argv
        or dry_run.get("argv_sha256")
        != _sha256(_canonical_json_bytes(expected_argv))
        or dry_run.get("returncode") != 0
        or any(
            not isinstance(dry_run.get(field), str)
            or SHA256_RE.fullmatch(dry_run[field]) is None
            for field in ("stdout_sha256", "stderr_sha256")
        )
    ):
        raise EndpointTransitionError("endpoint transition dry-run evidence is invalid")
    before = _load_manifest_reference(
        evidence_root, prepared.get("before", {}), phase="before"
    )
    _assert_manifest_bound_to_topology(before, topology)
    return prepared, content, before


def _assert_tools_match_receipt(
    observed: Mapping[str, Any], receipt_tools: Any
) -> None:
    if type(receipt_tools) is not dict or set(receipt_tools) != set(VERSION_ARGUMENTS):
        raise EndpointTransitionError("endpoint receipt tool set is invalid")
    for name in VERSION_ARGUMENTS:
        expected = receipt_tools[name]
        current = observed[name]
        for field in ("path", "version", "binary_sha256"):
            if expected.get(field) != current.get(field):
                raise EndpointTransitionError(f"installed {name} drifted from endpoint receipt")


def _restore_entry(
    entry_before: Mapping[str, Any],
    entry_after: Mapping[str, Any],
    *,
    evidence_root: Path,
) -> None:
    if entry_before.get("path") != entry_after.get("path") or entry_before.get("role") != entry_after.get("role"):
        raise EndpointTransitionError("rollback manifests do not describe the same file")
    path = Path(str(entry_before["path"]))
    current_item = TrackedPath(str(entry_before["role"]), str(entry_before["scope"]), path)
    # The caller has already verified the whole current manifest.  Re-read the
    # individual target immediately before replacement to catch a racing edit.
    current = _entry_for_path(current_item, roots=(path.parent,))
    current_semantic = _semantic_entries([current])
    before_semantic = _semantic_entries([entry_before])
    after_semantic = _semantic_entries([entry_after])
    if current_semantic == before_semantic:
        return
    if current_semantic != after_semantic:
        raise EndpointTransitionError(f"rollback target drifted concurrently: {path}")
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise EndpointTransitionError(f"rollback parent is unsafe: {parent}")
    directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if not entry_before.get("present"):
            os.unlink(path.name, dir_fd=directory_fd)
            os.fsync(directory_fd)
            return
        payload = entry_before.get("payload")
        if not isinstance(payload, str):
            raise EndpointTransitionError("rollback source payload is missing")
        content, _ = _regular_file(
            evidence_root / payload,
            label="rollback source payload",
            exact_mode=0o600,
            private=True,
        )
        if _sha256(content) != entry_before.get("sha256"):
            raise EndpointTransitionError("rollback source payload digest mismatch")
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.rollback.", dir=parent)
        try:
            os.fchmod(fd, int(entry_before["mode"]))
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(Path(temporary_name), path)
            os.chmod(path, int(entry_before["mode"]))
            os.fsync(directory_fd)
        except BaseException:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass
            raise
    finally:
        os.close(directory_fd)


def _restore_manifest(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    evidence_root: Path,
) -> None:
    before_entries = {entry["role"]: entry for entry in before["entries"]}
    after_entries = {entry["role"]: entry for entry in after["entries"]}
    if set(before_entries) != set(after_entries):
        raise EndpointTransitionError("rollback manifest role sets differ")
    # Restore rig state before city authority files, then runtime publication.
    order = (
        "aegis_metadata", "aegis_config", "aegis_port", "site_toml",
        "city_toml", "hq_metadata", "hq_config", "hq_port",
        "hq_provider_config", "hq_provider_log", "hq_provider_lock",
        "hq_provider_pid", "hq_provider_state", "hq_managed_state",
        "hq_provider_script",
    )
    for role in order:
        _restore_entry(before_entries[role], after_entries[role], evidence_root=evidence_root)


def _load_unreferenced_manifest(
    evidence_root: Path, *, phase: str
) -> dict[str, Any]:
    value, content = _read_private_json(
        evidence_root / phase / "manifest.json", label=f"{phase} manifest"
    )
    tree_sha256 = value.get("tree_sha256")
    reference = {
        "path": f"{phase}/manifest.json",
        "sha256": _sha256(content),
        "tree_sha256": tree_sha256,
    }
    return _load_manifest_reference(evidence_root, reference, phase=phase)


def _assert_no_live_transition_process(city: Path) -> None:
    expected = (city / "bin" / "gc").as_posix().encode()
    city_bytes = city.as_posix().encode()
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            metadata = process.stat()
            if metadata.st_uid != os.getuid():
                continue
            arguments = (process / "cmdline").read_bytes().split(b"\0")
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if not arguments or arguments[0] != expected:
            continue
        expected_tail = [
            b"--city",
            city_bytes,
            b"beads",
            b"city",
            b"use-external",
        ]
        if all(value in arguments for value in expected_tail):
            raise EndpointTransitionError(
                "interrupted transition gc process is still running"
            )


def _validate_interrupted_partial_state(
    topology: DiscoveredTopology,
    before: Mapping[str, Any],
    current: Mapping[str, Any],
) -> None:
    """Validate every possible mid-command mutation before recovery.

    The exact upstream process is no longer running and the runtime lock is
    held.  Each changed target must be a complete, safe state that the pinned
    command can publish; arbitrary concurrent bytes are not accepted.
    """

    _assert_no_live_transition_process(topology.city)
    if not _manifest_is_entrywise_mixture(current, before, current):
        raise EndpointTransitionError("interrupted transition manifest aliases targets")

    changed = {
        entry["role"]
        for entry in current["entries"]
        if _entry_semantic(entry)
        != _entry_semantic(_entry_by_role(before, str(entry["role"])))
    }
    if not changed:
        return

    if "city_toml" in changed:
        city_config = _load_toml(
            topology.city / "city.toml",
            label="interrupted city.toml",
            required=True,
        )
        dolt = city_config.get("dolt")
        if (
            type(dolt) is not dict
            or dolt.get("host") != HQ_HOST
            or dolt.get("port") != HQ_PORT
        ):
            raise EndpointTransitionError(
                "interrupted transition city.toml is not a complete target state"
            )

    if "hq_config" in changed:
        hq = _active_flat_yaml(
            topology.city / ".beads" / "config.yaml",
            label="interrupted HQ Beads config",
        )
        required_hq = {
            "gc.endpoint_origin": "city_canonical",
            "gc.endpoint_status": "verified",
            "dolt.host": HQ_HOST,
            "dolt.port": str(HQ_PORT),
            "dolt.user": HQ_USER,
            "dolt.auto-start": "false",
        }
        if any(hq.get(key) != value for key, value in required_hq.items()):
            raise EndpointTransitionError(
                "interrupted HQ config is not a complete external target"
            )

    if "hq_metadata" in changed:
        content, _ = _regular_file(
            topology.city / ".beads" / "metadata.json",
            label="interrupted HQ metadata",
        )
        metadata = _strict_json_bytes(content, label="interrupted HQ metadata")
        if (
            type(metadata) is not dict
            or metadata.get("backend") != "dolt"
            or metadata.get("database") != "dolt"
            or metadata.get("dolt_mode") != "server"
            or metadata.get("dolt_database") != HQ_DATABASE
        ):
            raise EndpointTransitionError(
                "interrupted HQ metadata is not a complete target"
            )

    if "aegis_config" in changed:
        aegis = _active_flat_yaml(
            topology.aegis / ".beads" / "config.yaml",
            label="interrupted Aegis Beads config",
        )
        required_aegis = {
            "gc.endpoint_origin": "explicit",
            "gc.endpoint_status": "verified",
            "dolt.host": AEGIS_HOST,
            "dolt.port": str(AEGIS_PORT),
            "dolt.user": AEGIS_USER,
            "dolt.auto-start": "false",
        }
        if any(aegis.get(key) != value for key, value in required_aegis.items()):
            raise EndpointTransitionError(
                "interrupted Aegis config is not a complete isolated target"
            )

    if "aegis_metadata" in changed:
        content, _ = _regular_file(
            topology.aegis / ".beads" / "metadata.json",
            label="interrupted Aegis metadata",
        )
        metadata = _strict_json_bytes(content, label="interrupted Aegis metadata")
        if (
            type(metadata) is not dict
            or metadata.get("backend") != "dolt"
            or metadata.get("database") != "dolt"
            or metadata.get("dolt_mode") != "server"
            or metadata.get("dolt_database") != "aegis_beads"
        ):
            raise EndpointTransitionError(
                "interrupted Aegis metadata is not a complete isolated target"
            )

    for role in ("hq_port", "aegis_port", "hq_managed_state", "hq_provider_pid"):
        if role in changed and _entry_by_role(current, role).get("present"):
            raise EndpointTransitionError(
                f"interrupted transition published unsafe residual {role}"
            )
    if "hq_provider_state" in changed:
        _verify_stopped_provider_state(topology)


def _recover_interrupted_transition(
    *,
    evidence_root: Path,
    city: Path,
    topology: DiscoveredTopology,
    current: Mapping[str, Any],
    lock: Path,
    lock_sha256: str,
    tools: Mapping[str, Any],
    version_commands: Mapping[str, Any],
    supervisor: Mapping[str, Any],
    supervisor_command: Mapping[str, Any],
    runner: Runner,
    environment: Mapping[str, str],
    password: str,
    expected_aegis_root: Path,
    now: dt.datetime | None,
) -> dict[str, Any]:
    """Resume a killed prepared transition by restoring its anchored pre-tree."""

    _, prepared_bytes, before = _load_transition_prepared(
        evidence_root,
        topology=topology,
        lock=lock,
        lock_sha256=lock_sha256,
        tools=tools,
        version_commands=version_commands,
        supervisor_command=supervisor_command,
    )
    prepared_sha256 = _sha256(prepared_bytes)
    _assert_no_live_transition_process(city)
    recovery_receipt_path = evidence_root / "recovery-receipt.json"
    if recovery_receipt_path.exists() or recovery_receipt_path.is_symlink():
        recovery_prepared, _ = _read_private_json(
            evidence_root / "recovery-prepared.json",
            label="interrupted transition recovery journal",
        )
        required_recovery_prepared = {
            "schema_version", "kind", "status", "city_root", "aegis_root",
            "runtime_lock", "transition_prepared_sha256", "before_tree_sha256",
            "observed", "tools", "commands",
        }
        expected_recovery_commands = {
            **version_commands,
            "supervisor_before": supervisor_command,
        }
        if (
            set(recovery_prepared) != required_recovery_prepared
            or recovery_prepared.get("schema_version") != TRANSITION_SCHEMA
            or recovery_prepared.get("kind")
            != "hq-host-interrupted-endpoint-transition-recovery-prepared"
            or recovery_prepared.get("status") != "prepared"
            or recovery_prepared.get("city_root") != city.as_posix()
            or recovery_prepared.get("aegis_root") != topology.aegis.as_posix()
            or recovery_prepared.get("runtime_lock")
            != {"path": lock.as_posix(), "sha256": lock_sha256}
            or recovery_prepared.get("transition_prepared_sha256")
            != prepared_sha256
            or recovery_prepared.get("before_tree_sha256")
            != before["tree_sha256"]
            or recovery_prepared.get("tools") != tools
            or recovery_prepared.get("commands") != expected_recovery_commands
        ):
            raise EndpointTransitionError(
                "interrupted transition recovery journal is invalid or drifted"
            )
        observed = _load_manifest_reference(
            evidence_root,
            recovery_prepared.get("observed", {}),
            phase="recovery-observed",
        )
        _assert_manifest_bound_to_topology(observed, topology)
        recovery_receipt, recovery_bytes = _read_private_json(
            recovery_receipt_path,
            label="interrupted transition recovery receipt",
        )
        required_receipt = {
            "schema_version", "kind", "status", "created_at", "city_root",
            "aegis_root", "runtime_lock", "transition_prepared_sha256",
            "before_tree_sha256", "observed_tree_sha256",
            "managed_service_started", "supervisor", "tools", "commands",
        }
        if (
            set(recovery_receipt) != required_receipt
            or recovery_receipt.get("schema_version") != TRANSITION_SCHEMA
            or recovery_receipt.get("kind")
            != "hq-host-interrupted-endpoint-transition-recovery"
            or recovery_receipt.get("status") != "verified"
            or recovery_receipt.get("city_root") != city.as_posix()
            or recovery_receipt.get("aegis_root") != topology.aegis.as_posix()
            or recovery_receipt.get("runtime_lock")
            != {"path": lock.as_posix(), "sha256": lock_sha256}
            or recovery_receipt.get("transition_prepared_sha256")
            != prepared_sha256
            or recovery_receipt.get("before_tree_sha256")
            != before["tree_sha256"]
            or recovery_receipt.get("observed_tree_sha256")
            != observed["tree_sha256"]
            or recovery_receipt.get("managed_service_started") is not False
            or recovery_receipt.get("supervisor")
            != {"before": supervisor, "after": supervisor}
            or recovery_receipt.get("commands")
            != {
                **version_commands,
                "supervisor_before": supervisor_command,
                "supervisor_after": supervisor_command,
            }
        ):
            raise EndpointTransitionError(
                "interrupted transition recovery receipt is invalid"
            )
        _assert_tools_match_receipt(tools, recovery_receipt.get("tools"))
        if not _manifests_equal(current, before):
            raise EndpointTransitionError(
                "recovered interrupted transition has drifted from its pre-state"
            )
        if _entry_by_role(current, "hq_managed_state").get("present"):
            raise EndpointTransitionError(
                "recovered transition unexpectedly publishes managed Dolt state"
            )
        if _entry_by_role(current, "hq_provider_pid").get("present"):
            raise EndpointTransitionError(
                "recovered transition unexpectedly publishes a managed Dolt pid"
            )
        _verify_stopped_provider_state(topology)
        _assert_lock_unchanged(lock, lock_sha256)
        return {
            "status": "already-recovered",
            "action": "none",
            "receipt_path": recovery_receipt_path.as_posix(),
            "receipt_sha256": _sha256(recovery_bytes),
        }

    recovery_prepared_path = evidence_root / "recovery-prepared.json"
    if recovery_prepared_path.exists() or recovery_prepared_path.is_symlink():
        recovery_prepared, _ = _read_private_json(
            recovery_prepared_path,
            label="interrupted transition recovery journal",
        )
        required_prepared = {
            "schema_version", "kind", "status", "city_root", "aegis_root",
            "runtime_lock", "transition_prepared_sha256", "before_tree_sha256",
            "observed", "tools", "commands",
        }
        if (
            set(recovery_prepared) != required_prepared
            or recovery_prepared.get("schema_version") != TRANSITION_SCHEMA
            or recovery_prepared.get("kind")
            != "hq-host-interrupted-endpoint-transition-recovery-prepared"
            or recovery_prepared.get("status") != "prepared"
            or recovery_prepared.get("city_root") != city.as_posix()
            or recovery_prepared.get("aegis_root") != topology.aegis.as_posix()
            or recovery_prepared.get("runtime_lock")
            != {"path": lock.as_posix(), "sha256": lock_sha256}
            or recovery_prepared.get("transition_prepared_sha256")
            != prepared_sha256
            or recovery_prepared.get("before_tree_sha256")
            != before["tree_sha256"]
            or recovery_prepared.get("tools") != tools
            or recovery_prepared.get("commands")
            != {**version_commands, "supervisor_before": supervisor_command}
        ):
            raise EndpointTransitionError(
                "interrupted transition recovery journal is invalid or drifted"
            )
        observed = _load_manifest_reference(
            evidence_root,
            recovery_prepared.get("observed", {}),
            phase="recovery-observed",
        )
        _assert_manifest_bound_to_topology(observed, topology)
        if not _manifest_is_entrywise_mixture(current, before, observed):
            raise EndpointTransitionError(
                "interrupted transition recovery refused non-journaled drift"
            )
    else:
        # A complete immediate after snapshot is preferred.  If the process was
        # killed before publishing it, accept only a fully valid external state
        # produced by the exact prepared upstream command.
        published_after = evidence_root / "after" / "manifest.json"
        if published_after.exists() or published_after.is_symlink():
            candidate = _load_unreferenced_manifest(evidence_root, phase="after")
            _assert_manifest_bound_to_topology(candidate, topology)
            if not _manifest_is_entrywise_mixture(current, before, candidate):
                raise EndpointTransitionError(
                    "interrupted transition files drifted from its captured after-state"
                )
        elif not _manifests_equal(current, before):
            _validate_interrupted_partial_state(topology, before, current)

        observed_phase = evidence_root / "recovery-observed" / "manifest.json"
        if observed_phase.exists() or observed_phase.is_symlink():
            observed = _load_unreferenced_manifest(
                evidence_root, phase="recovery-observed"
            )
            _assert_manifest_bound_to_topology(observed, topology)
            if not _manifest_is_entrywise_mixture(current, before, observed):
                raise EndpointTransitionError(
                    "interrupted transition recovery snapshot does not match current files"
                )
        else:
            observed, observed_bytes = _persist_manifest(
                topology,
                phase="recovery-observed",
                evidence_root=evidence_root,
            )
            observed_reference = _manifest_reference(
                evidence_root,
                observed,
                observed_bytes,
                phase="recovery-observed",
            )
            recovery_prepared = {
                "schema_version": TRANSITION_SCHEMA,
                "kind": "hq-host-interrupted-endpoint-transition-recovery-prepared",
                "status": "prepared",
                "city_root": city.as_posix(),
                "aegis_root": topology.aegis.as_posix(),
                "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
                "transition_prepared_sha256": prepared_sha256,
                "before_tree_sha256": before["tree_sha256"],
                "observed": observed_reference,
                "tools": tools,
                "commands": {
                    **version_commands,
                    "supervisor_before": supervisor_command,
                },
            }
            _write_json(recovery_prepared_path, recovery_prepared)
        if not recovery_prepared_path.exists():
            # A complete recovery snapshot can survive a kill before its
            # journal publication.  Bind that snapshot now before restoring.
            observed_bytes, _ = _regular_file(
                evidence_root / "recovery-observed" / "manifest.json",
                label="interrupted recovery observed manifest",
                exact_mode=0o600,
                private=True,
            )
            observed_reference = _manifest_reference(
                evidence_root,
                observed,
                observed_bytes,
                phase="recovery-observed",
            )
            recovery_prepared = {
                "schema_version": TRANSITION_SCHEMA,
                "kind": "hq-host-interrupted-endpoint-transition-recovery-prepared",
                "status": "prepared",
                "city_root": city.as_posix(),
                "aegis_root": topology.aegis.as_posix(),
                "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
                "transition_prepared_sha256": prepared_sha256,
                "before_tree_sha256": before["tree_sha256"],
                "observed": observed_reference,
                "tools": tools,
                "commands": {
                    **version_commands,
                    "supervisor_before": supervisor_command,
                },
            }
            _write_json(recovery_prepared_path, recovery_prepared)

    _restore_manifest(before, observed, evidence_root=evidence_root)
    restored_topology = _discover_topology(
        city, expected_aegis_root=expected_aegis_root
    )
    restored, _ = _manifest(restored_topology, phase="current")
    if not _manifests_equal(restored, before):
        raise EndpointTransitionError(
            "interrupted transition recovery did not restore exact pre-state"
        )
    if _entry_by_role(restored, "hq_managed_state").get("present"):
        raise EndpointTransitionError(
            "interrupted transition recovery would publish managed Dolt state"
        )
    if _entry_by_role(restored, "hq_provider_pid").get("present"):
        raise EndpointTransitionError(
            "interrupted transition recovery would publish a managed Dolt pid"
        )
    _verify_stopped_provider_state(restored_topology)
    supervisor_after, supervisor_after_command = _supervisor_stopped(
        city,
        runner=runner,
        environment=environment,
        password=password,
    )
    final_state, _ = _manifest(restored_topology, phase="current")
    if not _manifests_equal(final_state, before):
        raise EndpointTransitionError(
            "recovered topology changed while proving the supervisor stopped"
        )
    _assert_lock_unchanged(lock, lock_sha256)
    recovery_receipt = {
        "schema_version": TRANSITION_SCHEMA,
        "kind": "hq-host-interrupted-endpoint-transition-recovery",
        "status": "verified",
        "created_at": _format_utc(_utc_now() if now is None else now),
        "city_root": city.as_posix(),
        "aegis_root": topology.aegis.as_posix(),
        "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
        "transition_prepared_sha256": prepared_sha256,
        "before_tree_sha256": before["tree_sha256"],
        "observed_tree_sha256": observed["tree_sha256"],
        "managed_service_started": False,
        "supervisor": {"before": supervisor, "after": supervisor_after},
        "tools": tools,
        "commands": {
            **version_commands,
            "supervisor_before": supervisor_command,
            "supervisor_after": supervisor_after_command,
        },
    }
    recovery_sha256, _ = _write_json(recovery_receipt_path, recovery_receipt)
    return {
        "status": "recovered",
        "action": "restored-pre-transition",
        "receipt_path": recovery_receipt_path.as_posix(),
        "receipt_sha256": recovery_sha256,
        "restored_tree_sha256": before["tree_sha256"],
        "managed_service_started": False,
    }


def transition_hq_endpoint(
    city_root: Path,
    lock_path: Path,
    evidence_dir: Path,
    *,
    password: str,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    expected_city_root: Path = PRODUCTION_CITY_ROOT,
    expected_aegis_root: Path = PRODUCTION_AEGIS_ROOT,
    lock_loader: LockLoader = gas_city_ops.load_runtime_lock,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Transition the stopped host city to exact external HQ and prove it live."""

    city, lock, lock_bytes = _validate_city_and_lock(
        city_root, lock_path, expected_city_root=expected_city_root
    )
    lock_sha256 = _sha256(lock_bytes)
    env = _command_environment(city, password, environment)
    requested_evidence = _lexical_absolute(evidence_dir, label="transition evidence")

    with _exclusive_runtime_lock(lock):
        _assert_lock_unchanged(lock, lock_sha256)
        locked = lock_loader(lock)
        tools, version_commands = _verify_tools(
            city, locked, runner=runner, environment=env, password=password
        )
        supervisor, supervisor_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        topology = _discover_topology(city, expected_aegis_root=expected_aegis_root)
        current, _ = _manifest(topology, phase="current")

        if requested_evidence.exists() or requested_evidence.is_symlink():
            evidence_root = _evidence_directory(
                requested_evidence, city=city, category="endpoint-transition", create=False
            )
            transition_receipt_path = evidence_root / "transition-receipt.json"
            if not (
                transition_receipt_path.exists()
                or transition_receipt_path.is_symlink()
            ):
                return _recover_interrupted_transition(
                    evidence_root=evidence_root,
                    city=city,
                    topology=topology,
                    current=current,
                    lock=lock,
                    lock_sha256=lock_sha256,
                    tools=tools,
                    version_commands=version_commands,
                    supervisor=supervisor,
                    supervisor_command=supervisor_command,
                    runner=runner,
                    environment=env,
                    password=password,
                    expected_aegis_root=expected_aegis_root,
                    now=now,
                )
            receipt, receipt_bytes, before_receipt, after = _load_transition_receipt(
                evidence_root
            )
            _assert_manifest_bound_to_topology(before_receipt, topology)
            _assert_manifest_bound_to_topology(after, topology)
            if receipt.get("city_root") != city.as_posix() or receipt.get("aegis_root") != topology.aegis.as_posix():
                raise EndpointTransitionError("endpoint receipt is bound to another city or rig")
            runtime_lock = receipt.get("runtime_lock")
            if runtime_lock != {"path": lock.as_posix(), "sha256": lock_sha256}:
                raise EndpointTransitionError("runtime lock drifted from endpoint receipt")
            _assert_tools_match_receipt(tools, receipt.get("tools"))
            if not _manifests_equal(current, after):
                raise EndpointTransitionError("current endpoint files drifted from verified post-state")
            state = _verify_hq_state(topology)
            _verify_aegis_state(topology)
            proof_before, _ = _manifest(topology, phase="current")
            proof, proof_commands = _validate_connection_proof(
                city, runner=runner, environment=env, password=password
            )
            proof_after, _ = _manifest(topology, phase="current")
            if not _manifests_equal(proof_before, proof_after):
                raise EndpointTransitionError("idempotent endpoint proof mutated topology")
            _assert_lock_unchanged(lock, lock_sha256)
            return {
                "status": "already-verified",
                "action": "none",
                "receipt_path": (evidence_root / "transition-receipt.json").as_posix(),
                "receipt_sha256": _sha256(receipt_bytes),
                "endpoint": state,
                "connection_proof": proof,
                "commands": proof_commands,
            }

        # A stopped managed city must not publish a live/stale managed state.
        if _entry_by_role(current, "hq_managed_state").get("present"):
            raise EndpointTransitionError(
                "stopped HQ still has managed Dolt runtime state; stop it cleanly first"
            )
        if _entry_by_role(current, "hq_provider_pid").get("present"):
            raise EndpointTransitionError(
                "stopped HQ still has a managed Dolt pid file; stop it cleanly first"
            )
        _verify_stopped_provider_state(topology)

        dry_run = _run_checked(
            _transition_argv(city, dry_run=True),
            city=city,
            environment=env,
            password=password,
            runner=runner,
            label="gc external endpoint dry-run",
        )
        if "WOULD UPDATE: city endpoint" not in dry_run.stdout:
            raise EndpointTransitionError("gc dry-run did not describe the city endpoint transition")
        after_dry, _ = _manifest(topology, phase="current")
        _assert_dry_run_unchanged(current, after_dry)
        after_dry_topology = _discover_topology(
            city, expected_aegis_root=expected_aegis_root
        )
        rediscovered_dry, _ = _manifest(after_dry_topology, phase="current")
        _assert_dry_run_unchanged(current, rediscovered_dry)
        _assert_lock_unchanged(lock, lock_sha256)

        evidence_root = _evidence_directory(
            requested_evidence, city=city, category="endpoint-transition", create=True
        )
        before, before_bytes = _persist_manifest(
            topology, phase="before", evidence_root=evidence_root
        )
        prepared = {
            "schema_version": PREPARED_SCHEMA,
            "status": "prepared",
            "city_root": city.as_posix(),
            "aegis_root": topology.aegis.as_posix(),
            "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
            "endpoint": {
                "host": HQ_HOST,
                "port": HQ_PORT,
                "user": HQ_USER,
                "database": HQ_DATABASE,
            },
            "tools": tools,
            "commands": {**version_commands, "supervisor": supervisor_command, "dry_run": dry_run.evidence()},
            "before": _manifest_reference(evidence_root, before, before_bytes, phase="before"),
            "credential_transport": "owner-only-environment-file",
        }
        _write_json(evidence_root / "prepared.json", prepared)

        apply_started = False
        after: dict[str, Any] | None = None
        try:
            apply_started = True
            applied = _run_checked(
                _transition_argv(city, dry_run=False),
                city=city,
                environment=env,
                password=password,
                runner=runner,
                label="gc external endpoint transition",
            )
            # Capture every path the pinned upstream command can mutate before
            # interpreting its output or rediscovering topology.  Any later
            # validation failure therefore has a complete, byte-exact rollback
            # source rather than an unjournaled mutation window.
            after, after_bytes = _persist_manifest(
                topology, phase="after", evidence_root=evidence_root
            )
            if "UPDATED: city endpoint" not in applied.stdout:
                raise EndpointTransitionError("gc did not confirm the endpoint transition")
            _assert_lock_unchanged(lock, lock_sha256)
            post_topology = _discover_topology(city, expected_aegis_root=expected_aegis_root)
            post_current, _ = _manifest(post_topology, phase="current")
            if not _manifests_equal(post_current, after):
                raise EndpointTransitionError(
                    "endpoint topology changed while validating the applied state"
                )
            state = _verify_hq_state(post_topology)
            _assert_aegis_isolated(before, after)
            _verify_aegis_state(post_topology)
            proof_before, _ = _manifest(post_topology, phase="current")
            proof, proof_commands = _validate_connection_proof(
                city, runner=runner, environment=env, password=password
            )
            proof_after, _ = _manifest(post_topology, phase="current")
            if not _manifests_equal(proof_before, proof_after):
                raise EndpointTransitionError("read-only gc bd proof mutated endpoint topology")
            supervisor_after, supervisor_after_command = _supervisor_stopped(
                city, runner=runner, environment=env, password=password
            )
            final_topology, _ = _manifest(post_topology, phase="current")
            if not _manifests_equal(final_topology, after):
                raise EndpointTransitionError(
                    "endpoint files changed while proving the supervisor stopped"
                )
            _assert_lock_unchanged(lock, lock_sha256)
            receipt = {
                "schema_version": TRANSITION_SCHEMA,
                "kind": "hq-host-external-endpoint",
                "status": "verified",
                "created_at": _format_utc(_utc_now() if now is None else now),
                "city_root": city.as_posix(),
                "aegis_root": topology.aegis.as_posix(),
                "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
                "endpoint": state,
                "tools": tools,
                "commands": {
                    **version_commands,
                    "supervisor_before": supervisor_command,
                    "dry_run": dry_run.evidence(),
                    "apply": applied.evidence(),
                    **proof_commands,
                    "supervisor_after": supervisor_after_command,
                },
                "supervisor": {"before": supervisor, "after": supervisor_after},
                "before": _manifest_reference(evidence_root, before, before_bytes, phase="before"),
                "after": _manifest_reference(evidence_root, after, after_bytes, phase="after"),
                "connection_proof": proof,
                "credential_transport": "owner-only-environment-file",
            }
            receipt_sha256, receipt_bytes = _write_json(
                evidence_root / "transition-receipt.json", receipt
            )
            return {
                "status": "verified",
                "action": "transitioned",
                "receipt_path": (evidence_root / "transition-receipt.json").as_posix(),
                "receipt_sha256": receipt_sha256,
                "endpoint": state,
                "connection_proof": proof,
            }
        except BaseException as exc:
            recovery_error: BaseException | None = None
            if apply_started:
                try:
                    # Use the pre-command topology object: post-command config
                    # parsing may itself be the failing validation, but the
                    # original exact paths remain sufficient for restoration.
                    observed, _ = _manifest(topology, phase="current")
                    if not _manifests_equal(observed, before):
                        if after is not None and not _manifest_is_entrywise_mixture(
                            observed, before, after
                        ):
                            raise EndpointTransitionError(
                                "automatic rollback refused concurrent post-apply drift"
                            )
                        rollback_source = observed if after is None else after
                        _restore_manifest(
                            before, rollback_source, evidence_root=evidence_root
                        )
                    restored, _ = _manifest(topology, phase="current")
                    if not _manifests_equal(restored, before):
                        raise EndpointTransitionError(
                            "automatic rollback did not restore exact pre-transition bytes"
                        )
                    if _entry_by_role(restored, "hq_managed_state").get("present"):
                        raise EndpointTransitionError(
                            "automatic rollback left managed Dolt runtime state"
                        )
                    if _entry_by_role(restored, "hq_provider_pid").get("present"):
                        raise EndpointTransitionError(
                            "automatic rollback left a managed Dolt pid"
                        )
                    _verify_stopped_provider_state(topology)
                except BaseException as rollback_exc:
                    recovery_error = rollback_exc
            failure = {
                "schema_version": TRANSITION_SCHEMA,
                "kind": "hq-host-external-endpoint-failure",
                "status": "failed-closed",
                "runtime_lock_sha256": lock_sha256,
                "error_type": type(exc).__name__,
                "automatic_rollback": (
                    "verified" if recovery_error is None else "unproved"
                ),
            }
            if recovery_error is not None:
                failure["rollback_error_type"] = type(recovery_error).__name__
            try:
                _write_json(evidence_root / "failure.json", failure)
            except EndpointTransitionError:
                pass
            if recovery_error is not None:
                raise EndpointTransitionError(
                    "endpoint transition failed and automatic rollback could not be proved"
                ) from recovery_error
            raise


def verify_hq_endpoint_transition(
    city_root: Path,
    lock_path: Path,
    transition_receipt: Path,
    *,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    expected_city_root: Path = PRODUCTION_CITY_ROOT,
    expected_aegis_root: Path = PRODUCTION_AEGIS_ROOT,
    lock_loader: LockLoader = gas_city_ops.load_runtime_lock,
) -> dict[str, Any]:
    """Revalidate a completed transition against the exact stopped live tree."""

    city, lock, lock_bytes = _validate_city_and_lock(
        city_root, lock_path, expected_city_root=expected_city_root
    )
    lock_sha256 = _sha256(lock_bytes)
    password = "x" * 32
    env = dict(os.environ if environment is None else environment)
    for key in AMBIENT_ENDPOINT_KEYS:
        env.pop(key, None)
    env["PATH"] = f"{city / 'bin'}:/usr/bin:/bin"
    env["NO_COLOR"] = "1"

    with _exclusive_runtime_lock(lock):
        _assert_lock_unchanged(lock, lock_sha256)
        locked = lock_loader(lock)
        tools, version_commands = _verify_tools(
            city, locked, runner=runner, environment=env, password=password
        )
        supervisor, supervisor_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        topology = _discover_topology(city, expected_aegis_root=expected_aegis_root)
        receipt_path = _lexical_absolute(
            transition_receipt, label="transition receipt"
        )
        transition_root = receipt_path.parent
        if (
            receipt_path.name != "transition-receipt.json"
            or transition_root.parent
            != city / "runtime" / "evidence" / "endpoint-transition"
        ):
            raise EndpointTransitionError(
                "verification requires an exact city endpoint receipt"
            )
        _real_directory(transition_root, label="transition evidence", owner_only=True)
        receipt, receipt_bytes, before, after = _load_transition_receipt(
            transition_root
        )
        _assert_manifest_bound_to_topology(before, topology)
        _assert_manifest_bound_to_topology(after, topology)
        expected_endpoint = {
            "endpoint_origin": "city_canonical",
            "endpoint_status": "verified",
            "host": HQ_HOST,
            "port": HQ_PORT,
            "user": HQ_USER,
            "database": HQ_DATABASE,
        }
        if (
            receipt.get("runtime_lock")
            != {"path": lock.as_posix(), "sha256": lock_sha256}
            or receipt.get("city_root") != city.as_posix()
            or receipt.get("aegis_root") != topology.aegis.as_posix()
            or receipt.get("endpoint") != expected_endpoint
        ):
            raise EndpointTransitionError(
                "transition receipt is not bound to this city, lock, and endpoint"
            )
        _assert_tools_match_receipt(tools, receipt.get("tools"))
        current, _ = _manifest(topology, phase="current")
        if not _manifests_equal(current, after):
            raise EndpointTransitionError(
                "live endpoint topology no longer matches the transition receipt"
            )
        if _verify_hq_state(topology) != expected_endpoint:
            raise EndpointTransitionError("live HQ endpoint proof is inconsistent")
        _assert_aegis_isolated(before, after)
        _verify_aegis_state(topology)
        _assert_lock_unchanged(lock, lock_sha256)
        return {
            "status": "verified",
            "city_root": city.as_posix(),
            "runtime_lock_sha256": lock_sha256,
            "transition_receipt": receipt_path.as_posix(),
            "transition_receipt_sha256": _sha256(receipt_bytes),
            "endpoint": expected_endpoint,
            "supervisor": supervisor,
            "commands": {
                **version_commands,
                "supervisor": supervisor_command,
            },
        }


def rollback_hq_endpoint(
    city_root: Path,
    lock_path: Path,
    transition_receipt: Path,
    evidence_dir: Path,
    *,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    expected_city_root: Path = PRODUCTION_CITY_ROOT,
    expected_aegis_root: Path = PRODUCTION_AEGIS_ROOT,
    lock_loader: LockLoader = gas_city_ops.load_runtime_lock,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Restore the exact pre-transition topology without starting managed Dolt."""

    city, lock, lock_bytes = _validate_city_and_lock(
        city_root, lock_path, expected_city_root=expected_city_root
    )
    lock_sha256 = _sha256(lock_bytes)
    # Rollback needs no database credential.  A fixed non-secret sentinel is
    # used only by the common output-redaction seam and is never exported.
    password = "x" * 32
    env = dict(os.environ if environment is None else environment)
    for key in AMBIENT_ENDPOINT_KEYS:
        env.pop(key, None)
    env["PATH"] = f"{city / 'bin'}:/usr/bin:/bin"
    env["NO_COLOR"] = "1"
    requested_rollback = _lexical_absolute(evidence_dir, label="rollback evidence")

    with _exclusive_runtime_lock(lock):
        _assert_lock_unchanged(lock, lock_sha256)
        locked = lock_loader(lock)
        tools, version_commands = _verify_tools(
            city, locked, runner=runner, environment=env, password=password
        )
        supervisor, supervisor_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        topology = _discover_topology(city, expected_aegis_root=expected_aegis_root)

        receipt_path = _lexical_absolute(
            transition_receipt, label="transition receipt"
        )
        transition_root = receipt_path.parent
        if receipt_path.name != "transition-receipt.json" or transition_root.parent != city / "runtime" / "evidence" / "endpoint-transition":
            raise EndpointTransitionError("rollback requires an exact city endpoint receipt")
        _real_directory(transition_root, label="transition evidence", owner_only=True)
        receipt, receipt_bytes, before, after = _load_transition_receipt(transition_root)
        _assert_manifest_bound_to_topology(before, topology)
        _assert_manifest_bound_to_topology(after, topology)
        if receipt.get("runtime_lock") != {"path": lock.as_posix(), "sha256": lock_sha256}:
            raise EndpointTransitionError("runtime lock drifted from transition receipt")
        if receipt.get("city_root") != city.as_posix() or receipt.get("aegis_root") != topology.aegis.as_posix():
            raise EndpointTransitionError("transition receipt belongs to another city or rig")
        _assert_tools_match_receipt(tools, receipt.get("tools"))
        current, _ = _manifest(topology, phase="current")

        if requested_rollback.exists() or requested_rollback.is_symlink():
            rollback_root = _evidence_directory(
                requested_rollback, city=city, category="endpoint-rollback", create=False
            )
            rollback_receipt_path = rollback_root / "rollback-receipt.json"
            if rollback_receipt_path.exists() or rollback_receipt_path.is_symlink():
                rollback_receipt, rollback_bytes = _read_private_json(
                    rollback_receipt_path, label="endpoint rollback receipt"
                )
                required_receipt = {
                    "schema_version", "kind", "status", "created_at", "city_root",
                    "aegis_root", "runtime_lock", "transition_receipt_path",
                    "transition_receipt_sha256", "restored_tree_sha256",
                    "managed_service_started", "supervisor", "tools", "commands",
                }
                if (
                    set(rollback_receipt) != required_receipt
                    or rollback_receipt.get("schema_version") != ROLLBACK_SCHEMA
                    or rollback_receipt.get("kind") != "hq-host-endpoint-rollback"
                    or rollback_receipt.get("status") != "verified"
                    or rollback_receipt.get("city_root") != city.as_posix()
                    or rollback_receipt.get("aegis_root") != topology.aegis.as_posix()
                    or rollback_receipt.get("runtime_lock")
                    != {"path": lock.as_posix(), "sha256": lock_sha256}
                    or rollback_receipt.get("transition_receipt_path")
                    != receipt_path.as_posix()
                    or rollback_receipt.get("transition_receipt_sha256")
                    != _sha256(receipt_bytes)
                    or rollback_receipt.get("restored_tree_sha256")
                    != before["tree_sha256"]
                    or rollback_receipt.get("managed_service_started") is not False
                ):
                    raise EndpointTransitionError("endpoint rollback receipt is invalid")
                _assert_tools_match_receipt(tools, rollback_receipt.get("tools"))
                if not _manifests_equal(current, before):
                    raise EndpointTransitionError("rolled-back endpoint files have drifted")
                if _entry_by_role(current, "hq_managed_state").get("present"):
                    raise EndpointTransitionError(
                        "rolled-back endpoint unexpectedly publishes managed Dolt state"
                    )
                if _entry_by_role(current, "hq_provider_pid").get("present"):
                    raise EndpointTransitionError(
                        "rolled-back endpoint unexpectedly publishes a managed Dolt pid"
                    )
                _verify_stopped_provider_state(topology)
                _assert_lock_unchanged(lock, lock_sha256)
                return {
                    "status": "already-verified",
                    "action": "none",
                    "receipt_path": rollback_receipt_path.as_posix(),
                    "receipt_sha256": _sha256(rollback_bytes),
                }

            prepared_path = rollback_root / "prepared.json"
            prepared_value, _ = _read_private_json(
                prepared_path, label="endpoint rollback prepared journal"
            )
            expected_prepared = {
                "schema_version": ROLLBACK_SCHEMA,
                "kind": "hq-host-endpoint-rollback-prepared",
                "status": "prepared",
                "city_root": city.as_posix(),
                "aegis_root": topology.aegis.as_posix(),
                "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
                "transition_receipt_path": receipt_path.as_posix(),
                "transition_receipt_sha256": _sha256(receipt_bytes),
                "post_tree_sha256": after["tree_sha256"],
                "pre_tree_sha256": before["tree_sha256"],
                "tools": tools,
                "commands": {
                    **version_commands,
                    "supervisor_before": supervisor_command,
                },
            }
            if prepared_value != expected_prepared:
                raise EndpointTransitionError(
                    "endpoint rollback prepared journal is invalid or drifted"
                )
            if not _manifest_is_entrywise_mixture(current, before, after):
                raise EndpointTransitionError(
                    "rollback resume refused: files are not an exact pre/post mixture"
                )
        else:
            if not _manifests_equal(current, after):
                raise EndpointTransitionError(
                    "rollback refused: current files do not exactly match verified post-state"
                )
            _verify_hq_state(topology)
            rollback_root = _evidence_directory(
                requested_rollback, city=city, category="endpoint-rollback", create=True
            )
            prepared = {
            "schema_version": ROLLBACK_SCHEMA,
            "kind": "hq-host-endpoint-rollback-prepared",
            "status": "prepared",
            "city_root": city.as_posix(),
            "aegis_root": topology.aegis.as_posix(),
            "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
            "transition_receipt_path": receipt_path.as_posix(),
            "transition_receipt_sha256": _sha256(receipt_bytes),
            "post_tree_sha256": after["tree_sha256"],
            "pre_tree_sha256": before["tree_sha256"],
            "tools": tools,
            "commands": {**version_commands, "supervisor_before": supervisor_command},
            }
            _write_json(rollback_root / "prepared.json", prepared)
        _restore_manifest(before, after, evidence_root=transition_root)
        restored_topology = _discover_topology(
            city, expected_aegis_root=expected_aegis_root
        )
        restored, _ = _manifest(restored_topology, phase="current")
        if not _manifests_equal(restored, before):
            raise EndpointTransitionError("rollback did not restore exact pre-transition bytes")
        if _entry_by_role(restored, "hq_managed_state").get("present"):
            raise EndpointTransitionError("rollback would publish a managed service as running")
        if _entry_by_role(restored, "hq_provider_pid").get("present"):
            raise EndpointTransitionError("rollback would publish a managed Dolt pid")
        _verify_stopped_provider_state(restored_topology)
        supervisor_after, supervisor_after_command = _supervisor_stopped(
            city, runner=runner, environment=env, password=password
        )
        final_state, _ = _manifest(restored_topology, phase="current")
        if not _manifests_equal(final_state, before):
            raise EndpointTransitionError(
                "rollback topology changed while proving the supervisor stopped"
            )
        _assert_lock_unchanged(lock, lock_sha256)
        rollback_receipt = {
            "schema_version": ROLLBACK_SCHEMA,
            "kind": "hq-host-endpoint-rollback",
            "status": "verified",
            "created_at": _format_utc(_utc_now() if now is None else now),
            "city_root": city.as_posix(),
            "aegis_root": topology.aegis.as_posix(),
            "runtime_lock": {"path": lock.as_posix(), "sha256": lock_sha256},
            "transition_receipt_path": receipt_path.as_posix(),
            "transition_receipt_sha256": _sha256(receipt_bytes),
            "restored_tree_sha256": before["tree_sha256"],
            "managed_service_started": False,
            "supervisor": {"before": supervisor, "after": supervisor_after},
            "tools": tools,
            "commands": {
                **version_commands,
                "supervisor_before": supervisor_command,
                "supervisor_after": supervisor_after_command,
            },
        }
        rollback_sha256, _ = _write_json(
            rollback_root / "rollback-receipt.json", rollback_receipt
        )
        return {
            "status": "verified",
            "action": "rolled-back",
            "receipt_path": (rollback_root / "rollback-receipt.json").as_posix(),
            "receipt_sha256": rollback_sha256,
            "restored_tree_sha256": before["tree_sha256"],
            "managed_service_started": False,
        }
