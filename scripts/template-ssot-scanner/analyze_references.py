#!/usr/bin/env python3
"""
Reference Analyzer
Analyzes template references to find broken links and create dependency graphs
"""

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from scan_metadata import save_with_metadata, load_with_metadata
from validation_interface import finding_from_count, load_validation_rules

class ReferenceAnalyzer:
    """Analyzes references between template files"""
    
    def __init__(
        self,
        scan_results_file: str = "output/data/template_scan_results.json",
        config_file: str = "scanner_config.yaml",
        config_context=None,
        validation_rules: Dict | None = None,
        profile: str | None = None,
        environment: str | None = None,
        apply_environment_overrides: bool = False,
        environ: dict[str, str] | None = None,
    ):
        self.scan_results_file = scan_results_file
        self.config_context = config_context
        config_path = Path(config_file)
        if not config_path.is_absolute() and not config_path.exists():
            config_path = Path(__file__).parent / config_path
        self.config_file = str(config_path)
        if validation_rules is not None:
            self.validation_rules = validation_rules
        elif config_context is not None:
            self.validation_rules = config_context.validation_rules()
        else:
            self.validation_rules = load_validation_rules(
                config_path,
                profile=profile,
                environment=environment,
                apply_environment_overrides=apply_environment_overrides,
                environ=environ,
            )
        self.results = None
        self.base_path = None
        self.analysis = {
            "broken_references": [],
            "circular_dependencies": [],
            "dependency_graph": {},
            "reverse_dependencies": {},
            "orphaned_files": [],
            "most_referenced": [],
            "reference_stats": {},
            "duplicate_references": [],
            "monolith_reference_after_migration": [],  # New violation type
            "validation_findings": [],
        }
    
    def load_scan_results(self) -> bool:
        """Load scan results from JSON file"""
        if not Path(self.scan_results_file).exists():
            print(f"Error: {self.scan_results_file} not found. Run scanner.py first.")
            return False
        
        # Use load_with_metadata to handle both old and new formats
        data, metadata = load_with_metadata(Path(self.scan_results_file))
        if data is None:
            print(f"Error: Unable to load {self.scan_results_file}")
            return False
        self.results = data
        self.scan_metadata = metadata

        base_path_str = self.results.get("scan_metadata", {}).get("base_path")
        if not base_path_str:
            print("Warning: base_path missing from scan metadata; defaulting to current directory")
            self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path_str)
        return True
    
    def analyze(self) -> Dict:
        """Main analysis method"""
        import time
        start_time = time.time()
        
        if not self.load_scan_results():
            return {}
        
        # Load migration status to check for monolith references
        migration_status = self._load_migration_status()
        
        print(f"Analyzing references from {len(self.results['files'])} files...")
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Find broken references
        self._find_broken_references()
        
        # Check for references to migrated monoliths
        self._find_monolith_references_after_migration(migration_status)
        
        # Find circular dependencies
        self._find_circular_dependencies()
        
        # Find orphaned files
        self._find_orphaned_files()
        
        # Calculate reference statistics
        self._calculate_reference_stats()
        
        # Find duplicate references
        self._find_duplicate_references()

        # Generate configured severity findings
        self._generate_validation_findings()
        
        # Store duration for metadata
        self._duration = time.time() - start_time
        
        # Save analysis results
        self._save_analysis()
        
        return self.analysis
    
    def _load_migration_status(self) -> Dict:
        """Load migration status from detector if available"""
        migration_file = Path("output/data/migration_status.json")
        if migration_file.exists():
            print("Loading migration status for monolith reference checking...")
            data, _ = load_with_metadata(migration_file)
            if isinstance(data, dict):
                return data
            print("Warning: migration status file did not contain a JSON object")
        return {}
    
    def _build_dependency_graph(self) -> None:
        """Build dependency graph from references"""
        print("Building dependency graph...")
        
        for file_path, file_info in self.results["files"].items():
            references = file_info.get("references", [])
            
            # Forward dependencies (this file depends on these)
            self.analysis["dependency_graph"][file_path] = []
            
            for ref in references:
                # Normalize reference path
                normalized_ref = self._normalize_reference(ref, file_path)
                if normalized_ref:
                    self.analysis["dependency_graph"][file_path].append(normalized_ref)
                    
                    # Reverse dependencies (these files depend on this)
                    if normalized_ref not in self.analysis["reverse_dependencies"]:
                        self.analysis["reverse_dependencies"][normalized_ref] = []
                    self.analysis["reverse_dependencies"][normalized_ref].append(file_path)
    
    def _normalize_reference(self, ref: str, source_file: str) -> Optional[str]:
        """Normalize a reference path relative to source file"""
        # Handle absolute paths from project root
        if ref.startswith('templates/') or ref.startswith('.claude/') or ref.startswith('.codex/'):
            return ref
        
        # Handle relative paths
        if ref.startswith('../'):
            source_dir = Path(source_file).parent
            try:
                resolved = (self.base_path / source_dir / ref).resolve()
                return str(resolved.relative_to(self.base_path))
            except (ValueError, FileNotFoundError):
                return None
        
        # Assume relative to templates directory
        if not ref.startswith('/'):
            # Try to find the file
            possible_paths = [
                f"templates/{ref}",
                f".codex/{ref}",
                f".claude/{ref}",
                ref
            ]
            
            for path in possible_paths:
                if path in self.results["files"]:
                    return path
        
        return ref
    
    def _find_broken_references(self) -> None:
        """Find references to non-existent files and anchors"""
        print("Finding broken references...")
        
        all_files = set(self.results["files"].keys())
        
        for file_path, file_info in self.results["files"].items():
            for ref in file_info.get("references", []):
                # Skip mdc: protocol links (they're not file references)
                if ref.startswith('mdc:'):
                    continue
                
                # Split file and anchor
                if '#' in ref:
                    file_ref, anchor = ref.split('#', 1)
                else:
                    file_ref = ref
                    anchor = None
                
                normalized_ref = self._normalize_reference(file_ref, file_path)
                
                # Check if file reference exists
                ref_exists = False
                anchor_exists = True  # Assume anchor exists unless we can check
                
                if normalized_ref:
                    # Direct match
                    if normalized_ref in all_files:
                        ref_exists = True
                        # If there's an anchor, validate it
                        if anchor:
                            anchor_exists = self._validate_anchor(normalized_ref, anchor)
                    # Check if file exists on disk
                    elif (self.base_path / normalized_ref).exists():
                        ref_exists = True
                        if anchor:
                            anchor_exists = self._validate_anchor(normalized_ref, anchor)
                
                if not ref_exists or not anchor_exists:
                    self.analysis["broken_references"].append({
                        "source_file": file_path,
                        "broken_reference": ref,
                        "normalized": normalized_ref,
                        "type": "file" if not ref_exists else "anchor",
                        "anchor": anchor if not anchor_exists else None,
                        "line_count": file_info.get("line_count", 0)
                    })
        
        # Sort by source file
        self.analysis["broken_references"].sort(key=lambda x: x["source_file"])
    
    def _validate_anchor(self, file_path: str, anchor: str) -> bool:
        """Validate if an anchor exists in the target file"""
        # First check cached heading IDs if available
        if file_path in self.results["files"]:
            file_info = self.results["files"][file_path]
            metadata = file_info.get("metadata", {})
            heading_ids = metadata.get("heading_ids", [])
            
            # Quick check against cached IDs
            if anchor in heading_ids:
                return True
            
            # Also check case-insensitive match
            anchor_lower = anchor.lower()
            if any(h_id.lower() == anchor_lower for h_id in heading_ids):
                return True
        
        # Fall back to reading file if not in cache or not found
        target_path = self.base_path / file_path
        if not target_path.exists():
            return False
        
        try:
            content = target_path.read_text(encoding='utf-8')
            
            # Check for explicit anchor ID {#anchor}
            import re
            if re.search(rf'\{{#{re.escape(anchor)}\}}', content):
                return True
            
            # Convert anchor to heading format (remove dashes, match case-insensitive)
            anchor_text = anchor.replace('-', ' ')
            
            # Check for heading with this text
            # Match any heading level with this text (case-insensitive)
            heading_pattern = rf'^#+\s+.*{re.escape(anchor_text)}.*$'
            if re.search(heading_pattern, content, re.MULTILINE | re.IGNORECASE):
                return True
            
            # Also check for HTML anchor tags
            if f'id="{anchor}"' in content or f"id='{anchor}'" in content:
                return True
            
            return False
        except Exception:
            return True  # If we can't read, assume it exists to avoid false positives
    
    def _find_monolith_references_after_migration(self, migration_status: Dict) -> None:
        """Find references to monolithic files that have been fully migrated"""
        print("Checking for references to migrated monoliths...")
        
        # Get list of fully migrated monoliths
        fully_migrated = []
        for file_path, status in migration_status.items():
            if status.get("status") == "FULLY_MIGRATED":
                fully_migrated.append(file_path)
        
        if not fully_migrated:
            print("  No fully migrated monoliths found")
            return
        
        print(f"  Found {len(fully_migrated)} fully migrated monoliths")
        
        # Check all files for references to these monoliths
        for source_file, file_info in self.results["files"].items():
            # Skip checking the monolith itself
            if source_file in fully_migrated:
                continue
            
            references = file_info.get("references", [])
            for ref in references:
                # Check if reference points to a fully migrated monolith
                normalized_ref = self._normalize_reference(ref, source_file)
                if normalized_ref in fully_migrated:
                    violation = {
                        "source_file": source_file,
                        "target_file": normalized_ref,
                        "reference": ref,
                        "migration_status": migration_status[normalized_ref].get("status"),
                        "modular_files": migration_status[normalized_ref].get("modular_files", 0)
                    }
                    self.analysis["monolith_reference_after_migration"].append(violation)
        
        print(f"  Found {len(self.analysis['monolith_reference_after_migration'])} violations")

    def _add_validation_finding(self, rule_name: str, count: int, message: str) -> None:
        rule = self.validation_rules.get(rule_name)
        if not rule:
            return

        self.analysis["validation_findings"].append(
            finding_from_count(rule, count, message).to_dict()
        )

    def _generate_validation_findings(self) -> None:
        """Attach configured severity findings to the analysis report."""
        self._add_validation_finding(
            "broken_references",
            len(self.analysis["broken_references"]),
            "Broken references detected",
        )
        self._add_validation_finding(
            "migrated_monolith_references",
            len(self.analysis["monolith_reference_after_migration"]),
            "References to fully migrated monoliths detected",
        )
        self._add_validation_finding(
            "circular_dependencies",
            len(self.analysis["circular_dependencies"]),
            "Circular dependencies detected",
        )
        self._add_validation_finding(
            "orphaned_files",
            len(self.analysis["orphaned_files"]),
            "Orphaned files detected",
        )
        self._add_validation_finding(
            "duplicate_references",
            len(self.analysis["duplicate_references"]),
            "Duplicate references detected",
        )
    
    def _find_circular_dependencies(self) -> None:
        """Find circular dependencies in the graph"""
        print("Finding circular dependencies...")
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> List[str]:
            """DFS to detect cycles"""
            if node in rec_stack:
                # Found a cycle
                if node in path:
                    cycle_start = path.index(node)
                    return path[cycle_start:] + [node]
                else:
                    # Node is in recursion stack but not in current path
                    # This means we found a cycle through a different path
                    return []
            
            if node in visited:
                return []
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.analysis["dependency_graph"].get(node, []):
                cycle = has_cycle(neighbor, path[:])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return []
        
        # Check each node
        for node in self.analysis["dependency_graph"]:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle and len(cycle) > 1:
                    # Only add unique cycles
                    cycle_set = frozenset(cycle[:-1])  # Remove duplicate last element
                    already_found = False
                    for existing in self.analysis["circular_dependencies"]:
                        if frozenset(existing["cycle"][:-1]) == cycle_set:
                            already_found = True
                            break
                    
                    if not already_found:
                        self.analysis["circular_dependencies"].append({
                            "cycle": cycle,
                            "length": len(cycle) - 1
                        })
    
    def _find_orphaned_files(self) -> None:
        """Find files that are not referenced by any other file"""
        print("Finding orphaned files...")
        
        all_files = set(self.results["files"].keys())
        referenced_files = set()
        
        # Collect all referenced files
        for file_path, file_info in self.results["files"].items():
            for ref in file_info.get("references", []):
                normalized_ref = self._normalize_reference(ref, file_path)
                if normalized_ref:
                    referenced_files.add(normalized_ref)
        
        # Find orphans (not referenced by anyone)
        for file_path in all_files:
            if file_path not in referenced_files:
                # Some files should not be considered orphans
                skip_patterns = [
                    'README', 'index', 'CLAUDE.md', 'AGENT.md',
                    'registry/index', 'USER-GUIDE'
                ]
                
                if not any(pattern in file_path for pattern in skip_patterns):
                    file_info = self.results["files"][file_path]
                    self.analysis["orphaned_files"].append({
                        "file": file_path,
                        "type": file_info.get("type", "unknown"),
                        "line_count": file_info.get("line_count", 0)
                    })
        
        # Sort by type and path
        self.analysis["orphaned_files"].sort(key=lambda x: (x["type"], x["file"]))
    
    def _calculate_reference_stats(self) -> None:
        """Calculate statistics about references"""
        print("Calculating reference statistics...")
        
        # Count incoming references for each file
        reference_counts = defaultdict(int)
        
        for file_path in self.analysis["reverse_dependencies"]:
            reference_counts[file_path] = len(self.analysis["reverse_dependencies"][file_path])
        
        # Find most referenced files
        most_referenced = sorted(
            reference_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]  # Top 20
        
        self.analysis["most_referenced"] = [
            {
                "file": file_path,
                "reference_count": count,
                "referenced_by": self.analysis["reverse_dependencies"][file_path][:5]  # First 5
            }
            for file_path, count in most_referenced
        ]
        
        # Calculate overall stats
        total_refs = sum(
            len(file_info.get("references", []))
            for file_info in self.results["files"].values()
        )
        
        files_with_refs = sum(
            1 for file_info in self.results["files"].values()
            if file_info.get("references")
        )
        
        self.analysis["reference_stats"] = {
            "total_references": total_refs,
            "unique_references": len(self.analysis["reverse_dependencies"]),
            "files_with_references": files_with_refs,
            "files_without_references": len(self.results["files"]) - files_with_refs,
            "average_references_per_file": total_refs / len(self.results["files"]) if self.results["files"] else 0,
            "broken_reference_count": len(self.analysis["broken_references"]),
            "circular_dependency_count": len(self.analysis["circular_dependencies"]),
            "orphaned_file_count": len(self.analysis["orphaned_files"])
        }
    
    def _find_duplicate_references(self) -> None:
        """Find files that reference the same target multiple times"""
        print("Finding duplicate references...")
        
        for file_path, file_info in self.results["files"].items():
            references = file_info.get("references", [])
            if not references:
                continue
            
            # Count occurrences of each reference
            ref_counts = defaultdict(int)
            for ref in references:
                normalized = self._normalize_reference(ref, file_path)
                if normalized:
                    ref_counts[normalized] += 1
            
            # Find duplicates
            duplicates = {ref: count for ref, count in ref_counts.items() if count > 1}
            
            if duplicates:
                self.analysis["duplicate_references"].append({
                    "file": file_path,
                    "duplicates": duplicates
                })
    
    def _save_analysis(self) -> None:
        """Save analysis results with metadata"""
        output_file = getattr(self, '_output_file', Path("output/data/reference_analysis.json"))
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate stats for metadata
        stats = {
            "broken_references": len(self.analysis['broken_references']),
            "circular_dependencies": len(self.analysis['circular_dependencies']),
            "orphaned_files": len(self.analysis['orphaned_files']),
            "monolith_violations": len(self.analysis.get('monolith_reference_after_migration', [])),
            "duplicate_references": len(self.analysis.get('duplicate_references', [])),
            "validation_findings": len(self.analysis.get('validation_findings', []))
        }
        
        # Save with metadata wrapper
        save_with_metadata(
            data=self.analysis,
            output_file=output_file,
            scanner_name="reference_analyzer",
            version="1.1.0",
            stats=stats,
            duration_seconds=getattr(self, '_duration', 0.0)
        )
        
        print(f"\n✅ Analysis complete!")
        print(f"  Broken references: {len(self.analysis['broken_references'])}")
        print(f"  Circular dependencies: {len(self.analysis['circular_dependencies'])}")
        print(f"  Orphaned files: {len(self.analysis['orphaned_files'])}")
        print(f"  Results saved to: {output_file}")
        
        # Print summary
        if self.analysis["broken_references"]:
            print("\n⚠️  Top broken references:")
            for item in self.analysis["broken_references"][:5]:
                print(f"  {item['source_file']} -> {item['broken_reference']}")
        
        if self.analysis["circular_dependencies"]:
            print("\n🔄 Circular dependencies found:")
            for item in self.analysis["circular_dependencies"][:3]:
                cycle_str = " -> ".join(item["cycle"])
                print(f"  {cycle_str}")
        
        if self.analysis["most_referenced"]:
            print("\n📊 Most referenced files:")
            for item in self.analysis["most_referenced"][:5]:
                print(f"  {item['file']}: {item['reference_count']} references")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Reference Analyzer - Analyzes file references and dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Use default scan results
  %(prog)s --input custom_scan.json    # Use custom scan results
  %(prog)s --out analysis.json         # Custom output file
  %(prog)s --broken-threshold 10       # Exit with error if >10 broken refs
  %(prog)s --orphan-threshold 20       # Exit with error if >20 orphaned files
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
        help='Output analysis file (default: output/data/reference_analysis.json)',
        default='output/data/reference_analysis.json'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Validation rule config file (default: scanner_config.yaml next to this script)',
        default='scanner_config.yaml'
    )
    parser.add_argument(
        '--profile',
        type=str,
        help='Named scanner config profile to resolve before analysis',
        default=None
    )
    parser.add_argument(
        '--environment',
        type=str,
        help='Named scanner config environment overlay to resolve before analysis',
        default=None
    )
    parser.add_argument(
        '--env-overrides',
        action='store_true',
        help='Apply CODEX_SCANNER_ environment overrides after profile/environment resolution'
    )
    parser.add_argument(
        '--broken-threshold',
        type=int,
        help='Exit with error if broken references exceed this threshold',
        default=None
    )
    parser.add_argument(
        '--orphan-threshold',
        type=int,
        help='Exit with error if orphaned files exceed this threshold',
        default=None
    )
    parser.add_argument(
        '--circular-threshold',
        type=int,
        help='Exit with error if circular dependencies exceed this threshold',
        default=None
    )
    parser.add_argument(
        '--monolith-migration-threshold',
        type=int,
        help='Exit with error if references to migrated monoliths exceed this threshold',
        default=0  # Default to 0 - no references allowed to fully migrated monoliths
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
        print(f"Template Reference Analyzer v1.1.0")
        print(f"=" * 50)
    
    # Track timing
    start_time = time.time()
    
    analyzer = ReferenceAnalyzer(
        str(args.input),
        str(args.config),
        profile=args.profile,
        environment=args.environment,
        apply_environment_overrides=args.env_overrides,
    )
    
    # Set custom output path if specified (the _save_analysis method already handles metadata)
    if args.out != Path('output/data/reference_analysis.json'):
        analyzer._output_file = args.out
    
    analysis = analyzer.analyze()
    
    if analysis:
        # Check thresholds for CI/CD integration
        exit_code = 0
        
        if args.broken_threshold is not None:
            broken_count = len(analysis.get('broken_references', []))
            if broken_count > args.broken_threshold:
                print(f"\n❌ ERROR: Broken references ({broken_count}) exceed threshold ({args.broken_threshold})")
                exit_code = 1
        
        if args.orphan_threshold is not None:
            orphan_count = len(analysis.get('orphaned_files', []))
            if orphan_count > args.orphan_threshold:
                print(f"\n❌ ERROR: Orphaned files ({orphan_count}) exceed threshold ({args.orphan_threshold})")
                exit_code = 1
        
        if args.circular_threshold is not None:
            circular_count = len(analysis.get('circular_dependencies', []))
            if circular_count > args.circular_threshold:
                print(f"\n❌ ERROR: Circular dependencies ({circular_count}) exceed threshold ({args.circular_threshold})")
                exit_code = 1
        
        if args.monolith_migration_threshold is not None:
            monolith_ref_count = len(analysis.get('monolith_reference_after_migration', []))
            if monolith_ref_count > args.monolith_migration_threshold:
                print(f"\n❌ ERROR: References to migrated monoliths ({monolith_ref_count}) exceed threshold ({args.monolith_migration_threshold})")
                print("  These references must be updated to point to modular/registry paths")
                exit_code = 1
        
        if exit_code != 0:
            sys.exit(exit_code)
        
        if not args.quiet:
            print(f"\n{'=' * 50}")
            print(f"Analysis complete. Use find_duplicates.py to compare with monolithic files.")


if __name__ == "__main__":
    main()
