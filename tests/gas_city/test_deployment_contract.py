from __future__ import annotations

import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"


def _digest(relative: str) -> str:
    return hashlib.sha256((DEPLOY / relative).read_bytes()).hexdigest()


def _materialize_deployed_control_plane(city: Path) -> None:
    manifest_path = DEPLOY / "control-plane-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["entries"]:
        destination = city / record["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPLOY / record["source"], destination)
        destination.chmod(int(record["destination_mode"], 8))
    shutil.copyfile(manifest_path, city / manifest_path.name)
    (city / manifest_path.name).chmod(0o644)


def _toml(relative: str) -> dict[str, object]:
    with (DEPLOY / relative).open("rb") as stream:
        return tomllib.load(stream)


def _model_guard_module():
    path = DEPLOY / "docker" / "provider-supervisor.py"
    spec = importlib.util.spec_from_file_location("gas_city_provider_supervisor", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_lock_is_exact_and_does_not_fabricate_receipts() -> None:
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text())
    assert lock == {
        "schema_version": 1,
        "status": "staged_pending_provisioning",
        "tools": {
            "gc": {
                "version": "1.3.5",
                "binary_sha256": "ee26f66f39be5bde1f3ab1cc28115f57c6c553b595add893bba93fd2bfd2f637",
                "archive_sha256": "854fba2fd6c8cfa9d3f33b5262f95032d8036b08e8cdfe925bf4bc86e83b10a1",
            },
            "bd": {
                "version": "1.1.0",
                "binary_sha256": "f7dcf3d22eae0bf09d764a9a47ab5c6e263ee91b19f2243d9e0e077561cceb1e",
                "archive_sha256": "b0f3dd607c3fb989ee08d0a6854fba80d0402971eb108f9af6170bc14d491a34",
            },
            "dolt": {
                "version": "2.2.0",
                "binary_sha256": "72352f1d882472a7a8d6124e9c4dc12f80e2c2359ea95f1424c032e9250e35e6",
                "archive_sha256": "1f7ad8c2622995789420a3fb0f2d16b4aa7430000a825dd91d5938f36480cbf6",
            },
        },
        "packs": {
            "gascity_core_bd": {"commit": "f895c0ff47d6ee9334ed282a416387eb5b084d24"},
            "gastown": {"commit": "33d3a430a67d1782ad364556cb566bdb01d0afe3"},
        },
        "task_authority_runtime": {
            "source_path": "docker/task-authority.py",
            "image_path": "/opt/gas-city/task-authority.py",
            "sha256": _digest("docker/task-authority.py"),
        },
        "aegis_polecat_startup": {
            "source_path": "docker/aegis-polecat-startup.py",
            "image_path": "/opt/gas-city/aegis-polecat-startup.py",
            "sha256": _digest("docker/aegis-polecat-startup.py"),
            "receipt_path": "/run/gas-city/aegis-startup-receipt.json",
            "formula_path": "formulas/aegis/mol-polecat-work.toml",
            "formula_sha256": _digest("formulas/aegis/mol-polecat-work.toml"),
            "upstream_formula_sha256": (
                "86878dd7ae180e02905d88ac092944d2fece075ac22dab86dc54b59c10f6319e"
            ),
            "runtime_artifact_source_path": "artifacts/aegis-runtime.whl",
            "runtime_artifact_image_path": "/opt/gas-city/aegis-runtime.whl",
            "runtime_artifact_sha256": _digest("artifacts/aegis-runtime.whl"),
            "runtime_shim_source_path": "docker/aegis-runtime-shim.py",
            "runtime_shim_image_path": "/opt/gas-city/aegis-runtime-shim.py",
            "runtime_shim_sha256": _digest("docker/aegis-runtime-shim.py"),
            "local_launcher_path": ".aegis/bin/aegis",
            "local_launcher_sha256": hashlib.sha256(
                b"#!/bin/sh\n"
                b"set -eu\n"
                b'exec /usr/bin/python3 -I /opt/gas-city/aegis-runtime-shim.py "$@"\n'
            ).hexdigest(),
        },
        "git_worktree_broker": {
            "source_path": "bin/git-worktree-broker",
            "deployed_path": "bin/git-worktree-broker",
            "sha256": _digest("bin/git-worktree-broker"),
        },
        "model_evidence_broker": {
            "source_path": "bin/model-evidence-broker",
            "deployed_path": "bin/model-evidence-broker",
            "sha256": _digest("bin/model-evidence-broker"),
        },
        "github_delivery": {
            "broker_source_path": "bin/github-app-token-broker",
            "broker_deployed_path": "bin/github-app-token-broker",
            "broker_sha256": _digest("bin/github-app-token-broker"),
            "repository": "loucmane/codex-starter-pack",
            "default_branch": "main",
            "permissions": {
                "contents": "write",
                "metadata": "read",
                "pull_requests": "write",
            },
            "required_default_branch_rules": [
                "deletion",
                "non_fast_forward",
                "pull_request",
                "required_status_checks",
            ],
            "maximum_lifetime_seconds": 3900,
        },
        "codex_preflight_catalog": {
            "source_path": "config/codex-preflight-models.json",
            "image_path": "/opt/gas-city/codex-preflight-models.json",
            "sha256": _digest("config/codex-preflight-models.json"),
            "upstream_source_tag": "rust-v0.144.4",
            "upstream_source_commit": "8c68d4c87dc54d38861f5114e920c3de2efa5876",
            "advertised_tools": ["update_plan", "view_image"],
            "tool_invocation_policy": "zero",
        },
        "control_plane_manifest": {
            "path": "control-plane-manifest.json",
            "sha256": _digest("control-plane-manifest.json"),
        },
        "images": {
            "dolt_server": {"target": "dolt-server", "image_id": None},
            "egress_proxy": {"target": "egress-proxy", "image_id": None},
            "claude_worker": {"target": "claude-worker", "image_id": None},
            "codex_worker": {"target": "codex-worker", "image_id": None},
        },
        "image_receipt": {
            "path": "runtime/evidence/images/build-receipt.json",
            "sha256": None,
        },
        "promotion": {
            "canary": {
                "path": "runtime/evidence/promotion/canary-manifest.json",
                "sha256": None,
            },
            "production": {
                "path": "runtime/evidence/promotion/production-manifest.json",
                "sha256": None,
            },
        },
        "providers": {
            "claude": {
                "cli_version": "2.1.210",
                "binary_sha256": "e7d2ceb53ed4c2ced1fe7fc1c6331c98dc5f7b4c9b2722d9c5fa3dd5dff6f719",
                "requested_model": "claude-fable-5",
                "observed_model": None,
                "receipt_sha256": None,
                "receipt_path": "runtime/evidence/providers/claude-model-receipt.json",
            },
            "codex": {
                "cli_version": "0.144.4",
                "package": "@openai/codex@0.144.4-linux-x64",
                "package_sri": "sha512-2jxrmV6+/7eBNdg5uhhmOEPFu2o28eYY/ClLzWhSBHH8uo3f2KA1z9JQcVtwlbToW03nEPlEzYNYfCF1UBqsVQ==",
                "archive_sha256": "9a4a45314e80b53c4761b80067e3a68c2302f9a9026059b5f54f22dec8f34323",
                "binary_sha256": "2b3edc9cdfd1717fba3dbc92817205a8a2c7511d459e456d4817eeff6f78ed7a",
                "helper_sha256": {
                    "codex-code-mode-host": "49c528deb71531b7bfdcaa32e07c12de03f43d91f13edeeda51d527dac2c911e",
                    "rg": "ebeaf56f8a25e102e9419933423738b3a2a613a444fd749d695e15eba53f71f2",
                    "zsh": "67faaaa89242c4a332e16e508a1977cffc24bf7fca31d4411cdfd101f3831ef3",
                },
                "requested_model": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
                "observed_model": None,
                "receipt_sha256": None,
                "receipt_path": "runtime/evidence/providers/codex-model-receipt.json",
            },
        },
        "exclusions": ["graphiti", "cognee", "ollama"],
    }


def test_pack_and_city_are_pinned_suspended_and_external_dolt_only() -> None:
    pack = _toml("config/pack.toml")
    city = _toml("config/city.toml")
    packs_lock = _toml("config/packs.lock")

    assert pack["imports"]["bd"]["version"] == ("sha:f895c0ff47d6ee9334ed282a416387eb5b084d24")
    assert pack["imports"]["core"]["version"] == ("sha:f895c0ff47d6ee9334ed282a416387eb5b084d24")
    assert pack["imports"]["gastown"]["version"] == ("sha:33d3a430a67d1782ad364556cb566bdb01d0afe3")
    assert {item["commit"] for item in packs_lock["packs"].values()} == {
        "f895c0ff47d6ee9334ed282a416387eb5b084d24",
        "33d3a430a67d1782ad364556cb566bdb01d0afe3",
    }

    assert city["workspace"]["suspended_on_start"] is True
    assert city["dolt"] == {
        "host": "127.0.0.1",
        "port": 33070,
        "auto_gc_enabled": True,
        "archive_level": 0,
        "max_connections": 128,
        "read_timeout_millis": 30000,
        "write_timeout_millis": 300000,
    }
    [rig] = city["rigs"]
    assert rig["name"] == "aegis"
    assert rig["suspended_on_start"] is True
    assert rig["dolt_host"] == "127.0.0.1"
    assert rig["dolt_port"] == "33071"
    assert rig["prefix"] == "ags"

    assert city["workspace"]["provider"] == "claude-container"
    assert set(city["providers"]) == {
        "claude-container",
        "claude-auto",
        "codex-container",
    }
    assert city["providers"]["claude-container"]["base"] == "builtin:claude"
    assert city["providers"]["claude-container"]["option_defaults"]["model"] == ("fable-5")
    assert city["providers"]["claude-auto"]["base"] == "claude-container"
    assert city["providers"]["codex-container"]["base"] == "builtin:codex"
    assert city["providers"]["codex-container"]["resume_command"] == (
        "/home/loucmane/gas-city/bin/codex-container resume {{.SessionKey}}"
    )
    assert city["providers"]["codex-container"]["option_defaults"] == {
        "model": "gpt-5.6-sol",
        "effort": "xhigh",
        "permission_mode": "auto-edit",
    }
    patches = {patch["name"]: patch["provider"] for patch in city["patches"]["agent"]}
    assert patches["gastown.mayor"] == "claude-auto"
    assert patches["gastown.deacon"] == "codex-container"
    rig_patches = {patch["agent"]: patch["provider"] for patch in rig["patches"]}
    assert rig_patches["polecat"] == "codex-container"
    assert rig_patches["refinery"] == "claude-auto"
    assert rig_patches["witness"] == "claude-auto"


def test_compose_separates_databases_and_exposes_only_loopback() -> None:
    compose = yaml.safe_load((DEPLOY / "compose.yaml").read_text())
    services = compose["services"]
    hq = services["hq-dolt"]
    aegis = services["aegis-dolt"]
    hq_relay = services["hq-dolt-loopback"]
    aegis_relay = services["aegis-dolt-loopback"]

    assert hq["image"].startswith("${GAS_CITY_DOLT_IMAGE:")
    assert aegis["image"] == hq["image"]
    assert "build" not in hq and "build" not in aegis
    assert hq["volumes"] != aegis["volumes"]
    assert hq["volumes"][0] == {
        "type": "bind",
        "source": "${GAS_CITY_HQ_DOLT_DATA_DIR:?set exact owner-only HQ Dolt data directory}",
        "target": "/var/lib/dolt/data",
    }
    assert hq["volumes"][1] == {
        "type": "bind",
        "source": "${GAS_CITY_HQ_DOLT_BACKUP_DIR:?set owner-only HQ Dolt backup directory}",
        "target": "${GAS_CITY_HQ_DOLT_BACKUP_DIR:?set owner-only HQ Dolt backup directory}",
    }
    assert aegis["volumes"] == [
        "aegis_dolt_data:/var/lib/dolt/data",
        {
            "type": "bind",
            "source": "${GAS_CITY_AEGIS_DOLT_BACKUP_DIR:?set owner-only Aegis Dolt backup directory}",
            "target": "${GAS_CITY_AEGIS_DOLT_BACKUP_DIR:?set owner-only Aegis Dolt backup directory}",
        },
    ]
    assert hq["environment"]["DOLT_DATABASE"] == "hq"
    assert aegis["environment"]["DOLT_DATABASE"] == "aegis_beads"
    assert hq["environment"]["DOLT_APP_USER"] != aegis["environment"]["DOLT_APP_USER"]
    assert hq["networks"] == ["hq-control"]
    assert aegis["networks"] == ["aegis-control", "hq-control"]
    assert hq["networks"] == ["hq-control"]
    assert "ports" not in hq and hq["expose"] == ["3306"]
    assert "ports" not in aegis and aegis["expose"] == ["3306"]
    assert hq_relay["ports"] == ["127.0.0.1:33070:3306"]
    assert aegis_relay["ports"] == ["127.0.0.1:33071:3306"]
    assert all(
        port.startswith("127.0.0.1:")
        for service in (hq_relay, aegis_relay)
        for port in service["ports"]
    )
    assert compose["networks"]["hq-control"]["internal"] is True
    assert compose["networks"]["aegis-control"]["internal"] is True
    for relay, control, ingress, target in (
        (hq_relay, "hq-control", "hq-loopback-ingress", "TCP4:hq-dolt:3306,nodelay"),
        (
            aegis_relay,
            "aegis-control",
            "aegis-loopback-ingress",
            "TCP4:aegis-dolt:3306,nodelay",
        ),
    ):
        assert relay["image"].startswith("${GAS_CITY_EGRESS_PROXY_IMAGE:")
        assert relay["read_only"] is True
        assert relay["cap_drop"] == ["ALL"]
        assert relay["security_opt"] == ["no-new-privileges:true"]
        assert relay["command"][0] == "/usr/bin/socat"
        assert relay["command"][2] == target
        assert set(relay["networks"]) == {control, ingress}
    for ingress in ("hq-loopback-ingress", "aegis-loopback-ingress"):
        network = compose["networks"][ingress]
        assert network.get("internal") is not True
        assert network["driver_opts"] == {
            "com.docker.network.bridge.host_binding_ipv4": "127.0.0.1",
            "com.docker.network.bridge.enable_ip_masquerade": "false",
            "com.docker.network.bridge.enable_icc": "false",
        }
    assert set(compose["secrets"]) == {
        "hq_root_password",
        "hq_app_password",
        "aegis_root_password",
        "aegis_app_password",
    }
    assert compose["volumes"]["aegis_dolt_data"]["name"] == (
        "${GAS_CITY_AEGIS_DOLT_VOLUME:-gas-city-aegis-dolt-data}"
    )
    for secret in compose["secrets"].values():
        assert "GAS_CITY_SECRETS_DIR" in secret["file"]
        assert "/home/loucmane/gas-city/runtime/secrets" in secret["file"]
    assert set(services["hq-egress-proxy"]["networks"]) == {
        "hq-control",
        "hq-egress",
    }
    assert set(services["aegis-egress-proxy"]["networks"]) == {
        "aegis-control",
        "aegis-egress",
    }
    assert "aegis-control" not in services["hq-egress-proxy"]["networks"]
    assert "hq-control" not in services["aegis-egress-proxy"]["networks"]
    for proxy in (services["hq-egress-proxy"], services["aegis-egress-proxy"]):
        assert proxy["image"].startswith("${GAS_CITY_EGRESS_PROXY_IMAGE:")
        assert "build" not in proxy


def test_staged_compose_allows_only_bootstrap_services(tmp_path: Path) -> None:
    city = tmp_path / "city"
    (city / "bin").mkdir(parents=True)
    (city / "runtime-lock.json").write_text("{}\n")
    (city / "compose.yaml").write_text("services: {}\n")
    receipt = tmp_path / "stage-receipt.json"
    receipt.write_text("{}\n")
    image_reader = city / "bin" / "locked-images"
    image_reader.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = --verify-staged ]; then exit 0; fi\n'
        "if [ \"$1\" = --staged-image ]; then printf 'sha256:%064d\\n' 1; exit 0; fi\n"
        "exit 2\n"
    )
    image_reader.chmod(0o755)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    docker_log = tmp_path / "docker.log"
    docker = fake_bin / "docker"
    docker.write_text("#!/bin/sh\n" f"printf '%s\\n' \"$*\" >> {docker_log}\n" "exit 0\n")
    docker.chmod(0o755)
    environment = {
        **os.environ,
        "GC_CITY_ROOT": city.as_posix(),
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }
    command = [
        str(DEPLOY / "bin" / "compose-locked"),
        "--provisioning-stage",
        str(receipt),
        "up",
        "--detach",
        "hq-dolt",
        "aegis-dolt",
        "hq-egress-proxy",
        "aegis-egress-proxy",
        "hq-dolt-loopback",
        "aegis-dolt-loopback",
    ]
    accepted = subprocess.run(command, text=True, capture_output=True, check=False, env=environment)
    assert accepted.returncode == 0, accepted.stderr
    assert "compose --project-directory" in docker_log.read_text()
    assert (
        "hq-dolt aegis-dolt hq-egress-proxy aegis-egress-proxy "
        "hq-dolt-loopback aegis-dolt-loopback"
    ) in (docker_log.read_text())

    rejected = subprocess.run(
        [*command, "claude-worker"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert rejected.returncode == 64
    assert "exact six bootstrap services" in rejected.stderr


def test_worker_images_and_launcher_enforce_isolation() -> None:
    dockerfile = (DEPLOY / "docker" / "Dockerfile").read_text()
    launcher = (DEPLOY / "bin" / "provider-container").read_text()
    supervisor = (DEPLOY / "docker" / "provider-supervisor.py").read_text()

    assert "FROM worker-base AS codex-worker" in dockerfile
    assert "FROM worker-base AS claude-worker" in dockerfile
    for target in ("codex-worker", "claude-worker"):
        body = dockerfile.split(f"FROM worker-base AS {target}", 1)[1].split("\nFROM ", 1)[0]
        assert body.rstrip().endswith(('CMD ["codex"]', 'CMD ["claude"]'))
        assert "USER 1000:1000" in body
    assert "FROM " in dockerfile and " AS dolt-server" in dockerfile
    assert "groupadd --gid 10002 gasproxy" in dockerfile
    assert "ca-certificates socat tini tinyproxy" in dockerfile
    assert "USER 10002:10002" in dockerfile
    assert "COPY --from=verified-tools /opt/verified/dolt" in dockerfile
    assert "72352f1d882472a7a8d6124e9c4dc12f80e2c2359ea95f1424c032e9250e35e6" in dockerfile
    assert "COPY docker/dolt-bootstrap.yaml" in dockerfile
    assert "COPY docker/dolt-server.yaml" in dockerfile
    assert "2b3edc9cdfd1717fba3dbc92817205a8a2c7511d459e456d4817eeff6f78ed7a" in dockerfile
    assert "COPY docker/task-authority.py /opt/gas-city/task-authority.py" in dockerfile
    assert "5ea3e3cad6b71fbaf6c976c0ba5e1e948fc0cb1267575c5611a8d3bde9c1c11f" in dockerfile
    assert "chmod 0444 /opt/gas-city/task-authority.py" in dockerfile
    assert (
        "COPY config/codex-preflight-models.json " "/opt/gas-city/codex-preflight-models.json"
    ) in dockerfile
    assert _digest("config/codex-preflight-models.json") in dockerfile
    assert _digest("docker/provider-supervisor.py") in dockerfile
    for digest in (
        "e7d2ceb53ed4c2ced1fe7fc1c6331c98dc5f7b4c9b2722d9c5fa3dd5dff6f719",
        "49c528deb71531b7bfdcaa32e07c12de03f43d91f13edeeda51d527dac2c911e",
        "ebeaf56f8a25e102e9419933423738b3a2a613a444fd749d695e15eba53f71f2",
        "67faaaa89242c4a332e16e508a1977cffc24bf7fca31d4411cdfd101f3831ef3",
    ):
        assert digest in dockerfile

    for hardening in (
        "--read-only",
        "--cap-drop ALL",
        "--security-opt no-new-privileges",
        "--pids-limit",
        "--memory",
        "--cpus",
    ):
        assert hardening in launcher
    assert "gas-city-hq-control" in launcher
    assert "gas-city-aegis-control" in launcher
    assert "private-hq-control" in launcher
    assert "private-aegis-control" in launcher
    assert 'realpath -e "$rig_root/.git"' in launcher
    assert "src=$repo_root,dst=$repo_root" in launcher
    assert "src=$git_common,dst=$git_common" in launcher
    assert "src=$beads_dir,dst=$beads_dir,readonly" in launcher
    assert "src=$city_root/.gc,dst=$city_root/.gc" not in launcher
    assert "src=$city_root/.gc/runtime,dst=$city_root/.gc/runtime" in launcher
    assert '"$rig_root"\n' not in launcher.split("allowed_roots=(", 1)[1].split(")", 1)[0]
    assert "provider-auth/$provider" in launcher
    assert "provider-sessions/$credential_scope/$agent_safe/$provider/$session_safe" in launcher
    assert "src=$stable_home,dst=/run/gas-city/provider-home" in launcher
    assert "src=$session_state,dst=/run/gas-city/provider-session" in launcher
    assert "src=$config_source,dst=/run/gas-city/provider-config,readonly" in launcher
    assert "--tmpfs /home/worker:rw,nosuid,nodev" in launcher
    assert 'credential_scope="rig-$GC_RIG"' in launcher
    assert 'install -m 0600 "$auth_source" "$stable_home/$stable_credential_name"' in launcher
    assert "GC_PROVIDER_SYNC_RECEIPT_PATH=/run/gas-city/provider-auth-sync.json" in launcher
    assert "ProviderCredentialSync" in supervisor
    assert "provider-credentials/$provider" not in launcher
    assert "cp -a" not in launcher
    assert "seccomp=unconfined" not in launcher
    assert "GC_GITHUB_TOKEN_FILE=/run/secrets/github_token" in launcher
    assert "$GAS_CITY_SECRETS_DIR/github-token" not in launcher
    assert "$GAS_CITY_SECRETS_DIR/github-app-private-key.pem" in launcher
    assert '"$github_delivery_broker" issue' in launcher
    assert "GC_GITHUB_RECEIPT_SHA256" in launcher
    assert "github-delivery-receipt.json" in supervisor
    assert "git remote set-url" not in launcher
    assert "credential.https://github.com.helper" in supervisor
    assert "url.https://github.com/.insteadOf" in supervisor
    assert 'os.environ["GH_TOKEN"]' in supervisor
    assert "github_delivery_token_expiring" in supervisor
    assert "cleanup_session_github_token" in launcher
    assert "git remote set-url" not in supervisor

    forbidden_mounts = (
        "src=/home/loucmane,dst=/home/loucmane",
        "src=$HOME,dst=/home/worker",
        "src=$HOME,dst=$HOME",
        "src=/home/loucmane/.ssh",
    )
    assert not any(item in launcher for item in forbidden_mounts)
    assert '"$city_root/bin/locked-images"' in launcher
    assert '"$city_root/runtime-lock.json" "${provider}_worker"' in launcher
    assert "images/$provider.image" not in launcher
    assert "src=$city_root/.gc/runtime,dst=$city_root/.gc/runtime,readonly" in launcher
    assert "src=$city_root/.gc/events.jsonl,dst=$city_root/.gc/events.jsonl,readonly" in launcher
    assert "AEGIS_TASK_AUTHORITY_RUNTIME_FILE=/opt/gas-city/task-authority.py" in launcher
    assert "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256=$task_authority_sha256" in launcher
    assert "src=$authority_root,dst=/run/gas-city/authority,readonly" in launcher
    assert '/usr/bin/flock --shared "$authority_lock_file"' in launcher


def test_supervisor_requires_exact_fresh_github_app_delivery_receipt(
    tmp_path: Path, monkeypatch
) -> None:
    guard = _model_guard_module()
    token = "ghs_" + "t" * 64
    token_path = tmp_path / "token"
    receipt_path = tmp_path / "receipt.json"
    token_path.write_text(token + "\n", encoding="utf-8")
    token_path.chmod(0o400)
    now = guard.dt.datetime.now(guard.dt.timezone.utc)
    receipt = {
        "schema_version": 1,
        "kind": "gas-city-github-app-delivery-token",
        "status": "verified",
        "repository": {
            "id": 123,
            "name_with_owner": "loucmane/codex-starter-pack",
            "default_branch": "main",
        },
        "permissions": guard.GITHUB_DELIVERY_PERMISSIONS,
        "app_id_sha256": "a" * 64,
        "installation_id_sha256": "b" * 64,
        "token_sha256": hashlib.sha256(token_path.read_bytes()).hexdigest(),
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + guard.dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "lifetime_seconds": 3600,
        "effective_rules_sha256": "c" * 64,
        "effective_rule_types": sorted(guard.GITHUB_REQUIRED_DEFAULT_RULES),
        "ruleset_ids": [42],
        "rulesets_sha256": "d" * 64,
        "api_version": "2022-11-28",
    }
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    receipt_path.chmod(0o400)
    monkeypatch.setattr(guard, "GITHUB_SECRET_PATH", token_path)
    monkeypatch.setattr(guard, "GITHUB_DELIVERY_RECEIPT_PATH", receipt_path)
    monkeypatch.setenv("GC_GITHUB_REQUIRED", "true")
    monkeypatch.setenv("GC_GITHUB_TOKEN_FILE", str(token_path))
    monkeypatch.setenv("GC_GITHUB_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setenv(
        "GC_GITHUB_RECEIPT_SHA256", hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    )
    observed_expiry = guard.configure_github_delivery()
    assert os.environ["GH_TOKEN"] == token
    assert observed_expiry == now + guard.dt.timedelta(hours=1)

    receipt["expires_at"] = (now - guard.dt.timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    receipt["lifetime_seconds"] = -60
    receipt_path.chmod(0o600)
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    receipt_path.chmod(0o400)
    monkeypatch.setenv(
        "GC_GITHUB_RECEIPT_SHA256", hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    )
    with pytest.raises(RuntimeError, match="stale or outside"):
        guard.configure_github_delivery()


def test_dolt_runtime_revalidates_recovery_credentials_and_disables_file_reads() -> None:
    dockerfile = (DEPLOY / "docker" / "Dockerfile").read_text()
    entrypoint = (DEPLOY / "docker" / "dolt-entrypoint.sh").read_text()
    healthcheck = (DEPLOY / "docker" / "dolt-healthcheck.sh").read_text()
    bootstrap = yaml.safe_load((DEPLOY / "docker" / "dolt-bootstrap.yaml").read_text())
    server = yaml.safe_load((DEPLOY / "docker" / "dolt-server.yaml").read_text())

    assert bootstrap["listener"]["host"] == "127.0.0.1"
    assert server["listener"]["host"] == "0.0.0.0"
    for config in (bootstrap, server):
        assert config["system_variables"]["secure_file_priv"] == (
            "/var/lib/dolt/secure-file-disabled"
        )
        assert config["data_dir"] == "${DOLT_DATA_DIR}"

    assert "gas-city-dolt-credentials/v1:" in entrypoint
    assert "changed without an attended rotation" in entrypoint
    assert "dolt-bootstrap.yaml" in entrypoint
    assert "dolt-server.yaml" in entrypoint
    assert "ALTER USER 'root'@'localhost'" in entrypoint
    assert "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION" in entrypoint
    assert "GRANT ALL PRIVILEGES ON \\`%s\\`.*" in entrypoint
    assert entrypoint.count('DOLT_CLI_PASSWORD="$root_password"') >= 2
    assert 'DOLT_CLI_PASSWORD="$app_password"' in entrypoint
    assert entrypoint.count("--no-tls") == 7
    assert entrypoint.count("--user root --no-tls sql") >= 4
    assert "DOLT_ROOT_PASSWORD_FILE" in healthcheck
    assert healthcheck.count("--no-tls") == 2
    assert '--user root --no-tls --use-db "$DOLT_DATABASE"' in healthcheck
    assert '--user "$DOLT_APP_USER"' in healthcheck
    assert "ENV HOME=/tmp DOLT_DATA_DIR=/var/lib/dolt/data" in dockerfile


def test_locked_image_reader_binds_deployed_ids_to_private_receipt(tmp_path: Path) -> None:
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text())
    _materialize_deployed_control_plane(tmp_path)
    lock["status"] = "provisioned_pending_canary"
    image_ids = {name: f"sha256:{index:064x}" for index, name in enumerate(lock["images"], start=1)}
    for name, image_id in image_ids.items():
        lock["images"][name]["image_id"] = image_id
    receipt = {
        "schema_version": 1,
        "kind": "immutable-image-build",
        "status": "pass",
        "built_at": "2026-07-15T18:00:00Z",
        "source_lock_sha256": "1" * 64,
        "lock_schema_version": 1,
        "source_artifacts": {
            lock["task_authority_runtime"]["source_path"]: lock["task_authority_runtime"]["sha256"],
            lock["aegis_polecat_startup"]["source_path"]: lock["aegis_polecat_startup"]["sha256"],
            lock["aegis_polecat_startup"]["formula_path"]: lock["aegis_polecat_startup"][
                "formula_sha256"
            ],
            lock["aegis_polecat_startup"]["runtime_artifact_source_path"]: lock[
                "aegis_polecat_startup"
            ]["runtime_artifact_sha256"],
            lock["aegis_polecat_startup"]["runtime_shim_source_path"]: lock[
                "aegis_polecat_startup"
            ]["runtime_shim_sha256"],
            lock["codex_preflight_catalog"]["source_path"]: lock["codex_preflight_catalog"][
                "sha256"
            ],
        },
        "build_context": {
            "manifest_sha256": "2" * 64,
            "file_count": 20,
            "dockerfile_sha256": "3" * 64,
            "dockerignore_sha256": "4" * 64,
        },
        "docker": {
            "binary": "/usr/bin/docker",
            "binary_sha256": "5" * 64,
            "client_version": "25.0.3",
            "tagged": False,
            "pull": False,
            "no_cache": True,
        },
        "targets": {
            "dolt_server": "dolt-server",
            "egress_proxy": "egress-proxy",
            "claude_worker": "claude-worker",
            "codex_worker": "codex-worker",
        },
        "images": image_ids,
    }
    receipt_path = tmp_path / lock["image_receipt"]["path"]
    receipt_path.parent.mkdir(parents=True, mode=0o700)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    receipt_path.chmod(0o600)
    lock["image_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    lock_path = tmp_path / "runtime-lock.json"
    lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n")
    lock_path.chmod(0o600)

    command = [str(DEPLOY / "bin" / "locked-images"), str(lock_path), "claude_worker"]
    accepted = subprocess.run(command, text=True, capture_output=True, check=False)
    assert accepted.returncode == 0
    assert accepted.stdout.strip() == image_ids["claude_worker"]

    controlled = tmp_path / "bin" / "provider-container"
    original = controlled.read_bytes()
    controlled.write_bytes(original + b"\n# tampered after installation\n")
    controlled.chmod(0o755)
    control_plane_rejection = subprocess.run(command, text=True, capture_output=True, check=False)
    assert control_plane_rejection.returncode != 0
    assert control_plane_rejection.stdout == ""
    assert "control-plane destination bin/provider-container digest mismatch" in (
        control_plane_rejection.stderr
    )
    controlled.write_bytes(original)
    controlled.chmod(0o755)

    source_artifacts = receipt["source_artifacts"]
    startup_path = lock["aegis_polecat_startup"]["source_path"]
    startup_digest = source_artifacts.pop(startup_path)
    source_artifacts["docker/./aegis-polecat-startup.py"] = startup_digest
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    lock["image_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n")
    alias_rejection = subprocess.run(command, text=True, capture_output=True, check=False)
    assert alias_rejection.returncode != 0
    assert "does not prove" in alias_rejection.stderr

    source_artifacts.pop("docker/./aegis-polecat-startup.py")
    source_artifacts[startup_path] = startup_digest
    receipt["unexpected"] = True
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    lock["image_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n")
    semantic_rejection = subprocess.run(command, text=True, capture_output=True, check=False)
    assert semantic_rejection.returncode != 0
    assert "does not prove" in semantic_rejection.stderr

    receipt.pop("unexpected")
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    lock["image_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n")
    receipt_path.write_text(receipt_path.read_text() + " ")
    rejected = subprocess.run(command, text=True, capture_output=True, check=False)
    assert rejected.returncode != 0
    assert "digest mismatch" in rejected.stderr


def test_provider_settings_disable_unsafe_fallbacks_and_memory_autoload() -> None:
    claude = json.loads((DEPLOY / "config" / "claude-settings.json").read_text())
    codex = _toml("config/codex.toml")
    assert claude == {
        "switchModelsOnFlag": False,
        "disableAllHooks": False,
        "enableAllProjectMcpServers": False,
        "skipDangerousModePermissionPrompt": False,
    }
    assert codex["model"] == "gpt-5.6-sol"
    assert codex["model_reasoning_effort"] == "xhigh"
    assert codex["approval_policy"] == "never"
    assert codex["sandbox_mode"] == "danger-full-access"
    assert "mcp_servers" not in codex

    operational_files = [
        DEPLOY / "config" / "city.toml",
        DEPLOY / "config" / "codex.toml",
        DEPLOY / "config" / "claude-settings.json",
        DEPLOY / "compose.yaml",
        DEPLOY / "docker" / "Dockerfile",
        DEPLOY / "bin" / "provider-container",
        DEPLOY / "docker" / "provider-supervisor.py",
    ]
    excluded = re.compile(r"graphiti|cognee|ollama", re.IGNORECASE)
    assert all(not excluded.search(path.read_text()) for path in operational_files)


def test_model_guard_accepts_only_provider_authored_exact_receipts() -> None:
    guard = _model_guard_module()
    assert guard.extract_receipt(
        "claude", {"type": "assistant", "message": {"model": "claude-fable-5"}}
    ) == ("claude-fable-5", None)
    assert guard.extract_receipt(
        "codex",
        {
            "type": "turn_context",
            "payload": {"model": "gpt-5.6-sol", "effort": "xhigh"},
        },
    ) == ("gpt-5.6-sol", "xhigh")
    assert guard.extract_receipt(
        "codex",
        {
            "type": "turn_context",
            "payload": {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
        },
    ) == ("gpt-5.6-sol", "xhigh")
    assert guard.extract_receipt(
        "codex",
        {
            "type": "turn_context",
            "payload": {
                "model": "gpt-5.6-sol",
                "collaboration_mode": {"settings": {"reasoning_effort": "xhigh"}},
            },
        },
    ) == ("gpt-5.6-sol", "xhigh")
    fallback = {
        "type": "system",
        "subtype": "model_refusal_fallback",
        "originalModel": "claude-fable-5",
        "fallbackModel": "claude-opus-4-8",
    }
    assert guard.is_claude_refusal_fallback("claude", fallback) is True
    assert guard.is_model_receipt_event("claude", {"type": "assistant", "message": {}}) is True
    assert guard.is_model_receipt_event("codex", {"type": "turn_context", "payload": {}}) is True

    # Prompts and unrelated event structures cannot self-certify a worker.
    assert (
        guard.extract_receipt("claude", {"type": "user", "message": {"model": "claude-fable-5"}})
        is None
    )
    assert (
        guard.extract_receipt("codex", {"type": "event_msg", "payload": {"model": "gpt-5.6-sol"}})
        is None
    )
    assert (
        guard.extract_receipt("codex", {"type": "turn_context", "payload": {"effort": "xhigh"}})
        is None
    )


def test_model_guard_runtime_accepts_exact_and_kills_fallback(tmp_path: Path, monkeypatch) -> None:
    guard = _model_guard_module()

    def run_case(
        case: str,
        observed_model: str,
        terminal_fallback: bool = False,
        terminal_invalid: bool = False,
        terminal_missing_model: bool = False,
    ) -> tuple[int, dict[str, object]]:
        root = tmp_path / case
        binary_dir = root / "bin"
        worker_home = root / "home"
        provider_home = root / "provider-home"
        provider_session = root / "provider-session"
        provider_config = root / "claude-settings.json"
        transcript_root = worker_home / ".claude" / "projects"
        receipt = root / "receipt.json"
        sync_receipt = root / "sync-receipt.json"
        secret = root / "beads-password"
        city = root / "city"
        workdir = city / ".gc" / "agents" / "mayor" / "work"
        beads = city / ".beads"
        for directory in (
            binary_dir,
            worker_home,
            provider_home,
            provider_session,
            workdir,
            beads,
        ):
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory.chmod(0o700)
        for name in ("projects", "debug", "todos"):
            path = provider_session / name
            path.mkdir(mode=0o700)
            path.chmod(0o700)
        credential = provider_home / "credentials.json"
        credential.write_text('{"access_token":"fixture"}\n', encoding="utf-8")
        credential.chmod(0o600)
        marker = provider_home / ".seed-generation.json"
        marker.write_text(
            json.dumps(
                {
                    "provider": "claude",
                    "schema_version": 1,
                    "seed_sha256": hashlib.sha256(credential.read_bytes()).hexdigest(),
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        marker.chmod(0o400)
        provider_config.write_bytes((DEPLOY / "config" / "claude-settings.json").read_bytes())
        provider_config.chmod(0o644)
        secret.write_text("A" * 32)
        secret.chmod(0o600)
        fake_claude = binary_dir / "claude"
        fallback_code = ""
        if terminal_fallback:
            fallback_code = (
                "fallback = {'type': 'system', 'subtype': 'model_refusal_fallback', "
                "'originalModel': 'claude-fable-5', 'fallbackModel': 'claude-opus-4-8'}\n"
                "with (root / 'session.jsonl').open('a') as stream:\n"
                "    stream.write(json.dumps(fallback) + '\\n')\n"
            )
        if terminal_invalid:
            fallback_code = (
                "with (root / 'session.jsonl').open('a') as stream:\n"
                "    stream.write('{invalid-json}\\n')\n"
            )
        if terminal_missing_model:
            fallback_code = (
                "with (root / 'session.jsonl').open('a') as stream:\n"
                "    stream.write(json.dumps({'type': 'assistant', 'message': {}}) + '\\n')\n"
            )
        fake_claude.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, time\n"
            "root = pathlib.Path(os.environ['GC_TRANSCRIPT_ROOT'])\n"
            f"event = {{'type': 'assistant', 'message': {{'model': '{observed_model}'}}}}\n"
            "(root / 'session.jsonl').write_text(json.dumps(event) + '\\n')\n"
            "time.sleep(0.3)\n"
            f"{fallback_code}"
        )
        fake_claude.chmod(0o700)

        with monkeypatch.context() as environment:
            identity = {
                "GC_CITY_ROOT": str(city),
                "GC_DOLT_HOST": "gas-city-hq-dolt",
                "GC_DOLT_PORT": "3306",
                "GC_DOLT_USER": "gas_city_hq",
                "GC_DOLT_DATABASE": "hq",
                "BEADS_DOLT_SERVER_HOST": "gas-city-hq-dolt",
                "BEADS_DOLT_SERVER_PORT": "3306",
                "BEADS_DOLT_SERVER_USER": "gas_city_hq",
                "BEADS_DOLT_SERVER_DATABASE": "hq",
                "BEADS_CREDENTIALS_FILE": str(worker_home / ".config/beads/credentials"),
                "BEADS_DIR": str(beads),
                "GC_GITHUB_REQUIRED": "false",
            }
            environment.setattr(guard, "WORKER_HOME_PATH", worker_home)
            environment.setattr(guard, "PROVIDER_HOME_PATH", provider_home)
            environment.setattr(guard, "PROVIDER_SESSION_PATH", provider_session)
            environment.setattr(guard, "PROVIDER_CONFIG_PATH", provider_config)
            environment.setattr(guard, "PROVIDER_SYNC_RECEIPT_PATH", sync_receipt)
            environment.setattr(guard, "PASSWORD_SECRET_PATH", secret)
            environment.setattr(
                guard,
                "DOLT_CREDENTIALS_PATH",
                worker_home / ".config/beads/credentials",
            )
            environment.setattr(guard, "validate_worker_boundary", lambda: "hq")
            environment.setattr(
                guard,
                "_exact_mount_type",
                lambda path: "tmpfs" if path == worker_home else None,
            )
            environment.setattr(guard, "HQ_RUNTIME_IDENTITY", identity)
            environment.chdir(workdir)
            environment.setenv("PATH", f"{binary_dir}:{os.environ['PATH']}")
            for name, value in identity.items():
                environment.setenv(name, value)
            for name in (
                "GC_RIG",
                "GC_RIG_ROOT",
                "GC_BEADS_PREFIX",
                "AEGIS_TASK_AUTHORITY_FILE",
                "AEGIS_TASK_AUTHORITY_RUNTIME_FILE",
                "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256",
            ):
                environment.delenv(name, raising=False)
            environment.setenv("GC_EXPECTED_MODEL", "claude-fable-5")
            environment.delenv("GC_EXPECTED_EFFORT", raising=False)
            environment.setenv("GC_TRANSCRIPT_ROOT", str(transcript_root))
            environment.setenv("GC_MODEL_RECEIPT_PATH", str(receipt))
            environment.setenv("GC_PROVIDER_HOME", str(provider_home))
            environment.setenv("GC_PROVIDER_CONFIG", str(provider_config))
            environment.setenv("GC_PROVIDER_SESSION", str(provider_session))
            environment.setenv("GC_PROVIDER_SYNC_RECEIPT_PATH", str(sync_receipt))
            environment.setenv("CLAUDE_CONFIG_DIR", str(worker_home / ".claude"))
            environment.setenv("GC_MODEL_RECEIPT_TIMEOUT_SECONDS", "3")
            result = guard.main(["provider-supervisor", "claude"])
        return result, json.loads(receipt.read_text())

    accepted_code, accepted = run_case("accepted", "claude-fable-5")
    assert accepted_code == 0
    assert accepted["status"] == "verified"
    assert accepted["observed_model"] == "claude-fable-5"
    assert re.fullmatch(r"[0-9a-f]{64}", accepted["transcript_sha256"])

    rejected_code, rejected = run_case("rejected", "claude-opus-4-8")
    assert rejected_code == 86
    assert rejected["status"] == "rejected"
    assert rejected["observed_model"] == "claude-opus-4-8"

    terminal_code, terminal = run_case(
        "terminal-fallback", "claude-fable-5", terminal_fallback=True
    )
    assert terminal_code == 86
    assert terminal["status"] == "rejected"
    assert terminal["reason"] == "model_refusal_fallback"

    invalid_code, invalid = run_case("terminal-invalid", "claude-fable-5", terminal_invalid=True)
    assert invalid_code == 90
    assert invalid["status"] == "rejected"
    assert invalid["reason"] == "invalid_transcript_jsonl"

    missing_code, missing = run_case(
        "terminal-missing-model",
        "claude-fable-5",
        terminal_missing_model=True,
    )
    assert missing_code == 91
    assert missing["status"] == "rejected"
    assert missing["reason"] == "model_receipt_event_lacks_metadata"


def test_shell_and_python_entrypoints_parse() -> None:
    shells = [
        DEPLOY / "bin" / "provider-container",
        DEPLOY / "bin" / "claude-container",
        DEPLOY / "bin" / "codex-container",
        DEPLOY / "bin" / "compose-locked",
        DEPLOY / "docker" / "dolt-entrypoint.sh",
        DEPLOY / "docker" / "dolt-healthcheck.sh",
        DEPLOY / "docker" / "git-credential-github.sh",
    ]
    subprocess.run(["bash", "-n", *map(str, shells)], check=True)
    subprocess.run(
        [
            "python3",
            "-m",
            "py_compile",
            str(DEPLOY / "docker" / "provider-supervisor.py"),
            str(DEPLOY / "bin" / "locked-images"),
            str(DEPLOY / "bin" / "provision-control-plane"),
            str(DEPLOY / "bin" / "provider-auth-bootstrap"),
        ],
        check=True,
    )


def test_contract_contains_no_secret_value_or_committed_receipt() -> None:
    secret_assignment = re.compile(
        r"(?im)^\s*['\"]?(?:password|token|api[_-]?key|secret)['\"]?\s*[:=]\s*"
        r"(?:['\"](?![$<{])[^'\"\r\n]+['\"]|(?![$<{])[A-Za-z0-9_./+=-]{16,})\s*$"
    )
    for path in DEPLOY.rglob("*"):
        if (
            not path.is_file()
            or "artifacts" in path.parts
            or "__pycache__" in path.parts
            or path.suffix == ".pyc"
        ):
            continue
        assert not secret_assignment.search(path.read_text()), path

    tracked_receipts = [path for path in DEPLOY.rglob("*.json") if "receipt" in path.name]
    assert tracked_receipts == []
