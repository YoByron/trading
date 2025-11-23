#!/bin/bash

# .claude/hooks/check-documentation.sh
# Pre-commit hook to validate documentation consistency
#
# Created: November 23, 2025
# Purpose: Ensure documentation structure follows 2025 standards
#
# Checks:
# 1. No .md files in root (except README.md, LICENSE.md)
# 2. README.md contains links to all docs/ files
# 3. No broken links in documentation
# 4. Docs follow naming conventions (lowercase-with-hyphens.md)
# 5. Missing documentation for new features
#
# Usage: Automatically runs before each git commit
# Install: Linked via .git/hooks/pre-commit

set -e

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track errors and warnings
HAS_ERRORS=0
HAS_WARNINGS=0

echo -e "${BLUE}📚 Checking documentation structure...${NC}"

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

# Allowed root-level .md files
ALLOWED_ROOT_MD=(
    "README.md"
    "LICENSE.md"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
)

# ============================================================================
# CHECK 1: No .md files in root (except allowed ones)
# ============================================================================
echo -e "\n${BLUE}1️⃣  Checking for misplaced .md files in root...${NC}"

ROOT_MD_VIOLATIONS=()
for file in *.md; do
    # Skip if glob didn't match anything
    [ -e "$file" ] || continue

    # Check if this file is allowed
    ALLOWED=0
    for allowed in "${ALLOWED_ROOT_MD[@]}"; do
        if [ "$file" = "$allowed" ]; then
            ALLOWED=1
            break
        fi
    done

    # If not allowed and staged, it's a violation
    if [ "$ALLOWED" -eq 0 ] && echo "$STAGED_FILES" | grep -q "^${file}$"; then
        ROOT_MD_VIOLATIONS+=("$file")
    fi
done

if [ ${#ROOT_MD_VIOLATIONS[@]} -gt 0 ]; then
    echo -e "   ${RED}❌ ERROR: .md files found in root (should be in docs/)${NC}"
    for file in "${ROOT_MD_VIOLATIONS[@]}"; do
        echo -e "      ${RED}• $file${NC}"
    done
    echo -e "   ${YELLOW}Fix: Move to docs/ directory${NC}"
    echo -e "   ${BLUE}git mv $file docs/${NC}"
    HAS_ERRORS=1
else
    echo -e "   ${GREEN}✅ No misplaced .md files${NC}"
fi

# ============================================================================
# CHECK 2: README.md links to all docs/ files
# ============================================================================
echo -e "\n${BLUE}2️⃣  Checking README.md links to docs/ files...${NC}"

if [ -f "README.md" ]; then
    MISSING_LINKS=()

    # Find all .md files in docs/
    for doc_file in docs/*.md; do
        # Skip if glob didn't match anything
        [ -e "$doc_file" ] || continue

        # Check if README.md contains a link to this file
        if ! grep -q "docs/$(basename "$doc_file")" README.md; then
            MISSING_LINKS+=("$(basename "$doc_file")")
        fi
    done

    if [ ${#MISSING_LINKS[@]} -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  WARNING: docs/ files not linked in README.md${NC}"
        for file in "${MISSING_LINKS[@]}"; do
            echo -e "      ${YELLOW}• docs/$file${NC}"
        done
        echo -e "   ${YELLOW}Suggestion: Add links to README.md${NC}"
        HAS_WARNINGS=1
    else
        echo -e "   ${GREEN}✅ All docs/ files linked in README.md${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  WARNING: README.md not found${NC}"
    HAS_WARNINGS=1
fi

# ============================================================================
# CHECK 3: Broken links in documentation
# ============================================================================
echo -e "\n${BLUE}3️⃣  Checking for broken links in staged docs...${NC}"

BROKEN_LINKS=()

# Check staged .md files for broken internal links
for file in $STAGED_FILES; do
    # Skip non-.md files
    [[ "$file" =~ \.md$ ]] || continue

    # Skip if file doesn't exist (deleted)
    [ -e "$file" ] || continue

    # Extract markdown links: [text](path)
    # Look for relative links (not http/https)
    while IFS= read -r link; do
        # Skip external links
        [[ "$link" =~ ^http ]] && continue

        # Skip anchors
        [[ "$link" =~ ^# ]] && continue

        # Remove anchor from link if present
        link_path="${link%%#*}"

        # Resolve relative path
        if [[ "$link_path" =~ ^/ ]]; then
            # Absolute path from repo root
            target_path="${link_path:1}"
        else
            # Relative path from current file's directory
            file_dir=$(dirname "$file")
            target_path="$file_dir/$link_path"
        fi

        # Normalize path (remove ./ and ../)
        target_path=$(echo "$target_path" | sed 's|/\./|/|g')

        # Check if target exists
        if [ ! -e "$target_path" ]; then
            BROKEN_LINKS+=("$file -> $link_path (target not found: $target_path)")
        fi
    done < <(grep -oP '\[.*?\]\(\K[^)]+' "$file" 2>/dev/null || true)
done

if [ ${#BROKEN_LINKS[@]} -gt 0 ]; then
    echo -e "   ${YELLOW}⚠️  WARNING: Potential broken links detected${NC}"
    for link in "${BROKEN_LINKS[@]}"; do
        echo -e "      ${YELLOW}• $link${NC}"
    done
    echo -e "   ${YELLOW}Verify these links are correct${NC}"
    HAS_WARNINGS=1
else
    echo -e "   ${GREEN}✅ No broken links detected${NC}"
fi

# ============================================================================
# CHECK 4: Naming conventions (lowercase-with-hyphens.md)
# ============================================================================
echo -e "\n${BLUE}4️⃣  Checking documentation naming conventions...${NC}"

NAMING_VIOLATIONS=()

for file in $STAGED_FILES; do
    # Only check .md files in docs/
    [[ "$file" =~ ^docs/.*\.md$ ]] || continue

    # Skip if file doesn't exist (deleted)
    [ -e "$file" ] || continue

    filename=$(basename "$file")

    # Check if filename matches convention: lowercase letters, numbers, hyphens only
    if [[ ! "$filename" =~ ^[a-z0-9-]+\.md$ ]]; then
        NAMING_VIOLATIONS+=("$file")
    fi
done

if [ ${#NAMING_VIOLATIONS[@]} -gt 0 ]; then
    echo -e "   ${YELLOW}⚠️  WARNING: Files don't follow naming convention${NC}"
    echo -e "   ${YELLOW}Expected: lowercase-with-hyphens.md${NC}"
    for file in "${NAMING_VIOLATIONS[@]}"; do
        echo -e "      ${YELLOW}• $file${NC}"
        # Suggest correct name
        correct_name=$(basename "$file" | tr '[:upper:]' '[:lower:]' | tr '_' '-' | tr -s '-')
        echo -e "      ${BLUE}Suggested: docs/$correct_name${NC}"
    done
    HAS_WARNINGS=1
else
    echo -e "   ${GREEN}✅ All docs follow naming convention${NC}"
fi

# ============================================================================
# CHECK 5: Missing documentation for new features
# ============================================================================
echo -e "\n${BLUE}5️⃣  Checking for undocumented new features...${NC}"

POTENTIAL_FEATURES=()

# Look for new Python files in src/ that might need documentation
for file in $STAGED_FILES; do
    # Check for new .py files in src/
    if [[ "$file" =~ ^src/.*\.py$ ]] && [ -e "$file" ]; then
        # Check if file is new (added in this commit)
        if ! git ls-tree -r HEAD --name-only | grep -q "^${file}$"; then
            # This is a new file
            # Check if it contains class or function definitions (likely a feature)
            if grep -qE '^(class |def )' "$file"; then
                POTENTIAL_FEATURES+=("$file")
            fi
        fi
    fi
done

if [ ${#POTENTIAL_FEATURES[@]} -gt 0 ]; then
    echo -e "   ${YELLOW}⚠️  INFO: New Python modules detected${NC}"
    echo -e "   ${YELLOW}Consider documenting these features:${NC}"
    for file in "${POTENTIAL_FEATURES[@]}"; do
        echo -e "      ${YELLOW}• $file${NC}"
    done
    echo -e "   ${BLUE}Suggestion: Add docs/feature-name.md if appropriate${NC}"
    # This is just informational, not a warning
else
    echo -e "   ${GREEN}✅ No new features requiring documentation${NC}"
fi

# ============================================================================
# FINAL VERDICT
# ============================================================================
echo ""

if [ "$HAS_ERRORS" -eq 1 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ COMMIT BLOCKED - Documentation errors detected!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}🔧 How to Fix:${NC}"
    echo ""
    echo -e "   1. Move misplaced .md files to docs/ directory:"
    echo -e "      ${BLUE}git mv [file].md docs/${NC}"
    echo ""
    echo -e "   2. Update README.md with links to all docs:"
    echo -e "      ${BLUE}# Add to README.md:${NC}"
    echo -e "      ${BLUE}See [docs/filename.md](docs/filename.md) for details${NC}"
    echo ""
    echo -e "   3. Re-stage and commit:"
    echo -e "      ${BLUE}git add README.md docs/new-file.md${NC}"
    echo -e "      ${BLUE}git commit -m \"Fix documentation structure\"${NC}"
    echo ""
    echo -e "${YELLOW}📚 Reference:${NC}"
    echo -e "   - Documentation standards: .claude/CLAUDE.md (Documentation Protocol)"
    echo -e "   - Nov 2025 best practices: All .md files in docs/ (except README.md)"
    echo ""
    exit 1
elif [ "$HAS_WARNINGS" -eq 1 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  WARNING - Documentation improvements recommended${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}💡 Recommendations:${NC}"
    echo -e "   - Add missing links to README.md"
    echo -e "   - Fix broken links if any"
    echo -e "   - Follow naming conventions (lowercase-with-hyphens.md)"
    echo -e "   - Document new features in docs/"
    echo ""
    echo -e "${GREEN}✅ Commit allowed (warnings only)${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All documentation checks passed - Commit allowed${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 0
fi
