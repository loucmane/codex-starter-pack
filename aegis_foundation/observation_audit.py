"""Integrity checks for the one gate audit log emitted during observation.

This classifies evidence, not execution authority or cryptographic authorship.
Only well-formed appends to the exact log are expected runtime output; the
pre-existing bytes remain bound. No whole-directory exemption is introduced.
"""

from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Mapping

AUDIT_REL = ".aegis/reports/gate-decisions.jsonl"
MAX_AUDIT_BYTES = 16 * 1024 * 1024
FIELDS = {
    "ts",
    "hook",
    "tool_name",
    "payload_digest",
    "verdict",
    "reason",
    "readiness_state",
    "mode",
    "source_commit",
}


def _read(root: Path) -> tuple[bool, bytes]:
    # Open each component without following links; non-blocking avoids a FIFO hang.
    with ExitStack() as stack:
        parent = None
        try:
            for component in (str(root), ".aegis", "reports"):
                parent = os.open(
                    component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
                )
                stack.callback(os.close, parent)
            fd = os.open(
                "gate-decisions.jsonl",
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                dir_fd=parent,
            )
        except FileNotFoundError:
            return False, b""
        stack.callback(os.close, fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("audit is not a single-link regular file")
        if before.st_size > MAX_AUDIT_BYTES:
            raise ValueError("audit exceeds the bounded verification size")
        chunks = []
        remaining = MAX_AUDIT_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        named = os.stat("gate-decisions.jsonl", dir_fd=parent, follow_symlinks=False)

        def identity(value):
            return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

        if identity(before) != identity(after) or identity(after) != identity(named):
            raise ValueError("audit changed during verification")
        data = b"".join(chunks)
        if len(data) > MAX_AUDIT_BYTES:
            raise ValueError("audit exceeds the bounded verification size")
        return True, data


def capture(root: Path) -> dict[str, Any]:
    exists, data = _read(root)
    return {"exists": exists, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate audit field")
        result[key] = value
    return result


def _valid_record(line: bytes) -> bool:
    item = json.loads(line, object_pairs_hook=_unique_object)
    if not isinstance(item, dict) or set(item) != FIELDS:
        return False
    if any(
        not isinstance(item[key], str) or not item[key]
        for key in ("ts", "hook", "tool_name", "payload_digest", "verdict", "reason", "mode")
    ):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", item["payload_digest"]):
        return False
    if item["verdict"] not in {"allow", "block", "would_block"}:
        return False
    if item["mode"] not in {"strict", "advisory"}:
        return False
    if item["readiness_state"] is not None and not isinstance(item["readiness_state"], str):
        return False
    commit = item["source_commit"]
    if commit is not None and (
        not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit)
    ):
        return False
    return datetime.fromisoformat(item["ts"].replace("Z", "+00:00")).tzinfo is not None


def verify(root: Path, baseline: Mapping[str, Any] | None) -> dict[str, Any]:
    if baseline is None:
        return {"status": "legacy", "path": AUDIT_REL}
    try:
        if (
            set(baseline) != {"exists", "size", "sha256"}
            or type(baseline["exists"]) is not bool
            or type(baseline["size"]) is not int
            or not 0 <= baseline["size"] <= MAX_AUDIT_BYTES
            or not isinstance(baseline["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", baseline["sha256"])
        ):
            raise ValueError("invalid audit baseline")
        exists, data = _read(root)
        size = baseline["size"]
        if baseline["exists"] and not exists:
            raise ValueError("audit removed")
        if len(data) < size or hashlib.sha256(data[:size]).hexdigest() != baseline["sha256"]:
            raise ValueError("audit baseline bytes changed or truncated")
        tail = data[size:]
        if tail and ((size and data[size - 1 : size] != b"\n") or not tail.endswith(b"\n")):
            raise ValueError("audit append is not complete JSONL")
        lines = tail.splitlines()
        if any(not _valid_record(line) for line in lines):
            raise ValueError("audit append does not match the decision schema")
        return {
            "status": "verified",
            "path": AUDIT_REL,
            "appended_records": len(lines),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
    except (OSError, ValueError, TypeError, AttributeError):
        # Never include log payloads or arbitrary exception paths in this report.
        return {
            "status": "invalid",
            "path": AUDIT_REL,
            "error": "gate audit integrity or schema check failed",
        }
