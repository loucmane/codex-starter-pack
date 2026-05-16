"""MCP server scaffold for Aegis Foundation.

Task 110 keeps protocol wiring in this package and deterministic install behavior in
``scripts._aegis_installer``. Later subtasks register tools, resources, and prompts against
the server returned by ``create_server``.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from mcp.server.fastmcp import FastMCP

from scripts import _aegis_installer


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_NAME = "Aegis Foundation"


@dataclass(frozen=True)
class AegisMCPConfig:
    """Runtime configuration for the Aegis MCP server."""

    source_root: Path
    default_target_dir: Path

    @classmethod
    def from_paths(
        cls,
        *,
        source_root: str | Path | None = None,
        default_target_dir: str | Path | None = None,
    ) -> "AegisMCPConfig":
        """Create normalized server configuration from optional path inputs."""

        resolved_source = Path(
            source_root or os.environ.get("AEGIS_SOURCE_ROOT") or REPO_ROOT
        ).expanduser().resolve()
        resolved_target = Path(
            default_target_dir
            or os.environ.get("AEGIS_DEFAULT_TARGET_DIR")
            or resolved_source
        ).expanduser().resolve()
        return cls(source_root=resolved_source, default_target_dir=resolved_target)

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-friendly representation for diagnostics and tests."""

        return {
            "source_root": self.source_root.as_posix(),
            "default_target_dir": self.default_target_dir.as_posix(),
        }


def create_server(config: AegisMCPConfig | None = None) -> FastMCP:
    """Create the Aegis MCP server without starting a transport."""

    resolved_config = config or AegisMCPConfig.from_paths()
    server = FastMCP(SERVER_NAME, json_response=True)
    server.aegis_config = resolved_config  # type: ignore[attr-defined]
    server.aegis_installer = _aegis_installer  # type: ignore[attr-defined]
    return server


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the stdio entrypoint parser."""

    parser = argparse.ArgumentParser(description="Run the Aegis Foundation MCP server.")
    parser.add_argument(
        "--source-root",
        help="Path to the Aegis foundation source repository; defaults to this repository.",
    )
    parser.add_argument(
        "--default-target-dir",
        help="Default target directory for read-only operations; mutating tools still require explicit targets.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default="stdio",
        help="MCP transport to run; stdio is the project-local default.",
    )
    parser.add_argument(
        "--describe-config",
        action="store_true",
        help="Print resolved configuration as JSON and exit without starting the server.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Aegis MCP server entrypoint."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)
    config = AegisMCPConfig.from_paths(
        source_root=args.source_root,
        default_target_dir=args.default_target_dir,
    )
    if args.describe_config:
        print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
        return 0
    create_server(config).run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
