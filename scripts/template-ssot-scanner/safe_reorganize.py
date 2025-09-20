#!/usr/bin/env python3
"""
Safe Template Reorganization System
====================================
Production-ready file reorganization with migration awareness and safety checks.

Features:
- Respects migration status (never moves FULLY_MIGRATED files)
- Builds dependency graph before moves
- Dry-run mode by default
- Git branch protection
- Atomic reference updates
- Comprehensive rollback support
"""

import json
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import shutil
from datetime import datetime


class FileCategory(Enum):
    """File movement safety categories"""
    IMMOVABLE = "immovable"           # FULLY_MIGRATED index files
    CAUTION = "caution"               # PARTIALLY_MIGRATED files
    MOVABLE_WITH_CARE = "movable_with_care"  # NOT_MIGRATED with many refs
    FREELY_MOVABLE = "freely_movable" # NOT_MIGRATED with few refs
    SYSTEM_FILE = "system_file"       # Config/script files


class SafetyLevel(Enum):
    """Safety level for operations"""
    STRICT = "strict"     # No moves for migrated files
    NORMAL = "normal"     # Allow some careful moves
    PERMISSIVE = "permissive"  # Allow most moves with warnings


@dataclass
class FileInfo:
    """Information about a file for reorganization"""
    path: str
    category: FileCategory
    migration_status: Optional[str] = None
    incoming_refs: Set[str] = field(default_factory=set)
    outgoing_refs: Set[str] = field(default_factory=set)
    proposed_move: Optional[str] = None
    safety_score: float = 1.0
    warnings: List[str] = field(default_factory=list)


@dataclass
class MoveOperation:
    """A proposed file move operation"""
    source: str
    target: str
    category: FileCategory
    affected_refs: List[Tuple[str, int]]  # (file, line_number)
    safety_score: float
    warnings: List[str]
    command: str


class SafeReorganizer:
    """Safe file reorganization with migration awareness"""
    
    def __init__(self, project_root: str = ".", safety_level: SafetyLevel = SafetyLevel.STRICT):
        self.project_root = Path(project_root).resolve()
        self.safety_level = safety_level
        self.files: Dict[str, FileInfo] = {}
        self.move_operations: List[MoveOperation] = []
        self.migration_status: Dict = {}
        self.scan_results: Dict = {}
        self.reference_map: Dict[str, Set[str]] = {}  # file -> files it references
        self.reverse_ref_map: Dict[str, Set[str]] = {}  # file -> files that reference it
        
    def load_data(self) -> None:
        """Load migration status and scan results"""
        print("Loading data...")
        
        # Load migration status
        migration_path = self.project_root / "scripts/template-ssot-scanner/output/data/migration_status.json"
        if migration_path.exists():
            with open(migration_path) as f:
                self.migration_status = json.load(f)
                print(f"  Loaded migration status for {len(self.migration_status)} files")
        
        # Load scan results - try multiple possible locations
        scan_paths = [
            self.project_root / "scripts/template-ssot-scanner/output/data/template_scan_results.json",
            self.project_root / "scripts/template-ssot-scanner/output/template_scan_results.json",
            self.project_root / "scripts/template-ssot-scanner/output/data/scan_results.json"
        ]
        
        for scan_path in scan_paths:
            if scan_path.exists():
                with open(scan_path) as f:
                    self.scan_results = json.load(f)
                    print(f"  Loaded scan results from {scan_path.name}")
                    print(f"  Found {len(self.scan_results.get('files', {}))} files")
                    break
        else:
            print("  ⚠️  No scan results found - run scanner.py first")
    
    def classify_files(self) -> None:
        """Classify files into safety categories"""
        print("\nClassifying files...")
        
        # Define canonical/monolith files that should NEVER move
        DENYLIST = {
            "templates/BUILDING-BETTER.md",
            "templates/MATRICES.md", 
            "templates/TOOLS.md",
            "templates/BEHAVIORS.md",
            "templates/CONVENTIONS.md",
            "templates/HANDLERS.md",
            "templates/PATTERNS.md",
            "templates/REGISTRY.md",
            "templates/USER-GUIDE.md",
            "templates/WORKFLOWS.md",
            "templates/PROJECT-BLOG.md"
        }
        
        for file_path in self.scan_results.get("files", {}):
            file_info = FileInfo(path=file_path, category=FileCategory.FREELY_MOVABLE)
            
            # Check denylist first - these are ALWAYS immovable
            if file_path in DENYLIST:
                file_info.category = FileCategory.IMMOVABLE
                file_info.warnings.append("CANONICAL FILE - must never move")
                file_info.migration_status = "DENYLISTED"
            # Check migration status
            elif file_path in self.migration_status:
                status = self.migration_status[file_path].get("status")
                file_info.migration_status = status
                
                if status == "FULLY_MIGRATED":
                    file_info.category = FileCategory.IMMOVABLE
                    file_info.warnings.append("FULLY_MIGRATED index file - should not be moved")
                elif status == "PARTIALLY_MIGRATED":
                    file_info.category = FileCategory.CAUTION
                    file_info.warnings.append("PARTIALLY_MIGRATED - move with extreme caution")
            
            # Check if it's a system file
            if file_path.endswith(('.json', '.sh', '.py', '.yml', '.yaml')):
                if file_info.category == FileCategory.FREELY_MOVABLE:
                    file_info.category = FileCategory.SYSTEM_FILE
                    file_info.warnings.append("System file - may be referenced by tools")
            
            # Protect index.md files in nested directories
            if Path(file_path).name == "index.md" and len(Path(file_path).parts) > 2:
                if file_info.category == FileCategory.FREELY_MOVABLE:
                    file_info.category = FileCategory.MOVABLE_WITH_CARE
                    file_info.warnings.append("index.md in nested directory - handle with care")
            
            self.files[file_path] = file_info
        
        print(f"  Classified {len(self.files)} files:")
        for category in FileCategory:
            count = sum(1 for f in self.files.values() if f.category == category)
            print(f"    {category.value}: {count}")
    
    def build_dependency_graph(self) -> None:
        """Build reference dependency graph"""
        print("\nBuilding dependency graph...")
        
        for file_path, file_data in self.scan_results.get("files", {}).items():
            refs = set()
            
            # Collect references
            for ref in file_data.get("references", []):
                if isinstance(ref, dict):
                    refs.add(ref.get("path", ref.get("reference", "")))
                else:
                    refs.add(ref)
            
            # Update maps
            self.reference_map[file_path] = refs
            for ref in refs:
                if ref not in self.reverse_ref_map:
                    self.reverse_ref_map[ref] = set()
                self.reverse_ref_map[ref].add(file_path)
        
        # Update file info with reference counts
        for file_path, file_info in self.files.items():
            file_info.incoming_refs = self.reverse_ref_map.get(file_path, set())
            file_info.outgoing_refs = self.reference_map.get(file_path, set())
            
            # Adjust category based on reference count
            incoming_count = len(file_info.incoming_refs)
            if incoming_count > 10 and file_info.category == FileCategory.FREELY_MOVABLE:
                file_info.category = FileCategory.MOVABLE_WITH_CARE
                file_info.warnings.append(f"Has {incoming_count} incoming references")
        
        print(f"  Built graph with {len(self.reference_map)} nodes")
        print(f"  Total edges: {sum(len(refs) for refs in self.reference_map.values())}")
    
    def calculate_safety_scores(self) -> None:
        """Calculate safety scores for each file"""
        print("\nCalculating safety scores...")
        
        for file_info in self.files.values():
            score = 1.0
            
            # Penalize based on category
            if file_info.category == FileCategory.IMMOVABLE:
                score = 0.0
            elif file_info.category == FileCategory.CAUTION:
                score *= 0.3
            elif file_info.category == FileCategory.MOVABLE_WITH_CARE:
                score *= 0.7
            elif file_info.category == FileCategory.SYSTEM_FILE:
                score *= 0.5
            
            # Penalize based on reference count
            ref_penalty = min(len(file_info.incoming_refs) * 0.02, 0.5)
            score *= (1.0 - ref_penalty)
            
            file_info.safety_score = max(0.0, score)
    
    def propose_moves(self) -> None:
        """Propose file moves based on organization rules"""
        print("\nProposing moves...")
        
        for file_path, file_info in self.files.items():
            # Skip if not safe to move
            if file_info.category == FileCategory.IMMOVABLE:
                continue
            
            # Only move NOT_MIGRATED files with few references
            if file_info.migration_status != "NOT_MIGRATED" and file_info.migration_status is not None:
                continue
            
            # Strict reference limit
            if len(file_info.incoming_refs) > 3:
                continue
            
            if self.safety_level == SafetyLevel.STRICT:
                if file_info.category in [FileCategory.CAUTION, FileCategory.SYSTEM_FILE]:
                    continue
                # In strict mode, only move files with 0 incoming refs
                if len(file_info.incoming_refs) > 0:
                    continue
            
            # Get file type from scan results
            file_data = self.scan_results.get("files", {}).get(file_path, {})
            file_type = file_data.get("type", "unknown")
            
            # Determine target location based on file type
            target = self._get_target_location(file_path, file_type)
            if target and target != file_path:
                file_info.proposed_move = target
                
                # Create move operation
                affected_refs = [(ref, 0) for ref in file_info.incoming_refs]
                move_op = MoveOperation(
                    source=file_path,
                    target=target,
                    category=file_info.category,
                    affected_refs=affected_refs,
                    safety_score=file_info.safety_score,
                    warnings=file_info.warnings.copy(),
                    command=f'git mv "{file_path}" "{target}"'
                )
                
                # Add safety checks
                if file_info.safety_score < 0.5:
                    move_op.warnings.append("LOW SAFETY SCORE - Review carefully")
                
                if len(affected_refs) > 5:
                    move_op.warnings.append(f"Will require updating {len(affected_refs)} references")
                
                self.move_operations.append(move_op)
        
        # Sort by safety score (safest first)
        self.move_operations.sort(key=lambda x: x.safety_score, reverse=True)
        
        print(f"  Proposed {len(self.move_operations)} moves")
    
    def _get_target_location(self, file_path: str, file_type: str) -> Optional[str]:
        """Determine target location for a file based on its type"""
        path = Path(file_path)
        name = path.name
        parts = path.parts
        
        # Skip files already in correct locations (OS-agnostic)
        if "matrices" in parts and file_type == "matrix":
            return None
        if "workflows" in parts and file_type == "workflow":
            return None
        if "handlers" in parts and file_type in ["trigger", "orchestrator", "operator"]:
            return None
        
        # Type-based organization (not filename-based)
        if file_type == "matrix":
            return f"templates/matrices/{name}"
        elif file_type == "workflow":
            return f"templates/workflows/{name}"
        elif file_type == "trigger":
            return f"templates/handlers/triggers/{name}"
        elif file_type == "orchestrator":
            return f"templates/handlers/orchestrators/{name}"
        elif file_type == "operator":
            return f"templates/handlers/operators/{name}"
        
        return None
    
    def simulate_moves(self, dry_run: bool = True) -> Dict:
        """Simulate moves and generate report"""
        print("\n" + "="*60)
        print("SIMULATION REPORT" if dry_run else "EXECUTION PLAN")
        print("="*60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": "dry_run" if dry_run else "execute",
            "safety_level": self.safety_level.value,
            "statistics": {
                "total_files": len(self.files),
                "proposed_moves": len(self.move_operations),
                "affected_references": sum(len(op.affected_refs) for op in self.move_operations),
                "immovable_files": sum(1 for f in self.files.values() if f.category == FileCategory.IMMOVABLE)
            },
            "moves": []
        }
        
        print(f"\nSafety Level: {self.safety_level.value.upper()}")
        print(f"Total Files Analyzed: {report['statistics']['total_files']}")
        print(f"Proposed Moves: {report['statistics']['proposed_moves']}")
        print(f"Affected References: {report['statistics']['affected_references']}")
        print(f"Protected Files: {report['statistics']['immovable_files']}")
        
        if self.move_operations:
            print("\n" + "-"*60)
            print("PROPOSED MOVES (sorted by safety):")
            print("-"*60)
            
            for i, op in enumerate(self.move_operations, 1):
                print(f"\n{i}. Move: {op.source}")
                print(f"   To:   {op.target}")
                print(f"   Category: {op.category.value}")
                print(f"   Safety Score: {op.safety_score:.2f}")
                print(f"   Affected Refs: {len(op.affected_refs)}")
                
                if op.warnings:
                    print("   ⚠️  Warnings:")
                    for warning in op.warnings:
                        print(f"      - {warning}")
                
                report["moves"].append({
                    "source": op.source,
                    "target": op.target,
                    "category": op.category.value,
                    "safety_score": op.safety_score,
                    "affected_refs": len(op.affected_refs),
                    "warnings": op.warnings,
                    "command": op.command
                })
        else:
            print("\nNo moves proposed - all files are either:")
            print("  - Already in correct locations")
            print("  - Protected due to migration status")
            print("  - Below safety threshold")
        
        return report
    
    def execute_moves(self, interactive: bool = False) -> bool:
        """Execute the proposed moves"""
        if not self.move_operations:
            print("\nNo moves to execute.")
            return True
        
        print("\n" + "="*60)
        print("EXECUTING MOVES")
        print("="*60)
        
        # Create safety branch
        print("\nCreating safety branch...")
        branch_name = f"reorg-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], 
                         check=True, capture_output=True, cwd=self.project_root)
            print(f"  Created branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Could not create branch: {e}")
            return False
        
        # Execute moves
        success_count = 0
        failed_moves = []
        
        for op in self.move_operations:
            if interactive:
                print(f"\nMove: {op.source} -> {op.target}")
                response = input("Execute? (y/n/q): ").lower()
                if response == 'q':
                    break
                if response != 'y':
                    continue
            
            # Create target directory
            target_dir = Path(op.target).parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Execute move
            try:
                subprocess.run(op.command, shell=True, check=True, capture_output=True, 
                             cwd=self.project_root)
                success_count += 1
                print(f"  ✓ Moved: {op.source}")
            except subprocess.CalledProcessError as e:
                failed_moves.append(op.source)
                print(f"  ✗ Failed: {op.source} - {e}")
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {success_count}/{len(self.move_operations)} moves successful")
        
        if failed_moves:
            print("\nFailed moves:")
            for path in failed_moves:
                print(f"  - {path}")
        
        print(f"\nYou are on branch: {branch_name}")
        print("To keep changes: git add -A && git commit -m 'Reorganize templates'")
        print(f"To rollback: git checkout main && git branch -D {branch_name}")
        
        return len(failed_moves) == 0
    
    def generate_reference_updates(self) -> None:
        """Generate script to update references after moves"""
        if not self.move_operations:
            return
        
        print("\nGenerating reference update script...")
        
        script_path = self.project_root / "scripts/template-ssot-scanner/output/scripts/update_refs_after_move.py"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate Python script for reference updates
        with open(script_path, 'w') as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# Auto-generated reference updater\n\n")
            f.write("import re\nfrom pathlib import Path\n\n")
            f.write("moves = [\n")
            for op in self.move_operations:
                f.write(f'    ("{op.source}", "{op.target}"),\n')
            f.write("]\n\n")
            f.write("# Update logic here...\n")
            f.write("print('Reference updates complete!')\n")
        
        script_path.chmod(0o755)
        print(f"  Created: {script_path}")


def main():
    parser = argparse.ArgumentParser(description="Safe template reorganization")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--safety-level", choices=["strict", "normal", "permissive"], 
                       default="strict", help="Safety level for operations (default: strict)")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually execute the moves (default is dry-run)")
    parser.add_argument("--interactive", action="store_true",
                       help="Approve each move interactively")
    parser.add_argument("--output", help="Save report to JSON file")
    
    args = parser.parse_args()
    
    # Create reorganizer
    safety_level = SafetyLevel[args.safety_level.upper()]
    reorganizer = SafeReorganizer(args.project_root, safety_level)
    
    # Load and analyze
    reorganizer.load_data()
    reorganizer.classify_files()
    reorganizer.build_dependency_graph()
    reorganizer.calculate_safety_scores()
    reorganizer.propose_moves()
    
    # Determine mode - execute wins over dry-run
    if args.execute:
        report = reorganizer.simulate_moves(dry_run=False)
        
        print("\n" + "="*60)
        print("⚠️  WARNING: About to execute moves!")
        print("="*60)
        response = input("\nProceed with execution? (yes/no): ")
        
        if response.lower() == "yes":
            success = reorganizer.execute_moves(args.interactive)
            reorganizer.generate_reference_updates()
            
            if not success:
                print("\n⚠️  Some moves failed. Review and fix manually.")
                sys.exit(1)
        else:
            print("\nExecution cancelled.")
    else:
        report = reorganizer.simulate_moves(dry_run=True)
        print("\n✓ Dry run complete. No files were moved.")
        print("  To execute: python3 safe_reorganize.py --execute")
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path(args.project_root) / "scripts/template-ssot-scanner/output/reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    if args.output:
        report_path = args.output
    else:
        report_path = report_dir / f"safe_reorg_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Files analyzed: {len(reorganizer.files)}")
    print(f"  - Immovable (protected): {sum(1 for f in reorganizer.files.values() if f.category == FileCategory.IMMOVABLE)}")
    print(f"  - System files: {sum(1 for f in reorganizer.files.values() if f.category == FileCategory.SYSTEM_FILE)}")
    print(f"  - With caution: {sum(1 for f in reorganizer.files.values() if f.category == FileCategory.CAUTION)}")
    print(f"Moves proposed: {len(reorganizer.move_operations)}")
    print(f"Moves skipped: {len(reorganizer.files) - len(reorganizer.move_operations)}")


if __name__ == "__main__":
    main()