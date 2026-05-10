#!/bin/bash

set -u

# Engine surface verification script
# Retains the historical filename for continuity, but validates the current
# repo layout rather than the older .claude-era Phase 1 extraction.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

REQUIRED_FILES=(
  "templates/engine/README.md"
  "templates/engine/MODULARIZATION-COMPLETE.md"
  "templates/engine/activation/context-aware.md"
  "templates/engine/core/codex-readiness.md"
  "templates/engine/core/enforcement-check.md"
  "templates/engine/core/pre-ultrathink.md"
  "templates/engine/core/session-resolver.md"
  "templates/engine/core/ultrathink-protocol.md"
  "templates/engine/debugging/system-debug.md"
  "templates/engine/enforcement/behavioral-hooks.md"
  "templates/engine/enforcement/cannot-proceed.md"
  "templates/engine/enforcement/meta-workflow-guard-ci-plan.md"
  "templates/engine/enforcement/meta-workflow-guard-remediation.md"
  "templates/engine/examples/practical.md"
  "templates/engine/execution/swhe-format.md"
  "templates/engine/fallbacks/error-handling.md"
  "templates/engine/navigation/common-flows.md"
  "templates/engine/navigation/template-protocol.md"
  "templates/engine/structure/template-system.md"
  "templates/engine/validation/ENFORCEMENT-SUMMARY.md"
  "templates/engine/validation/foundation-adoption-guide.md"
  "templates/engine/validation/integration-guide.md"
  "templates/engine/validation/validation-framework.md"
)

FRONTMATTER_CHECKS=(
  "templates/engine/core/enforcement-check.md|id|enforcement-check|critical-enforcement"
  "templates/engine/core/pre-ultrathink.md|id|pre-ultrathink-protocol|critical-enforcement"
  "templates/engine/core/session-resolver.md|id|session-resolver|engine-component"
  "templates/engine/core/ultrathink-protocol.md|id|ultrathink-protocol|engine-component"
  "templates/engine/enforcement/behavioral-hooks.md|id|behavioral-hooks|engine-component"
  "templates/engine/enforcement/cannot-proceed.md|id|cannot-proceed|engine-component"
  "templates/engine/enforcement/meta-workflow-guard-ci-plan.md|id|meta-workflow-guard-ci-plan|enforcement-plan"
  "templates/engine/examples/practical.md|id|practical-examples|engine-component"
  "templates/engine/navigation/common-flows.md|id|common-request-flows|engine-component"
  "templates/engine/structure/template-system.md|id|template-system-structure|engine-component"
  "templates/engine/validation/foundation-adoption-guide.md|name|foundation-adoption-guide|documentation"
  "templates/engine/validation/integration-guide.md|name|integration-guide|documentation"
  "templates/engine/validation/validation-framework.md|name|validation-framework|enforcement"
)

DISCOVERY_REFERENCES=(
  "templates/registry/index.json|templates/engine/core/session-resolver.md"
  "templates/registry/index.json|templates/engine/enforcement/behavioral-hooks.md"
  "templates/registry/index.json|templates/engine/navigation/template-protocol.md"
  "templates/registry/index.json|templates/engine/validation/foundation-adoption-guide.md"
  "templates/registry/index.json|templates/engine/validation/integration-guide.md"
  "templates/registry/index.json|templates/engine/validation/validation-framework.md"
  "templates/metadata/template-inventory.txt|templates/engine/core/codex-readiness.md"
  "templates/metadata/template-inventory.txt|templates/engine/core/session-resolver.md"
  "templates/metadata/template-inventory.txt|templates/engine/enforcement/behavioral-hooks.md"
  "templates/metadata/template-inventory.txt|templates/engine/validation/foundation-adoption-guide.md"
  "templates/metadata/template-overview.md|templates/engine/core/session-resolver.md"
  "templates/metadata/template-overview.md|templates/engine/validation/foundation-adoption-guide.md"
  "templates/metadata/template-overview.md|templates/engine/validation/validation-framework.md"
  "templates/metadata/template-summary.csv|templates/engine/core/session-resolver.md"
  "templates/metadata/template-summary.csv|templates/engine/validation/foundation-adoption-guide.md"
  "templates/metadata/template-summary.csv|templates/engine/validation/validation-framework.md"
)

STALE_REFERENCES=(
  "execution-engine.md"
  "mode-detection.md"
  "explicit.md"
  "implicit.md"
  "behavioral.md"
  "protocol-echo.md"
  "handler-validation.md"
  "evidence-based.md"
  "handler-loading.md"
  "natural-execution.md"
  ".claude/templates/engine"
)

pass() {
  echo -e "${GREEN}✓${NC} $1"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
  echo -e "${RED}✗${NC} $1"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

check_file_exists() {
  local file_path="$1"
  if [ -f "$file_path" ]; then
    pass "File exists: $file_path"
  else
    fail "Missing file: $file_path"
  fi
}

check_frontmatter() {
  local file_path="$1"
  local metadata_key="$2"
  local expected_value="$3"
  local expected_type="$4"

  echo "Checking metadata: $file_path"

  if [ ! -f "$file_path" ]; then
    fail "Missing file for metadata check: $file_path"
    return
  fi

  if grep -q "^---$" "$file_path"; then
    pass "Frontmatter block present in $file_path"
  else
    fail "Missing frontmatter block in $file_path"
  fi

  if grep -q "^${metadata_key}: ${expected_value}$" "$file_path"; then
    pass "Correct ${metadata_key} in $file_path"
  else
    fail "Incorrect ${metadata_key} in $file_path (expected $expected_value)"
  fi

  if grep -q "^type: $expected_type$" "$file_path"; then
    pass "Correct type in $file_path"
  else
    fail "Incorrect type in $file_path (expected $expected_type)"
  fi
}

check_contains() {
  local file_path="$1"
  local pattern="$2"
  if grep -q "$pattern" "$file_path"; then
    pass "Reference present in $file_path: $pattern"
  else
    fail "Missing reference in $file_path: $pattern"
  fi
}

check_absent() {
  local file_path="$1"
  local pattern="$2"
  if grep -q "$pattern" "$file_path"; then
    fail "Unexpected stale reference in $file_path: $pattern"
  else
    pass "No stale reference in $file_path: $pattern"
  fi
}

echo "=== Current Engine Surface Verification ==="
echo ""

echo "=== Required Files ==="
for file_path in "${REQUIRED_FILES[@]}"; do
  check_file_exists "$file_path"
done
echo ""

echo "=== Frontmatter Checks ==="
for check in "${FRONTMATTER_CHECKS[@]}"; do
  IFS='|' read -r file_path metadata_key expected_value expected_type <<< "$check"
  check_frontmatter "$file_path" "$metadata_key" "$expected_value" "$expected_type"
done
echo ""

echo "=== Discovery Surface Checks ==="
for check in "${DISCOVERY_REFERENCES[@]}"; do
  IFS='|' read -r file_path pattern <<< "$check"
  check_contains "$file_path" "$pattern"
done
echo ""

echo "=== Current Layout Checks ==="
check_contains "CLAUDE.md" "@\\./\\.taskmaster/CLAUDE\\.md"
for stale in "${STALE_REFERENCES[@]}"; do
  check_absent "templates/engine/README.md" "$stale"
done
check_absent "CLAUDE.md" "\\.claude/templates/engine"
echo ""

echo "=== Test Summary ==="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"

if [ "$TESTS_FAILED" -eq 0 ]; then
  echo -e "\n${GREEN}✓ Current engine surface verification passed.${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Current engine surface verification failed.${NC}"
  exit 1
fi
