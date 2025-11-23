#!/bin/bash

# .claude/hooks/check-file-sizes.sh
# Pre-commit hook to enforce file size limits on .claude/ directory files
#
# Created: November 23, 2025
# Purpose: Prevent oversized CLAUDE.md and other .claude files from degrading performance
#
# Usage: Automatically runs before each git commit
# Install: ln -sf ../../.claude/hooks/check-file-sizes.sh .git/hooks/pre-commit

set -e

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# File size limits (in characters)
CLAUDE_MD_WARNING=32000  # 80% of max (warning threshold)
CLAUDE_MD_MAX=40000      # Hard limit for .claude/CLAUDE.md
GENERAL_WARNING=20000    # Warning for other .claude/ files
GENERAL_MAX=25000        # Hard limit for other .claude/ files

# Track if any errors occurred
HAS_ERRORS=0
HAS_WARNINGS=0

echo -e "${BLUE}🔍 Checking .claude/ file sizes...${NC}"

# Function to check file size
check_file_size() {
    local file="$1"
    local warning_limit="$2"
    local max_limit="$3"

    if [ ! -f "$file" ]; then
        return
    fi

    # Get file size in characters
    local size=$(wc -c < "$file" | tr -d ' ')

    # Calculate percentage of max
    local percent=$((size * 100 / max_limit))

    # Check if file is staged for commit
    if ! git diff --cached --name-only | grep -q "^${file}$"; then
        # File not staged, skip
        return
    fi

    echo -e "\n📄 ${file}"
    echo -e "   Size: ${size} characters"

    if [ "$size" -gt "$max_limit" ]; then
        echo -e "   ${RED}❌ ERROR: Exceeds maximum (${max_limit} chars) - ${percent}% of limit${NC}"
        echo -e "   ${RED}   This file is TOO LARGE and will degrade performance!${NC}"
        HAS_ERRORS=1
    elif [ "$size" -gt "$warning_limit" ]; then
        echo -e "   ${YELLOW}⚠️  WARNING: Approaching maximum (${max_limit} chars) - ${percent}% of limit${NC}"
        echo -e "   ${YELLOW}   Consider extracting detailed content to docs/ directory${NC}"
        HAS_WARNINGS=1
    else
        echo -e "   ${GREEN}✅ OK - ${percent}% of limit${NC}"
    fi
}

# Check .claude/CLAUDE.md (highest priority)
check_file_size ".claude/CLAUDE.md" "$CLAUDE_MD_WARNING" "$CLAUDE_MD_MAX"

# Check other .claude/ markdown files
for file in .claude/*.md; do
    if [ -f "$file" ] && [ "$file" != ".claude/CLAUDE.md" ]; then
        check_file_size "$file" "$GENERAL_WARNING" "$GENERAL_MAX"
    fi
done

# Check .claude subdirectories
for file in .claude/*/*.md; do
    if [ -f "$file" ]; then
        check_file_size "$file" "$GENERAL_WARNING" "$GENERAL_MAX"
    fi
done

echo ""

# Final verdict
if [ "$HAS_ERRORS" -eq 1 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ COMMIT BLOCKED - File size errors detected!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}🔧 How to Fix:${NC}"
    echo ""
    echo -e "   1. Extract detailed content to docs/ directory:"
    echo -e "      ${BLUE}claude \"Use claude-md-optimizer skill to optimize CLAUDE.md\"${NC}"
    echo ""
    echo -e "   2. Or manually:"
    echo -e "      - Move detailed sections to docs/*.md files"
    echo -e "      - Replace with concise summaries + links"
    echo -e "      - Keep file under 40,000 characters"
    echo ""
    echo -e "   3. Re-stage and commit:"
    echo -e "      ${BLUE}git add .claude/CLAUDE.md docs/new-file.md${NC}"
    echo -e "      ${BLUE}git commit -m \"Optimize CLAUDE.md file size\"${NC}"
    echo ""
    echo -e "${YELLOW}📚 Reference:${NC}"
    echo -e "   - Skill documentation: .claude/skills/claude-md-optimizer.md"
    echo -e "   - Nov 2025 best practices: Keep CLAUDE.md <40k chars"
    echo ""
    exit 1
elif [ "$HAS_WARNINGS" -eq 1 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  WARNING - Files approaching size limits${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}💡 Recommendation:${NC}"
    echo -e "   Consider optimizing before files get too large."
    echo -e "   Run: ${BLUE}claude \"Use claude-md-optimizer skill\"${NC}"
    echo ""
    echo -e "${GREEN}✅ Commit allowed (warning only)${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All file sizes OK - Commit allowed${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 0
fi
