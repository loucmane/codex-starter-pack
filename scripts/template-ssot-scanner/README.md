# Template SSOT Scanner Suite

A comprehensive suite of analysis tools for maintaining consistency and quality in the template system.

## Overview

The SSOT (Single Source of Truth) scanner suite provides automated analysis and fixing capabilities for:
- Template reference validation
- Migration status tracking
- Duplicate content detection
- Automated fix generation
- Reference graph analysis

## Scanner Components

### 1. Main Scanner (`scanner.py`)
Scans all template and Claude files to build a comprehensive index.
- **Output**: `output/data/template_scan_results.json`
- **Purpose**: Creates the base data for all other analyses

### 2. Migration Detector (`migration_detector.py`)
Tracks migration progress from monolithic to modular templates.
- **Output**: `output/data/migration_status.json`
- **Purpose**: Identifies fully/partially migrated and pending files

### 3. Reference Analyzer (`analyze_references.py`)
Analyzes file references to find broken links and dependencies.
- **Output**: `output/data/reference_analysis.json`
- **Purpose**: Validates reference integrity and finds circular dependencies

### 4. Duplicate Finder (`find_duplicates.py`)
Compares monolithic and modular files to find duplicate content.
- **Output**: `output/data/duplicate_analysis.json`
- **Purpose**: Helps complete migration by identifying overlaps

### 5. Fix Generator (`generate_fixes.py`)
Creates actionable fix recommendations and scripts.
- **Output**: `output/data/fix_recommendations.json`
- **Scripts**: `output/scripts/apply_reference_fixes.py`
- **Purpose**: Automates the fixing of identified issues

## Output Metadata Format (v2.0.0)

As of 2025-09-03, all scanner outputs include standardized metadata for tracking and comparison:

```json
{
  "metadata": {
    "scan_timestamp": "ISO-8601 timestamp",
    "scanner": "scanner_name",
    "scanner_version": "1.0.0",
    "output_format_version": "2.0.0",
    "duration_seconds": 0.123,
    "stats": {
      // Scanner-specific statistics
    },
    "previous_scan": "ISO-8601 timestamp or null",
    "changes_from_previous": {
      // Delta information if previous scan exists
    }
  },
  "data": {
    // Actual scan results (backward compatible)
  }
}
```

### Metadata Fields

- **scan_timestamp**: When the scan was performed (ISO-8601 format)
- **scanner**: Name of the scanner that generated the output
- **scanner_version**: Version of the scanner
- **output_format_version**: Version of the output format (currently "2.0.0")
- **duration_seconds**: Time taken to perform the scan
- **stats**: Scanner-specific statistics (e.g., files scanned, issues found)
- **previous_scan**: Timestamp of the previous scan if it exists
- **changes_from_previous**: Delta between current and previous scan

### Backward Compatibility

The metadata wrapper maintains backward compatibility:
- Old consumers can access the `data` field directly
- New consumers can utilize metadata for tracking and comparison
- The `scan_metadata.py` module provides utilities for loading both formats

## Usage

### Full Suite Run
```bash
# Run all scanners in sequence
./run_full_scan.sh

# Or run individually:
python3 scanner.py
python3 migration_detector.py  
python3 analyze_references.py
python3 find_duplicates.py
python3 generate_fixes.py
```

### Apply Fixes
```bash
# Apply reference fixes (most common)
python3 output/scripts/apply_reference_fixes.py

# Dry run to see what would change
python3 output/scripts/apply_reference_fixes.py --dry-run
```

### CI/CD Integration
All scanners support threshold-based exits for CI/CD:
```bash
# Exit with error if too many broken references
python3 analyze_references.py --broken-threshold 50

# Exit with error if migration below threshold
python3 find_duplicates.py --migration-threshold 80
```

## Utility Modules

### scan_metadata.py
Provides utilities for working with metadata-wrapped outputs:

```python
from scan_metadata import save_with_metadata, load_with_metadata

# Save with metadata
save_with_metadata(
    data=my_data,
    output_file=Path("output.json"),
    scanner_name="my_scanner",
    version="1.0.0",
    stats={"files": 100}
)

# Load with backward compatibility
data, metadata = load_with_metadata("output.json")
```

## Configuration

The scanner configuration contract is defined in `config/scanner_config.schema.json`.
The current default config is `scanner_config.yaml`, and a full example lives at
`config/examples/scanner_config.example.yaml`.
`config/config_loader.py` provides the Task 4.2 loader boundary for thread-safe singleton
access, lazy loading, schema validation, default fallback, and hot reload detection.
`config/validation.py` provides the Task 4.6 jsonschema validation layer with normalized
issue reports, file/data validation helpers, schema preflight checks, and validation timing.
`config/env_override.py` provides the Task 4.7 `CODEX_SCANNER_` environment override layer.
`config/inheritance.py` provides the Task 4.5 profile and environment overlay resolver.
`config/rule_engine.py` provides the Task 4.3 rule registry and execution layer.
`config/pattern_matcher.py` provides the Task 4.4 allowlist/blocklist matcher.
`config/integration.py` provides the Task 4.8 dependency-injection context for scanner modules.

The Task 4 configuration model covers:

- scan include/exclude patterns and config directories
- validation rule categories, scanner output severities, rule-engine priorities, thresholds, enablement, parameters, and future auto-fix intent
- path/reference allowlists and blocklists using `glob` or `regex`
- profile and environment overlay inheritance metadata for later merge behavior
- `CODEX_SCANNER_` environment variable overrides using double underscores for nested keys

Profiles and environment overlays resolve with explicit `deep_merge` or `replace` strategies. Deep
merge recursively merges mapping values and replaces lists/scalars; replace swaps top-level sections
from the override. The resolver detects unknown parents and inheritance cycles before returning a
validated config. Environment variables are applied after YAML/profile/overlay resolution and before
runtime validation, so they take precedence over file-based values.

The rule engine maps `critical`, `high`, `medium`, `low`, and `info` priorities onto the existing
`error`, `warning`, and `info` scanner finding contract. The pattern matcher supports path/reference
targets, rule-scoped entries, expiration dates, and blocklist precedence. `ScannerConfigContext`
packages the loader, rule engine, pattern matcher, and file-discovery settings so scanner modules
can receive resolved config explicitly. `scanner.py`, `analyze_references.py`, and
`run_all_scanners.py` accept `--config`, `--profile`, `--environment`, and `--env-overrides` for
config-driven runs.

```python
from pathlib import Path

from config.integration import (
    create_reference_analyzer,
    create_scanner_config_context,
    create_template_scanner,
    scanner_module_examples,
)

context = create_scanner_config_context(
    Path("scanner_config.yaml"),
    profile="ci",
    apply_environment_overrides=True,
)
scanner = create_template_scanner(Path.cwd(), context=context, checkpoint_interval=0)
analyzer = create_reference_analyzer(context=context)
examples = scanner_module_examples()
```

`scanner_module_examples()` lists the integration entry point for each scanner module in the suite.

## Output Directory Structure
```
output/
├── data/
│   ├── template_scan_results.json   # Base scan data
│   ├── migration_status.json        # Migration tracking
│   ├── reference_analysis.json      # Reference validation
│   ├── duplicate_analysis.json      # Duplicate detection
│   └── fix_recommendations.json     # Generated fixes
├── scripts/
│   └── apply_reference_fixes.py     # Auto-generated fix script
└── .checkpoints/                    # Scan checkpoints
```

## Development

### Adding a New Scanner
1. Import `scan_metadata` utilities
2. Track timing with `time.time()`
3. Use `save_with_metadata()` for output
4. Include scanner-specific stats
5. Follow the naming convention: `output/data/{scanner_name}.json`

### Version History
- **v2.0.0** (2025-09-03): Added metadata wrapper format
- **v1.1.0** (2025-08-22): Enhanced reference analysis
- **v1.0.0** (2025-08-20): Initial release
