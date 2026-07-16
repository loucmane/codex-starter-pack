"""Version and public package identity for Aegis Foundation."""

from __future__ import annotations

DISTRIBUTION_NAME = "aegis-foundation"
FOUNDATION_NAME = "Aegis Foundation"
PACKAGE_VERSION = "0.1.0"
FOUNDATION_VERSION = PACKAGE_VERSION
INSTALLER_VERSION = PACKAGE_VERSION
SCHEMA_VERSION = "1.0.0"

__version__ = PACKAGE_VERSION

__all__ = [
    "DISTRIBUTION_NAME",
    "FOUNDATION_NAME",
    "FOUNDATION_VERSION",
    "INSTALLER_VERSION",
    "PACKAGE_VERSION",
    "SCHEMA_VERSION",
    "__version__",
]
