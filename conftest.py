"""Pytest session setup shared across the whole suite.

TM 193: isolate git config from the developer's global/system config. Without this the suite
only passed *serially* by accident of ordering — one test leaked `git config --global` state
(notably `commit.gpgsign=false`) that masked another test's git commit run with the
developer's real `commit.gpgsign=true`. That made the suite order-dependent and unsafe to
parallelize with pytest-xdist. Pointing GIT_CONFIG_GLOBAL/GIT_CONFIG_SYSTEM at an isolated,
per-worker config gives every test (and every xdist worker) a clean, reproducible git
environment that matches CI, so parallel runs are deterministic.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_git_config():
    """Give the test session (and each xdist worker) its own git config, independent of the
    developer's ~/.gitconfig and any system config."""

    tmp = Path(tempfile.mkdtemp(prefix="aegis-test-gitconfig-"))
    global_config = tmp / "gitconfig"
    global_config.write_text(
        "[user]\n"
        "\temail = aegis-test@example.com\n"
        "\tname = Aegis Test\n"
        "[commit]\n"
        "\tgpgsign = false\n"
        "[tag]\n"
        "\tgpgsign = false\n"
        "[init]\n"
        "\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    system_config = tmp / "gitconfig-system"
    system_config.write_text("[commit]\n\tgpgsign = false\n", encoding="utf-8")

    keys = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["GIT_CONFIG_GLOBAL"] = str(global_config)
    os.environ["GIT_CONFIG_SYSTEM"] = str(system_config)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(tmp, ignore_errors=True)
