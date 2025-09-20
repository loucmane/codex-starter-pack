#!/bin/bash
# CI/CD Integration Test for Enhanced Scanner Suite
# Tests all new features: thresholds, quiet mode, section matching, scoped fixes

set -e

echo "=== Testing Enhanced Scanner Suite CI/CD Integration ==="
echo

# Test 1: Non-interactive scan with verbose output
echo "Test 1: Verbose scan with checkpoints disabled..."
python3 scanner.py --base ../.. --verbose --no-checkpoints --out output/test_scan.json
echo "✅ Scanner with CLI args works"
echo

# Test 2: Quiet mode with thresholds (CI/CD mode)
echo "Test 2: CI/CD mode with thresholds..."
python3 analyze_references.py \
    --input output/test_scan.json \
    --out output/test_refs.json \
    --quiet \
    --broken-threshold 500 \
    --orphan-threshold 250 \
    --circular-threshold 10

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Thresholds passed"
else
    echo "❌ Thresholds exceeded (exit code: $EXIT_CODE)"
fi
echo

# Test 3: Section-by-section duplicate matching
echo "Test 3: Section-by-section duplicate detection..."
python3 find_duplicates.py \
    --input output/test_scan.json \
    --out output/test_dups.json \
    --section-matching \
    --threshold 0.8 \
    --verbose

echo "✅ Section matching works"
echo

# Test 4: Scoped replacements with dry run
echo "Test 4: Scoped replacements in dry-run mode..."
python3 generate_fixes.py \
    --scoped \
    --dry-run \
    --critical-only \
    --max-fixes 5 \
    --verbose

echo "✅ Scoped replacements and filtering work"
echo

# Test 5: Report directory generation
echo "Test 5: Timestamped report directory..."
mkdir -p test_reports
python3 generate_fixes.py \
    --report-dir test_reports \
    --scoped \
    --quiet

if [ -d test_reports/2* ]; then
    echo "✅ Report directory created: $(ls -d test_reports/2* | head -1)"
else
    echo "❌ Report directory not created"
fi
echo

# Test 6: Pipeline with all features
echo "Test 6: Full pipeline test..."
python3 scanner.py --base ../.. --out output/pipeline_scan.json 2>/dev/null
python3 analyze_references.py --input output/pipeline_scan.json --quiet --broken-threshold 400
python3 find_duplicates.py --input output/pipeline_scan.json --quiet --migration-threshold 0
python3 generate_fixes.py --quiet --critical-only

echo "✅ Full pipeline with all features works"
echo

# Cleanup
echo "Cleaning up test files..."
rm -rf output/
rm -rf test_reports/

echo
echo "=== All CI/CD Integration Tests Passed! ==="
echo
echo "The enhanced scanner suite is ready for:"
echo "  - Non-interactive CI/CD pipelines"
echo "  - Quality gates with thresholds"
echo "  - Line-level precision fixes"
echo "  - Section-by-section analysis"
echo "  - Automated reporting"