"""TM 219: keep packaged assets/scripts mirrors byte-identical to live scripts.

The packaged copy under aegis_foundation/assets/scripts/ is what ships in the wheel/sdist
and installs into target repos; the live scripts/ copy is what runs in-repo. They silently
drifted — assets/scripts/_aegis_installer.py missed the TM 215/218/221 fixes and still
carried the reverted TM-197 observation-globs — because no test guarded the mirror. This
locks the .py mirrors so a future fix to one can't be dropped from the other.

The Codex-owned shell tools (scripts/codex-guard, scripts/codex-task) are also mirrored into
the package. TM 223 re-synced them and moved them into byte-parity coverage so drift is no
longer a documented exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_SCRIPTS = REPO_ROOT / "scripts"
ASSETS_SCRIPTS = REPO_ROOT / "aegis_foundation" / "assets" / "scripts"

# Live scripts that MUST stay byte-identical in the packaged assets copy.
MIRRORED_ASSET_SCRIPTS = (
    "_aegis_installer.py",
    "_repo_structure.py",
    "codex-guard",
    "codex-task",
    "template_governance.py",
    "template_registry.py",
    "template_versioning.py",
)


@pytest.mark.parametrize("name", MIRRORED_ASSET_SCRIPTS)
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
            assert asset.name in MIRRORED_ASSET_SCRIPTS, (
                f"assets/scripts/{asset.name} mirrors a live script but is not guarded; "
                "add it to MIRRORED_ASSET_SCRIPTS."
            )


def test_advisory_pending_lifecycle_doc_matches_packaged_asset() -> None:
    name = "advisory-pending-lifecycle.md"
    live = REPO_ROOT / "docs" / "aegis" / name
    asset = REPO_ROOT / "aegis_foundation" / "assets" / "docs" / "aegis" / name
    assert live.is_file()
    assert asset.is_file()
    assert asset.read_bytes() == live.read_bytes()
    text = live.read_text(encoding="utf-8")
    assert "Blog Task 40" in text
    assert "advisory-only" in text.lower()
    assert "Do not drain" in text
    assert "aegis update --target-dir ." in text
