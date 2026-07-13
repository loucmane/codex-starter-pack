"""Deterministic managed-asset rendering and update planning for Aegis.

This module is intentionally installer-agnostic.  The installer supplies its policy
constants and renderer callbacks through small compatibility adapters, while this module
owns the reusable asset model, target materialization, prior-byte recovery, and
fail-closed operation classification.

Keeping the core independent of the installer entrypoint lets source-root and packaged
execution call the same implementation without copying mutable state into target repos.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True)
class Asset:
    """One target file managed by Aegis."""

    path: str
    content: bytes
    executable: bool = False
    kind: str = "managed"


@dataclass(frozen=True)
class AssetBuildPolicy:
    """Installer policy values needed to assemble the managed asset set."""

    contract_rel: str
    local_bin_rel: str
    runtime_env_rel: str
    brief_rel: str
    shared_schema_files: tuple[str, ...]
    workflow_template_source_root: str
    workflow_template_target_root: str
    workflow_template_names: tuple[str, ...]
    claude_required_files: tuple[str, ...]
    claude_support_files: tuple[str, ...]
    claude_runtime_hook_phases: Mapping[str, str]
    codex_required_files: tuple[str, ...]
    codex_hooks_rel: str


@dataclass(frozen=True)
class AssetRenderers:
    """Installer-owned render callbacks used by the generic asset assembler."""

    read_bytes: Callable[[Path, str], bytes]
    render_agents_doc: Callable[[str, Sequence[str]], bytes]
    render_contract: Callable[[str, Sequence[str]], bytes]
    render_local_cli_shim: Callable[[Path], bytes]
    render_runtime_env: Callable[[Path], bytes]
    render_default_brief: Callable[[], bytes]
    render_claude_entrypoint: Callable[[], bytes]
    render_claude_settings: Callable[[], bytes]
    render_claude_runtime_dispatcher: Callable[[str], bytes]
    render_codex_hooks: Callable[[], bytes]


@dataclass(frozen=True)
class TargetMaterializers:
    """Installer-owned merge callbacks for project-authored entrypoint content."""

    read_json: Callable[[Path], dict[str, Any] | None]
    wrap_claude_entrypoint: Callable[[bytes], bytes]
    merge_claude_entrypoint: Callable[[bytes, bytes], bytes | None]
    render_codex_continuation_block: Callable[[], bytes]
    merge_codex_entrypoint: Callable[[bytes, bytes], bytes | None]
    merge_codex_hooks: Callable[[bytes, bytes | None], bytes | None]
    merge_agents_entrypoint: Callable[[bytes, bytes], bytes | None]
    wrap_agents_entrypoint: Callable[[bytes], bytes]


@dataclass(frozen=True)
class PlanPolicy:
    """Path policy needed for fail-closed managed update classification."""

    manifest_rel: str
    codex_hooks_rel: str
    shared_schema_files: tuple[str, ...]
    claude_support_files: tuple[str, ...]
    codex_required_files: tuple[str, ...]
    workflow_template_source_root: str
    workflow_template_target_root: str
    workflow_template_names: tuple[str, ...]


def asset_from_source(
    source_root: Path,
    rel_path: str,
    *,
    read_bytes: Callable[[Path, str], bytes],
    kind: str = "managed",
) -> Asset:
    """Build an asset whose source and target paths are identical."""

    path = source_root / rel_path
    return Asset(
        path=rel_path,
        content=read_bytes(source_root, rel_path),
        executable=os.access(path, os.X_OK),
        kind=kind,
    )


def asset_from_source_as(
    source_root: Path,
    source_rel_path: str,
    target_rel_path: str,
    *,
    read_bytes: Callable[[Path, str], bytes],
    kind: str = "managed",
) -> Asset:
    """Build an asset whose source and target paths intentionally differ."""

    path = source_root / source_rel_path
    return Asset(
        path=target_rel_path,
        content=read_bytes(source_root, source_rel_path),
        executable=os.access(path, os.X_OK),
        kind=kind,
    )


def build_base_assets(
    source_root: Path,
    primary_agent: str,
    enabled_agents: Sequence[str],
    *,
    policy: AssetBuildPolicy,
    renderers: AssetRenderers,
) -> list[Asset]:
    """Render assets shared by every enabled agent combination."""

    assets = [
        Asset("AGENTS.md", renderers.render_agents_doc(primary_agent, enabled_agents)),
        Asset(
            policy.contract_rel,
            renderers.render_contract(primary_agent, enabled_agents),
        ),
        Asset(
            policy.local_bin_rel,
            renderers.render_local_cli_shim(source_root),
            executable=True,
        ),
        Asset(
            policy.runtime_env_rel,
            renderers.render_runtime_env(source_root),
            kind="runtime",
        ),
        Asset(policy.brief_rel, renderers.render_default_brief(), kind="config"),
    ]
    for rel_path in policy.shared_schema_files:
        assets.append(
            asset_from_source(
                source_root,
                rel_path,
                read_bytes=renderers.read_bytes,
            )
        )
    for template_name in policy.workflow_template_names:
        assets.append(
            asset_from_source_as(
                source_root,
                f"{policy.workflow_template_source_root}/{template_name}",
                f"{policy.workflow_template_target_root}/{template_name}",
                read_bytes=renderers.read_bytes,
            )
        )
    return assets


def build_adapter_assets(
    source_root: Path,
    enabled_agents: Sequence[str],
    *,
    policy: AssetBuildPolicy,
    renderers: AssetRenderers,
) -> list[Asset]:
    """Render assets for the explicitly enabled client adapters."""

    assets: list[Asset] = []
    if "claude" in enabled_agents:
        assets.extend(
            [
                Asset(
                    "CLAUDE.md",
                    renderers.render_claude_entrypoint(),
                    kind="adapter",
                ),
                Asset(
                    ".claude/settings.json",
                    renderers.render_claude_settings(),
                    kind="adapter",
                ),
            ]
        )
        for rel_path in policy.claude_required_files:
            if rel_path in {"CLAUDE.md", ".claude/settings.json"}:
                continue
            phase = policy.claude_runtime_hook_phases.get(rel_path)
            if phase is not None:
                assets.append(
                    Asset(
                        rel_path,
                        renderers.render_claude_runtime_dispatcher(phase),
                        executable=True,
                        kind="adapter",
                    )
                )
                continue
            assets.append(
                asset_from_source(
                    source_root,
                    rel_path,
                    read_bytes=renderers.read_bytes,
                    kind="adapter",
                )
            )
        for rel_path in policy.claude_support_files:
            assets.append(
                asset_from_source(
                    source_root,
                    rel_path,
                    read_bytes=renderers.read_bytes,
                    kind="adapter",
                )
            )
    if "codex" in enabled_agents:
        for rel_path in policy.codex_required_files:
            if rel_path == policy.codex_hooks_rel:
                assets.append(
                    Asset(
                        rel_path,
                        renderers.render_codex_hooks(),
                        kind="adapter",
                    )
                )
                continue
            assets.append(
                asset_from_source(
                    source_root,
                    rel_path,
                    read_bytes=renderers.read_bytes,
                    kind="adapter",
                )
            )
    return assets


def build_managed_assets(
    source_root: Path,
    primary_agent: str,
    enabled_agents: Sequence[str],
    *,
    policy: AssetBuildPolicy,
    renderers: AssetRenderers,
) -> list[Asset]:
    """Return the complete deterministic asset set for one target profile."""

    return build_base_assets(
        source_root,
        primary_agent,
        enabled_agents,
        policy=policy,
        renderers=renderers,
    ) + build_adapter_assets(
        source_root,
        enabled_agents,
        policy=policy,
        renderers=renderers,
    )


def content_checksum(content: bytes) -> str:
    """Return the canonical checksum representation used by Aegis manifests."""

    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def manifest_file_record(
    manifest: Mapping[str, Any], key: str, path: str
) -> Mapping[str, Any] | None:
    records = manifest.get(key)
    if not isinstance(records, list):
        return None
    for record in records:
        if isinstance(record, Mapping) and record.get("path") == path:
            return record
    return None


def recorded_managed_checksum(manifest: Mapping[str, Any], path: str) -> str | None:
    """Read a valid managed checksum without trusting malformed manifest data."""

    record = manifest_file_record(manifest, "managed_files", path)
    if record is None:
        return None
    checksum = record.get("checksum")
    if not isinstance(checksum, str):
        return None
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", checksum):
        return None
    return checksum


def materialize_assets_for_target(
    target_root: Path,
    assets: Sequence[Asset],
    *,
    manifest_rel: str,
    codex_hooks_rel: str,
    claude_block_begin: str,
    materializers: TargetMaterializers,
) -> list[Asset]:
    """Merge managed blocks/hooks while preserving project-authored target content."""

    baseline_manifest = materializers.read_json(target_root / manifest_rel)
    materialized: list[Asset] = []
    for asset in assets:
        if asset.path == "CLAUDE.md" and asset.kind == "adapter":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                existing = target.read_bytes()
                recorded_checksum = (
                    recorded_managed_checksum(baseline_manifest, asset.path)
                    if isinstance(baseline_manifest, Mapping)
                    else None
                )
                if claude_block_begin.encode(
                    "utf-8"
                ) not in existing and recorded_checksum == content_checksum(existing):
                    merged = materializers.wrap_claude_entrypoint(asset.content)
                else:
                    merged = materializers.merge_claude_entrypoint(
                        existing,
                        asset.content,
                    )
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=asset.executable,
                            kind=asset.kind,
                        )
                    )
                    continue
            else:
                materialized.append(
                    Asset(
                        path=asset.path,
                        content=materializers.wrap_claude_entrypoint(asset.content),
                        executable=asset.executable,
                        kind=asset.kind,
                    )
                )
                continue
        if asset.path == "CODEX.md" and asset.kind == "adapter":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                merged = materializers.merge_codex_entrypoint(
                    target.read_bytes(),
                    materializers.render_codex_continuation_block(),
                )
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=asset.executable,
                            kind=asset.kind,
                        )
                    )
                    continue
        if asset.path == codex_hooks_rel and asset.kind == "adapter":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                merged = materializers.merge_codex_hooks(
                    target.read_bytes(),
                    asset.content,
                )
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=False,
                            kind=asset.kind,
                        )
                    )
                    continue
        if asset.path == "AGENTS.md":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                merged = materializers.merge_agents_entrypoint(
                    target.read_bytes(),
                    asset.content,
                )
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=asset.executable,
                            kind=asset.kind,
                        )
                    )
                    continue
            else:
                materialized.append(
                    Asset(
                        path=asset.path,
                        content=materializers.wrap_agents_entrypoint(asset.content),
                        executable=asset.executable,
                        kind=asset.kind,
                    )
                )
                continue
        materialized.append(asset)
    return materialized


def manifest_path_set(manifest: Mapping[str, Any], key: str) -> set[str]:
    records = manifest.get(key)
    if not isinstance(records, list):
        return set()
    paths: set[str] = set()
    for record in records:
        if isinstance(record, str) and record:
            paths.add(record)
            continue
        if not isinstance(record, Mapping):
            continue
        path = record.get("path")
        if isinstance(path, str) and path:
            paths.add(path)
    return paths


def source_path_for_managed_asset(path: str, *, policy: PlanPolicy) -> str | None:
    if path in policy.shared_schema_files or path in policy.claude_support_files:
        return path
    if path in policy.codex_required_files and path not in {"CODEX.md", policy.codex_hooks_rel}:
        return path
    template_prefix = f"{policy.workflow_template_target_root}/"
    if path.startswith(template_prefix):
        template_name = path.removeprefix(template_prefix)
        if template_name in policy.workflow_template_names:
            return f"{policy.workflow_template_source_root}/{template_name}"
    return None


def git_blob_checksum(source_root: Path, commit: str, source_path: str) -> str | None:
    """Recover prior managed bytes from an explicitly recorded source commit."""

    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit):
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "show", f"{commit}:{source_path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return content_checksum(result.stdout)


def legacy_managed_checksum(
    manifest: Mapping[str, Any],
    current_source_root: Path,
    path: str,
    *,
    policy: PlanPolicy,
) -> str | None:
    source_path = source_path_for_managed_asset(path, policy=policy)
    runtime = manifest.get("runtime")
    if source_path is None or not isinstance(runtime, Mapping):
        return None
    commit = runtime.get("source_commit")
    if not isinstance(commit, str):
        return None

    roots: list[Path] = []
    recorded_root = runtime.get("source_root")
    if isinstance(recorded_root, str):
        roots.append(Path(recorded_root).expanduser())
    roots.append(current_source_root)
    seen: set[Path] = set()
    for candidate in roots:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        checksum = git_blob_checksum(resolved, commit, source_path)
        if checksum is not None:
            return checksum
    return None


def managed_baseline_checksum(
    manifest: Mapping[str, Any],
    current_source_root: Path,
    path: str,
    *,
    policy: PlanPolicy,
) -> tuple[str | None, str | None]:
    checksum = recorded_managed_checksum(manifest, path)
    if checksum is not None:
        return checksum, "manifest checksum"
    checksum = legacy_managed_checksum(
        manifest,
        current_source_root,
        path,
        policy=policy,
    )
    if checksum is not None:
        return checksum, "legacy source commit"
    return None, None


def plan_operations(
    target_root: Path,
    assets: Sequence[Asset],
    manifest_bytes: bytes,
    *,
    source_root: Path,
    policy: PlanPolicy,
    read_json: Callable[[Path], dict[str, Any] | None],
    render_codex_hooks: Callable[[], bytes],
    merge_codex_hooks: Callable[[bytes, bytes | None], bytes | None],
    managed_baseline_checksum_fn: (
        Callable[[Mapping[str, Any], Path, str], tuple[str | None, str | None]] | None
    ) = None,
    source_path_for_managed_asset_fn: Callable[[str], str | None] | None = None,
    baseline_manifest: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Classify every desired write, refusing unknown semantic overwrites."""

    all_assets = [*assets, Asset(policy.manifest_rel, manifest_bytes)]
    installed_manifest = baseline_manifest
    if not isinstance(installed_manifest, Mapping):
        installed_manifest = read_json(target_root / policy.manifest_rel)
    if not isinstance(installed_manifest, Mapping):
        installed_manifest = {}
    managed_paths = manifest_path_set(installed_manifest, "managed_files")
    customized_paths = manifest_path_set(installed_manifest, "customized_files")
    resolve_baseline = managed_baseline_checksum_fn or (
        lambda manifest, root, path: managed_baseline_checksum(
            manifest,
            root,
            path,
            policy=policy,
        )
    )
    resolve_source_path = source_path_for_managed_asset_fn or (
        lambda path: source_path_for_managed_asset(path, policy=policy)
    )
    operations: list[dict[str, Any]] = []
    for asset in all_assets:
        target = target_root / asset.path
        if not target.exists():
            operations.append(
                {
                    "action": "create",
                    "path": asset.path,
                    "classification": "create",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Target file is missing.",
                }
            )
            continue
        if target.is_dir():
            operations.append(
                {
                    "action": "conflict",
                    "path": asset.path,
                    "classification": "conflict",
                    "safe_to_apply": False,
                    "managed": False,
                    "reason": "Target path is a directory.",
                }
            )
            continue
        if target.read_bytes() == asset.content:
            operations.append(
                {
                    "action": "skip",
                    "path": asset.path,
                    "classification": "skip",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Target file already matches expected content.",
                }
            )
            continue
        if asset.kind == "config":
            operations.append(
                {
                    "action": "skip",
                    "path": asset.path,
                    "classification": "skip",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": (
                        "Per-repo Aegis configuration is owner-maintained; seeded only when missing."
                    ),
                }
            )
            continue
        if asset.path == "CLAUDE.md" and asset.kind == "adapter":
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": (
                        "Existing Claude instructions will be preserved below an "
                        "Aegis-managed runtime block."
                    ),
                }
            )
            continue
        if asset.path == "CODEX.md" and asset.kind == "adapter":
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": (
                        "Existing Codex instructions will be preserved below an "
                        "Aegis-managed continuation block."
                    ),
                }
            )
            continue
        if asset.path == policy.codex_hooks_rel and asset.kind == "adapter":
            if merge_codex_hooks(target.read_bytes(), render_codex_hooks()) is None:
                operations.append(
                    {
                        "action": "manual-review",
                        "path": asset.path,
                        "classification": "manual-review",
                        "safe_to_apply": False,
                        "managed": False,
                        "reason": (
                            "Existing Codex hooks are not a mergeable JSON hooks object; "
                            "refusing to replace project-owned hook configuration."
                        ),
                    }
                )
            else:
                operations.append(
                    {
                        "action": "modify",
                        "path": asset.path,
                        "classification": "modify",
                        "safe_to_apply": True,
                        "managed": True,
                        "reason": (
                            "Merge Aegis Codex recorders structurally while preserving "
                            "all unrelated project hook registrations."
                        ),
                    }
                )
            continue
        if asset.path == "AGENTS.md":
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": (
                        "Existing agent instructions will be preserved below an "
                        "Aegis-managed runtime block."
                    ),
                }
            )
            continue
        if asset.path in managed_paths and asset.path not in customized_paths:
            baseline_checksum, baseline_source = resolve_baseline(
                installed_manifest,
                source_root,
                asset.path,
            )
            if baseline_checksum is not None:
                installed_checksum = content_checksum(target.read_bytes())
                if installed_checksum != baseline_checksum:
                    operations.append(
                        {
                            "action": "manual-review",
                            "path": asset.path,
                            "classification": "manual-review",
                            "safe_to_apply": False,
                            "managed": True,
                            "reason": (
                                "Installed Aegis-managed file diverged from its "
                                f"{baseline_source}; refusing semantic overwrite."
                            ),
                        }
                    )
                    continue
            elif resolve_source_path(asset.path) is not None:
                operations.append(
                    {
                        "action": "manual-review",
                        "path": asset.path,
                        "classification": "manual-review",
                        "safe_to_apply": False,
                        "managed": True,
                        "reason": (
                            "A legacy source-backed managed file differs, but its prior "
                            "expected bytes cannot be recovered; refusing semantic overwrite."
                        ),
                    }
                )
                continue
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": (
                        "Existing Aegis-managed file will be upgraded to the current managed asset."
                    ),
                }
            )
            continue
        operations.append(
            {
                "action": "manual-review",
                "path": asset.path,
                "classification": "manual-review",
                "safe_to_apply": False,
                "managed": False,
                "reason": "Existing file differs and Aegis V1 refuses unsafe overwrites.",
            }
        )
    return operations


def summarize_operations(operations: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in ("creates", "modifies", "skips", "conflicts", "manual_reviews")}
    for operation in operations:
        classification = operation.get("classification")
        if classification == "create":
            counts["creates"] += 1
        elif classification == "modify":
            counts["modifies"] += 1
        elif classification == "skip":
            counts["skips"] += 1
        elif classification == "conflict":
            counts["conflicts"] += 1
        elif classification == "manual-review":
            counts["manual_reviews"] += 1
    return counts
