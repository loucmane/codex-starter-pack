#!/usr/bin/env python3
"""
Shared metadata utilities for SSOT scanner suite
Provides consistent metadata tracking across all scanner outputs
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def load_with_metadata(filepath: Path) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """
    Load JSON file and extract data, handling both old and new formats
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Tuple of (data, metadata) where metadata may be None for old format
    """
    if not filepath.exists():
        return None, None
    
    with open(filepath, 'r') as f:
        content = json.load(f)
    
    # Handle old format (direct data) vs new format (with metadata)
    if "metadata" in content and "data" in content:
        return content["data"], content["metadata"]
    else:
        # Old format - treat entire content as data
        return content, None


def save_with_metadata(
    data: Any,
    output_file: Path,
    scanner_name: str,
    version: str = "1.0.0",
    stats: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """
    Save scan data with metadata wrapper
    
    Args:
        data: The actual scan data to save
        output_file: Path to save the output
        scanner_name: Name of the scanner (e.g., "migration_detector")
        version: Scanner version
        stats: Optional statistics about the scan
        duration_seconds: Optional scan duration
    """
    output_file = Path(output_file)
    
    # Build metadata
    metadata = {
        "scan_timestamp": datetime.now().isoformat(),
        "scanner": scanner_name,
        "scanner_version": version,
        "output_format_version": "2.0.0"  # Version of the metadata format itself
    }
    
    # Add optional fields
    if duration_seconds is not None:
        metadata["duration_seconds"] = round(duration_seconds, 2)
    
    if stats:
        metadata["stats"] = stats
    
    # Check for previous scan to track history
    if output_file.exists():
        try:
            previous_data, previous_metadata = load_with_metadata(output_file)
            if previous_metadata:
                metadata["previous_scan"] = previous_metadata.get("scan_timestamp")
                
                # Calculate changes if possible
                if stats and previous_metadata.get("stats"):
                    metadata["changes_from_previous"] = calculate_changes(
                        previous_metadata["stats"], 
                        stats
                    )
        except Exception:
            # If we can't load previous, just continue without it
            pass
    
    # Create output structure
    output = {
        "metadata": metadata,
        "data": data
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with nice formatting
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, sort_keys=False)


def calculate_changes(old_stats: Dict[str, Any], new_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate changes between old and new statistics
    
    Args:
        old_stats: Previous scan statistics
        new_stats: Current scan statistics
        
    Returns:
        Dictionary of changes
    """
    changes = {}
    
    # Find common numeric keys and calculate deltas
    for key in new_stats:
        if key in old_stats:
            old_val = old_stats[key]
            new_val = new_stats[key]
            
            # Only calculate delta for numeric values
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                delta = new_val - old_val
                if delta != 0:
                    changes[f"{key}_delta"] = delta
                    if old_val != 0:
                        changes[f"{key}_change_percent"] = round((delta / old_val) * 100, 1)
    
    # Note new keys
    new_keys = set(new_stats.keys()) - set(old_stats.keys())
    if new_keys:
        changes["new_metrics"] = list(new_keys)
    
    # Note removed keys
    removed_keys = set(old_stats.keys()) - set(new_stats.keys())
    if removed_keys:
        changes["removed_metrics"] = list(removed_keys)
    
    return changes if changes else {"no_changes": True}


def get_scanner_version(scanner_file: str) -> str:
    """
    Extract version from scanner docstring or default
    
    Args:
        scanner_file: Path to the scanner Python file
        
    Returns:
        Version string
    """
    # For now, return a default version
    # Could be enhanced to extract from __version__ or docstring
    return "1.0.0"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "1m 23s" or "45.2s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"