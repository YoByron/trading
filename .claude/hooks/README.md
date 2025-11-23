# Pre-Commit Hooks Documentation

**Created**: November 23, 2025
**Last Updated**: November 23, 2025

This directory contains pre-commit hooks that enforce project quality standards and prevent degraded performance.

## Overview

All hooks in this directory are automatically run by `.git/hooks/pre-commit` before each commit. They enforce November 2025 best practices for:
- File size limits
- Documentation structure
- Code quality
- Security standards

## Available Hooks

### 1. check-file-sizes.sh

**Purpose**: Enforce .claude/ file size limits to prevent performance degradation

**What it checks**:
- `.claude/CLAUDE.md` must be <40,000 characters (warning at 32,000)
- Other `.claude/*.md` files must be <25,000 characters (warning at 20,000)
- Provides clear error messages with fix instructions

**Exit codes**:
- `0`: All files within limits
- `1`: File(s) exceed maximum size (blocks commit)

**Fix suggestions**:
- Use `claude-md-optimizer` skill to extract content to docs/
- Manual extraction to docs/ directory with links back

**Test**:
```bash
bash .claude/hooks/check-file-sizes.sh
```

**Created**: November 23, 2025
**Related**: `.claude/skills/claude-md-optimizer.md`

---

### 2. check-documentation.sh

**Purpose**: Ensure documentation structure follows 2025 standards

**What it checks**:
1. **Root directory protection** - No .md files in root (except README.md, LICENSE.md, etc.)
2. **README link validation** - All docs/ files should be linked in README.md
3. **Broken link detection** - Finds broken internal markdown links
4. **Naming conventions** - Files follow `lowercase-with-hyphens.md` format
5. **Feature documentation** - Reminds to document new Python modules

**Exit codes**:
- `0`: All checks pass or warnings only
- `1`: Critical errors (blocks commit)

**Fix suggestions**:
- Move loose .md files to docs/: `git mv file.md docs/`
- Add missing links to README.md
- Fix broken links or rename files
- Follow naming conventions

**Test**:
```bash
bash .claude/hooks/check-documentation.sh
```

**Created**: November 23, 2025
**Related**: `.claude/skills/readme-sync-validator.md`, `.claude/skills/docs-organizer.md`

---

## Integration with Git

### How Pre-Commit Hooks Work

When you run `git commit`, the `.git/hooks/pre-commit` script automatically:

1. Runs `check-file-sizes.sh` first
2. Runs `check-documentation.sh` second
3. Runs repository hygiene checks
4. Runs security scans
5. Only allows commit if all checks pass

### Installation

Hooks are already installed and active. No manual setup needed.

**Verify installation**:
```bash
ls -la .git/hooks/pre-commit
```

### Bypassing Hooks (NOT RECOMMENDED)

**Never bypass hooks in production**. Only use for emergency hotfixes:
```bash
git commit --no-verify -m "Emergency fix"
```

CEO directive: **"No manual anything!"** - Let automation do its job.

---

## Hook Development Standards

### Creating New Hooks

**Location**: `.claude/hooks/[hook-name].sh`

**Required elements**:
1. Shebang: `#!/bin/bash`
2. Header comment with purpose and creation date
3. Color-coded output (RED/YELLOW/GREEN/BLUE)
4. Clear error messages with fix instructions
5. Exit codes: 0 (pass), 1 (fail)
6. Help text for users
7. Executable permissions: `chmod +x`

**Template**:
```bash
#!/bin/bash
# .claude/hooks/check-[feature].sh
# Pre-commit hook to check [feature]
#
# Created: [DATE]
# Purpose: [DESCRIPTION]

set -e

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

HAS_ERRORS=0
HAS_WARNINGS=0

echo -e "${BLUE}🔍 Checking [feature]...${NC}"

# Check logic here

if [ "$HAS_ERRORS" -eq 1 ]; then
    echo -e "${RED}❌ COMMIT BLOCKED - [reason]${NC}"
    exit 1
elif [ "$HAS_WARNINGS" -eq 1 ]; then
    echo -e "${YELLOW}⚠️  WARNING - [reason]${NC}"
    exit 0
else
    echo -e "${GREEN}✅ All checks passed${NC}"
    exit 0
fi
```

### Testing Hooks

**Test individual hook**:
```bash
bash .claude/hooks/check-[feature].sh
```

**Test full pre-commit flow**:
```bash
.git/hooks/pre-commit
```

**Test with actual commit**:
```bash
git add [files]
git commit -m "Test commit"
# Hooks run automatically
```

---

## Troubleshooting

### Hook fails unexpectedly

1. **Check file permissions**:
   ```bash
   ls -la .claude/hooks/*.sh
   # Should show -rwxr-xr-x
   ```

2. **Run hook directly**:
   ```bash
   bash .claude/hooks/check-[feature].sh
   # See detailed error output
   ```

3. **Verify integration**:
   ```bash
   cat .git/hooks/pre-commit | grep "check-[feature]"
   ```

### False positives

If a hook incorrectly blocks a valid commit:

1. Review the error message carefully
2. Check if files match the criteria
3. Update hook logic if needed (create PR)
4. Only use `--no-verify` as last resort

### Performance issues

If hooks slow down commits significantly:

1. Optimize hook logic (avoid full repo scans)
2. Cache results where possible
3. Run expensive checks only on changed files
4. Consider async checks post-commit

---

## Related Files

**Pre-commit hook**: `.git/hooks/pre-commit` (main integration point)

**Claude Skills**:
- `.claude/skills/claude-md-optimizer.md` - CLAUDE.md size optimization
- `.claude/skills/readme-sync-validator.md` - README link validation
- `.claude/skills/docs-organizer.md` - docs/ structure organization

**Project documentation**:
- `.claude/CLAUDE.md` - Project instructions and mandates
- `docs/` - All detailed documentation

---

## Maintenance

### Weekly Review

Every Sunday (automated):
- Check hook effectiveness
- Review false positive rate
- Update thresholds if needed
- Add new checks as project evolves

### Monthly Audit

Every month:
- Review all hooks for relevance
- Remove obsolete checks
- Consolidate similar checks
- Update documentation

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Nov 23, 2025 | Initial creation: check-file-sizes.sh, check-documentation.sh |

---

## Philosophy

**From CLAUDE.md mandate**:
> "THE SYSTEM IS FULLY AUTOMATED. PERIOD."

Pre-commit hooks embody this principle by:
- Automatically enforcing standards
- Preventing errors before they reach the repo
- Providing clear fix instructions
- Never requiring manual intervention
- Learning and improving over time

**Key principle**: Hooks should be **helpful**, not **obstructive**. Block only critical errors, warn for improvements.

---

**Last Updated**: November 23, 2025
**Maintained by**: Claude (CTO)
**CEO**: Igor Ganapolsky
