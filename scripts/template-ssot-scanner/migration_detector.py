#!/usr/bin/env python3
"""
Migration Status Detector
Properly identifies files that have been successfully migrated to modular structure
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scan_metadata import save_with_metadata

class MigrationDetector:
    """Detects true migration status of template files"""
    
    # Migration status markers to look for
    MIGRATION_MARKERS = [
        r"Status.*:.*✅.*MODULARIZED",
        r"Migration Complete",
        r"MODULARIZED.*All.*extracted to",
        r"This file now serves as an index",
        r"Migration Date",
        r"PATTERNS MODULARIZED",
        r"WORKFLOWS MODULARIZED",
        r"BEHAVIORS MODULARIZED",
        r"HANDLERS MODULARIZED",
        r"modular.*system.*complete"
    ]
    
    # Files known to be monolithic that should be checked
    MONOLITHIC_FILES = [
        "templates/REGISTRY.md",
        "templates/WORKFLOWS.md", 
        "templates/PATTERNS.md",
        "templates/HANDLERS.md",
        "templates/CONVENTIONS.md",
        "templates/BEHAVIORS.md",
        "templates/MATRICES.md",
        "templates/TOOLS.md",
        "templates/USER-GUIDE.md",
        "templates/BUILDING-BETTER.md",
        "templates/PROJECT-BLOG.md"
    ]
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.results = {
            "scan_timestamp": datetime.now().isoformat(),
            "files_analyzed": 0,
            "migration_status": {},
            "summary": {
                "fully_migrated": [],
                "partially_migrated": [],
                "not_migrated": [],
                "already_modular": []
            }
        }
        
    def detect_all(self) -> Dict:
        """Run detection on all monolithic files and return API-compliant format"""
        # Build migration_status dict in the exact API shape
        migration_status = {}
        
        for file_path in self.MONOLITHIC_FILES:
            full_path = self.base_path / file_path
            if full_path.exists():
                status = self._detect_file_status(full_path)
                migration_status[file_path] = status
                self.results["files_analyzed"] += 1
                
                # Categorize for summary
                if status["status"] == "FULLY_MIGRATED":
                    self.results["summary"]["fully_migrated"].append(file_path)
                elif status["status"] == "PARTIALLY_MIGRATED":
                    self.results["summary"]["partially_migrated"].append(file_path)
                elif status["status"] == "NOT_MIGRATED":
                    self.results["summary"]["not_migrated"].append(file_path)
        
        # Store in API format
        self.results["migration_status"] = migration_status
        return migration_status
        
    def _detect_file_status(self, file_path: Path) -> Dict:
        """Detect migration status of a single file per developer specifications"""
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        # Initialize result per API shape
        result = {
            "status": "NOT_MIGRATED",
            "markers": [],
            "link_ratio": 0.0,
            "nonempty_lines": 0,
            "modular_files": 0,
            "reason": "detector"
        }
        
        # Signal 1: Check for explicit markers
        for marker_pattern in self.MIGRATION_MARKERS:
            if re.search(marker_pattern, content, re.IGNORECASE | re.MULTILINE):
                result["markers"].append(marker_pattern)
        
        # Signal 2: Calculate link-to-content ratio
        # Count non-empty, non-header lines
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        result["nonempty_lines"] = len(non_empty_lines)
        
        if non_empty_lines:
            # Count lines that contain markdown links
            link_lines = [line for line in non_empty_lines if re.search(r'\[.*\]\(.*\)', line)]
            result["link_ratio"] = len(link_lines) / len(non_empty_lines)
        
        # Signal 3: Check for matching modular directory
        file_stem = file_path.stem.lower()
        possible_dirs = [
            file_path.parent / file_stem,
            file_path.parent / f"{file_stem}s",  # pluralized
            file_path.parent / file_stem.rstrip('s')  # singularized
        ]
        
        for dir_path in possible_dirs:
            if dir_path.exists() and dir_path.is_dir():
                # Count .md files in subdirectory
                md_files = list(dir_path.rglob("*.md"))
                result["modular_files"] = len(md_files)
                break
        
        # Apply decision logic per developer specs
        has_markers = len(result["markers"]) > 0
        has_structure = (result["link_ratio"] >= 0.6 and result["nonempty_lines"] <= 120)
        has_modular_dir = result["modular_files"] >= 1
        
        if has_markers or (has_structure and has_modular_dir):
            result["status"] = "FULLY_MIGRATED"
        elif has_modular_dir and result["modular_files"] > 0:
            # Has some modular content but doesn't meet full migration criteria
            result["status"] = "PARTIALLY_MIGRATED"
        else:
            result["status"] = "NOT_MIGRATED"
            
        return result
    
    def generate_manifest(self, output_path: Path) -> None:
        """Generate migration manifest file with only computed fields"""
        manifest = {
            "generated": datetime.now().isoformat(),
            "migration_tracking": {},
            "recommended_actions": []
        }
        
        for file_path, status in self.results["migration_status"].items():
            # Only include fields we actually compute
            manifest["migration_tracking"][file_path] = {
                "status": status["status"],
                "markers": status.get("markers", []),
                "link_ratio": status.get("link_ratio", 0.0),
                "nonempty_lines": status.get("nonempty_lines", 0),
                "modular_files": status.get("modular_files", 0),
                "reason": status.get("reason", "detector")
            }
            
            # Add recommendations
            if status["status"] == "NOT_MIGRATED":
                manifest["recommended_actions"].append({
                    "file": file_path,
                    "action": "MIGRATE",
                    "priority": "HIGH"
                })
            elif status["status"] == "PARTIALLY_MIGRATED":
                manifest["recommended_actions"].append({
                    "file": file_path,
                    "action": "COMPLETE_MIGRATION",
                    "priority": "MEDIUM"
                })
                
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def print_summary(self) -> None:
        """Print summary of migration detection"""
        print("\n" + "=" * 60)
        print("MIGRATION STATUS DETECTION SUMMARY")
        print("=" * 60)
        
        print(f"\n📊 Files Analyzed: {self.results['files_analyzed']}")
        
        print(f"\n✅ Fully Migrated ({len(self.results['summary']['fully_migrated'])}):")
        for file in self.results['summary']['fully_migrated']:
            status = self.results['migration_status'][file]
            print(f"  - {file}")
            if status.get('markers'):
                print(f"    Markers: {', '.join(status['markers'][:2])}")
            print(f"    Lines: {status['nonempty_lines']} (link ratio: {status['link_ratio']:.2f})")
            print(f"    Modular files: {status['modular_files']}")
            
        print(f"\n⚠️  Partially Migrated ({len(self.results['summary']['partially_migrated'])}):")
        for file in self.results['summary']['partially_migrated']:
            status = self.results['migration_status'][file]
            print(f"  - {file}")
            print(f"    Lines: {status['nonempty_lines']}")
            print(f"    Modular files: {status['modular_files']}")
                
        print(f"\n❌ Not Migrated ({len(self.results['summary']['not_migrated'])}):")
        for file in self.results['summary']['not_migrated']:
            status = self.results['migration_status'][file]
            print(f"  - {file}")
            print(f"    Lines: {status['nonempty_lines']}")
            
        # Calculate true migration percentage
        total = self.results['files_analyzed']
        if total > 0:
            fully_migrated_pct = (len(self.results['summary']['fully_migrated']) / total) * 100
            partially_migrated_pct = (len(self.results['summary']['partially_migrated']) / total) * 100
            
            print(f"\n📈 True Migration Status:")
            print(f"  Fully Migrated: {fully_migrated_pct:.1f}%")
            print(f"  Partially Migrated: {partially_migrated_pct:.1f}%")
            print(f"  Not Migrated: {100 - fully_migrated_pct - partially_migrated_pct:.1f}%")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Detect true migration status of template files"
    )
    parser.add_argument(
        '--base', '-b',
        type=Path,
        help='Base directory (default: auto-detect)',
        default=None
    )
    parser.add_argument(
        '--manifest', '-m',
        action='store_true',
        help='Generate migration manifest file'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Determine base path
    if args.base:
        base_path = args.base
    else:
        # Try to find project root
        current = Path.cwd()
        while current != current.parent:
            if (current / "templates").exists():
                base_path = current
                break
            current = current.parent
        else:
            base_path = Path.cwd()
    
    print(f"Migration Status Detector v1.0.0")
    print(f"Base path: {base_path}")
    
    # Track timing
    start_time = time.time()
    
    detector = MigrationDetector(base_path)
    migration_status = detector.detect_all()  # Returns API-shaped dict
    
    # Calculate duration
    duration = time.time() - start_time
    
    if args.json:
        print(json.dumps(migration_status, indent=2))
    else:
        detector.print_summary()
    
    # Prepare statistics for metadata
    stats = {
        "files_scanned": len(migration_status.get("files", {})),
        "fully_migrated": len(migration_status.get("fully_migrated", [])),
        "pending_migration": len(migration_status.get("pending_migration", [])),
        "base_path": str(base_path)
    }
    
    # Save results with metadata
    output_dir = Path("output/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    save_with_metadata(
        data=migration_status,
        output_file=output_dir / "migration_status.json",
        scanner_name="migration_detector",
        version="1.0.0",
        stats=stats,
        duration_seconds=duration
    )
    print(f"\nResults saved to: {output_dir / 'migration_status.json'}")
    
    if args.manifest:
        manifest_path = output_dir / "migration_manifest.json"
        detector.generate_manifest(manifest_path)
        print(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()