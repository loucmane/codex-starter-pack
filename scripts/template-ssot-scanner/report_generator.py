#!/usr/bin/env python3
"""Report-writing helpers for Template SSOT scanner outputs."""

from pathlib import Path
from typing import Any, Dict, Optional

from scan_metadata import save_with_metadata, validate_output_file


def save_scanner_report(
    data: Any,
    output_file: Path,
    scanner_name: str,
    version: str,
    stats: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None,
) -> None:
    """Save and validate a scanner report using the shared v2 metadata wrapper."""
    save_with_metadata(
        data=data,
        output_file=output_file,
        scanner_name=scanner_name,
        version=version,
        stats=stats,
        duration_seconds=duration_seconds,
    )
    validate_output_file(output_file)
