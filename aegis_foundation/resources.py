"""Packaged Aegis asset resolution helpers."""

from __future__ import annotations

from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator


ASSET_PACKAGE = "aegis_foundation"
ASSET_DIR = "assets"


def packaged_assets() -> resources.abc.Traversable:
    """Return the packaged Aegis asset tree as an importlib resource."""

    return resources.files(ASSET_PACKAGE).joinpath(ASSET_DIR)


@contextmanager
def packaged_asset_root() -> Iterator[Path]:
    """Yield a filesystem path for packaged Aegis assets.

    Wheels installed by pip are normally unpacked on disk, while some import contexts can
    expose resources as virtual traversables. `as_file` keeps both cases behind one API.
    """

    with resources.as_file(packaged_assets()) as asset_root:
        yield asset_root


def packaged_asset_root_path() -> Path:
    """Return the packaged asset path for installed/unpacked package contexts."""

    asset_root = packaged_assets()
    return Path(str(asset_root)).resolve()


__all__ = [
    "ASSET_DIR",
    "ASSET_PACKAGE",
    "packaged_asset_root",
    "packaged_asset_root_path",
    "packaged_assets",
]
