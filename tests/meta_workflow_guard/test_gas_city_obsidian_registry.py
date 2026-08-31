from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from aegis_foundation.obsidian_registry import load_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugins" / "gas-city-workflow"
SCRIPT = PLUGIN / "scripts" / "build_obsidian_registry.py"
WORKFLOW_REGISTRY = PLUGIN / "config" / "projects.json"
OBSIDIAN_REGISTRY = PLUGIN / "config" / "obsidian-projects.json"


def _module():
    name = "gas_city_obsidian_registry_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_tracked_registry_is_exact_generated_projection_of_project_registry() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    workflow = json.loads(WORKFLOW_REGISTRY.read_text(encoding="utf-8"))
    obsidian = load_registry(OBSIDIAN_REGISTRY)
    assert obsidian.managed_output_root == Path("/home/loucmane/vaults/main/GasCity")
    assert [project.id for project in obsidian.projects] == [
        project["id"] for project in workflow["projects"]
    ]
    for source, project in zip(workflow["projects"], obsidian.projects, strict=True):
        assert project.target_dir == Path(source["root"])
        assert project.output_dir == Path(
            f"/home/loucmane/vaults/main/GasCity/{source['id']}/Aegis"
        )
        assert project.bead_export_argv[2] == (f"/home/loucmane/gascity/city/rigs/{source['rig']}")
        assert project.live_index is not None
        assert project.live_index.probe_path == f"GasCity/{source['id']}/Aegis/Home.md"
    assert obsidian.continuity_dashboard is not None
    assert obsidian.continuity_dashboard.output_dir == Path(
        "/home/loucmane/vaults/main/GasCity/Continuity"
    )


def test_descriptor_onboarding_changes_one_generated_project_entry(tmp_path: Path) -> None:
    module = _module()
    source = json.loads(WORKFLOW_REGISTRY.read_text(encoding="utf-8"))
    source["projects"].append(
        {
            "id": "future-project",
            "root": "/srv/future-project",
            "repository": "example/future-project",
            "rig": "future-project",
            "workflow_authority": "beads",
            "workflow_profile": "beads-with-aegis-evidence",
        }
    )
    registry = tmp_path / "projects.json"
    registry.write_text(json.dumps(source), encoding="utf-8")

    payload = module.build_payload(
        registry,
        canonical_source_root=Path("/srv/gas-city-ops"),
        city=Path("/srv/gascity/city"),
        bd=Path("/srv/gascity/bin/bd"),
        vault_root=Path("/srv/vault/GasCity"),
        obsidian_cli=Path("/srv/bin/obsidian"),
        signing_policies=Path("/etc/signing.json"),
    )

    project = payload["projects"][-1]
    assert project["id"] == "future-project"
    assert project["target_dir"] == "/srv/future-project"
    assert project["output_dir"] == "/srv/vault/GasCity/future-project/Aegis"
    assert project["bead_export_argv"][2] == "/srv/gascity/city/rigs/future-project"
    assert project["live_index"]["probe_path"] == "GasCity/future-project/Aegis/Home.md"
