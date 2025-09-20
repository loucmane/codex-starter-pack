#!/bin/bash
# Apply all template system fixes
# Generated: 2025-09-20T16:43:41.415746

set -e

echo 'Applying all template system fixes...'
echo 'This will:'
echo '  - Fix 181 broken references'
echo '  - Remove 0 duplicate files'
echo '  - Move 0 files'
echo
read -p 'Continue? (y/n) ' -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

python3 output/scripts/apply_reference_fixes.py

# For file reorganization, use: python3 safe_reorganize.py --execute

echo 'All fixes applied!'
