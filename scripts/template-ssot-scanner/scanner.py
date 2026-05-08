#!/usr/bin/env python3
"""
Template System Scanner
Scans all template files and collects metadata for SSOT analysis
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from report_generator import save_scanner_report
from scan_core import (
    DEFAULT_EXCLUDE_PATTERNS,
    ScannerConfig,
    collect_scannable_files,
    discover_config_dirs,
)


class TemplateScanner:
    """Scanner for template system files"""
    
    def __init__(self, base_path: Path, checkpoint_interval: int = 25, 
                 include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None,
                 scanner_config: Optional[ScannerConfig] = None, config_context: Any = None,
                 profile_scan: bool = False, profile_limit: int = 10):
        self.base_path = base_path
        self.checkpoint_interval = checkpoint_interval
        self.templates_dir = base_path / "templates"
        self.config_context = config_context
        self.profile_scan = profile_scan
        self.profile_limit = max(0, profile_limit)
        self._profile_directories: list[Dict[str, Any]] = []
        self._profile_files: list[Dict[str, Any]] = []
        if scanner_config is not None:
            self.config = scanner_config
        elif config_context is not None:
            self.config = config_context.file_discovery_config(base_path, include_pattern, exclude_pattern)
        else:
            self.config = ScannerConfig.from_cli(base_path, include_pattern, exclude_pattern)
        self.config_dirs = discover_config_dirs(base_path, self.config.config_dirs)
        self.results = {
            "scan_metadata": {
                "timestamp": datetime.now().isoformat(),
                "base_path": str(base_path),
                "config_source": getattr(config_context, "source", None),
                "config_profile": getattr(config_context, "profile", None),
                "config_environment": getattr(config_context, "environment", None),
                "total_files": 0,
                "total_lines": 0,
                "checkpoints_saved": 0
            },
            "files": {},
            "file_types": {},
            "references": {},
            "errors": []
        }
        self.checkpoint_dir = Path("output/.checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
    def scan(self) -> Dict:
        """Main scanning method"""
        print(f"Starting scan of {self.base_path}")
        print(f"Templates dir: {self.templates_dir}")
        if self.config_dirs:
            config_listing = ", ".join(str(path) for path in self.config_dirs)
            print(f"Config dirs: {config_listing}")
        else:
            print("Config dirs: (none found)")

        # Scan both directories
        self._scan_directory(self.templates_dir, "templates")
        for config_dir in self.config_dirs:
            category = config_dir.name.lstrip('.') or "config"
            self._scan_directory(config_dir, category)
        
        # Final analysis
        self._analyze_file_types()
        self._finalize_performance_profile()
        self._save_final_results()
        
        return self.results
    
    def _scan_directory(self, directory: Path, category: str) -> None:
        """Scan a specific directory with optional filtering"""
        if not directory.exists():
            print(f"Warning: {directory} does not exist")
            return

        files_processed = 0
        discovery_start = time.perf_counter()
        all_files = collect_scannable_files(directory, self.config)
        discovery_seconds = time.perf_counter() - discovery_start
        processing_start = time.perf_counter()
        
        print(f"\nFound {len(all_files)} files in {category} (after filtering)")
        
        for file_path in all_files:
            try:
                file_start = time.perf_counter()
                self._process_file(file_path, category)
                file_seconds = time.perf_counter() - file_start
                if self.profile_scan:
                    self._record_file_profile(file_path, category, file_seconds)
                files_processed += 1
                self.results["scan_metadata"]["total_files"] += 1
                
                # Save checkpoint
                if self.checkpoint_interval > 0 and files_processed % self.checkpoint_interval == 0:
                    self._save_checkpoint(files_processed)
                    
                # Progress indicator
                if files_processed % 10 == 0:
                    print(f"  Processed {files_processed}/{len(all_files)} files...")
                    
            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                print(f"  ERROR: {error_msg}")
                self.results["errors"].append(error_msg)

        if self.profile_scan:
            self._profile_directories.append({
                "category": category,
                "path": str(directory),
                "files_discovered": len(all_files),
                "files_processed": files_processed,
                "discovery_seconds": round(discovery_seconds, 6),
                "processing_seconds": round(time.perf_counter() - processing_start, 6),
            })
    
    def _process_file(self, file_path: Path, category: str) -> None:
        """Process a single file"""
        relative_path = file_path.relative_to(self.base_path)
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')
        
        lines = content.splitlines()
        line_count = len(lines)
        self.results["scan_metadata"]["total_lines"] += line_count
        
        # Detect file type
        file_type = self._detect_file_type(file_path, content)
        
        # Extract references with line numbers
        references_data = self._extract_references(content)
        references = [r['reference'] for r in references_data]
        
        # Extract metadata
        metadata = self._extract_metadata(content)
        
        # Store file info
        file_key = str(relative_path)
        self.results["files"][file_key] = {
            "path": str(file_path),
            "relative_path": file_key,
            "category": category,
            "type": file_type,
            "line_count": line_count,
            "size_bytes": file_path.stat().st_size,
            "references": references,
            "references_detailed": references_data,
            "metadata": metadata,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        # Store references for reverse lookup
        for ref in references:
            if ref not in self.results["references"]:
                self.results["references"][ref] = []
            self.results["references"][ref].append(file_key)
    
    def _detect_file_type(self, file_path: Path, content: str) -> str:
        """Detect the type of template file"""
        path_str = str(file_path).lower()
        content_lower = content[:1000].lower()  # Check first 1000 chars
        
        # Path-based detection
        if 'handler' in path_str:
            if 'trigger' in path_str:
                return 'trigger'
            elif 'orchestrator' in path_str:
                return 'orchestrator'
            elif 'operator' in path_str:
                return 'operator'
            return 'handler'
        elif 'workflow' in path_str:
            return 'workflow'
        elif 'pattern' in path_str:
            return 'pattern'
        elif 'convention' in path_str:
            return 'convention'
        elif 'behavior' in path_str:
            return 'behavior'
        elif 'matri' in path_str:
            return 'matrix'
        elif 'registry' in path_str:
            return 'registry'
        elif 'agent' in path_str:
            return 'agent'
        elif 'command' in path_str:
            return 'command'
        elif 'hook' in path_str:
            return 'hook'
        elif 'engine' in path_str:
            return 'engine'
        elif 'guide' in path_str:
            return 'guide'
        elif 'prompt' in path_str:
            return 'prompt'
        elif 'integration' in path_str:
            return 'integration'
        
        # Content-based detection
        if '## trigger' in content_lower:
            return 'trigger'
        elif '## orchestrator' in content_lower:
            return 'orchestrator'
        elif '## operator' in content_lower:
            return 'operator'
        elif 'workflow' in content_lower:
            return 'workflow'
        elif file_path.suffix == '.json':
            return 'json-config'
        elif file_path.suffix in ['.yml', '.yaml']:
            return 'yaml-config'
        
        return 'other'
    
    def _extract_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract file references from content with line numbers"""
        references = []
        lines = content.splitlines()
        
        # Pattern 1: Markdown links to .md files (with optional anchors)
        md_link_pattern = r'\[[^\]]+\]\(([^)]+?\.md(?:#[^)]+)?)\)'
        
        # Pattern 2: Direct path references (with optional anchors)
        path_pattern = r'`(templates/[^`]+\.md(?:#[^`]+)?)`'
        
        # Pattern 3: Configuration directory references (with optional anchors)
        config_pattern = r'`(\.(?:codex|claude)/[^`]+\.md(?:#[^`]+)?)`'
        
        # Pattern 4: Relative paths (with optional anchors)
        relative_pattern = r'`(\.\./[^`]+\.md(?:#[^`]+)?)`'
        
        # Pattern 5: MDC protocol links (common in rules)
        mdc_pattern = r'\((mdc:[^)]+)\)'
        
        patterns = [
            ('markdown_link', md_link_pattern),
            ('path_reference', path_pattern),
            ('config_reference', config_pattern),
            ('relative_reference', relative_pattern),
            ('mdc_protocol', mdc_pattern)
        ]
        
        # Process each line to find references with line numbers
        for line_num, line in enumerate(lines, 1):
            for ref_type, pattern in patterns:
                for match in re.finditer(pattern, line):
                    ref = match.group(1)
                    # Clean reference
                    ref_clean = ref.strip('`"\'')
                    if ref_clean.startswith('./'):
                        ref_clean = ref_clean[2:]
                    
                    references.append({
                        'reference': ref_clean,
                        'line': line_num,
                        'column': match.start() + 1,
                        'type': ref_type,
                        'raw': ref
                    })
        
        # Deduplicate by reference but keep all line numbers
        ref_map = {}
        for ref_info in references:
            ref_key = ref_info['reference']
            if ref_key not in ref_map:
                ref_map[ref_key] = {
                    'reference': ref_key,
                    'locations': [],
                    'types': set()
                }
            ref_map[ref_key]['locations'].append({
                'line': ref_info['line'],
                'column': ref_info['column'],
                'type': ref_info['type']
            })
            ref_map[ref_key]['types'].add(ref_info['type'])
        
        # Convert back to list format
        result = []
        for ref_key, ref_data in ref_map.items():
            ref_data['types'] = list(ref_data['types'])
            result.append(ref_data)
        
        return result
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from file content"""
        metadata = {}
        
        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1)
        
        # Extract all heading IDs for anchor validation
        heading_ids = []
        # Pattern 1: Explicit IDs in headings like {#some-id}
        explicit_ids = re.findall(r'^#+\s+.*?\{#([^}]+)\}', content, re.MULTILINE)
        heading_ids.extend(explicit_ids)
        
        # Pattern 2: Auto-generated IDs from heading text (GitHub-style)
        # Convert heading text to lowercase, replace spaces with hyphens, remove special chars
        all_headings = re.findall(r'^(#+)\s+(.+?)(?:\s*\{#[^}]+\})?$', content, re.MULTILINE)
        for heading_level, heading_text in all_headings:
            # Skip if this heading has an explicit ID
            if not any(heading_text.endswith(f'{{#{id}}}') for id in explicit_ids):
                # Generate ID: lowercase, replace spaces/special chars with hyphens
                auto_id = re.sub(r'[^\w\s-]', '', heading_text.lower())
                auto_id = re.sub(r'[-\s]+', '-', auto_id).strip('-')
                if auto_id:
                    heading_ids.append(auto_id)
        
        if heading_ids:
            metadata['heading_ids'] = heading_ids
        
        # Extract trigger keyword
        trigger_match = re.search(r'## Trigger\s*\n.*?"([^"]+)"', content, re.DOTALL)
        if trigger_match:
            metadata['trigger'] = trigger_match.group(1)
        
        # Extract handler type
        handler_match = re.search(r'## (Trigger|Orchestrator|Operator)', content)
        if handler_match:
            metadata['handler_type'] = handler_match.group(1).lower()
        
        # Count sections
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        metadata['section_count'] = len(sections)
        metadata['sections'] = sections[:10]  # First 10 sections
        
        # Check for CRITICAL markers
        critical_count = content.count('[CRITICAL')
        if critical_count > 0:
            metadata['critical_markers'] = critical_count
        
        # Check for TODO/FIXME
        todo_count = content.count('TODO')
        fixme_count = content.count('FIXME')
        if todo_count > 0:
            metadata['todo_count'] = todo_count
        if fixme_count > 0:
            metadata['fixme_count'] = fixme_count
        
        return metadata
    
    def _analyze_file_types(self) -> None:
        """Analyze distribution of file types"""
        for file_info in self.results["files"].values():
            file_type = file_info["type"]
            if file_type not in self.results["file_types"]:
                self.results["file_types"][file_type] = {
                    "count": 0,
                    "total_lines": 0,
                    "files": []
                }
            
            self.results["file_types"][file_type]["count"] += 1
            self.results["file_types"][file_type]["total_lines"] += file_info["line_count"]
            self.results["file_types"][file_type]["files"].append(file_info["relative_path"])

    def _record_file_profile(self, file_path: Path, category: str, duration_seconds: float) -> None:
        """Record per-file scan timings for optional profiling output."""
        relative_path = file_path.relative_to(self.base_path).as_posix()
        file_info = self.results["files"].get(relative_path, {})
        self._profile_files.append({
            "relative_path": relative_path,
            "category": category,
            "duration_seconds": round(duration_seconds, 6),
            "size_bytes": file_info.get("size_bytes", file_path.stat().st_size),
            "line_count": file_info.get("line_count", 0),
            "references": len(file_info.get("references", [])),
        })

    def _finalize_performance_profile(self) -> None:
        """Attach optional scanner profiling data to scan metadata."""
        if not self.profile_scan:
            return

        def slow_key(item: Dict[str, Any]) -> tuple[float, str]:
            return (-item["duration_seconds"], item["relative_path"])

        def size_key(item: Dict[str, Any]) -> tuple[int, str]:
            return (-item["size_bytes"], item["relative_path"])

        limit = self.profile_limit
        slowest_files = sorted(self._profile_files, key=slow_key)[:limit] if limit else []
        largest_files = sorted(self._profile_files, key=size_key)[:limit] if limit else []
        self.results["scan_metadata"]["performance_profile"] = {
            "enabled": True,
            "profile_limit": limit,
            "directories": self._profile_directories,
            "slowest_files": slowest_files,
            "largest_files": largest_files,
            "total_discovery_seconds": round(
                sum(directory["discovery_seconds"] for directory in self._profile_directories),
                6,
            ),
            "total_processing_seconds": round(
                sum(directory["processing_seconds"] for directory in self._profile_directories),
                6,
            ),
        }
    
    def _save_checkpoint(self, files_processed: int) -> None:
        """Save checkpoint during scanning"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{files_processed}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.results["scan_metadata"]["checkpoints_saved"] += 1
        print(f"  Checkpoint saved: {checkpoint_file}")
    
    def _save_final_results(self) -> None:
        """Save final results"""
        output_file = Path("output/data/template_scan_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Scan complete!")
        print(f"  Total files: {self.results['scan_metadata']['total_files']}")
        print(f"  Total lines: {self.results['scan_metadata']['total_lines']}")
        print(f"  Results saved to: {output_file}")
        
        # Print summary by type
        print("\nFile type distribution:")
        for file_type, info in sorted(self.results["file_types"].items()):
            print(f"  {file_type}: {info['count']} files, {info['total_lines']} lines")
        
        if self.results["errors"]:
            print(f"\n⚠️  {len(self.results['errors'])} errors occurred during scanning")
            print(f"  Check {output_file} for details")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Template System Scanner - Scans template files for SSOT analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Scan from current directory
  %(prog)s --base /path/to/project  # Scan specific project
  %(prog)s --out results.json       # Custom output file
  %(prog)s --include "handlers/**"  # Only scan handlers
  %(prog)s --exclude "*test*"       # Exclude test files
  %(prog)s --checkpoint 50          # Save checkpoint every 50 files
        """
    )
    
    parser.add_argument(
        '--base', '-b',
        type=Path,
        help='Base directory to scan (default: auto-detect or current)',
        default=None
    )
    parser.add_argument(
        '--out', '-o',
        type=Path,
        help='Output file path (default: output/data/template_scan_results.json)',
        default='output/data/template_scan_results.json'
    )
    parser.add_argument(
        '--include', '-i',
        type=str,
        help='Glob pattern for files to include (e.g., "handlers/**")',
        default=None
    )
    parser.add_argument(
        '--exclude', '-e',
        type=str,
        help='Glob pattern for files to exclude (e.g., "*test*")',
        default=None
    )
    parser.add_argument(
        '--checkpoint', '-c',
        type=int,
        help='Save checkpoint every N files (default: 25)',
        default=25
    )
    parser.add_argument(
        '--no-checkpoints',
        action='store_true',
        help='Disable checkpoint saving'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--profile-scan',
        action='store_true',
        help='Record scanner discovery and per-file timing metadata'
    )
    parser.add_argument(
        '--profile-limit',
        type=int,
        default=10,
        help='Number of slowest/largest files to keep when --profile-scan is enabled (default: 10)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Scanner config YAML path (default: scanner_config.yaml next to this script)',
        default=Path(__file__).parent / 'scanner_config.yaml'
    )
    parser.add_argument(
        '--profile',
        type=str,
        help='Named scanner config profile to resolve before scanning',
        default=None
    )
    parser.add_argument(
        '--environment',
        type=str,
        help='Named scanner config environment overlay to resolve before scanning',
        default=None
    )
    parser.add_argument(
        '--env-overrides',
        action='store_true',
        help='Apply CODEX_SCANNER_ environment overrides after profile/environment resolution'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.1.0'
    )
    
    args = parser.parse_args()
    
    # Determine base path
    if args.base:
        base_path = args.base
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Legacy support for positional argument
        base_path = Path(sys.argv[1])
    else:
        # Try to find project root
        current = Path.cwd()
        while current != current.parent:
            if (current / "templates").exists() or (current / ".codex").exists() or (current / ".claude").exists():
                base_path = current
                break
            current = current.parent
        else:
            base_path = Path.cwd()
    
    print(f"Template System Scanner v1.1.0")
    print(f"=" * 50)
    
    if args.verbose:
        print(f"Configuration:")
        print(f"  Base path: {base_path}")
        print(f"  Output: {args.out}")
        print(f"  Include: {args.include or 'all'}")
        exclude_summary = ", ".join(DEFAULT_EXCLUDE_PATTERNS)
        if args.exclude:
            exclude_summary = f"{exclude_summary}, {args.exclude}"
        print(f"  Exclude: {exclude_summary}")
        print(f"  Checkpoints: {'disabled' if args.no_checkpoints else f'every {args.checkpoint} files'}")
        print()
    
    checkpoint_interval = 0 if args.no_checkpoints else args.checkpoint
    from config.integration import create_scanner_config_context

    config_context = create_scanner_config_context(
        args.config,
        profile=args.profile,
        environment=args.environment,
        apply_environment_overrides=args.env_overrides,
    )
    scanner = TemplateScanner(base_path, checkpoint_interval, 
                            include_pattern=args.include, 
                            exclude_pattern=args.exclude,
                            config_context=config_context,
                            profile_scan=args.profile_scan,
                            profile_limit=args.profile_limit)
    
    # Track timing
    start_time = time.time()
    results = scanner.scan()
    duration = time.time() - start_time
    
    # Prepare statistics
    scan_metadata = results.get("scan_metadata", {})
    file_types = results.get("file_types", {})
    files = results.get("files", {})
    stats = {
        "files_scanned": scan_metadata.get("total_files", 0),
        "total_lines": scan_metadata.get("total_lines", 0),
        "handlers_found": sum(
            file_types.get(file_type, {}).get("count", 0)
            for file_type in ("handler", "trigger", "orchestrator", "operator")
        ),
        "references_found": sum(len(file_info.get("references", [])) for file_info in files.values()),
        "issues_detected": len(results.get("errors", [])),
        "profile_enabled": bool(scan_metadata.get("performance_profile", {}).get("enabled")),
        "base_path": str(base_path),
        "include_pattern": args.include,
        "exclude_pattern": args.exclude
    }
    
    # Save with metadata
    output_path = Path(args.out)
    save_scanner_report(
        data=results,
        output_file=output_path,
        scanner_name="template_scanner",
        version="1.1.0",
        stats=stats,
        duration_seconds=duration
    )
    print(f"\nResults saved to: {output_path}")
    
    print(f"\n{'=' * 50}")
    print(f"Scan complete. Use analyze_references.py for detailed analysis.")


if __name__ == "__main__":
    main()
