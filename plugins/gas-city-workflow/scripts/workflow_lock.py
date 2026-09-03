"""Serialize this CLI's mutations of one repository's workflow journals."""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

from project_context import DEFAULT_REGISTRY, build_context
from workflow_common import CommandRunner, WorkflowError, git_common_dir


@contextmanager
def workflow_lock(runner: CommandRunner, root: Path, registry: Path = DEFAULT_REGISTRY):
    context = build_context(root, registry)
    common = git_common_dir(runner, Path(context["workspace"]["canonical_root"]))
    directory = common / "gas-city-workflow"
    directory.mkdir(exist_ok=True)
    fd = os.open(
        directory / "source-transition.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
    )
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorkflowError("another source workflow transition is active") from exc
        yield
    finally:
        os.close(fd)
