"""Aegis hook gate: loaders."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def script_dir() -> Path:
    configured = os.environ.get("AEGIS_HOOK_SCRIPT_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    source_root = Path(__file__).resolve().parents[3]
    source_adapter = source_root / ".claude" / "scripts"
    return source_adapter if source_adapter.is_dir() else Path(__file__).resolve().parent


def _load_ledger_lib_module():
    script = script_dir() / "ledger_lib.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_gate_ledger_lib", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_brief_lib_module():
    script = script_dir() / "brief_lib.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_gate_brief_lib", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
