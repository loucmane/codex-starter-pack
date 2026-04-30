#!/usr/bin/env python3
"""
Duplicate Content Finder
Compares monolithic vs modular template files to find duplicates and track migration progress
"""

import argparse
import difflib
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
from scan_metadata import save_with_metadata, load_with_metadata

class DuplicateFinder:
    """Finds duplicate content between monolithic and modular template files"""
    
    def __init__(self, scan_results_file: str = "output/data/template_scan_results.json",
                 section_matching: bool = False,
                 similarity_threshold: float = 0.7,
                 generate_diffs: bool = False):
        self.scan_results_file = scan_results_file
        self.results = None
        self.base_path = None
        self.section_matching = section_matching
        self.similarity_threshold = similarity_threshold
        self.generate_diffs = generate_diffs
        self.duplicates = {
            "content_duplicates": [],
            "partial_duplicates": [],
            "monolithic_files": {},
            "migration_status": {},
            "content_hashes": defaultdict(list),
            "section_mapping": [],
            "statistics": {}
        }
        
        # Define monolithic files to check
        self.monolithic_files = [
            "templates/REGISTRY.md",
            "templates/WORKFLOWS.md", 
            "templates/PATTERNS.md",
            "templates/HANDLERS.md",
            "templates/CONVENTIONS.md",
            "templates/BEHAVIORS.md",
            "templates/MATRICES.md",
            "templates/TOOLS.md"
        ]
    
    def load_scan_results(self) -> bool:
        """Load scan results from JSON file"""
        if not Path(self.scan_results_file).exists():
            print(f"Error: {self.scan_results_file} not found. Run scanner.py first.")
            return False
        
        data, metadata = load_with_metadata(Path(self.scan_results_file))
        if data is None:
            print(f"Error: Unable to load {self.scan_results_file}")
            return False
        self.results = data
        base_path_str = self.results.get("scan_metadata", {}).get("base_path")
        if not base_path_str:
            print("Warning: base_path missing from scan metadata; defaulting to current directory")
            self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path_str)
        return True
    
    def _load_migration_status(self) -> Dict:
        """Load migration status from detector if available"""
        migration_file = Path("output/data/migration_status.json")
        if migration_file.exists():
            print("Loading migration status from detector...")
            data, _ = load_with_metadata(migration_file)
            if isinstance(data, dict):
                return data
            print("Warning: migration status file did not contain a JSON object")
        else:
            print("No migration detector results found, using similarity-based detection")
        return {}
    
    def analyze(self) -> Dict:
        """Main analysis method"""
        if not self.load_scan_results():
            return {}
        
        # Load migration status from detector (if available)
        migration_status = self._load_migration_status()
        
        print(f"Finding duplicates and analyzing migration status...")
        
        # Analyze monolithic files
        self._analyze_monolithic_files()
        
        # Find exact content duplicates
        self._find_exact_duplicates()
        
        # Find partial/section duplicates (skip for FULLY_MIGRATED files)
        self._find_partial_duplicates(migration_status)
        
        # Calculate migration status (use detector results where available)
        self._calculate_migration_status(migration_status)
        
        # Generate statistics
        self._generate_statistics()
        
        # Save results
        self._save_results()
        
        return self.duplicates
    
    def _analyze_monolithic_files(self) -> None:
        """Analyze content of monolithic files"""
        print("Analyzing monolithic files...")
        
        for mono_file in self.monolithic_files:
            if mono_file not in self.results["files"]:
                print(f"  Warning: {mono_file} not found in scan results")
                continue
            
            file_path = self.base_path / mono_file
            if not file_path.exists():
                continue
            
            content = file_path.read_text(encoding='utf-8')
            sections = self._extract_sections(content)
            
            self.duplicates["monolithic_files"][mono_file] = {
                "line_count": len(content.splitlines()),
                "section_count": len(sections),
                "sections": list(sections.keys()),
                "content_hash": hashlib.md5(content.encode()).hexdigest()
            }
            
            print(f"  {mono_file}: {len(sections)} sections")
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.splitlines():
            # Check for section headers
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line[3:].strip()
                current_content = [line]
            elif line.startswith('# ') and not current_section:
                # Top-level header
                current_section = "header"
                current_content = [line]
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _find_exact_duplicates(self) -> None:
        """Find files with exact duplicate content"""
        print("Finding exact content duplicates...")
        
        # Calculate content hashes for all files
        for file_path, file_info in self.results["files"].items():
            if file_path in self.monolithic_files:
                continue  # Skip monolithic files
            
            full_path = self.base_path / file_path
            if not full_path.exists():
                continue
            
            try:
                content = full_path.read_text(encoding='utf-8')
                # Normalize whitespace for comparison
                normalized = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
                content_hash = hashlib.md5(normalized.encode()).hexdigest()
                
                self.duplicates["content_hashes"][content_hash].append({
                    "file": file_path,
                    "line_count": file_info["line_count"],
                    "type": file_info.get("type", "unknown")
                })
            except Exception as e:
                print(f"  Error processing {file_path}: {e}")
        
        # Find duplicates (same hash, multiple files)
        for content_hash, files in self.duplicates["content_hashes"].items():
            if len(files) > 1:
                self.duplicates["content_duplicates"].append({
                    "hash": content_hash,
                    "files": files,
                    "duplicate_count": len(files)
                })
        
        # Sort by duplicate count
        self.duplicates["content_duplicates"].sort(
            key=lambda x: x["duplicate_count"],
            reverse=True
        )
    
    def _find_partial_duplicates(self, migration_status: Dict) -> None:
        """Find partial content matches between monolithic and modular files"""
        print("Finding partial duplicates and section mappings...")
        
        for mono_file in self.monolithic_files:
            # Skip if file is FULLY_MIGRATED according to detector
            if mono_file in migration_status:
                if migration_status[mono_file].get("status") == "FULLY_MIGRATED":
                    print(f"  Skipping {mono_file} - marked as FULLY_MIGRATED by detector")
                    continue
            
            if mono_file not in self.results["files"]:
                continue
            
            mono_path = self.base_path / mono_file
            if not mono_path.exists():
                continue
            
            mono_content = mono_path.read_text(encoding='utf-8')
            mono_sections = self._extract_sections(mono_content)
            
            # Check each modular file for matches
            for file_path, file_info in self.results["files"].items():
                if file_path in self.monolithic_files:
                    continue
                
                # Focus on related files (similar names/paths)
                if not self._is_related_file(mono_file, file_path):
                    continue
                
                modular_path = self.base_path / file_path
                if not modular_path.exists():
                    continue
                
                try:
                    modular_content = modular_path.read_text(encoding='utf-8')
                    
                    # Check for section matches
                    for section_name, section_content in mono_sections.items():
                        if self.section_matching:
                            # Section-to-section matching for more granular comparison
                            modular_sections = self._extract_sections(modular_content)
                            for mod_section_name, mod_section_content in modular_sections.items():
                                similarity = self._calculate_similarity(section_content, mod_section_content)
                                if similarity > self.similarity_threshold:
                                    mapping_info = {
                                        "monolithic_file": mono_file,
                                        "monolithic_section": section_name,
                                        "modular_file": file_path,
                                        "modular_section": mod_section_name,
                                        "similarity": round(similarity, 3),
                                        "monolithic_lines": len(section_content.splitlines()),
                                        "modular_lines": len(mod_section_content.splitlines())
                                    }
                                    if self.generate_diffs:
                                        mapping_info["diff_snippet"] = self._generate_diff_snippet(
                                            section_content, mod_section_content, max_lines=5
                                        )
                                    self.duplicates["section_mapping"].append(mapping_info)
                        else:
                            # Original file-level matching
                            similarity = self._calculate_similarity(section_content, modular_content)
                            
                            if similarity > self.similarity_threshold:
                                mapping_info = {
                                    "monolithic_file": mono_file,
                                    "monolithic_section": section_name,
                                    "modular_file": file_path,
                                    "similarity": round(similarity, 3),
                                    "monolithic_lines": len(section_content.splitlines()),
                                    "modular_lines": len(modular_content.splitlines())
                                }
                                if self.generate_diffs and similarity > 0.8:  # Only for high similarity
                                    mapping_info["diff_snippet"] = self._generate_diff_snippet(
                                        section_content, modular_content, max_lines=5
                                    )
                                self.duplicates["section_mapping"].append(mapping_info)
                    
                    # Check overall similarity
                    overall_similarity = self._calculate_similarity(mono_content, modular_content)
                    if overall_similarity > 0.3:  # 30% threshold for partial match
                        partial_info = {
                            "monolithic_file": mono_file,
                            "modular_file": file_path,
                            "similarity": round(overall_similarity, 3)
                        }
                        if self.generate_diffs and overall_similarity > 0.7:  # Only for higher similarity
                            partial_info["diff_snippet"] = self._generate_diff_snippet(
                                mono_content, modular_content, max_lines=10
                            )
                        self.duplicates["partial_duplicates"].append(partial_info)
                
                except Exception as e:
                    print(f"  Error comparing {mono_file} with {file_path}: {e}")
        
        # Sort by similarity
        self.duplicates["section_mapping"].sort(
            key=lambda x: x["similarity"],
            reverse=True
        )
        self.duplicates["partial_duplicates"].sort(
            key=lambda x: x["similarity"],
            reverse=True
        )
    
    def _is_related_file(self, mono_file: str, modular_file: str) -> bool:
        """Check if modular file is likely related to monolithic file"""
        mono_name = Path(mono_file).stem.lower()
        modular_path = modular_file.lower()
        
        # Check for keyword matches
        keywords_map = {
            "registry": ["registry", "index"],
            "workflows": ["workflow", "flow"],
            "patterns": ["pattern"],
            "handlers": ["handler", "trigger", "orchestrator", "operator"],
            "conventions": ["convention", "standard", "style"],
            "behaviors": ["behavior", "behaviour"],
            "matrices": ["matrix", "matrices", "mapping"],
            "tools": ["tool"]
        }
        
        keywords = keywords_map.get(mono_name, [mono_name])
        return any(keyword in modular_path for keyword in keywords)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Normalize texts
        lines1 = [line.strip() for line in text1.splitlines() if line.strip()]
        lines2 = [line.strip() for line in text2.splitlines() if line.strip()]
        
        if not lines1 or not lines2:
            return 0.0
        
        # Use difflib to calculate similarity
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        return matcher.ratio()
    
    def _generate_diff_snippet(self, text1: str, text2: str, max_lines: int = 10) -> str:
        """Generate a diff snippet showing differences between two texts"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Generate unified diff
        diff = difflib.unified_diff(
            lines1[:max_lines],
            lines2[:max_lines],
            lineterm='',
            n=2  # Context lines
        )
        
        diff_lines = list(diff)
        if len(diff_lines) > max_lines * 2:
            diff_lines = diff_lines[:max_lines * 2] + ['... (truncated)']
        
        return '\n'.join(diff_lines) if diff_lines else 'No differences in first {} lines'.format(max_lines)
    
    def _calculate_migration_status(self, migration_status: Dict) -> None:
        """Calculate migration progress for each monolithic file"""
        print("Calculating migration status...")
        
        for mono_file in self.monolithic_files:
            # Use detector results if available
            if mono_file in migration_status:
                detector_status = migration_status[mono_file]
                if detector_status["status"] == "FULLY_MIGRATED":
                    # Use detector results for FULLY_MIGRATED files
                    self.duplicates["migration_status"][mono_file] = {
                        "migration_percentage": 100.0,
                        "migrated_sections": "ALL",
                        "total_sections": "ALL",
                        "status": "FULLY_MIGRATED",
                        "reason": "detector",
                        "markers": detector_status.get("markers", []),
                        "link_ratio": detector_status.get("link_ratio", 0),
                        "nonempty_lines": detector_status.get("nonempty_lines", 0),
                        "modular_files": detector_status.get("modular_files", 0)
                    }
                    continue
                elif detector_status["status"] == "PARTIALLY_MIGRATED":
                    # For partially migrated, still use similarity but note detector status
                    pass  # Continue with similarity-based calculation
            
            if mono_file not in self.duplicates["monolithic_files"]:
                continue
            
            # Count migrated sections (for NOT_MIGRATED or PARTIALLY_MIGRATED)
            migrated_sections = set()
            for mapping in self.duplicates["section_mapping"]:
                if mapping["monolithic_file"] == mono_file:
                    migrated_sections.add(mapping["monolithic_section"])
            
            total_sections = len(self.duplicates["monolithic_files"][mono_file]["sections"])
            migrated_count = len(migrated_sections)
            
            # Count related modular files
            related_files = set()
            for mapping in self.duplicates["section_mapping"]:
                if mapping["monolithic_file"] == mono_file:
                    related_files.add(mapping["modular_file"])
            
            self.duplicates["migration_status"][mono_file] = {
                "total_sections": total_sections,
                "migrated_sections": migrated_count,
                "migration_percentage": round(migrated_count / total_sections * 100, 1) if total_sections > 0 else 0,
                "migrated_section_names": list(migrated_sections),
                "related_modular_files": list(related_files),
                "related_file_count": len(related_files),
                "status": "PARTIALLY_MIGRATED" if migrated_count > 0 else "NOT_MIGRATED",
                "reason": "similarity"
            }
    
    def _generate_statistics(self) -> None:
        """Generate overall statistics"""
        print("Generating statistics...")
        
        total_files = len(self.results["files"])
        monolithic_count = len(self.monolithic_files)
        modular_count = total_files - monolithic_count
        
        # Calculate total migration percentage
        total_migration = 0
        if self.duplicates["migration_status"]:
            total_migration = sum(
                status["migration_percentage"]
                for status in self.duplicates["migration_status"].values()
            ) / len(self.duplicates["migration_status"])
        
        self.duplicates["statistics"] = {
            "total_files_scanned": total_files,
            "monolithic_files": monolithic_count,
            "modular_files": modular_count,
            "exact_duplicate_groups": len(self.duplicates["content_duplicates"]),
            "partial_duplicate_pairs": len(self.duplicates["partial_duplicates"]),
            "section_mappings": len(self.duplicates["section_mapping"]),
            "overall_migration_percentage": round(total_migration, 1),
            "files_with_duplicates": sum(
                len(group["files"]) for group in self.duplicates["content_duplicates"]
            )
        }
    
    def _save_results(self) -> None:
        """Save analysis results"""
        output_file = Path("output/data/duplicate_analysis.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.duplicates, f, indent=2)
        
        print(f"\n✅ Duplicate analysis complete!")
        print(f"  Exact duplicate groups: {self.duplicates['statistics']['exact_duplicate_groups']}")
        print(f"  Partial duplicates: {self.duplicates['statistics']['partial_duplicate_pairs']}")
        print(f"  Section mappings: {self.duplicates['statistics']['section_mappings']}")
        print(f"  Overall migration: {self.duplicates['statistics']['overall_migration_percentage']}%")
        print(f"  Results saved to: {output_file}")
        
        # Print migration summary
        print("\n📊 Migration Status:")
        for mono_file, status in self.duplicates["migration_status"].items():
            file_name = Path(mono_file).name
            print(f"  {file_name}: {status['migration_percentage']}% migrated")
            print(f"    - {status['migrated_sections']}/{status['total_sections']} sections")
            # Only print related file count if it exists (not for FULLY_MIGRATED from detector)
            if 'related_file_count' in status:
                print(f"    - {status['related_file_count']} related modular files")
            elif status.get('status') == 'FULLY_MIGRATED':
                print(f"    - FULLY MIGRATED (detector confirmed)")
        
        # Print top duplicates
        if self.duplicates["content_duplicates"]:
            print("\n⚠️  Top exact duplicates:")
            for group in self.duplicates["content_duplicates"][:3]:
                print(f"  {group['duplicate_count']} files with identical content:")
                for file_info in group["files"][:3]:
                    print(f"    - {file_info['file']}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Duplicate Content Finder - Identifies duplicate content across templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Basic duplicate detection
  %(prog)s --section-matching          # Compare section by section
  %(prog)s --threshold 0.9             # Only flag >90%% similar as duplicates
  %(prog)s --migration-threshold 80    # Exit error if migration <80%% complete
  %(prog)s --quiet                     # Suppress output for automation
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=Path,
        help='Input scan results file (default: output/data/template_scan_results.json)',
        default='output/data/template_scan_results.json'
    )
    parser.add_argument(
        '--out', '-o',
        type=Path,
        help='Output analysis file (default: output/data/duplicate_analysis.json)',
        default='output/data/duplicate_analysis.json'
    )
    parser.add_argument(
        '--section-matching', '-s',
        action='store_true',
        help='Enable section-by-section comparison for more granular matching'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        help='Similarity threshold for duplicates (0.0-1.0, default: 0.7)',
        default=0.7
    )
    parser.add_argument(
        '--migration-threshold',
        type=int,
        help='Exit with error if migration percentage is below this',
        default=None
    )
    parser.add_argument(
        '--duplicate-threshold',
        type=int,
        help='Exit with error if duplicate count exceeds this',
        default=None
    )
    parser.add_argument(
        '--generate-diffs', '-d',
        action='store_true',
        help='Generate diff snippets for high-similarity duplicates'
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
        print(f"Template Duplicate Finder v1.1.0")
        print(f"=" * 50)
        if args.section_matching:
            print(f"  Mode: Section-by-section matching enabled")
        print(f"  Similarity threshold: {args.threshold}")
        print()
    
    # Track timing
    start_time = time.time()
    
    finder = DuplicateFinder(
        str(args.input),
        section_matching=args.section_matching,
        similarity_threshold=args.threshold,
        generate_diffs=args.generate_diffs
    )
    
    # Suppress output if quiet mode
    if args.quiet:
        # Monkey-patch print functions
        original_print = print
        finder.print = lambda *args, **kwargs: None
        import builtins
        builtins.print = lambda *args, **kwargs: None if not str(args[0]).startswith('\u274c') else original_print(*args, **kwargs)
    
    duplicates = finder.analyze()
    duration = time.time() - start_time
    
    # Prepare statistics
    if duplicates:
        stats = {
            "total_duplicates": len(duplicates.get("duplicates", [])),
            "migration_pending": len(duplicates.get("migration_status", {}).get("pending_migration", [])),
            "fully_migrated": len(duplicates.get("migration_status", {}).get("fully_migrated", [])),
            "migration_progress_percent": duplicates.get("statistics", {}).get("migration_progress", 0),
            "section_matching": args.section_matching,
            "similarity_threshold": args.threshold
        }
        
        # Save with metadata
        save_with_metadata(
            data=duplicates,
            output_file=args.out,
            scanner_name="duplicate_finder",
            version="1.1.0",
            stats=stats,
            duration_seconds=duration
        )
        if not args.quiet:
            print(f"Results saved to: {args.out}")
    
    if duplicates:
        # Check thresholds for CI/CD
        exit_code = 0
        
        if args.migration_threshold is not None:
            migration_pct = duplicates['statistics'].get('overall_migration_percentage', 0)
            if migration_pct < args.migration_threshold:
                print(f"\n❌ ERROR: Migration ({migration_pct}%) below threshold ({args.migration_threshold}%)")
                exit_code = 1
        
        if args.duplicate_threshold is not None:
            dup_count = duplicates['statistics'].get('files_with_duplicates', 0)
            if dup_count > args.duplicate_threshold:
                print(f"\n❌ ERROR: Duplicates ({dup_count}) exceed threshold ({args.duplicate_threshold})")
                exit_code = 1
        
        if exit_code != 0:
            sys.exit(exit_code)
        
        if not args.quiet:
            print(f"\n{'=' * 50}")
            print(f"Analysis complete. Use generate_fixes.py to create fix scripts.")


if __name__ == "__main__":
    main()
