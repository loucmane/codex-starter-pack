"""Stable typed contracts for the Aegis workflow gate."""

from __future__ import annotations

from dataclasses import dataclass


READY = "READY"
WARN = "WARN"
BLOCKED = "BLOCKED"
DEFAULT_MAX_LINES = 60
DEFAULT_MAX_BYTES = 8 * 1024
DEFAULT_SAMPLE_SIZE = 5
VERBOSE_MAX_LINES = 120
VERBOSE_MAX_BYTES = 32 * 1024
VERBOSE_SAMPLE_SIZE = 20


@dataclass(frozen=True)
class Check:
    status: str
    message: str
