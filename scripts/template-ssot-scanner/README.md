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