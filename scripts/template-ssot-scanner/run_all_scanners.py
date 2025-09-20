#!/usr/bin/env python3
"""
Template Scanner Runner
Executes all scanner scripts in the correct sequence
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
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
    """Check if Python 3.8+ is available"""
    try:
        import platform
        version = platform.python_version()
        major, minor = map(int, version.split('.')[:2])
        
        if major < 3 or (major == 3 and minor < 8):
            print(f"❌ Python 3.8+ required, found {version}")
            return False
        
        print(f"✅ Python version: {version}")
        return True
    except Exception as e:
        print(f"❌ Error checking Python version: {e}")
        return False


def main():
    """Main runner function"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          Template SSOT Scanner Suite - Full Analysis        ║
╚══════════════════════════════════════════════════════════════╝

Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Directory: {Path.cwd()}
""")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install Python 3.8+")
        sys.exit(1)
    
    # Get project root (2 levels up from scripts/template-ssot-scanner/)
    project_root = Path(__file__).parent.parent.parent
    print(f"Project root: {project_root}")
    
    # Define execution sequence - MIGRATION DETECTOR MUST RUN FIRST
    scripts = [
        {
            "script": "migration_detector.py",
            "args": "",
            "description": "Detecting true migration status of monolithic files",
            "required": True
        },
        {
            "script": "scanner.py",
            "args": f"--base {project_root}",
            "description": "Scanning all template files and collecting metadata",
            "required": True
        },
        {
            "script": "analyze_references.py",
            "args": "",
            "description": "Analyzing file references and dependencies",
            "required": True
        },
        {
            "script": "find_duplicates.py", 
            "args": "",
            "description": "Finding duplicate content and migration status",
            "required": True
        },
        {
            "script": "generate_fixes.py",
            "args": "",
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
        
        cmd = f"python3 {script_info['script']} {script_info['args']}"
        
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
    
    # Check for output files
    print(f"\n{'=' * 60}")
    print("OUTPUT FILES")
    print(f"{'=' * 60}")
    
    output_files = [
        "output/data/migration_status.json",
        "output/data/template_scan_results.json",
        "output/data/reference_analysis.json",
        "output/data/duplicate_analysis.json",
        "output/data/fix_recommendations.json",
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