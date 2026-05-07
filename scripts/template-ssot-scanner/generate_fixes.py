#!/usr/bin/env python3
"""
Fix Generator
Generates shell scripts and recommendations to fix SSOT issues
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
from scan_metadata import save_with_metadata, load_with_metadata

class FixGenerator:
    """Generates fixes for template system issues"""
    
    def __init__(self, scoped_replacements: bool = False, 
                 report_dir: str = None):
        self.scan_results = None
        self.reference_analysis = None
        self.duplicate_analysis = None
        self.scoped_replacements = scoped_replacements
        self.report_dir = report_dir
        self.fixes = {
            "timestamp": datetime.now().isoformat(),
            "broken_references": [],
            "duplicate_removals": [],
            "file_moves": [],
            "content_updates": [],
            "recommendations": [],
            "statistics": {}
        }
    
    def load_analyses(self) -> bool:
        """Load all analysis files"""
        files = {
            "scan": "output/data/template_scan_results.json",
            "references": "output/data/reference_analysis.json",
            "duplicates": "output/data/duplicate_analysis.json",
            "migration": "output/data/migration_status.json"
        }
        
        try:
            if Path(files["scan"]).exists():
                data, _ = load_with_metadata(Path(files["scan"]))
                if data is None:
                    raise ValueError("scan results missing data")
                self.scan_results = data
            
            if Path(files["references"]).exists():
                data, _ = load_with_metadata(Path(files["references"]))
                if data is None:
                    raise ValueError("reference analysis missing data")
                self.reference_analysis = data
            
            if Path(files["duplicates"]).exists():
                data, _ = load_with_metadata(Path(files["duplicates"]))
                if data is None:
                    raise ValueError("duplicate analysis missing data")
                self.duplicate_analysis = data
            
            # Load migration status if available
            self.migration_status = {}
            if Path(files["migration"]).exists():
                data, _ = load_with_metadata(Path(files["migration"]))
                if data is None:
                    raise ValueError("migration status missing data")
                self.migration_status = data
                print(f"Loaded migration status for {len(self.migration_status)} files")
            
            return True
        except Exception as e:
            print(f"Error loading analysis files: {e}")
            return False
    
    def generate_fixes(self, duration: float = None) -> Dict:
        """Generate all fixes"""
        if not self.load_analyses():
            print("Error: Could not load analysis files. Run previous scripts first.")
            return {}
        
        print("Generating fixes...")
        
        # Generate fixes for broken references
        self._fix_broken_references()
        
        # Generate fixes for duplicates
        self._fix_duplicates()
        
        # Generate file organization fixes
        self._fix_file_organization()
        
        # Generate content update recommendations
        self._generate_content_updates()
        
        # Generate overall recommendations
        self._generate_recommendations()
        
        # Calculate statistics
        self._calculate_statistics()
        
        # Save fixes with duration
        self._save_fixes(duration)
        
        # Generate shell scripts
        self._generate_shell_scripts()
        
        return self.fixes
    
    def _fix_broken_references(self) -> None:
        """Generate fixes for broken references"""
        if not self.reference_analysis:
            return
        
        print("Generating fixes for broken references...")
        
        # First, handle references to migrated monoliths (high priority)
        monolith_refs = self.reference_analysis.get("monolith_reference_after_migration", [])
        if monolith_refs:
            print(f"  Fixing {len(monolith_refs)} references to migrated monoliths...")
            for ref in monolith_refs:
                source_file = ref["source_file"]
                target_file = ref["target_file"]
                
                # Suggest replacement based on the monolith type
                suggested_fix = self._get_modular_replacement(target_file)
                
                fix = {
                    "file": source_file,
                    "old_reference": target_file,
                    "suggested_fix": suggested_fix,
                    "action": "update_reference_scoped" if self.scoped_replacements else "update_reference",
                    "reason": "monolith_migrated",
                    "priority": "HIGH"
                }
                
                # Get line numbers if available
                line_numbers = self._get_reference_line_numbers(source_file, target_file)
                if line_numbers:
                    fix["line_numbers"] = line_numbers
                
                self.fixes["broken_references"].append(fix)
        
        for broken_ref in self.reference_analysis.get("broken_references", []):
            source_file = broken_ref["source_file"]
            bad_reference = broken_ref["broken_reference"]
            
            # Try to find the correct file
            possible_fix = self._find_correct_reference(bad_reference)
            
            if self.scoped_replacements:
                # Get line numbers for scoped replacement
                line_nums = self._get_reference_line_numbers(source_file, bad_reference)
                fix = {
                    "file": source_file,
                    "old_reference": bad_reference,
                    "suggested_fix": possible_fix,
                    "line_numbers": line_nums,
                    "action": "update_reference_scoped" if possible_fix and line_nums else "update_reference" if possible_fix else "manual_review"
                }
            else:
                fix = {
                    "file": source_file,
                    "old_reference": bad_reference,
                    "suggested_fix": possible_fix,
                    "action": "update_reference" if possible_fix else "manual_review"
                }
            
            self.fixes["broken_references"].append(fix)
    
    def _get_modular_replacement(self, monolith_file: str) -> str:
        """Get the modular/registry replacement for a monolithic file"""
        # Map monolithic files to their modular equivalents
        replacements = {
            "templates/REGISTRY.md": "templates/registry/index.md",
            "templates/WORKFLOWS.md": "templates/workflows/",
            "templates/PATTERNS.md": "templates/patterns/",
            "templates/HANDLERS.md": "templates/handlers/",
            "templates/CONVENTIONS.md": "templates/conventions/",
            "templates/BEHAVIORS.md": "templates/behaviors/",
            "templates/MATRICES.md": "templates/matrices/",
            "templates/TOOLS.md": "templates/tools/"
        }
        
        return replacements.get(monolith_file, "templates/registry/index.md")
    
    def _find_correct_reference(self, bad_reference: str) -> Optional[str]:
        """Try to find the correct reference path"""
        if not self.scan_results:
            return None
        
        # Extract filename from bad reference
        filename = Path(bad_reference).name
        
        # Search for files with same name
        for file_path in self.scan_results["files"]:
            if Path(file_path).name == filename:
                return file_path
        
        # Try partial match
        name_parts = filename.replace('-', ' ').replace('_', ' ').split()
        for file_path in self.scan_results["files"]:
            file_name = Path(file_path).name.lower()
            if all(part.lower() in file_name for part in name_parts):
                return file_path
        
        return None
    
    def _fix_duplicates(self) -> None:
        """Generate fixes for duplicate files"""
        if not self.duplicate_analysis:
            return
        
        print("Generating fixes for duplicates...")
        
        for duplicate_group in self.duplicate_analysis.get("content_duplicates", []):
            files = duplicate_group["files"]
            if len(files) <= 1:
                continue
            
            # Skip if any file is a FULLY_MIGRATED monolith (these are index files, not duplicates)
            skip_group = False
            for file_info in files:
                file_path = file_info["file"]
                if file_path in self.migration_status:
                    if self.migration_status[file_path].get("status") == "FULLY_MIGRATED":
                        print(f"  Skipping duplicate group - {file_path} is FULLY_MIGRATED index")
                        skip_group = True
                        break
            
            if skip_group:
                continue
            
            # Keep the file in the most logical location
            files_sorted = sorted(files, key=lambda x: self._get_file_priority(x["file"]))
            keep_file = files_sorted[0]
            remove_files = files_sorted[1:]
            
            for remove_file in remove_files:
                # Skip if this is a FULLY_MIGRATED monolith
                if remove_file["file"] in self.migration_status:
                    if self.migration_status[remove_file["file"]].get("status") == "FULLY_MIGRATED":
                        print(f"  Skipping {remove_file['file']} - FULLY_MIGRATED index file")
                        continue
                
                archive_path = f"archive/{remove_file['file']}"
                src_file = remove_file["file"]
                parent_dir = str(Path(archive_path).parent)
                self.fixes["duplicate_removals"].append({
                    "remove": src_file,
                    "keep": keep_file["file"],
                    "archive_to": archive_path,
                    "reason": "exact_duplicate",
                    "command": f'mkdir -p "{parent_dir}" && git mv "{src_file}" "{archive_path}"'
                })
    
    def _get_file_priority(self, file_path: str) -> int:
        """Get priority for keeping a file (lower is better)"""
        # Prefer files in main directories
        if file_path.startswith("templates/registry/"):
            return 1
        elif file_path.startswith("templates/handlers/"):
            return 2
        elif file_path.startswith("templates/"):
            return 3
        elif file_path.startswith(".codex/") or file_path.startswith(".claude/"):
            return 4
        else:
            return 5

    def _get_reference_line_numbers(self, file_path: str, reference: str) -> str:
        """Get line numbers where reference appears"""
        if not self.scan_results or file_path not in self.scan_results["files"]:
            return ""
        
        file_info = self.scan_results["files"][file_path]
        if "references_detailed" in file_info:
            for ref_detail in file_info["references_detailed"]:
                if ref_detail["reference"] == reference:
                    line_nums = [str(loc["line"]) for loc in ref_detail["locations"]]
                    return ",".join(line_nums)
        
        return ""
    
    def _fix_file_organization(self) -> None:
        """Generate fixes for file organization - DEPRECATED"""
        print("File organization has been moved to safe_reorganize.py")
        print("  Use: python3 safe_reorganize.py --dry-run")
        print("  This ensures migration-aware, safe file moves")
        # Don't generate any file moves here - use safe_reorganize.py instead
        return
    
    def _get_expected_location(self, file_type: str, current_path: str) -> Optional[str]:
        """Get expected location for a file type"""
        # Only suggest moves for clearly misplaced files
        filename = Path(current_path).name
        
        location_map = {
            "trigger": f"templates/handlers/triggers/{filename}",
            "orchestrator": f"templates/handlers/orchestrators/{filename}",
            "operator": f"templates/handlers/operators/{filename}",
            "workflow": f"templates/workflows/{filename}",
            "pattern": f"templates/patterns/{filename}",
            "convention": f"templates/conventions/{filename}",
            "behavior": f"templates/behaviors/{filename}",
            "matrix": f"templates/matrices/{filename}",
            "agent": f"templates/agents/{filename}"
        }
        
        expected = location_map.get(file_type)
        
        # Don't suggest move if already in correct general area
        if expected and current_path != expected:
            if file_type in current_path.lower():
                return None  # Already in appropriate directory
            return expected
        
        return None
    
    def _generate_content_updates(self) -> None:
        """Generate content update recommendations"""
        if not self.duplicate_analysis:
            return
        
        print("Generating content update recommendations...")
        
        # Check migration status
        for mono_file, status in self.duplicate_analysis.get("migration_status", {}).items():
            if status["migration_percentage"] < 100:
                # Get the actual section names from monolithic_files
                mono_sections = self.duplicate_analysis.get("monolithic_files", {}).get(mono_file, {}).get("sections", [])
                unmigrated = sorted(set(mono_sections) - set(status["migrated_section_names"]))
                
                if unmigrated:
                    self.fixes["content_updates"].append({
                        "file": mono_file,
                        "action": "complete_migration",
                        "unmigrated_sections": list(unmigrated)[:10],  # First 10
                        "migration_percentage": status["migration_percentage"],
                        "recommendation": f"Migrate remaining {len(unmigrated)} sections to modular files"
                    })
    
    def _generate_recommendations(self) -> None:
        """Generate overall recommendations"""
        print("Generating recommendations...")
        
        recommendations = []
        
        # Broken references
        if self.reference_analysis and self.reference_analysis.get("broken_references"):
            count = len(self.reference_analysis["broken_references"])
            recommendations.append({
                "priority": "high",
                "category": "broken_references",
                "issue": f"{count} broken references found",
                "action": "Run python3 apply_reference_fixes.py to update references"
            })
        
        # Duplicates
        if self.duplicate_analysis and self.duplicate_analysis.get("content_duplicates"):
            count = self.duplicate_analysis["statistics"]["files_with_duplicates"]
            recommendations.append({
                "priority": "medium",
                "category": "duplicates",
                "issue": f"{count} duplicate files found",
                "action": "Review and run ./archive_duplicates.sh carefully"
            })
        
        # Orphaned files
        if self.reference_analysis and self.reference_analysis.get("orphaned_files"):
            count = len(self.reference_analysis["orphaned_files"])
            if count > 10:
                recommendations.append({
                    "priority": "low",
                    "category": "orphaned_files",
                    "issue": f"{count} orphaned files found",
                    "action": "Review orphaned files and add references or remove"
                })
        
        # Migration completion
        if self.duplicate_analysis and self.duplicate_analysis.get("migration_status"):
            avg_migration = self.duplicate_analysis["statistics"]["overall_migration_percentage"]
            if avg_migration < 100:
                recommendations.append({
                    "priority": "medium",
                    "category": "migration",
                    "issue": f"Migration {avg_migration}% complete",
                    "action": "Complete migration from monolithic to modular files"
                })
        
        # Circular dependencies
        if self.reference_analysis and self.reference_analysis.get("circular_dependencies"):
            count = len(self.reference_analysis["circular_dependencies"])
            if count > 0:
                recommendations.append({
                    "priority": "high",
                    "category": "circular_dependencies",
                    "issue": f"{count} circular dependencies found",
                    "action": "Refactor to remove circular dependencies"
                })
        
        self.fixes["recommendations"] = sorted(
            recommendations,
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]]
        )
    
    def _calculate_statistics(self) -> None:
        """Calculate fix statistics"""
        self.fixes["statistics"] = {
            "broken_references_to_fix": len(self.fixes["broken_references"]),
            "duplicates_to_remove": len(self.fixes["duplicate_removals"]),
            "files_to_move": len(self.fixes["file_moves"]),
            "content_updates_needed": len(self.fixes["content_updates"]),
            "total_fixes": (
                len(self.fixes["broken_references"]) +
                len(self.fixes["duplicate_removals"]) +
                len(self.fixes["file_moves"])
            )
        }
    
    def _save_fixes(self, duration: float = None) -> None:
        """Save fix recommendations to JSON with metadata"""
        output_file = Path("output/data/fix_recommendations.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare statistics for metadata
        stats = self.fixes.get("statistics", {})
        stats["recommendations_count"] = len(self.fixes.get("recommendations", []))
        
        # Save with metadata
        save_with_metadata(
            data=self.fixes,
            output_file=output_file,
            scanner_name="fix_generator",
            version="1.1.0",
            stats=stats,
            duration_seconds=duration
        )
        
        print(f"\n✅ Fix generation complete!")
        print(f"  Broken reference fixes: {self.fixes['statistics']['broken_references_to_fix']}")
        print(f"  Duplicate removals: {self.fixes['statistics']['duplicates_to_remove']}")
        print(f"  File moves: {self.fixes['statistics']['files_to_move']}")
        print(f"  Results saved to: {output_file}")
    
    def _generate_shell_scripts(self) -> None:
        """Generate shell scripts for fixes"""
        print("\nGenerating shell scripts...")
        
        # Python script for fixing broken references
        if self.fixes["broken_references"]:
            script_path = Path("output/scripts/apply_reference_fixes.py")
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, 'w') as f:
                f.write("#!/usr/bin/env python3\n")
                f.write('"""Fix broken references in template files"""\n\n')
                f.write("import json\n")
                f.write("from pathlib import Path\n")
                f.write("import sys\n\n")
                
                f.write("def fix_references():\n")
                f.write("    fixes = [\n")
                
                for fix in self.fixes["broken_references"]:
                    if fix["action"] in ["update_reference", "update_reference_scoped"]:
                        f.write(f"        {{\n")
                        f.write(f'            "file": "{fix["file"]}",\n')
                        f.write(f'            "old": "{fix["old_reference"]}",\n')
                        f.write(f'            "new": "{fix["suggested_fix"]}",\n')
                        f.write(f'            "action": "{fix["action"]}",\n')
                        if "line_numbers" in fix:
                            f.write(f'            "line_numbers": "{fix["line_numbers"]}"\n')
                        else:
                            f.write(f'            "line_numbers": ""\n')
                        f.write(f"        }},\n")
                
                f.write("    ]\n\n")
                
                f.write("    for fix in fixes:\n")
                f.write("        if fix['action'] == 'manual_review':\n")
                f.write("            print(f\"⚠️  Manual review needed: {fix['file']} - {fix['old']}\")\n")
                f.write("            continue\n\n")
                f.write("        file_path = Path(fix['file'])\n")
                f.write("        if not file_path.exists():\n")
                f.write("            print(f\"❌ File not found: {fix['file']}\")\n")
                f.write("            continue\n\n")
                f.write("        try:\n")
                f.write("            content = file_path.read_text()\n")
                f.write("            \n")
                f.write("            # Use scoped replacement if line numbers are available\n")
                f.write("            if fix.get('line_numbers') and fix['action'] == 'update_reference_scoped':\n")
                f.write("                lines = content.splitlines()\n")
                f.write("                line_nums = [int(n) for n in fix['line_numbers'].split(',') if n]\n")
                f.write("                changes_made = False\n")
                f.write("                \n")
                f.write("                # Replace only on specified lines (checking for markdown links and backticks)\n")
                f.write("                for line_num in line_nums:\n")
                f.write("                    if 1 <= line_num <= len(lines):\n")
                f.write("                        line_idx = line_num - 1\n")
                f.write("                        original_line = lines[line_idx]\n")
                f.write("                        import re\n")
                f.write("                        \n")
                f.write("                        # Pattern 1: Replace in markdown links [...](...)\n")
                f.write("                        pattern1 = r'\\[([^\\]]+)\\]\\(' + re.escape(fix['old']) + r'\\)'\n")
                f.write("                        replacement1 = r'[\\1](' + fix['new'] + ')'\n")
                f.write("                        updated_line = re.sub(pattern1, replacement1, original_line)\n")
                f.write("                        \n")
                f.write("                        # Pattern 2: Replace in backtick references `path`\n")
                f.write("                        if updated_line == original_line:  # If no markdown link was replaced\n")
                f.write("                            pattern2 = r'`' + re.escape(fix['old']) + r'`'\n")
                f.write("                            replacement2 = '`' + fix['new'] + '`'\n")
                f.write("                            updated_line = re.sub(pattern2, replacement2, original_line)\n")
                f.write("                        \n")
                f.write("                        if updated_line != original_line:\n")
                f.write("                            lines[line_idx] = updated_line\n")
                f.write("                            changes_made = True\n")
                f.write("                \n")
                f.write("                if changes_made:\n")
                f.write("                    updated = '\\\\n'.join(lines) + ('\\\\n' if content.endswith('\\\\n') else '')\n")
                f.write("                    file_path.write_text(updated)\n")
                f.write("                    print(f\"✅ Fixed (scoped): {fix['file']} on lines {fix['line_numbers']}\")\n")
                f.write("                else:\n")
                f.write("                    print(f\"⚪ No change needed: {fix['file']}\")\n")
                f.write("            else:\n")
                f.write("                # Fall back to global replacement\n")
                f.write("                updated = content.replace(fix['old'], fix['new'])\n")
                f.write("                if content != updated:\n")
                f.write("                    file_path.write_text(updated)\n")
                f.write("                    print(f\"✅ Fixed (global): {fix['file']}\")\n")
                f.write("                else:\n")
                f.write("                    print(f\"⚪ No change needed: {fix['file']}\")\n")
                f.write("        except Exception as e:\n")
                f.write("            print(f\"❌ Error fixing {fix['file']}: {e}\")\n\n")
                
                f.write('if __name__ == "__main__":\n')
                f.write('    print("Fixing broken references...")\n')
                f.write('    fix_references()\n')
                f.write('    print("Done!")\n')

            # Replace the historical one-off mutation script with a thin wrapper
            # around the tracked safe runner. The supported runner is dry-run by
            # default and requires --apply before writing template files.
            script_path.write_text(
                """#!/usr/bin/env python3
\"\"\"Generated wrapper for the tracked safe reference-fix runner.\"\"\"

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts" / "template-ssot-scanner" / "apply_reference_fixes.py").exists():
            return parent
    raise SystemExit("Could not locate repository root from generated wrapper")


if __name__ == "__main__":
    root = find_repo_root()
    runner = root / "scripts" / "template-ssot-scanner" / "apply_reference_fixes.py"
    fixes_file = root / "scripts" / "template-ssot-scanner" / "output" / "data" / "fix_recommendations.json"
    sys.argv = [str(runner), "--fixes-file", str(fixes_file), *sys.argv[1:]]
    runpy.run_path(str(runner), run_name="__main__")
""",
                encoding="utf-8",
            )
            
            script_path.chmod(0o755)
            print(f"  Created: {script_path}")
        
        # Script for archiving duplicates
        if self.fixes["duplicate_removals"]:
            script_path = Path("output/scripts/archive_duplicates.sh")
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Archive duplicate template files (using git mv)\n")
                f.write("# Generated: " + datetime.now().isoformat() + "\n\n")
                f.write("set -e\n\n")
                
                f.write("echo 'Archiving duplicate files...'\n")
                f.write("echo 'This will move files to archive/ directory using git mv'\n")
                f.write("read -p 'Continue? (y/n) ' -n 1 -r\n")
                f.write("echo\n")
                f.write("if [[ ! $REPLY =~ ^[Yy]$ ]]; then\n")
                f.write("    exit 1\n")
                f.write("fi\n\n")
                
                f.write("# Create archive directory if needed\n")
                f.write('mkdir -p archive\n\n')
                
                for removal in self.fixes["duplicate_removals"]:
                    f.write(f"# Duplicate of: {removal['keep']}\n")
                    f.write(f"{removal['command']}\n\n")
                
                f.write("echo 'Duplicates archived!'\n")
            
            script_path.chmod(0o755)
            print(f"  Created: {script_path}")
        
        # Don't generate reorganize_files.sh - use safe_reorganize.py instead
        if self.fixes["file_moves"]:
            print("  ⚠️  File reorganization detected - use safe_reorganize.py instead")
            print("     Run: python3 safe_reorganize.py --dry-run")
        
        # Master script
        script_path = Path("output/scripts/apply_all_fixes.sh")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Apply all template system fixes\n")
            f.write("# Generated: " + datetime.now().isoformat() + "\n\n")
            f.write("set -e\n\n")
            
            f.write("echo 'Applying all template system fixes...'\n")
            f.write("echo 'This will:'\n")
            f.write(f"echo '  - Fix {self.fixes['statistics']['broken_references_to_fix']} broken references'\n")
            f.write(f"echo '  - Remove {self.fixes['statistics']['duplicates_to_remove']} duplicate files'\n")
            f.write(f"echo '  - Move {self.fixes['statistics']['files_to_move']} files'\n")
            f.write("echo\n")
            f.write("DRY_RUN=1\n")
            f.write("YES=0\n")
            f.write("ROLLBACK=0\n")
            f.write("for arg in \"$@\"; do\n")
            f.write("    case \"$arg\" in\n")
            f.write("        --dry-run) DRY_RUN=1 ;;\n")
            f.write("        --apply) DRY_RUN=0 ;;\n")
            f.write("        --yes|-y) YES=1 ;;\n")
            f.write("        --rollback) ROLLBACK=1 ;;\n")
            f.write("        *) echo \"Unknown argument: $arg\" >&2; exit 2 ;;\n")
            f.write("    esac\n")
            f.write("done\n\n")
            f.write("if [[ \"$DRY_RUN\" != \"1\" && \"$YES\" != \"1\" ]]; then\n")
            f.write("    read -p 'Apply all generated fixes now? (y/n) ' -n 1 -r\n")
            f.write("    echo\n")
            f.write("    if [[ ! $REPLY =~ ^[Yy]$ ]]; then\n")
            f.write("        exit 1\n")
            f.write("    fi\n")
            f.write("fi\n\n")
            if Path("output/scripts/apply_reference_fixes.py").exists():
                f.write("REFERENCE_ARGS=()\n")
                f.write("if [[ \"$DRY_RUN\" == \"1\" ]]; then\n")
                f.write("    REFERENCE_ARGS+=(--dry-run)\n")
                f.write("else\n")
                f.write("    REFERENCE_ARGS+=(--apply)\n")
                f.write("fi\n")
                f.write("if [[ \"$ROLLBACK\" == \"1\" ]]; then\n")
                f.write("    REFERENCE_ARGS+=(--rollback)\n")
                f.write("fi\n")
                f.write("python3 output/scripts/apply_reference_fixes.py \"${REFERENCE_ARGS[@]}\"\n")
            if Path("output/scripts/archive_duplicates.sh").exists():
                f.write("if [[ \"$DRY_RUN\" == \"1\" ]]; then\n")
                f.write("    echo 'Dry-run: duplicate archive script not executed.'\n")
                f.write("else\n")
                f.write("    ./output/scripts/archive_duplicates.sh\n")
                f.write("fi\n")
            # Don't run reorganize_files.sh - use safe_reorganize.py instead
            f.write("\n# For file reorganization, use: python3 safe_reorganize.py --execute\n")
            
            f.write("\necho 'All fixes applied!'\n")
        
        script_path.chmod(0o755)
        print(f"  Created: {script_path}")
        
        print("\n📋 Recommendations:")
        for rec in self.fixes["recommendations"][:5]:
            print(f"  [{rec['priority'].upper()}] {rec['issue']}")
            print(f"    → {rec['action']}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fix Generator - Generates fixes for template SSOT issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Generate all fixes
  %(prog)s --scoped                    # Use line-scoped replacements
  %(prog)s --critical-only             # Only generate critical fixes
  %(prog)s --dry-run                   # Generate but don't save scripts
  %(prog)s --report-dir reports/       # Save to timestamped directory
        """
    )
    
    parser.add_argument(
        '--scoped', '-s',
        action='store_true',
        help='Enable scoped replacements (only replace within markdown links)'
    )
    parser.add_argument(
        '--report-dir', '-d',
        type=Path,
        help='Directory for timestamped reports (e.g., reports/2024-01-01-12-00)'
    )
    parser.add_argument(
        '--critical-only',
        action='store_true',
        help='Only generate fixes for critical issues (broken refs, circular deps)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate analysis but don\'t save shell scripts'
    )
    parser.add_argument(
        '--max-fixes',
        type=int,
        help='Maximum number of fixes to generate per category',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.1.0'
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print(f"Template Fix Generator v1.1.0")
        print(f"=" * 50)
        if args.scoped:
            print("  Mode: Scoped replacements enabled")
        if args.critical_only:
            print("  Filter: Critical fixes only")
        if args.dry_run:
            print("  Mode: Dry run (no scripts saved)")
        print()
    
    # Track timing
    start_time = time.time()
    
    # Create timestamped report directory if requested
    report_dir = None
    if args.report_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = args.report_dir / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        if not args.quiet:
            print(f"Report directory: {report_dir}")
    
    generator = FixGenerator(
        scoped_replacements=args.scoped,
        report_dir=str(report_dir) if report_dir else None
    )
    
    # Override methods for filtering if needed
    if args.critical_only:
        original_gen_recs = generator._generate_recommendations
        def filtered_recs():
            original_gen_recs()
            generator.fixes["recommendations"] = [
                r for r in generator.fixes["recommendations"] 
                if r["priority"] == "high"
            ]
        generator._generate_recommendations = filtered_recs
    
    if args.max_fixes:
        # Limit fixes per category
        original_save = generator._save_fixes
        def limited_save():
            for key in ["broken_references", "duplicate_removals", "file_moves"]:
                if key in generator.fixes:
                    generator.fixes[key] = generator.fixes[key][:args.max_fixes]
            original_save()
        generator._save_fixes = limited_save
    
    if args.dry_run:
        # Skip script generation
        generator._generate_shell_scripts = lambda: None
    
    duration = time.time() - start_time
    fixes = generator.generate_fixes(duration)
    
    # Save to report directory if specified
    if report_dir and fixes:
        import shutil
        # Copy all generated files from output/ to report directory
        output_dir = Path("output")
        for file in ["data/fix_recommendations.json", "scripts/apply_reference_fixes.py", 
                    "scripts/archive_duplicates.sh", "scripts/apply_all_fixes.sh"]:
            source_file = output_dir / file
            if source_file.exists():
                shutil.copy(source_file, report_dir / file)
        
        if not args.quiet:
            print(f"\nAll files copied to: {report_dir}")
    
    if fixes and not args.quiet:
        print(f"\n{'=' * 50}")
        print(f"Fix generation complete!")
        print(f"\nNext steps:")
        print(f"  1. Review fix_recommendations.json")
        print(f"  2. Backup your templates directory")
        if not args.dry_run:
            print(f"  3. Run ./output/scripts/apply_all_fixes.sh (or individual scripts)")
        print(f"  4. Test the system after applying fixes")


if __name__ == "__main__":
    main()
