#!/usr/bin/env python3
"""Safely apply generated template reference fixes.

The fix generator writes recommendations to output/data/fix_recommendations.json.
This runner is the supported mutation path for applying those recommendations:
dry-run by default, explicit --apply for writes, backups before modification,
and explicit git-backed rollback.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from scan_metadata import load_with_metadata


@dataclass(frozen=True)
class ReferenceFix:
    file: str
    old: str
    new: str
    action: str
    line_numbers: Sequence[int]


@dataclass
class FixResult:
    file: str
    status: str
    detail: str
    replacements: int = 0
    backup: Optional[str] = None


SUPPORTED_ACTIONS = {"update_reference", "update_reference_scoped"}


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Find the repository root from cwd or this script's location."""
    starts = [start or Path.cwd(), Path(__file__).resolve()]
    for candidate in starts:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in (current, *current.parents):
            if (parent / "templates").is_dir() and (parent / "scripts" / "template-ssot-scanner").exists():
                return parent
            if (parent / ".git").exists() and (parent / "templates").is_dir():
                return parent
    return (start or Path.cwd()).resolve()


def parse_line_numbers(raw: Any) -> Sequence[int]:
    if raw is None:
        return []
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, list):
        return [int(value) for value in raw if str(value).strip()]
    if isinstance(raw, str):
        return [int(value.strip()) for value in raw.split(",") if value.strip()]
    return []


def load_fix_data(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Fix recommendation file not found: {path}")
    data, _metadata = load_with_metadata(path)
    if data is not None:
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def load_reference_fixes(path: Path) -> List[ReferenceFix]:
    data = load_fix_data(path)
    fixes: List[ReferenceFix] = []
    for item in data.get("broken_references", []):
        action = item.get("action", "")
        old = item.get("old_reference", item.get("old"))
        new = item.get("suggested_fix", item.get("new"))
        file_path = item.get("file")
        if action not in SUPPORTED_ACTIONS or not file_path or not old or not new:
            continue
        fixes.append(
            ReferenceFix(
                file=str(file_path),
                old=str(old),
                new=str(new),
                action=action,
                line_numbers=parse_line_numbers(item.get("line_numbers")),
            )
        )
    return fixes


def resolve_target(root: Path, file_name: str) -> Path:
    candidate = Path(file_name)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.parent.resolve(strict=False) / candidate.name
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Refusing path outside repo root: {file_name}") from exc
    return resolved


def replace_scoped(content: str, fix: ReferenceFix) -> tuple[str, int]:
    if not fix.line_numbers:
        return content.replace(fix.old, fix.new), content.count(fix.old)

    lines = content.splitlines(keepends=True)
    replacements = 0
    for line_number in fix.line_numbers:
        if line_number < 1 or line_number > len(lines):
            continue
        index = line_number - 1
        original = lines[index]
        updated = original.replace(f"]({fix.old})", f"]({fix.new})")
        updated = updated.replace(f"`{fix.old}`", f"`{fix.new}`")
        if updated == original:
            updated = original.replace(fix.old, fix.new)
        if updated != original:
            replacements += original.count(fix.old)
            lines[index] = updated
    return "".join(lines), replacements


def preview_update(content: str, fix: ReferenceFix) -> tuple[str, int]:
    if fix.action == "update_reference_scoped":
        return replace_scoped(content, fix)
    return content.replace(fix.old, fix.new), content.count(fix.old)


def create_backup(root: Path, target: Path, backup_root: Path) -> Path:
    relative = target.relative_to(root)
    backup_path = backup_root / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(target, backup_path)
    return backup_path


def apply_fixes(
    fixes: Iterable[ReferenceFix],
    *,
    root: Path,
    dry_run: bool,
    backup_root: Path,
    allow_symlinks: bool,
) -> List[FixResult]:
    results: List[FixResult] = []
    for fix in fixes:
        try:
            target = resolve_target(root, fix.file)
        except ValueError as exc:
            results.append(FixResult(fix.file, "error", str(exc)))
            continue

        if not target.exists():
            results.append(FixResult(fix.file, "missing", "file does not exist"))
            continue
        if target.is_symlink() and not allow_symlinks:
            results.append(FixResult(fix.file, "skipped", "symlink target skipped; pass --allow-symlinks to modify"))
            continue
        if not target.is_file():
            results.append(FixResult(fix.file, "skipped", "not a regular file"))
            continue

        try:
            content = target.read_text(encoding="utf-8")
            updated, replacements = preview_update(content, fix)
            if updated == content:
                results.append(FixResult(fix.file, "unchanged", f"{fix.old} not present"))
                continue

            if dry_run:
                results.append(
                    FixResult(
                        fix.file,
                        "would-change",
                        f"{fix.old} -> {fix.new}",
                        replacements=replacements,
                    )
                )
                continue

            backup_path = create_backup(root, target, backup_root)
            target.write_text(updated, encoding="utf-8")
            results.append(
                FixResult(
                    fix.file,
                    "changed",
                    f"{fix.old} -> {fix.new}",
                    replacements=replacements,
                    backup=str(backup_path.relative_to(root)),
                )
            )
        except Exception as exc:  # pragma: no cover - defensive path
            results.append(FixResult(fix.file, "error", str(exc)))
    return results


def rollback_fixes(fixes: Iterable[ReferenceFix], *, root: Path, dry_run: bool) -> List[FixResult]:
    files = sorted({fix.file for fix in fixes})
    if not files:
        return []

    if dry_run:
        return [FixResult(file_name, "would-rollback", "git restore would run") for file_name in files]

    command = ["git", "restore", "--", *files]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or "git restore failed"
        return [FixResult(file_name, "error", detail) for file_name in files]
    return [FixResult(file_name, "rolled-back", "restored from git index/HEAD") for file_name in files]


def summarize(results: Sequence[FixResult]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts


def print_results(results: Sequence[FixResult], *, mode: str) -> None:
    print(f"Reference fix mode: {mode}")
    for result in results:
        suffix = f" ({result.replacements} replacement{'s' if result.replacements != 1 else ''})" if result.replacements else ""
        backup = f"; backup={result.backup}" if result.backup else ""
        print(f"- {result.status}: {result.file}: {result.detail}{suffix}{backup}")
    counts = summarize(results)
    print("Summary: " + ", ".join(f"{status}={count}" for status, count in sorted(counts.items())) if counts else "Summary: no fixes")


def write_log(path: Path, *, mode: str, root: Path, results: Sequence[FixResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "repo_root": str(root),
        "summary": summarize(results),
        "results": [result.__dict__ for result in results],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely apply template reference fixes")
    parser.add_argument(
        "--fixes-file",
        type=Path,
        default=Path("scripts/template-ssot-scanner/output/data/fix_recommendations.json"),
        help="Path to fix_recommendations.json, relative to repo root or current directory",
    )
    parser.add_argument("--apply", action="store_true", help="Actually write changes. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files (default).")
    parser.add_argument("--rollback", action="store_true", help="Use git restore on files referenced by fixes.")
    parser.add_argument("--allow-symlinks", action="store_true", help="Allow modifying symlink targets.")
    parser.add_argument("--backup-dir", type=Path, help="Backup directory for apply mode.")
    parser.add_argument("--log-file", type=Path, help="Optional JSON summary log path.")
    parser.add_argument("--repo-root", type=Path, help="Override repository root discovery.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = (args.repo_root.resolve() if args.repo_root else find_repo_root())
    fixes_file = args.fixes_file
    if not fixes_file.is_absolute():
        root_relative = root / fixes_file
        fixes_file = root_relative if root_relative.exists() else (Path.cwd() / fixes_file)

    fixes = load_reference_fixes(fixes_file)
    dry_run = not args.apply or args.dry_run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = args.backup_dir or (root / "scripts" / "template-ssot-scanner" / "output" / "backups" / "reference-fixes" / timestamp)
    if not backup_root.is_absolute():
        backup_root = root / backup_root

    if args.rollback:
        results = rollback_fixes(fixes, root=root, dry_run=dry_run)
        mode = "rollback-dry-run" if dry_run else "rollback-apply"
    else:
        results = apply_fixes(
            fixes,
            root=root,
            dry_run=dry_run,
            backup_root=backup_root,
            allow_symlinks=args.allow_symlinks,
        )
        mode = "dry-run" if dry_run else "apply"

    print_results(results, mode=mode)
    if args.log_file:
        log_file = args.log_file if args.log_file.is_absolute() else root / args.log_file
        write_log(log_file, mode=mode, root=root, results=results)
    return 1 if any(result.status == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
