#!/usr/bin/env python3
"""
Test backward compatibility of metadata wrapper format
"""

import json
import tempfile
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scan_metadata import (
    MetadataSchemaError,
    load_with_metadata,
    save_with_metadata,
    validate_output_file,
    validate_output_structure,
)


def test_backward_compatibility():
    """Test that old format files can still be loaded"""
    print("Testing backward compatibility...")
    
    # Create old format data (without metadata wrapper)
    old_format_data = {
        "broken_references": [
            {"source": "file1.md", "target": "missing.md"}
        ],
        "statistics": {"total": 1}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(old_format_data, f, indent=2)
        old_file = Path(f.name)
    
    try:
        # Load old format with compatibility function
        data, metadata = load_with_metadata(old_file)
        
        # Verify data is preserved
        assert data == old_format_data, "Data not preserved in backward compat mode"
        assert metadata is None, "Metadata should be None for old format"
        
        print("✅ Old format loading: PASSED")
        
    finally:
        old_file.unlink()


def test_new_format_roundtrip():
    """Test that new format preserves data and metadata"""
    print("Testing new format roundtrip...")
    
    test_data = {
        "results": ["item1", "item2"],
        "count": 2
    }
    
    test_stats = {
        "files_processed": 100,
        "errors": 0
    }
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_file = Path(f.name)
    
    try:
        # Save with metadata
        save_with_metadata(
            data=test_data,
            output_file=output_file,
            scanner_name="test_scanner",
            version="1.0.0",
            stats=test_stats,
            duration_seconds=1.23
        )
        
        # Load it back
        loaded_data, loaded_metadata = load_with_metadata(output_file)
        
        # Verify data preserved
        assert loaded_data == test_data, "Data not preserved in new format"
        
        # Verify metadata
        assert loaded_metadata is not None, "Metadata missing"
        assert loaded_metadata["scanner"] == "test_scanner", "Scanner name mismatch"
        assert loaded_metadata["scanner_version"] == "1.0.0", "Version mismatch"
        assert loaded_metadata["output_format_version"] == "2.0.0", "Format version mismatch"
        assert loaded_metadata["stats"] == test_stats, "Stats mismatch"
        assert loaded_metadata["duration_seconds"] == 1.23, "Duration mismatch"
        validate_output_file(output_file)
        
        print("✅ New format roundtrip: PASSED")
        
    finally:
        output_file.unlink()


def test_schema_validation_rejects_missing_metadata_fields():
    """Test that malformed v2 outputs fail schema validation."""
    print("Testing schema validation rejection...")

    invalid_output = {
        "metadata": {
            "scan_timestamp": "2026-04-26T11:56:00",
            "scanner": "test_scanner",
            "output_format_version": "2.0.0",
        },
        "data": {},
    }

    try:
        validate_output_structure(invalid_output)
    except MetadataSchemaError:
        print("✅ Schema rejection: PASSED")
    else:
        raise AssertionError("Malformed metadata output was accepted")


def test_incremental_updates():
    """Test that previous scan tracking works"""
    print("Testing incremental update tracking...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_file = Path(f.name)
    
    try:
        # First scan with stats
        save_with_metadata(
            data={"count": 1},
            output_file=output_file,
            scanner_name="test",
            version="1.0.0",
            stats={"items": 10, "errors": 0}
        )
        
        # Second scan with different stats - should detect previous
        save_with_metadata(
            data={"count": 2},
            output_file=output_file,
            scanner_name="test",
            version="1.0.0",
            stats={"items": 15, "errors": 1}
        )
        
        # Load and check
        data, metadata = load_with_metadata(output_file)
        
        assert metadata["previous_scan"] is not None, "Previous scan not tracked"
        assert "changes_from_previous" in metadata, "Changes not tracked"
        assert data["count"] == 2, "Latest data not saved"
        
        # Check changes calculation
        if "changes_from_previous" in metadata:
            changes = metadata["changes_from_previous"]
            assert "items_delta" in changes or "no_changes" in changes, "Changes not calculated"
        
        print("✅ Incremental updates: PASSED")
        
    finally:
        output_file.unlink()


def test_mixed_environment():
    """Test interoperability between old and new consumers"""
    print("Testing mixed environment compatibility...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_file = Path(f.name)
    
    try:
        # New tool saves with metadata
        save_with_metadata(
            data={"results": [1, 2, 3]},
            output_file=output_file,
            scanner_name="new_tool",
            version="2.0.0"
        )
        
        # Old tool reads directly (simulated)
        with open(output_file) as f:
            raw = json.load(f)
        
        # Old tool should be able to access data directly
        if "data" in raw:  # New format
            old_tool_data = raw["data"]
        else:  # Old format
            old_tool_data = raw
        
        assert old_tool_data == {"results": [1, 2, 3]}, "Old tool can't read new format"
        
        print("✅ Mixed environment: PASSED")
        
    finally:
        output_file.unlink()


def main():
    """Run all compatibility tests"""
    print("=" * 50)
    print("METADATA COMPATIBILITY TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_backward_compatibility,
        test_new_format_roundtrip,
        test_incremental_updates,
        test_mixed_environment,
        test_schema_validation_rejects_missing_metadata_fields,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__}: FAILED")
            print(f"   {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: ERROR")
            print(f"   {str(e)}")
            failed += 1
    
    print("=" * 50)
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"❌ {failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
