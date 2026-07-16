"""Deterministic, read-only Obsidian projection for Aegis evidence.

The vault is a disposable view, never workflow authority.  It consumes normalized
ledger events plus authoritative Beads, capsule, and legacy workflow files and
renders a bounded graph of Markdown notes and Obsidian Bases.  It never writes to
the target repository, never copies raw commands, and never edits an existing
directory that it cannot prove it owns.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "2"
GENERATOR = "aegis-foundation:obsidian-vault"
MANIFEST_NAME = ".aegis-vault.json"
DEFAULT_VAULT_DIRNAME = "obsidian-vault"
BEADS_EXPORT_COMMAND = ("bd", "--readonly", "-C", "<repository>", "export")

HIGH_SIGNAL_EVENT_TYPES = frozenset(
    {
        "checkpoint",
        "delivery",
        "operator_authority",
        "risk",
        "scope",
        "session_begin",
        "session_end",
        "task_truth",
        "tool_failure",
        "verification",
        "witness",
    }
)
EVIDENCE_EVENT_TYPES = frozenset(
    {
        "delivery",
        "operator_authority",
        "risk",
        "task_truth",
        "tool_failure",
        "verification",
        "witness",
    }
)
LEGACY_PREFIXES = (
    "sessions/",
    "plans/",
    "docs/ai/work-tracking/",
)
LEGACY_ROOT_FILES = frozenset({"HANDOFF.md", "STATUS.md"})
SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/=]+"), "Bearer [REDACTED]"),
    (re.compile(r"\b(?:ghp|github_pat|sk)_[A-Za-z0-9_\-]{8,}\b"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}(?:\.[A-Za-z0-9_\-]+){1,2}"), "[REDACTED]"),
)
_TASK_IN_TEXT = re.compile(r"(?i)(?:task[-_ ]?)(\d+(?:\.\d+)?)")
_TASK_BRANCH = re.compile(r"(?i)(?:^|/)feat/task-(\d+)(?:-|$)")
_TASKMASTER_EXTERNAL_REF = re.compile(r"^taskmaster:master:(\d+(?:\.\d+)*)$")
_SAFE_BEAD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_RELATION_TYPE = re.compile(r"^[a-z][a-z0-9-]*$")
_MARKER_BEGIN = re.compile(r"<!--\s*AEGIS:BEGIN\b")
_MARKER_END = re.compile(r"<!--\s*AEGIS:END\b")


class VaultError(RuntimeError):
    """Raised when a vault cannot be derived or safely replaced."""


@dataclass(frozen=True)
class VaultLimits:
    """Hard ceilings that keep the derived view safe for agents and humans."""

    max_tasks: int = 2_000
    max_sessions: int = 500
    max_branches: int = 500
    max_agents: int = 2_000
    max_worktrees: int = 500
    max_identity_edges: int = 5_000
    max_evidence_notes: int = 1_000
    max_legacy_documents: int = 5_000
    max_legacy_bytes: int = 2 * 1024 * 1024
    max_body_chars: int = 2_000


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_json(value: Any) -> str:
    return _digest_bytes(_canonical_json(value).encode("utf-8"))


def _redact(value: Any, *, limit: int = 500) -> str:
    text = " ".join(str(value or "").split())
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    if len(text) > limit:
        suffix = "…#" + _digest_bytes(text.encode("utf-8"))[:10]
        text = text[: max(0, limit - len(suffix))] + suffix
    return text


def _yaml_value(value: Any) -> str:
    """Render JSON scalars/collections; JSON is valid YAML and deterministic."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _frontmatter(properties: Mapping[str, Any]) -> str:
    lines = ["---"]
    for key in sorted(properties):
        lines.append(f"{key}: {_yaml_value(properties[key])}")
    lines.extend(("---", ""))
    return "\n".join(lines)


def _markdown(properties: Mapping[str, Any], title: str, body: Iterable[str]) -> str:
    lines = [_frontmatter(properties), f"# {_redact(title, limit=200)}", ""]
    lines.extend(body)
    return "\n".join(lines).rstrip() + "\n"


def _slug(value: Any, *, fallback: str = "unknown", limit: int = 60) -> str:
    source = _redact(value, limit=300).lower()
    slug = re.sub(r"[^a-z0-9._-]+", "-", source).strip("-._") or fallback
    slug = slug[:limit].rstrip("-._") or fallback
    return f"{slug}-{_digest_bytes(source.encode('utf-8'))[:8]}"


def _link(path: str, label: str | None = None) -> str:
    target = path[:-3] if path.endswith(".md") else path
    return f"[[{target}|{_redact(label, limit=160)}]]" if label else f"[[{target}]]"


def _git(target: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise VaultError(f"unable to inspect git repository at {target}: {exc}") from exc
    if result.returncode != 0:
        detail = _redact(result.stderr or result.stdout, limit=300)
        raise VaultError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def repository_root(target_dir: str | Path) -> Path:
    target = Path(target_dir).expanduser().resolve()
    root = Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    if not root.is_dir():
        raise VaultError(f"repository root does not exist: {root}")
    return root


def default_vault_path(ledger_store_dir: str | Path) -> Path:
    return Path(ledger_store_dir).expanduser().resolve() / DEFAULT_VAULT_DIRNAME


def _run_beads_command(
    executable: str | Path,
    root: Path,
    arguments: Sequence[str],
    *,
    pass_fds: Sequence[int] = (),
) -> bytes:
    command = [str(executable), *arguments]
    try:
        result = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            timeout=60,
            check=False,
            pass_fds=tuple(pass_fds),
        )
    except FileNotFoundError as exc:
        raise VaultError(
            "unable to read authoritative Beads tasks: bd is not installed or not on PATH"
        ) from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VaultError(f"unable to read authoritative Beads tasks: {exc}") from exc
    if result.returncode != 0:
        try:
            diagnostic = (result.stderr or result.stdout).decode("utf-8", errors="replace")
        except AttributeError:  # pragma: no cover - defensive injected runner guard.
            diagnostic = str(result.stderr or result.stdout)
        detail = _redact(diagnostic, limit=500) or "no diagnostic"
        raise VaultError(f"read-only Beads command failed: {detail}")
    return result.stdout


def _beads_head(
    executable: str | Path,
    root: Path,
    *,
    pass_fds: Sequence[int] = (),
) -> str:
    content = _run_beads_command(
        executable,
        root,
        [
            "--json",
            "--readonly",
            "-C",
            str(root),
            "sql",
            "SELECT HASHOF('main') AS head;",
        ],
        pass_fds=pass_fds,
    )

    def reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, child in pairs:
            if key in result:
                raise VaultError(f"duplicate Beads Dolt-head response key: {key!r}")
            result[key] = child
        return result

    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VaultError(f"invalid Beads Dolt-head response: {exc}") from exc

    heads: list[str] = []

    def collect_heads(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key).lower() == "head" and isinstance(child, str):
                    if re.fullmatch(r"[0-9a-v]{20,128}", child.lower()):
                        heads.append(child)
                collect_heads(child)
        elif isinstance(item, list):
            for child in item:
                collect_heads(child)

    collect_heads(value)
    if len(heads) != 1:
        raise VaultError(
            "Beads Dolt-head response must contain exactly one valid main head"
        )
    return heads[0]


def _digest_open_file(descriptor: int) -> str:
    """Hash an already-open regular file without changing the caller's offset."""

    try:
        original_offset = os.lseek(descriptor, 0, os.SEEK_CUR)
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        os.lseek(descriptor, original_offset, os.SEEK_SET)
    except OSError as exc:
        raise VaultError("unable to hash the open Beads executable") from exc
    return digest.hexdigest()


def _beads_snapshot(
    root: Path,
    *,
    executable: str | Path,
    expected_sha256: str | None,
) -> tuple[bytes, dict[str, str]]:
    raw = str(executable)
    if os.sep in raw or (os.altsep and os.altsep in raw):
        candidate = Path(raw).expanduser()
    else:
        located = shutil.which(raw)
        if located is None:
            raise VaultError("unable to read authoritative Beads tasks: bd is not on PATH")
        candidate = Path(located)
    try:
        binary = candidate.resolve(strict=True)
    except OSError as exc:
        raise VaultError(f"unable to resolve Beads executable: {candidate}") from exc
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - Gas City workers are Linux.
        raise VaultError("this runtime cannot bind the Beads executable safely")
    try:
        descriptor = os.open(binary, os.O_RDONLY | os.O_CLOEXEC | no_follow)
    except (OSError, ValueError) as exc:
        raise VaultError(f"unable to open Beads executable safely: {binary}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise VaultError(f"Beads executable is not a regular file: {binary}")
        if before.st_mode & 0o022:
            raise VaultError("Beads executable must not be group- or world-writable")
        if not before.st_mode & 0o111:
            raise VaultError(f"Beads executable is not executable: {binary}")
        binary_sha256 = _digest_open_file(descriptor)
        if expected_sha256 is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
                raise VaultError("expected Beads executable SHA-256 is invalid")
            if binary_sha256 != expected_sha256:
                raise VaultError("Beads executable SHA-256 does not match the projection pin")
        descriptor_path = f"/proc/self/fd/{descriptor}"
        if not Path("/proc/self/fd").is_dir():  # pragma: no cover - Gas City is Linux.
            raise VaultError("this runtime cannot execute the pinned Beads file descriptor")
        version_bytes = _run_beads_command(
            descriptor_path,
            root,
            ["--version"],
            pass_fds=(descriptor,),
        )
        try:
            version = version_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise VaultError("Beads version output is not valid UTF-8") from exc
        if re.fullmatch(r"bd version 1\.1\.0 \([0-9a-f]+\)", version) is None:
            raise VaultError("Obsidian projection requires exact Beads 1.1.0")
        head_before = _beads_head(
            descriptor_path,
            root,
            pass_fds=(descriptor,),
        )
        export = _run_beads_command(
            descriptor_path,
            root,
            ["--readonly", "-C", str(root), "export"],
            pass_fds=(descriptor,),
        )
        head_after = _beads_head(
            descriptor_path,
            root,
            pass_fds=(descriptor,),
        )
        if head_before != head_after:
            raise VaultError("Beads main head changed while the projection export was captured")
        after = os.fstat(descriptor)
        path_after = os.stat(binary, follow_symlinks=False)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        path_identity_after = (
            path_after.st_dev,
            path_after.st_ino,
            path_after.st_size,
            path_after.st_mtime_ns,
        )
        if identity_before != identity_after or identity_before != path_identity_after:
            raise VaultError("Beads executable changed while the projection was captured")
        if _digest_open_file(descriptor) != binary_sha256:
            raise VaultError("Beads executable content changed while the projection was captured")
    except OSError as exc:
        raise VaultError(f"unable to attest Beads executable: {binary}") from exc
    finally:
        os.close(descriptor)
    return export, {
        "binary": binary.as_posix(),
        "binary_sha256": binary_sha256,
        "version": version,
        "raw_export_sha256": _digest_bytes(export),
        "dolt_main_head": head_after,
    }


def _validated_bead_id(value: Any, *, context: str) -> str:
    if not isinstance(value, str):
        raise VaultError(f"invalid Beads export {context}: id must be a string")
    issue_id = value.strip()
    if value != issue_id or not _SAFE_BEAD_ID.fullmatch(issue_id) or issue_id in {".", ".."}:
        raise VaultError(f"invalid Beads export {context}: unsafe issue id {value!r}")
    return issue_id


def _normalized_beads_status(value: Any, *, issue_id: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VaultError(f"invalid Beads export issue {issue_id}: status must be a string")
    status = value.strip().lower().replace("-", "_").replace(" ", "_")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", status):
        raise VaultError(f"invalid Beads export issue {issue_id}: unsafe status {value!r}")
    return status


def _normalized_beads_priority(value: Any, *, issue_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4:
        raise VaultError(
            f"invalid Beads export issue {issue_id}: priority must be an integer from 0 to 4"
        )
    return value


def _taskmaster_alias(external_ref: str) -> str:
    match = _TASKMASTER_EXTERNAL_REF.fullmatch(external_ref)
    return match.group(1) if match else ""


def _task_records(raw_export_bytes: bytes, limits: VaultLimits) -> list[dict[str, Any]]:
    """Parse every issue and typed relationship from ``bd export`` JSONL."""

    def reject_duplicate_keys(
        pairs: Sequence[tuple[str, Any]],
    ) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, child in pairs:
            if key in value:
                raise VaultError(
                    f"invalid Beads export: duplicate JSON object key {key!r}"
                )
            value[key] = child
        return value

    def reject_non_finite(value: str) -> None:
        raise VaultError(
            f"invalid Beads export: non-finite JSON number {value!r} is not allowed"
        )

    try:
        raw_export = raw_export_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VaultError("authoritative Beads export is not valid UTF-8") from exc
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_aliases: dict[str, str] = {}
    for line_number, line in enumerate(raw_export.splitlines(), start=1):
        if not line.strip():
            raise VaultError(f"invalid Beads export line {line_number}: blank JSONL record")
        try:
            issue = json.loads(
                line,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_non_finite,
            )
        except (json.JSONDecodeError, RecursionError) as exc:
            raise VaultError(f"invalid Beads export line {line_number}: {exc}") from exc
        if not isinstance(issue, Mapping):
            raise VaultError(f"invalid Beads export line {line_number}: expected an object")
        if issue.get("_type") != "issue":
            raise VaultError(
                f"invalid Beads export line {line_number}: expected _type=issue"
            )
        issue_id = _validated_bead_id(issue.get("id"), context=f"line {line_number}")
        if issue_id in seen_ids:
            raise VaultError(f"invalid Beads export: duplicate issue id {issue_id}")
        seen_ids.add(issue_id)
        title = issue.get("title")
        if not isinstance(title, str) or not title.strip():
            raise VaultError(f"invalid Beads export issue {issue_id}: title must be a string")
        description = issue.get("description")
        if description is not None and not isinstance(description, str):
            raise VaultError(
                f"invalid Beads export issue {issue_id}: description must be a string or null"
            )
        external_ref = issue.get("external_ref")
        if external_ref is None:
            external_ref = ""
        elif not isinstance(external_ref, str):
            raise VaultError(
                f"invalid Beads export issue {issue_id}: external_ref must be a string or null"
            )
        alias = _taskmaster_alias(external_ref)
        if alias:
            previous = seen_aliases.get(alias)
            if previous is not None:
                raise VaultError(
                    "invalid Beads export: duplicate Taskmaster alias "
                    f"{alias} on {previous} and {issue_id}"
                )
            seen_aliases[alias] = issue_id
        raw_dependencies = issue.get("dependencies", [])
        if raw_dependencies is None:
            raw_dependencies = []
        if not isinstance(raw_dependencies, list):
            raise VaultError(
                f"invalid Beads export issue {issue_id}: dependencies must be a list"
            )
        relationships: list[dict[str, str]] = []
        seen_relationships: set[tuple[str, str]] = set()
        for dependency_number, dependency in enumerate(raw_dependencies, start=1):
            context = f"issue {issue_id} dependency {dependency_number}"
            if not isinstance(dependency, Mapping):
                raise VaultError(f"invalid Beads export {context}: expected an object")
            source_id = _validated_bead_id(dependency.get("issue_id"), context=context)
            if source_id != issue_id:
                raise VaultError(
                    f"invalid Beads export {context}: issue_id does not match containing issue"
                )
            target_id = _validated_bead_id(dependency.get("depends_on_id"), context=context)
            raw_type = dependency.get("type")
            if not isinstance(raw_type, str):
                raise VaultError(f"invalid Beads export {context}: type must be a string")
            relation_type = raw_type.strip()
            if not _SAFE_RELATION_TYPE.fullmatch(relation_type):
                raise VaultError(
                    f"invalid Beads export {context}: unsafe relationship type {raw_type!r}"
                )
            relation = (relation_type, target_id)
            if relation in seen_relationships:
                raise VaultError(
                    f"invalid Beads export {context}: duplicate {relation_type} edge to {target_id}"
                )
            seen_relationships.add(relation)
            relationships.append({"type": relation_type, "target_id": target_id})
        raw_issue_type = issue.get("issue_type", "task")
        if not isinstance(raw_issue_type, str) or not raw_issue_type.strip():
            raise VaultError(
                f"invalid Beads export issue {issue_id}: issue_type must be a string"
            )
        issue_type = raw_issue_type.strip()
        if not _SAFE_RELATION_TYPE.fullmatch(issue_type):
            raise VaultError(
                f"invalid Beads export issue {issue_id}: unsafe issue_type {raw_issue_type!r}"
            )
        records.append(
            {
                "id": issue_id,
                "title": _redact(title, limit=240),
                "status": _normalized_beads_status(issue.get("status"), issue_id=issue_id),
                "priority": _normalized_beads_priority(
                    issue.get("priority"), issue_id=issue_id
                ),
                "issue_type": issue_type,
                "external_ref": _redact(external_ref, limit=500),
                "taskmaster_alias": alias,
                "description": _redact(description, limit=limits.max_body_chars),
                "relationships": sorted(
                    relationships,
                    key=lambda item: (item["type"], _natural_id_key(item["target_id"])),
                ),
            }
        )
    if len(records) > limits.max_tasks:
        raise VaultError(
            f"Beads projection exceeds task limit ({len(records)} > {limits.max_tasks})"
        )
    return sorted(records, key=lambda item: _natural_id_key(item["id"]))


def _natural_id_key(value: str) -> tuple[Any, ...]:
    """Return a total-order key for arbitrary mixed numeric and textual IDs."""

    parts = re.split(r"(\d+)", str(value))
    tokens: list[tuple[Any, ...]] = []
    for part in parts:
        if part.isdigit():
            tokens.append((0, int(part), len(part), part))
        else:
            tokens.append((1, part.casefold(), part))
    return (*tokens, (2, str(value)))


def _selected_capsule(root: Path) -> dict[str, Any]:
    path = root / ".aegis" / "capsule" / "current.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "invalid"}
    if not isinstance(payload, Mapping):
        return {"status": "invalid"}
    selected: dict[str, Any] = {"status": "available"}
    keys = (
        "active_task",
        "active_subtask",
        "next_action",
        "orientation_source",
        "branch",
        "head",
        "suggested_next",
    )
    containers = [payload]
    for name in ("task_truth", "orientation", "repository", "git"):
        value = payload.get(name)
        if isinstance(value, Mapping):
            containers.append(value)
    for key in keys:
        for container in containers:
            if key in container:
                value = container[key]
                if isinstance(value, Mapping):
                    selected[key] = {
                        str(item_key): _redact(item_value, limit=240)
                        for item_key, item_value in value.items()
                        if item_key in {"id", "title", "status", "action", "command", "reason"}
                    }
                elif isinstance(value, (str, int, float, bool)) or value is None:
                    selected[key] = _redact(value, limit=500) if isinstance(value, str) else value
                break
    selected["source_digest"] = _digest_bytes(path.read_bytes())
    return selected


def _legacy_kind(path: Path) -> str:
    name = path.name.upper()
    if name == "DECISIONS.MD":
        return "decision-record"
    if name in {"FINDINGS.MD", "HANDOFF.MD"}:
        return "risk-context"
    if name == "TRACKER.MD":
        return "tracker"
    if name == "IMPLEMENTATION.MD":
        return "implementation"
    if name == "CHANGELOG.MD":
        return "changelog"
    if "SESSION" in name or path.parts[0:1] == ("sessions",):
        return "session"
    if "PLAN" in name or path.parts[0:1] == ("plans",):
        return "plan"
    return "legacy-document"


def _legacy_inventory(root: Path, limits: VaultLimits) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    for prefix in LEGACY_PREFIXES:
        base = root / prefix
        if base.is_dir():
            candidates.extend(
                path for path in base.rglob("*.md") if path.is_file() and not path.is_symlink()
            )
    for filename in LEGACY_ROOT_FILES:
        path = root / filename
        if path.is_file() and not path.is_symlink():
            candidates.append(path)
    unique = sorted({path.resolve() for path in candidates})
    if len(unique) > limits.max_legacy_documents:
        raise VaultError(
            f"legacy projection exceeds document limit ({len(unique)} > {limits.max_legacy_documents})"
        )
    records: list[dict[str, Any]] = []
    for path in unique:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        size = path.stat().st_size
        if size > limits.max_legacy_bytes:
            records.append(
                {
                    "path": relative,
                    "kind": _legacy_kind(Path(relative)),
                    "bytes": size,
                    "status": "oversized-not-read",
                    "human_nonblank_lines": None,
                    "headings": [],
                    "checkboxes": None,
                    "sweh_entries": None,
                    "generated_blocks": None,
                    "task_ids": sorted(set(_TASK_IN_TEXT.findall(relative)), key=_natural_id_key),
                    "content_digest": None,
                }
            )
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        outside: list[str] = []
        headings: list[str] = []
        generated_depth = 0
        generated_blocks = 0
        for line in text.splitlines():
            if _MARKER_BEGIN.search(line):
                generated_depth += 1
                generated_blocks += 1
                continue
            if _MARKER_END.search(line):
                generated_depth = max(0, generated_depth - 1)
                continue
            if generated_depth:
                continue
            if line.strip():
                outside.append(line.rstrip())
                if line.lstrip().startswith("#") and len(headings) < 24:
                    headings.append(_redact(line.lstrip("# "), limit=180))
        normalized = "\n".join(" ".join(line.split()) for line in outside)
        task_ids = set(_TASK_IN_TEXT.findall(relative + "\n" + "\n".join(headings)))
        records.append(
            {
                "path": relative,
                "kind": _legacy_kind(Path(relative)),
                "bytes": size,
                "status": "read",
                "human_nonblank_lines": len(outside),
                "headings": headings,
                "checkboxes": sum(1 for line in outside if re.match(r"^\s*[-*]\s+\[[ xX]\]", line)),
                "sweh_entries": sum(1 for line in outside if "[S:" in line and "|W:" in line),
                "generated_blocks": generated_blocks,
                "task_ids": sorted(task_ids, key=_natural_id_key),
                "content_digest": _digest_bytes(normalized.encode("utf-8")),
            }
        )
    return records


def _safe_extra(event: Mapping[str, Any]) -> dict[str, Any]:
    raw_extra = event.get("extra")
    extra: Mapping[str, Any] = raw_extra if isinstance(raw_extra, Mapping) else {}
    allowed = (
        "action",
        "gate",
        "package",
        "passed",
        "pr_number",
        "reason",
        "report_path",
        "status",
        "task_id",
        "work_id",
    )
    result: dict[str, Any] = {}
    for key in allowed:
        value = extra.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = _redact(value, limit=500) if isinstance(value, str) else value
    return result


def _event_record(event: Mapping[str, Any]) -> dict[str, Any]:
    raw_paths = event.get("paths")
    paths: list[Any] = raw_paths if isinstance(raw_paths, list) else []
    return {
        "event_id": _redact(event.get("event_id"), limit=100),
        "ts": _redact(event.get("ts"), limit=80),
        "event_type": _redact(event.get("event_type"), limit=80) or "unknown",
        "session_id": _redact(event.get("session_id"), limit=160),
        "branch": _redact(event.get("branch"), limit=240),
        "head": _redact(event.get("head"), limit=80),
        "worktree": _redact(event.get("worktree_root"), limit=500),
        "agent_id": _redact(event.get("agent_id"), limit=240),
        "agent_type": _redact(event.get("agent_type"), limit=80),
        "parent_agent_id": _redact(event.get("parent_agent_id"), limit=240),
        "outcome": _redact(event.get("outcome"), limit=40),
        "exit_class": _redact(event.get("exit_class"), limit=40),
        "handler": _redact(event.get("handler"), limit=120),
        "tool_name": _redact(event.get("tool_name"), limit=120),
        "paths": [_redact(path, limit=400) for path in paths[:64]],
        "extra": _safe_extra(event),
    }


def _identity_records(
    events: Sequence[Mapping[str, Any]], limits: VaultLimits
) -> list[dict[str, str]]:
    """Deduplicate stable topology from all rows without copying low-level events."""

    fields = (
        "session_id",
        "branch",
        "worktree",
        "agent_id",
        "agent_type",
        "parent_agent_id",
    )
    records = {
        tuple(str(event.get(field) or "") for field in fields)
        for event in events
        if any(event.get(field) for field in fields)
    }
    if len(records) > limits.max_identity_edges:
        raise VaultError(
            "identity projection exceeds edge limit "
            f"({len(records)} > {limits.max_identity_edges})"
        )
    result = [dict(zip(fields, values)) for values in sorted(records)]
    ceilings = {
        "session_id": limits.max_sessions,
        "branch": limits.max_branches,
        "agent_id": limits.max_agents,
        "worktree": limits.max_worktrees,
    }
    for field, ceiling in ceilings.items():
        values = {record[field] for record in result if record[field]}
        if field == "agent_id":
            values.update(
                record["parent_agent_id"] for record in result if record["parent_agent_id"]
            )
        if len(values) > ceiling:
            raise VaultError(
                f"identity projection exceeds {field} limit ({len(values)} > {ceiling})"
            )
    return result


def _task_from_event(event: Mapping[str, Any]) -> str:
    raw_extra = event.get("extra")
    extra: Mapping[str, Any] = raw_extra if isinstance(raw_extra, Mapping) else {}
    for value in (extra.get("task_id"), extra.get("task"), extra.get("work_id")):
        if isinstance(value, Mapping):
            value = value.get("id")
        text = str(value or "").strip()
        if _SAFE_BEAD_ID.fullmatch(text):
            return text
        match = _TASK_IN_TEXT.search(text)
        if match:
            return match.group(1)
    match = _TASK_BRANCH.search(str(event.get("branch") or ""))
    return match.group(1) if match else ""


def collect_snapshot(
    target_dir: str | Path,
    events: Sequence[Mapping[str, Any]],
    *,
    repository_identity: str | None = None,
    limits: VaultLimits | None = None,
    bd_executable: str | Path = "bd",
    expected_bd_sha256: str | None = None,
) -> dict[str, Any]:
    """Collect a deterministic, redacted model without modifying the target."""

    active_limits = limits or VaultLimits()
    root = repository_root(target_dir)
    normalized_events = [_event_record(event) for event in events]
    high_signal = [
        event for event in normalized_events if event["event_type"] in HIGH_SIGNAL_EVENT_TYPES
    ]
    high_signal.sort(key=lambda event: (event["ts"], event["event_id"]))
    common_dir = Path(_git(root, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = (root / common_dir).resolve()
    canonical_name = common_dir.parent.name if common_dir.name == ".git" else root.name
    context_identity = repository_identity or next(
        (
            _redact(event.get("repository_identity"), limit=160)
            for event in events
            if event.get("repository_identity")
        ),
        "",
    )
    if not context_identity:
        context_identity = "sha256:" + _digest_bytes(common_dir.as_posix().encode("utf-8"))
    beads_export, beads_provenance = _beads_snapshot(
        root,
        executable=bd_executable,
        expected_sha256=expected_bd_sha256,
    )
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "repository": {
            "name": _redact(canonical_name, limit=160),
            "identity": context_identity,
            "head": _git(root, "rev-parse", "HEAD"),
            "branch": _git(root, "branch", "--show-current"),
        },
        "task_source": {
            "authority": "beads/dolt",
            "command": " ".join(BEADS_EXPORT_COMMAND),
            **beads_provenance,
        },
        "tasks": _task_records(beads_export, active_limits),
        "capsule": _selected_capsule(root),
        "legacy_documents": _legacy_inventory(root, active_limits),
        "events": high_signal,
        "identities": _identity_records(normalized_events, active_limits),
        "event_summary": {
            "high_signal_count": len(high_signal),
            "by_type": dict(sorted(Counter(event["event_type"] for event in high_signal).items())),
            "latest_ts": max((event["ts"] for event in high_signal), default=""),
        },
        "limits": active_limits.__dict__,
    }
    snapshot["source_digest"] = _digest_json(snapshot)
    return snapshot


def _relation_maps(snapshot: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    tasks = {str(task["id"]): f"Tasks/task-{task['id']}.md" for task in snapshot["tasks"]}
    task_aliases = {
        str(task["taskmaster_alias"]): str(task["id"])
        for task in snapshot["tasks"]
        if task.get("taskmaster_alias")
    }
    identities = [item for item in snapshot.get("identities", []) if isinstance(item, Mapping)]
    sessions = sorted(
        {str(item.get("session_id") or "") for item in identities if item.get("session_id")}
    )
    branches = sorted({str(item.get("branch") or "") for item in identities if item.get("branch")})
    agents = sorted(
        {
            value
            for item in identities
            for value in (
                str(item.get("agent_id") or ""),
                str(item.get("parent_agent_id") or ""),
            )
            if value
        }
    )
    worktrees = sorted(
        {str(item.get("worktree") or "") for item in identities if item.get("worktree")}
    )
    return {
        "tasks": tasks,
        "task_aliases": task_aliases,
        "sessions": {value: f"Sessions/{_slug(value)}.md" for value in sessions},
        "branches": {value: f"Branches/{_slug(value)}.md" for value in branches},
        "agents": {value: f"Agents/{_slug(value)}.md" for value in agents},
        "worktrees": {value: f"Worktrees/{_slug(value)}.md" for value in worktrees},
    }


def _canonical_task_id(value: Any, maps: Mapping[str, Mapping[str, str]]) -> str:
    task_id = str(value or "").strip()
    if task_id in maps["tasks"]:
        return task_id
    alias_match = maps["task_aliases"].get(task_id)
    if alias_match:
        return alias_match
    legacy_match = _TASK_IN_TEXT.search(task_id)
    if legacy_match:
        return maps["task_aliases"].get(legacy_match.group(1), "")
    return ""


def _task_link(
    task_id: str,
    maps: Mapping[str, Mapping[str, str]],
    *,
    external_label: str | None = None,
) -> str:
    if task_id in maps["tasks"]:
        return _link(maps["tasks"][task_id], external_label or f"Bead {task_id}")
    return f"`{_redact(task_id, limit=160)}` (outside this export)"


def _event_links(event: Mapping[str, Any], maps: Mapping[str, Mapping[str, str]]) -> list[str]:
    links: list[str] = []
    source_task_id = _task_from_event(event)
    task_id = _canonical_task_id(source_task_id, maps)
    if task_id:
        label = f"Bead {task_id}"
        if source_task_id != task_id:
            label += f" (Taskmaster {source_task_id})"
        links.append(_task_link(task_id, maps, external_label=label))
    for field, key, label in (
        ("session_id", "sessions", "Session"),
        ("branch", "branches", "Branch"),
        ("agent_id", "agents", "Agent"),
        ("parent_agent_id", "agents", "Parent agent"),
        ("worktree", "worktrees", "Worktree"),
    ):
        value = str(event.get(field) or "")
        if value and value in maps[key]:
            display = Path(value).name if field == "worktree" else value
            links.append(_link(maps[key][value], f"{label}: {_redact(display, limit=80)}"))
    return links


def _render_base(kind: str, title: str, columns: Sequence[str]) -> str:
    order = "\n".join(f"      - {column}" for column in columns)
    return (
        "filters:\n"
        "  and:\n"
        f"    - 'aegis_kind == \"{kind}\"'\n"
        "views:\n"
        "  - type: table\n"
        f"    name: {_yaml_value(title)}\n"
        "    order:\n"
        f"{order}\n"
    )


def render_vault(snapshot: Mapping[str, Any]) -> dict[str, bytes]:
    """Render every owned file as UTF-8 bytes, excluding the ownership manifest."""

    limits = VaultLimits(**dict(snapshot.get("limits") or {}))
    maps = _relation_maps(snapshot)
    files: dict[str, bytes] = {}

    def add(path: str, text: str) -> None:
        normalized = Path(path).as_posix()
        if normalized.startswith("/") or ".." in Path(normalized).parts:
            raise VaultError(f"unsafe generated path: {path}")
        files[normalized] = text.encode("utf-8")

    repository = snapshot["repository"]
    event_summary = snapshot["event_summary"]
    legacy = snapshot["legacy_documents"]
    home_body = [
        "This vault is a generated, read-only view of Aegis evidence. Edit the authoritative repository or ledger—not these notes.",
        "",
        "## Current repository truth",
        f"- Branch: `{_redact(repository['branch'], limit=160)}`",
        f"- HEAD: `{_redact(repository['head'], limit=80)}`",
        f"- Task authority: `{snapshot['task_source']['authority']}` via read-only export",
        f"- High-signal ledger events: {event_summary['high_signal_count']}",
        f"- Stable identity relationships: {len(snapshot.get('identities') or [])}",
        f"- Preserved legacy documents inventoried: {len(legacy)}",
        "- Low-level mutation and gate traffic is intentionally not expanded into notes.",
        "",
        "## Views",
        "- " + _link("Views/Tasks.base", "Tasks"),
        "- " + _link("Views/Evidence.base", "Evidence"),
        "- " + _link("Views/Legacy.base", "Legacy documents"),
        "- " + _link("Orientation.md", "Computed orientation snapshot"),
        "- " + _link("Indexes/Activity.md", "Activity and evidence index"),
    ]
    add(
        "Home.md",
        _markdown(
            {
                "aegis_kind": "home",
                "aegis_schema": SCHEMA_VERSION,
                "repository": repository["name"],
                "source_digest": snapshot["source_digest"],
                "tags": ["aegis-vault"],
            },
            f"{repository['name']} Aegis Knowledge Vault",
            home_body,
        ),
    )
    add(
        "README.md",
        _markdown(
            {
                "aegis_kind": "readme",
                "aegis_schema": SCHEMA_VERSION,
                "tags": ["aegis-vault", "generated"],
            },
            "About this generated vault",
            [
                "- Authority remains in Git, Beads/Dolt, the passive Aegis ledger, and deterministic delivery evidence.",
                "- Task notes come only from `bd --readonly -C <repository> export`; export failure stops the build.",
                "- Rebuild with `aegis vault build`; verify with `aegis vault check`.",
                "- The generator refuses directories containing files it does not own.",
                "- Raw commands and low-level event payloads are not copied into the vault.",
                "- `.obsidian/` configuration and third-party plugins are intentionally not generated.",
            ],
        ),
    )

    raw_capsule = snapshot.get("capsule")
    capsule: Mapping[str, Any] = raw_capsule if isinstance(raw_capsule, Mapping) else {}
    orientation_body = [
        "The capsule is a computed orientation input; this note is only its bounded projection.",
        "",
    ]
    for key in sorted(capsule):
        if key == "source_digest":
            continue
        orientation_body.append(f"- **{key}**: `{_redact(capsule[key], limit=500)}`")
    active_task = capsule.get("active_task")
    if isinstance(active_task, Mapping):
        source_task_id = str(active_task.get("id") or "")
        task_id = _canonical_task_id(source_task_id, maps)
        if task_id:
            orientation_body.append(f"- Related: {_task_link(task_id, maps)}")
    add(
        "Orientation.md",
        _markdown(
            {
                "aegis_kind": "orientation",
                "aegis_schema": SCHEMA_VERSION,
                "branch": repository["branch"],
                "head": repository["head"],
                "tags": ["aegis-vault", "orientation"],
            },
            "Computed orientation",
            orientation_body,
        ),
    )

    legacy_by_task: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for document in legacy:
        for source_task_id in document["task_ids"]:
            task_id = _canonical_task_id(source_task_id, maps)
            if task_id:
                legacy_by_task[task_id].append(document)

    incoming_relationships: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source_task in snapshot["tasks"]:
        for relationship in source_task["relationships"]:
            incoming_relationships[str(relationship["target_id"])].append(
                {"type": str(relationship["type"]), "source_id": str(source_task["id"])}
            )
    for relationships in incoming_relationships.values():
        relationships.sort(
            key=lambda item: (item["type"], _natural_id_key(item["source_id"]))
        )

    for task in snapshot["tasks"]:
        task_id = str(task["id"])
        body = [
            f"- Status: **{task['status']}**",
            f"- Priority: `P{task['priority']}`",
            f"- Type: `{task['issue_type']}`",
        ]
        if task["taskmaster_alias"]:
            body.append(
                "- Migration alias: "
                f"`taskmaster:master:{task['taskmaster_alias']}` (non-authoritative)"
            )
        elif task["external_ref"]:
            body.append(f"- External reference: `{task['external_ref']}`")
        if task["description"]:
            body.extend(("", "## Description", task["description"]))
        outbound_by_type: dict[str, list[str]] = defaultdict(list)
        for relationship in task["relationships"]:
            outbound_by_type[str(relationship["type"])].append(
                str(relationship["target_id"])
            )
        incoming_by_type: dict[str, list[str]] = defaultdict(list)
        for relationship in incoming_relationships.get(task_id, []):
            incoming_by_type[str(relationship["type"])].append(
                str(relationship["source_id"])
            )
        outbound_headings = {"blocks": "Blocked by", "parent-child": "Parents"}
        incoming_headings = {"blocks": "Blocks", "parent-child": "Children"}
        for relation_type in sorted(outbound_by_type):
            heading = outbound_headings.get(
                relation_type, f"Depends on ({relation_type})"
            )
            body.extend(
                (
                    "",
                    f"## {heading}",
                    *(
                        f"- {_task_link(target_id, maps)}"
                        for target_id in outbound_by_type[relation_type]
                    ),
                )
            )
        for relation_type in sorted(incoming_by_type):
            heading = incoming_headings.get(
                relation_type, f"Depended on by ({relation_type})"
            )
            body.extend(
                (
                    "",
                    f"## {heading}",
                    *(
                        f"- {_task_link(source_id, maps)}"
                        for source_id in incoming_by_type[relation_type]
                    ),
                )
            )
        related_legacy = legacy_by_task.get(task_id, [])
        if related_legacy:
            body.extend(
                (
                    "",
                    "## Preserved legacy context",
                    *(
                        f"- {_link('Legacy/' + _slug(item['path']) + '.md', item['path'])}"
                        for item in related_legacy[:40]
                    ),
                )
            )
        add(
            maps["tasks"][task_id],
            _markdown(
                {
                    "aegis_kind": "task",
                    "aegis_schema": SCHEMA_VERSION,
                    "bead_id": task_id,
                    "external_ref": task["external_ref"],
                    "incoming_relationships": len(incoming_relationships.get(task_id, [])),
                    "issue_type": task["issue_type"],
                    "outbound_relationships": len(task["relationships"]),
                    "priority": task["priority"],
                    "status": task["status"],
                    "task_id": task_id,
                    "taskmaster_alias": task["taskmaster_alias"],
                    "tags": ["aegis-vault", "aegis/task"],
                },
                f"Bead {task_id}: {task['title']}",
                body,
            ),
        )

    grouped_fields = {
        "sessions": "session_id",
        "branches": "branch",
        "agents": "agent_id",
        "worktrees": "worktree",
    }
    identity_records = [
        item for item in snapshot.get("identities", []) if isinstance(item, Mapping)
    ]
    for group, field in grouped_fields.items():
        grouped: dict[str, list[Mapping[str, Any]]] = {value: [] for value in maps[group]}
        identity_grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for event in snapshot["events"]:
            value = str(event.get(field) or "")
            if value:
                grouped[value].append(event)
            if group == "agents":
                parent = str(event.get("parent_agent_id") or "")
                if parent and parent != value:
                    grouped[parent].append(event)
        for identity in identity_records:
            value = str(identity.get(field) or "")
            if value:
                identity_grouped[value].append(identity)
            if group == "agents":
                parent = str(identity.get("parent_agent_id") or "")
                if parent and parent != value:
                    identity_grouped[parent].append(identity)
        for value in sorted(grouped):
            events = grouped[value]
            associations = identity_grouped[value]
            kind = group[:-1] if group.endswith("s") else group
            display = Path(value).name if group == "worktrees" else value
            event_types = dict(sorted(Counter(event["event_type"] for event in events).items()))
            body = [
                f"- High-signal evidence events: {len(events)}",
                f"- Stable identity relationships: {len(associations)}",
            ]
            if events:
                body.append(
                    f"- Latest high-signal evidence: `{max(event['ts'] for event in events)}`"
                )
            if event_types:
                body.append(
                    "- Event classes: "
                    + ", ".join(f"`{key}`={count}" for key, count in event_types.items())
                )
            relations: list[str] = []
            for event in events:
                relations.extend(_event_links(event, maps))
            for association in associations:
                relations.extend(_event_links(association, maps))
            unique_relations = list(dict.fromkeys(relations))[:80]
            if unique_relations:
                body.extend(("", "## Related nodes", *(f"- {item}" for item in unique_relations)))
            properties: dict[str, Any] = {
                "aegis_kind": kind,
                "aegis_schema": SCHEMA_VERSION,
                "event_count": len(events),
                "identity_relationships": len(associations),
                "tags": ["aegis-vault", f"aegis/{kind}"],
            }
            if events:
                properties["latest_evidence"] = max(event["ts"] for event in events)
            if group == "worktrees":
                properties["worktree_fingerprint"] = _digest_bytes(value.encode("utf-8"))
            elif group == "agents":
                properties["agent_fingerprint"] = _digest_bytes(value.encode("utf-8"))
                types = sorted(
                    {
                        str(item.get("agent_type"))
                        for item in [*events, *associations]
                        if item.get("agent_type")
                    }
                )
                properties["agent_types"] = types
            else:
                properties[field] = value
            add(maps[group][value], _markdown(properties, f"{kind.title()}: {display}", body))

    evidence = [
        event for event in snapshot["events"] if event["event_type"] in EVIDENCE_EVENT_TYPES
    ]
    evidence = evidence[-limits.max_evidence_notes :]
    evidence_links: list[str] = []
    for event in evidence:
        event_id = event["event_id"] or _digest_json(event)
        note_path = f"Evidence/{event['event_type']}/{_slug(event['ts'] + '-' + event_id)}.md"
        evidence_links.append(_link(note_path, f"{event['event_type']} {event['ts']}"))
        body = [
            f"- Timestamp: `{event['ts']}`",
            f"- Outcome: `{event['outcome'] or event['exit_class'] or 'unknown'}`",
            f"- Handler: `{event['handler'] or event['tool_name'] or 'unknown'}`",
        ]
        if event["head"]:
            body.append(f"- HEAD: `{event['head']}`")
        if event["paths"]:
            body.extend(("", "## Affected paths", *(f"- `{path}`" for path in event["paths"][:20])))
        if event["extra"]:
            body.extend(
                (
                    "",
                    "## Bounded metadata",
                    *(
                        f"- **{key}**: `{_redact(value, limit=500)}`"
                        for key, value in sorted(event["extra"].items())
                    ),
                )
            )
        relations = _event_links(event, maps)
        if relations:
            body.extend(("", "## Relations", *(f"- {item}" for item in relations)))
        add(
            note_path,
            _markdown(
                {
                    "aegis_kind": "evidence",
                    "aegis_schema": SCHEMA_VERSION,
                    "event_id": event_id,
                    "event_type": event["event_type"],
                    "outcome": event["outcome"] or event["exit_class"] or "unknown",
                    "timestamp": event["ts"],
                    "tags": ["aegis-vault", "aegis/evidence", f"aegis/{event['event_type']}"],
                },
                f"{event['event_type'].replace('_', ' ').title()} evidence",
                body,
            ),
        )

    legacy_links: list[str] = []
    for document in legacy:
        note_path = f"Legacy/{_slug(document['path'])}.md"
        legacy_links.append(_link(note_path, document["path"]))
        body = [
            "This note inventories preserved human-authored workflow context. The source file remains authoritative for its narrative.",
            "",
            f"- Source: `{document['path']}`",
            f"- Bytes: {document['bytes']}",
            f"- Human-authored nonblank lines: {document['human_nonblank_lines']}",
            f"- Generated Aegis blocks: {document['generated_blocks']}",
            f"- Checkboxes: {document['checkboxes']}",
            f"- S:W:H:E entries outside generated blocks: {document['sweh_entries']}",
        ]
        if document["headings"]:
            body.extend(("", "## Headings", *(f"- {heading}" for heading in document["headings"])))
        task_links = []
        for source_task_id in document["task_ids"]:
            task_id = _canonical_task_id(source_task_id, maps)
            if task_id:
                task_links.append(_task_link(task_id, maps))
        if task_links:
            body.extend(("", "## Related tasks", *(f"- {item}" for item in task_links)))
        add(
            note_path,
            _markdown(
                {
                    "aegis_kind": "legacy-document",
                    "aegis_schema": SCHEMA_VERSION,
                    "content_digest": document["content_digest"],
                    "document_kind": document["kind"],
                    "human_nonblank_lines": document["human_nonblank_lines"],
                    "source_path": document["path"],
                    "tags": ["aegis-vault", "aegis/legacy", f"aegis/{document['kind']}"],
                },
                document["path"],
                body,
            ),
        )

    activity_body = ["## High-signal evidence by class"]
    activity_body.extend(
        f"- `{key}`: {value}" for key, value in sorted(event_summary["by_type"].items())
    )
    if evidence_links:
        activity_body.extend(
            ("", "## Recent evidence", *(f"- {item}" for item in evidence_links[-100:]))
        )
    if legacy_links:
        activity_body.extend(
            ("", "## Preserved legacy context", *(f"- {item}" for item in legacy_links[:100]))
        )
    add(
        "Indexes/Activity.md",
        _markdown(
            {
                "aegis_kind": "index",
                "aegis_schema": SCHEMA_VERSION,
                "latest_evidence": event_summary["latest_ts"],
                "tags": ["aegis-vault", "aegis/index"],
            },
            "Activity and evidence index",
            activity_body,
        ),
    )
    add(
        "Views/Tasks.base",
        _render_base(
            "task",
            "Tasks",
            ("file.name", "status", "priority", "issue_type", "bead_id", "taskmaster_alias"),
        ),
    )
    add(
        "Views/Evidence.base",
        _render_base("evidence", "Evidence", ("timestamp", "event_type", "outcome", "file.name")),
    )
    add(
        "Views/Legacy.base",
        _render_base(
            "legacy-document",
            "Legacy context",
            ("source_path", "document_kind", "human_nonblank_lines", "file.name"),
        ),
    )
    return dict(sorted(files.items()))


def _manifest(snapshot: Mapping[str, Any], files: Mapping[str, bytes]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "managed_root": True,
        "task_authority": snapshot["task_source"]["authority"],
        "task_export_command": snapshot["task_source"]["command"],
        "task_bd_binary": snapshot["task_source"]["binary"],
        "task_bd_binary_sha256": snapshot["task_source"]["binary_sha256"],
        "task_bd_version": snapshot["task_source"]["version"],
        "task_raw_export_sha256": snapshot["task_source"]["raw_export_sha256"],
        "task_dolt_main_head": snapshot["task_source"]["dolt_main_head"],
        "repository_identity": snapshot["repository"]["identity"],
        "repository_name": snapshot["repository"]["name"],
        "source_branch": snapshot["repository"]["branch"],
        "source_head": snapshot["repository"]["head"],
        "source_digest": snapshot["source_digest"],
        "latest_evidence_ts": snapshot["event_summary"]["latest_ts"],
        "counts": {
            "files": len(files),
            "high_signal_events": snapshot["event_summary"]["high_signal_count"],
            "identity_relationships": len(snapshot.get("identities") or []),
            "legacy_documents": len(snapshot["legacy_documents"]),
            "task_relationships": sum(
                len(task["relationships"]) for task in snapshot["tasks"]
            ),
            "tasks": len(snapshot["tasks"]),
        },
        "files": {path: _digest_bytes(content) for path, content in sorted(files.items())},
    }


def _read_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VaultError(
            f"existing vault is not Aegis-owned (missing {MANIFEST_NAME}): {root}"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise VaultError(f"invalid vault ownership manifest at {path}: {exc}") from exc
    if (
        not isinstance(payload, Mapping)
        or payload.get("generator") != GENERATOR
        or payload.get("managed_root") is not True
    ):
        raise VaultError(f"existing directory is not an Aegis-owned vault: {root}")
    return dict(payload)


def check_vault(
    output_dir: str | Path,
    *,
    expected_source_digest: str | None = None,
) -> dict[str, Any]:
    """Verify ownership, exact file inventory, hashes, and optional freshness."""

    requested = Path(output_dir).expanduser()
    if requested.is_symlink():
        return {
            "status": "failed",
            "ok": False,
            "output": requested.absolute().as_posix(),
            "problems": ["vault directory is missing or is a symlink"],
        }
    root = requested.resolve()
    if not root.is_dir() or root.is_symlink():
        return {
            "status": "failed",
            "ok": False,
            "output": root.as_posix(),
            "problems": ["vault directory is missing or is a symlink"],
        }
    try:
        manifest = _read_manifest(root)
    except VaultError as exc:
        return {"status": "failed", "ok": False, "output": root.as_posix(), "problems": [str(exc)]}
    raw_declared = manifest.get("files")
    declared: Mapping[str, Any] = raw_declared if isinstance(raw_declared, Mapping) else {}
    actual_files = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    )
    expected_files = sorted([MANIFEST_NAME, *declared.keys()])
    problems: list[str] = []
    if actual_files != expected_files:
        missing = sorted(set(expected_files) - set(actual_files))
        extra = sorted(set(actual_files) - set(expected_files))
        if missing:
            problems.append("missing owned files: " + ", ".join(missing[:20]))
        if extra:
            problems.append("unknown files present: " + ", ".join(extra[:20]))
    for relative, expected in sorted(declared.items()):
        path = root / relative
        if path.is_symlink():
            problems.append(f"owned file is a symlink: {relative}")
            continue
        if path.is_file() and _digest_bytes(path.read_bytes()) != expected:
            problems.append(f"hash mismatch: {relative}")
    fresh = (
        expected_source_digest is None or manifest.get("source_digest") == expected_source_digest
    )
    if not fresh:
        problems.append("vault source digest is stale")
    return {
        "status": "passed" if not problems else "failed",
        "ok": not problems,
        "fresh": fresh,
        "output": root.as_posix(),
        "source_digest": manifest.get("source_digest"),
        "file_count": len(declared),
        "problems": problems,
    }


def _assert_output_safe(output: Path, repository: Path) -> None:
    requested = output.expanduser()
    if requested.is_symlink():
        raise VaultError(f"vault output must not be a symlink: {requested.absolute()}")
    resolved = requested.resolve()
    if resolved == repository or repository in resolved.parents:
        raise VaultError("vault output must live outside the source repository")


def _validate_existing_for_replacement(output: Path) -> dict[str, Any] | None:
    if not output.exists():
        return None
    if not output.is_dir() or output.is_symlink():
        raise VaultError(f"vault output exists but is not a regular directory: {output}")
    if not any(output.iterdir()):
        return None
    result = check_vault(output)
    if not result["ok"]:
        raise VaultError(
            "refusing to replace untrusted or modified vault: " + "; ".join(result["problems"])
        )
    return _read_manifest(output)


def build_vault(
    snapshot: Mapping[str, Any],
    output_dir: str | Path,
    *,
    target_dir: str | Path,
) -> dict[str, Any]:
    """Atomically replace an owned vault; leave source and unknown files untouched."""

    repository = repository_root(target_dir)
    requested_output = Path(output_dir).expanduser()
    _assert_output_safe(requested_output, repository)
    output = requested_output.resolve()
    files = render_vault(snapshot)
    manifest = _manifest(snapshot, files)
    previous = _validate_existing_for_replacement(output)
    if (
        previous is not None
        and previous.get("source_digest") == manifest["source_digest"]
        and previous.get("files") == manifest["files"]
    ):
        return {
            "status": "current",
            "changed": False,
            "output": output.as_posix(),
            "source_digest": manifest["source_digest"],
            "file_count": len(files),
            "counts": manifest["counts"],
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=str(output.parent)))
    backup: Path | None = None
    try:
        for relative, content in files.items():
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        (stage / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        staged_check = check_vault(stage, expected_source_digest=manifest["source_digest"])
        if not staged_check["ok"]:
            raise VaultError(
                "staged vault failed self-check: " + "; ".join(staged_check["problems"])
            )
        if output.exists():
            backup = Path(
                tempfile.mkdtemp(prefix=f".{output.name}.backup-", dir=str(output.parent))
            )
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except Exception:
            if backup is not None and backup.exists() and not output.exists():
                os.replace(backup, output)
            raise
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        if backup is not None and backup.exists() and output.exists():
            shutil.rmtree(backup)
    return {
        "status": "built",
        "changed": True,
        "output": output.as_posix(),
        "source_digest": manifest["source_digest"],
        "file_count": len(files),
        "counts": manifest["counts"],
    }


__all__ = [
    "BEADS_EXPORT_COMMAND",
    "DEFAULT_VAULT_DIRNAME",
    "GENERATOR",
    "HIGH_SIGNAL_EVENT_TYPES",
    "MANIFEST_NAME",
    "SCHEMA_VERSION",
    "VaultError",
    "VaultLimits",
    "build_vault",
    "check_vault",
    "collect_snapshot",
    "default_vault_path",
    "render_vault",
    "repository_root",
]
