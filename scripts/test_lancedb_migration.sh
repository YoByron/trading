#!/bin/bash
# Test LanceDB Migration End-to-End
#
# This script:
# 1. Checks dependencies
# 2. Runs dry-run migration
# 3. Runs actual migration
# 4. Verifies migration
# 5. Reports results

set -e  # Exit on error

echo "========================================"
echo "LanceDB Migration Test Suite"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Step 1: Check dependencies
print_info "Checking dependencies..."
DEPS_MISSING=0

for package in lancedb fastembed pyarrow tqdm chromadb; do
    if python3 -c "import $package" 2>/dev/null; then
        print_status 0 "$package installed"
    else
        print_status 1 "$package NOT installed"
        DEPS_MISSING=1
    fi
done

if [ $DEPS_MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing dependencies! Install with:${NC}"
    echo "pip install lancedb fastembed pyarrow tqdm chromadb"
    exit 1
fi

echo ""

# Step 2: Dry run
print_info "Running dry-run migration..."
if python3 scripts/migrate_to_lancedb.py --dry-run; then
    print_status 0 "Dry run completed"
else
    print_status 1 "Dry run failed"
    exit 1
fi

echo ""
read -p "Continue with actual migration? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled by user"
    exit 0
fi

# Step 3: Run migration
print_info "Running actual migration..."
if python3 scripts/migrate_to_lancedb.py --source all; then
    print_status 0 "Migration completed"
else
    print_status 1 "Migration failed"
    exit 1
fi

echo ""

# Step 4: Verify migration
print_info "Verifying migration..."
if python3 scripts/verify_lancedb_migration.py; then
    print_status 0 "Verification passed"
else
    print_status 1 "Verification failed"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}✓ Migration test completed successfully!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Review migration statistics above"
echo "2. Test vector search manually"
echo "3. Update RAG code to use LanceDB"
echo "4. Run integration tests"
echo ""
