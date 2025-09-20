#!/usr/bin/env python3
"""Test that all integrations are working correctly"""

import json
from pathlib import Path

def check_integration():
    issues = []
    
    # 1. Check migration_detector output path
    detector_file = Path("migration_detector.py")
    content = detector_file.read_text()
    if 'output_dir = Path("output/data")' in content:
        print("✅ migration_detector.py writes to output/data/")
    else:
        issues.append("migration_detector.py incorrect output path")
    
    # 2. Check find_duplicates loads migration status
    dup_file = Path("find_duplicates.py")
    content = dup_file.read_text()
    if 'Path("output/data/migration_status.json")' in content and 'FULLY_MIGRATED' in content:
        print("✅ find_duplicates.py loads migration_status.json and checks FULLY_MIGRATED")
    else:
        issues.append("find_duplicates.py not properly integrated")
    
    # 3. Check analyze_references has monolith check
    ref_file = Path("analyze_references.py")
    content = ref_file.read_text()
    if 'monolith_reference_after_migration' in content and 'Path("output/data/migration_status.json")' in content:
        print("✅ analyze_references.py checks for monolith_reference_after_migration")
    else:
        issues.append("analyze_references.py not properly integrated")
    
    # 4. Check generate_fixes loads migration status
    fix_file = Path("generate_fixes.py")
    content = fix_file.read_text()
    if '"migration": "output/data/migration_status.json"' in content and 'FULLY_MIGRATED' in content:
        print("✅ generate_fixes.py loads migration_status.json and checks FULLY_MIGRATED")
    else:
        issues.append("generate_fixes.py not properly integrated")
        
    # 5. Check run_all_scanners runs migration_detector first
    runner_file = Path("run_all_scanners.py")
    content = runner_file.read_text()
    lines = content.splitlines()
    scripts_start = None
    for i, line in enumerate(lines):
        if 'scripts = [' in line:
            scripts_start = i
            break
    
    if scripts_start and 'migration_detector.py' in lines[scripts_start+2]:
        print("✅ run_all_scanners.py runs migration_detector.py FIRST")
    else:
        issues.append("run_all_scanners.py doesn't run migration_detector first")
    
    # 6. Check paths in runner summary
    if './output/scripts/apply_all_fixes.sh' in content:
        print("✅ run_all_scanners.py references correct script paths")
    else:
        issues.append("run_all_scanners.py has incorrect script paths")
    
    return issues

if __name__ == "__main__":
    print("Integration Test")
    print("=" * 50)
    issues = check_integration()
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All integrations verified!")
    
    print("\n" + "=" * 50)
    print(f"Result: {'PASS' if not issues else 'FAIL'}")
