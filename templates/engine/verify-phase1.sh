#!/bin/bash

# Phase 1 Modularization Verification Script
# Tests that extracted modules exist and contain expected content

echo "=== Phase 1 Modularization Verification ==="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Counter for tests
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check if file exists and contains expected content
check_module() {
    local file_path=$1
    local expected_id=$2
    local expected_type=$3
    
    echo "Checking: $file_path"
    
    # Check if file exists
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✓${NC} File exists"
        ((TESTS_PASSED++))
        
        # Check for YAML frontmatter
        if grep -q "^---$" "$file_path" && grep -q "^id: $expected_id$" "$file_path"; then
            echo -e "${GREEN}✓${NC} Has valid YAML frontmatter with id: $expected_id"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗${NC} Missing or invalid YAML frontmatter"
            ((TESTS_FAILED++))
        fi
        
        # Check for type
        if grep -q "^type: $expected_type$" "$file_path"; then
            echo -e "${GREEN}✓${NC} Has correct type: $expected_type"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗${NC} Missing or incorrect type"
            ((TESTS_FAILED++))
        fi
        
        # Check for dependencies
        if grep -q "^dependencies:" "$file_path"; then
            echo -e "${GREEN}✓${NC} Has dependencies section"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗${NC} Missing dependencies section"
            ((TESTS_FAILED++))
        fi
        
        # Check for exports
        if grep -q "^exports:" "$file_path"; then
            echo -e "${GREEN}✓${NC} Has exports section"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗${NC} Missing exports section"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "${RED}✗${NC} File not found!"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Test each module
echo "=== Testing Extracted Modules ==="
echo ""

check_module ".claude/templates/engine/examples/practical.md" "practical-examples" "engine-component"
check_module ".claude/templates/engine/navigation/common-flows.md" "common-request-flows" "engine-component"
check_module ".claude/templates/engine/structure/template-system.md" "template-system-structure" "engine-component"

# Check CLAUDE.md for references
echo "=== Testing CLAUDE.md References ==="
echo ""

if grep -q "<!-- Import: .claude/templates/engine/navigation/common-flows.md -->" "CLAUDE.md"; then
    echo -e "${GREEN}✓${NC} CLAUDE.md has reference to common-flows.md"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Missing reference to common-flows.md"
    ((TESTS_FAILED++))
fi

if grep -q "<!-- Import: .claude/templates/engine/structure/template-system.md -->" "CLAUDE.md"; then
    echo -e "${GREEN}✓${NC} CLAUDE.md has reference to template-system.md"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Missing reference to template-system.md"
    ((TESTS_FAILED++))
fi

if grep -q "<!-- Import: .claude/templates/engine/examples/practical.md -->" "CLAUDE.md"; then
    echo -e "${GREEN}✓${NC} CLAUDE.md has reference to practical.md"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Missing reference to practical.md"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo "=== Test Summary ==="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! Phase 1 modularization successful.${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please review the modularization.${NC}"
    exit 1
fi