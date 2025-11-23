#!/bin/bash

# Unused File Detection System
# Detects orphaned files across Python, JSON, docs, tests, scripts, and configs
# Exit code: 0 (warnings only - doesn't block commits)

set -euo pipefail

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(git rev-parse --show-toplevel)"
DAYS_THRESHOLD=90
TODAY=$(date +%s)

# Whitelisted files (always keep)
WHITELIST=(
    "main.py"
    "README.md"
    "LICENSE"
    ".gitignore"
    ".env.example"
    "requirements.txt"
    "pyproject.toml"
    "setup.py"
    "Dockerfile"
    "docker-compose.yml"
    ".claude/CLAUDE.md"
    ".claude/hooks/pre-commit"
    "src/__init__.py"
)

# Arrays to track findings
declare -a HIGH_CONFIDENCE=()
declare -a MEDIUM_CONFIDENCE=()
declare -a KEEP_FILES=()

# Helper: Check if file is whitelisted
is_whitelisted() {
    local file="$1"
    local basename=$(basename "$file")

    for whitelist_file in "${WHITELIST[@]}"; do
        if [[ "$file" == *"$whitelist_file"* ]]; then
            return 0
        fi
    done
    return 1
}

# Helper: Get last modification date in days
get_file_age_days() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        echo "0"
        return
    fi

    # Get last commit date for this file
    local last_commit_date=$(git log -1 --format="%at" -- "$file" 2>/dev/null || echo "0")

    if [[ "$last_commit_date" == "0" ]]; then
        # File not in git yet, use filesystem date
        if [[ "$(uname)" == "Darwin" ]]; then
            last_commit_date=$(stat -f "%m" "$file")
        else
            last_commit_date=$(stat -c "%Y" "$file")
        fi
    fi

    local age_seconds=$((TODAY - last_commit_date))
    local age_days=$((age_seconds / 86400))

    echo "$age_days"
}

# Helper: Count references to a file
count_references() {
    local file="$1"
    local basename=$(basename "$file")
    local name_without_ext="${basename%.*}"

    local count=0

    # Search for Python imports
    if [[ "$file" == *.py ]]; then
        # Convert path to module notation (src/core/main.py -> src.core.main)
        local module_path="${file%.py}"
        module_path="${module_path//\//.}"

        # Search for various import patterns
        count=$((count + $(grep -r "import $name_without_ext" "$REPO_ROOT" --include="*.py" 2>/dev/null | wc -l || echo 0)))
        count=$((count + $(grep -r "from .* import.*$name_without_ext" "$REPO_ROOT" --include="*.py" 2>/dev/null | wc -l || echo 0)))
        count=$((count + $(grep -r "$module_path" "$REPO_ROOT" --include="*.py" 2>/dev/null | wc -l || echo 0)))
    fi

    # Search for JSON/data file references
    if [[ "$file" == *.json ]] || [[ "$file" == *.csv ]] || [[ "$file" == *.txt ]]; then
        count=$((count + $(grep -r "$basename" "$REPO_ROOT" --include="*.py" --include="*.sh" 2>/dev/null | wc -l || echo 0)))
    fi

    # Search for documentation links
    if [[ "$file" == *.md ]]; then
        count=$((count + $(grep -r "$basename" "$REPO_ROOT" --include="*.md" 2>/dev/null | grep -v "^$file:" | wc -l || echo 0)))
    fi

    # Search for script references
    if [[ "$file" == *.sh ]]; then
        count=$((count + $(grep -r "$basename" "$REPO_ROOT" --include="*.sh" --include="*.py" --include="*.yml" --include="*.yaml" 2>/dev/null | grep -v "^$file:" | wc -l || echo 0)))
    fi

    # Search for config file references
    if [[ "$file" == *.yml ]] || [[ "$file" == *.yaml ]] || [[ "$file" == *.toml ]] || [[ "$file" == *.ini ]]; then
        count=$((count + $(grep -r "$basename" "$REPO_ROOT" --include="*.py" --include="*.sh" --include="*.md" 2>/dev/null | grep -v "^$file:" | wc -l || echo 0)))
    fi

    echo "$count"
}

# Helper: Check if test file has corresponding source
test_has_source() {
    local test_file="$1"
    local basename=$(basename "$test_file")

    # Extract module name (test_foo.py -> foo.py)
    if [[ "$basename" == test_*.py ]]; then
        local source_name="${basename#test_}"

        # Search for source file
        if find "$REPO_ROOT/src" -name "$source_name" -type f 2>/dev/null | grep -q .; then
            return 0
        fi
    fi

    return 1
}

# Helper: Check if config is for installed tool
config_tool_installed() {
    local config_file="$1"
    local basename=$(basename "$config_file")

    # Map config files to tools
    case "$basename" in
        ".flake8"|"flake8.cfg")
            grep -q "flake8" "$REPO_ROOT/requirements.txt" 2>/dev/null && return 0
            ;;
        ".pylintrc"|"pylint.cfg")
            grep -q "pylint" "$REPO_ROOT/requirements.txt" 2>/dev/null && return 0
            ;;
        ".mypy.ini"|"mypy.ini")
            grep -q "mypy" "$REPO_ROOT/requirements.txt" 2>/dev/null && return 0
            ;;
        "pytest.ini"|".pytest.ini")
            grep -q "pytest" "$REPO_ROOT/requirements.txt" 2>/dev/null && return 0
            ;;
        ".coveragerc")
            grep -q "coverage" "$REPO_ROOT/requirements.txt" 2>/dev/null && return 0
            ;;
    esac

    return 1
}

# Main detection function
detect_unused_files() {
    echo -e "${BLUE}🔍 Scanning for unused files (threshold: ${DAYS_THRESHOLD}+ days, no references)...${NC}\n"

    cd "$REPO_ROOT"

    # Get all tracked files
    while IFS= read -r file; do
        # Skip directories
        [[ -d "$file" ]] && continue

        # Skip whitelisted files
        is_whitelisted "$file" && continue

        # Get file age
        local age=$(get_file_age_days "$file")

        # Only check files older than threshold
        if [[ "$age" -lt "$DAYS_THRESHOLD" ]]; then
            continue
        fi

        # Count references
        local refs=$(count_references "$file")

        # Classify file
        local classification=""
        local reason=""

        if [[ "$refs" -eq 0 ]]; then
            # Special cases
            if [[ "$file" == */test_*.py ]]; then
                if ! test_has_source "$file"; then
                    classification="HIGH"
                    reason="test for non-existent code"
                else
                    classification="KEEP"
                    reason="valid test file"
                fi
            elif [[ "$file" == *.yml ]] || [[ "$file" == *.yaml ]] || [[ "$file" == *.ini ]] || [[ "$file" == *.toml ]]; then
                if ! config_tool_installed "$file"; then
                    classification="HIGH"
                    reason="config for non-installed tool"
                else
                    classification="KEEP"
                    reason="valid config file"
                fi
            else
                classification="HIGH"
                reason="no imports/references"
            fi
        elif [[ "$refs" -le 2 ]]; then
            classification="MEDIUM"
            reason="$refs reference(s)"
        else
            classification="KEEP"
            reason="actively used ($refs references)"
        fi

        # Store results
        local file_info="$file (last used: ${age} days ago, ${reason})"

        case "$classification" in
            HIGH)
                HIGH_CONFIDENCE+=("$file_info")
                ;;
            MEDIUM)
                MEDIUM_CONFIDENCE+=("$file_info")
                ;;
            KEEP)
                KEEP_FILES+=("$file_info")
                ;;
        esac

    done < <(git ls-files)
}

# Print results
print_results() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🗑️  UNUSED FILE DETECTION REPORT${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # High confidence
    if [[ ${#HIGH_CONFIDENCE[@]} -gt 0 ]]; then
        echo -e "${RED}HIGH CONFIDENCE (safe to delete):${NC}"
        for file_info in "${HIGH_CONFIDENCE[@]}"; do
            echo -e "${RED}  ❌ $file_info${NC}"
        done
        echo ""
    fi

    # Medium confidence
    if [[ ${#MEDIUM_CONFIDENCE[@]} -gt 0 ]]; then
        echo -e "${YELLOW}MEDIUM CONFIDENCE (review before delete):${NC}"
        for file_info in "${MEDIUM_CONFIDENCE[@]}"; do
            echo -e "${YELLOW}  ⚠️  $file_info${NC}"
        done
        echo ""
    fi

    # Summary
    local total_unused=$((${#HIGH_CONFIDENCE[@]} + ${#MEDIUM_CONFIDENCE[@]}))

    if [[ $total_unused -gt 0 ]]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}SUMMARY:${NC}"
        echo -e "  ${RED}High Confidence: ${#HIGH_CONFIDENCE[@]} files${NC}"
        echo -e "  ${YELLOW}Medium Confidence: ${#MEDIUM_CONFIDENCE[@]} files${NC}"
        echo -e "  ${GREEN}Active Files: ${#KEEP_FILES[@]} files${NC}"
        echo -e "\n${YELLOW}💡 TIP: Review and delete unused files to keep codebase clean${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    else
        echo -e "${GREEN}✅ No unused files detected! Codebase is clean.${NC}\n"
    fi
}

# Main execution
detect_unused_files
print_results

# Exit with 0 (warnings only, don't block commits)
exit 0
