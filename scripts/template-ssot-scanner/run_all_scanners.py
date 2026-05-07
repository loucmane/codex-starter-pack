#!/usr/bin/env python3
"""
Template Scanner Runner
Executes all scanner scripts in the correct sequence
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from baseline_summary import write_baseline_summary

REQUIRED_PYTHON = (3, 11)


def format_command(cmd: list[str]) -> str:
    """Return a shell-readable command string for display only."""
    return " ".join(shlex.quote(part) for part in cmd)


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {format_command(cmd)}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        print(result.stdout)
        
        if result.stderr:
            print(f"Warnings/Errors:\n{result.stderr}")
        
        if result.returncode != 0:
            print(f"❌ Failed with return code: {result.returncode}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False


def check_dependencies() -> bool:
    """Check if the Codex project Python version is available."""
    try:
        import platform
        version = platform.python_version()
        major, minor = map(int, version.split('.')[:2])
        
        if (major, minor) < REQUIRED_PYTHON:
            required = ".".join(str(part) for part in REQUIRED_PYTHON)
            print(f"❌ Python {required}+ required, found {version}")
            return False
        
        print(f"✅ Python version: {version}")
        return True
    except Exception as e:
        print(f"❌ Error checking Python version: {e}")
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Template SSOT scanner suite in dependency order.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Run all scanners without checkpoints
  %(prog)s --base /path/to/repo     # Scan a specific repository root
  %(prog)s --with-checkpoints       # Opt in to checkpoint generation
        """,
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="Repository root to scan (default: auto-detect from this script location)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run scanner scripts (default: current interpreter)",
    )
    parser.add_argument(
        "--with-checkpoints",
        action="store_true",
        help="Allow scanner.py to generate checkpoint files (disabled by default)",
    )
    parser.add_argument(
        "--checkpoint",
        type=int,
        default=25,
        help="Checkpoint interval when --with-checkpoints is enabled (default: 25)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Scanner config YAML path passed to config-aware scanner modules",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Named scanner config profile passed to config-aware scanner modules",
    )
    parser.add_argument(
        "--environment",
        default=None,
        help="Named scanner config environment overlay passed to config-aware scanner modules",
    )
    parser.add_argument(
        "--env-overrides",
        action="store_true",
        help="Apply CODEX_SCANNER_ environment overrides in config-aware scanner modules",
    )
    return parser


def main(argv: list[str] | None = None):
    """Main runner function"""
    args = build_parser().parse_args(argv)
    project_root = (args.base or Path(__file__).parent.parent.parent).resolve()
    scanner_args = ["--base", str(project_root)]
    if args.with_checkpoints:
        scanner_args.extend(["--checkpoint", str(args.checkpoint)])
    else:
        scanner_args.append("--no-checkpoints")
    config_module_args = []
    if args.config:
        config_module_args.extend(["--config", str(args.config)])
    if args.profile:
        config_module_args.extend(["--profile", args.profile])
    if args.environment:
        config_module_args.extend(["--environment", args.environment])
    if args.env_overrides:
        config_module_args.append("--env-overrides")
    scanner_args.extend(config_module_args)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          Template SSOT Scanner Suite - Full Analysis        ║
╚══════════════════════════════════════════════════════════════╝

Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Directory: {project_root}
""")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install Python 3.11+")
        sys.exit(1)
    
    print(f"Project root: {project_root}")
    
    # Define execution sequence - MIGRATION DETECTOR MUST RUN FIRST
    scripts = [
        {
            "script": "migration_detector.py",
            "args": [],
            "description": "Detecting true migration status of monolithic files",
            "required": True
        },
        {
            "script": "scanner.py",
            "args": scanner_args,
            "description": "Scanning all template files and collecting metadata",
            "required": True
        },
        {
            "script": "security_validator.py",
            "args": ["--base", str(project_root), *config_module_args],
            "description": "Scanning template and config files for security validation findings",
            "required": True
        },
        {
            "script": "analyze_references.py",
            "args": config_module_args,
            "description": "Analyzing file references and dependencies",
            "required": True
        },
        {
            "script": "find_duplicates.py", 
            "args": [],
            "description": "Finding duplicate content and migration status",
            "required": True
        },
        {
            "script": "generate_fixes.py",
            "args": [],
            "description": "Generating fix scripts and recommendations",
            "required": False
        }
    ]
    
    # Track execution results
    results = []
    all_success = True
    
    # Execute each script
    for i, script_info in enumerate(scripts, 1):
        script_path = Path(__file__).parent / script_info["script"]
        
        if not script_path.exists():
            print(f"\n❌ Script not found: {script_path}")
            if script_info["required"]:
                all_success = False
                break
            continue
        
        cmd = [args.python, script_info["script"], *script_info["args"]]
        
        success = run_command(cmd, f"[{i}/{len(scripts)}] {script_info['description']}")
        
        results.append({
            "script": script_info["script"],
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        if not success and script_info["required"]:
            print(f"\n❌ Required script failed: {script_info['script']}")
            all_success = False
            break
    
    # Generate summary
    print(f"\n{'=' * 60}")
    print("EXECUTION SUMMARY")
    print(f"{'=' * 60}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['script']}")

    if all_success:
        try:
            summary_path = Path(__file__).parent / "output/data/baseline_summary.json"
            summary = write_baseline_summary(
                Path(__file__).parent / "output/data",
                summary_path,
            )
            print("\nBaseline summary generated:")
            print(f"  output/data/baseline_summary.json ({summary_path.stat().st_size:,} bytes)")
            print(f"  Total references: {summary['metrics'].get('total_references')}")
            print(f"  Broken references: {summary['metrics'].get('broken_references')}")
            print(f"  Duplicate count: {summary['metrics'].get('duplicate_count')}")
            print(f"  Migration percentage: {summary['metrics'].get('migration_percentage')}")
        except Exception as exc:
            print(f"\n❌ Failed to generate baseline summary: {exc}")
            all_success = False
    
    # Check for output files
    print(f"\n{'=' * 60}")
    print("OUTPUT FILES")
    print(f"{'=' * 60}")
    
    output_files = [
        "output/data/migration_status.json",
        "output/data/template_scan_results.json",
        "output/data/security_validation.json",
        "output/data/reference_analysis.json",
        "output/data/duplicate_analysis.json",
        "output/data/fix_recommendations.json",
        "output/data/baseline_summary.json",
        "output/scripts/apply_reference_fixes.py",
        "output/scripts/archive_duplicates.sh",
        "output/scripts/apply_all_fixes.sh"
    ]
    
    found_files = []
    for file_name in output_files:
        file_path = Path(__file__).parent / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            found_files.append(f"✅ {file_name} ({size:,} bytes)")
        else:
            found_files.append(f"⚪ {file_name} (not created)")
    
    for file_info in found_files:
        print(file_info)
    
    # Final status
    print(f"\n{'=' * 60}")
    if all_success:
        print("✅ ALL SCANNERS COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Review the generated JSON files in output/data/ directory")
        print("2. Check output/data/fix_recommendations.json for prioritized actions")
        print("3. Review the generated scripts in output/scripts/ before running")
        print("4. Backup your templates directory before applying fixes")
        print("5. Run ./output/scripts/apply_all_fixes.sh to apply all fixes (with caution)")
    else:
        print("⚠️  SOME SCANNERS FAILED")
        print("\nCheck the output above for error details.")
        print("You may need to run individual scripts manually.")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
