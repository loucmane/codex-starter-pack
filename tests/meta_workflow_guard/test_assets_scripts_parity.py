"""TM 219: keep packaged assets/scripts mirrors byte-identical to live scripts.

The packaged copy under aegis_foundation/assets/scripts/ is what ships in the wheel/sdist
and installs into target repos; the live scripts/ copy is what runs in-repo. They silently
drifted — assets/scripts/_aegis_installer.py missed the TM 215/218/221 fixes and still
carried the reverted TM-197 observation-globs — because no test guarded the mirror. This
locks the .py mirrors so a future fix to one can't be dropped from the other.

The Codex-owned shell tools (scripts/codex-guard, scripts/codex-task) are also drifted, but
Claude must not edit Codex-owned paths; re-syncing them is a Codex-led follow-up (recorded in
this task's DECISIONS.md). They are listed here as known drift so the gap is explicit, not
silently uncovered.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_SCRIPTS = REPO_ROOT / "scripts"
ASSETS_SCRIPTS = REPO_ROOT / "aegis_foundation" / "assets" / "scripts"

# Claude-maintainable .py mirrors that MUST stay byte-identical.
MIRRORED_PY = (
    "_aegis_installer.py",
    "_repo_structure.py",
    "template_governance.py",
    "template_registry.py",
    "template_versioning.py",
)

# Codex-owned tools that are drifted; re-sync is a Codex-led follow-up (DECISIONS.md).
KNOWN_CODEX_OWNED_DRIFT = ("codex-guard", "codex-task")


@pytest.mark.parametrize("name", MIRRORED_PY)
def test_assets_script_matches_live(name: str) -> None:
    live = LIVE_SCRIPTS / name
    asset = ASSETS_SCRIPTS / name
    assert live.is_file(), f"missing live scripts/{name}"
    assert asset.is_file(), f"missing packaged assets/scripts/{name}"
    assert asset.read_bytes() == live.read_bytes(), (
        f"assets/scripts/{name} drifted from scripts/{name}. Re-sync with "
        f"`cp scripts/{name} aegis_foundation/assets/scripts/{name}` so the packaged copy "
        "ships the same code that runs in-repo."
    )


def test_no_new_unmirrored_py_under_assets_scripts() -> None:
    # Any *.py the package ships under assets/scripts that also exists in live scripts must be
    # in the guarded mirror set (or it could drift unguarded). New mirrors must be added above.
    for asset in ASSETS_SCRIPTS.glob("*.py"):
        if (LIVE_SCRIPTS / asset.name).is_file():
            assert asset.name in MIRRORED_PY, (
                f"assets/scripts/{asset.name} mirrors a live script but is not guarded; "
                "add it to MIRRORED_PY."
            )


def test_codex_owned_drift_is_tracked() -> None:
    # Documents (does not fix) the Codex-owned drift so it stays visible. Claude cannot edit
    # scripts/codex-*; re-sync is Codex-led. If a pair becomes identical, drop it from the list.
    still_drifted = [
        name
        for name in KNOWN_CODEX_OWNED_DRIFT
        if (LIVE_SCRIPTS / name).is_file()
        and (ASSETS_SCRIPTS / name).is_file()
        and (LIVE_SCRIPTS / name).read_bytes() != (ASSETS_SCRIPTS / name).read_bytes()
    ]
    assert set(still_drifted) <= set(KNOWN_CODEX_OWNED_DRIFT)
