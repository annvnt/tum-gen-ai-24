#!/bin/bash

# Webpack Gitignore Verification Script
# This script verifies that webpack cache files are properly ignored by git

echo "=== Webpack Gitignore Verification ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Check if .gitignore exists
if [ ! -f .gitignore ]; then
    echo -e "${RED}Error: .gitignore file not found${NC}"
    exit 1
fi

# Test 1: Check if webpack patterns are in .gitignore
echo "1. Checking .gitignore for webpack patterns..."
PATTERNS=(
    "*.pack"
    "*.pack.gz"
    "*.hot-update.js"
    "*.hot-update.json"
    ".next/"
)

for pattern in "${PATTERNS[@]}"; do
    if grep -q "$pattern" .gitignore; then
        echo -e "${GREEN}  ✓ Found pattern: $pattern${NC}"
    else
        echo -e "${RED}  ✗ Missing pattern: $pattern${NC}"
    fi
done

echo

# Test 2: Check if any webpack files are currently tracked
echo "2. Checking for tracked webpack cache files..."
TRACKED_FILES=$(git ls-files | grep -E '\.(pack|pack\.gz|hot-update)' || echo "")

if [ -z "$TRACKED_FILES" ]; then
    echo -e "${GREEN}✓ No webpack cache files are tracked by git${NC}"
else
    echo -e "${RED}✗ Found tracked webpack cache files:${NC}"
    echo "$TRACKED_FILES" | sed 's/^/  - /'
fi

echo

# Test 3: Check if .next directory is properly ignored
echo "3. Checking .next directory ignore status..."
NEXT_IGNORED=$(git check-ignore .next 2>/dev/null; echo $?)
if [ $NEXT_IGNORED -eq 0 ]; then
    echo -e "${GREEN}✓ .next directory is properly ignored${NC}"
else
    echo -e "${RED}✗ .next directory is not properly ignored${NC}"
fi

echo

# Test 4: Simulate creating webpack cache files
echo "4. Testing ignore rules with simulated webpack files..."

# Create test files
test_files=(
    "test.pack"
    "test.pack.gz"
    "test.hot-update.js"
    "test.hot-update.json"
    "webpack-cache/test.pack"
)

# Create directory for test
mkdir -p webpack-cache

for file in "${test_files[@]}"; do
    touch "$file" 2>/dev/null || true
    
    IGNORED=$(git check-ignore "$file" 2>/dev/null; echo $?)
    if [ $IGNORED -eq 0 ]; then
        echo -e "${GREEN}  ✓ $file is properly ignored${NC}"
    else
        echo -e "${RED}  ✗ $file is NOT ignored${NC}"
    fi
done

# Clean up test files
rm -f test.pack test.pack.gz test.hot-update.js test.hot-update.json
rm -rf webpack-cache

echo

# Test 5: Check for any remaining build artifacts
echo "5. Checking for remaining build artifacts..."
BUILD_ARTIFACTS=$(find . -type f \( -name "*.pack" -o -name "*.pack.gz" -o -name "*.hot-update.*" \) -not -path "./node_modules/*" -not -path "./.git/*" 2>/dev/null)

if [ -z "$BUILD_ARTIFACTS" ]; then
    echo -e "${GREEN}✓ No webpack cache files found in working directory${NC}"
else
    echo -e "${YELLOW}! Found webpack cache files in working directory:${NC}"
    echo "$BUILD_ARTIFACTS" | sed 's/^/  - /'
    echo
    echo -e "${YELLOW}These files should be ignored by the updated .gitignore${NC}"
fi

echo

echo "=== Summary ==="
echo "Run 'git status' to see current state"
echo "Run './verify_gitignore.sh' anytime to re-verify"
echo
echo "Note: If you have existing webpack cache files in your working directory,"
echo "they may still appear in 'git status' as untracked. This is expected behavior."