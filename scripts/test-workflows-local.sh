#!/bin/bash
# Local workflow testing script using ACT
# Tests GitHub Actions workflows before pushing to prevent failures

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Testing GitHub Actions Workflows Locally${NC}\n"

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}❌ ACT is not installed!${NC}"
    echo ""
    echo "Install with:"
    echo "  brew install act"
    echo ""
    echo "Or:"
    echo "  curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Start Docker Desktop and try again."
    exit 1
fi

# Check if .actrc exists
if [ ! -f .actrc ]; then
    echo -e "${YELLOW}⚠️  .actrc not found. Creating default configuration...${NC}"
    cat > .actrc << 'EOF'
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P macos-latest=catthehacker/macos:act-latest
--reuse
-v
EOF
fi

# Get list of workflow files
WORKFLOW_DIR=".github/workflows"
WORKFLOWS=$(find "$WORKFLOW_DIR" -name "*.yml" -o -name "*.yaml" | grep -v ".disabled" | sort)

if [ -z "$WORKFLOWS" ]; then
    echo -e "${RED}❌ No workflow files found in $WORKFLOW_DIR${NC}"
    exit 1
fi

echo "📋 Found $(echo "$WORKFLOWS" | wc -l | tr -d ' ') workflow(s) to test\n"

# Test each workflow
FAILED=0
PASSED=0
SKIPPED=0

for workflow in $WORKFLOWS; do
    workflow_name=$(basename "$workflow")
    
    # Skip workflows that require secrets or external services for basic testing
    if [[ "$workflow_name" == *"diagnose"* ]] || \
       [[ "$workflow_name" == *"notify"* ]] || \
       [[ "$workflow_name" == *"health-check"* ]]; then
        echo -e "${YELLOW}⏭️  Skipping $workflow_name (requires GitHub API)${NC}"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    echo -e "${GREEN}Testing: $workflow_name${NC}"
    
    # Test workflow syntax with act (dry-run)
    if act workflow_dispatch --workflows "$workflow" --dryrun 2>&1 | grep -q "Error"; then
        echo -e "${RED}❌ $workflow_name: Syntax error detected${NC}"
        FAILED=$((FAILED + 1))
    else
        echo -e "${GREEN}✅ $workflow_name: Syntax valid${NC}"
        PASSED=$((PASSED + 1))
    fi
    echo ""
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${YELLOW}⏭️  Skipped: $SKIPPED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: $FAILED${NC}"
    echo ""
    echo "Fix the errors above before pushing to GitHub!"
    exit 1
else
    echo -e "${GREEN}✅ All tested workflows passed!${NC}"
    exit 0
fi

