---
name: docs-organizer
description: Ensure docs/ directory follows Nov 2025 best practices for organization
location: project
---

# Documentation Organizer Skill

## Purpose

This skill ensures the `docs/` directory follows November 2025 best practices for documentation organization, preventing documentation rot, duplicate content, and structural issues.

## Nov 2025 Documentation Standards

**Directory Structure**:
```
project-root/
├── README.md (ONLY .md file at root)
├── docs/
│   ├── verification-protocols.md
│   ├── r-and-d-phase.md
│   ├── research-findings.md
│   ├── profit-optimization.md
│   └── [other-docs].md
├── .claude/
│   ├── CLAUDE.md (optimized, <40k chars)
│   └── skills/
└── [other-project-files]
```

**File Naming Conventions**:
- Lowercase with hyphens: `verification-protocols.md`
- Descriptive names: `r-and-d-phase.md` not `phase.md`
- No spaces, underscores, or camelCase
- Date prefixes for time-sensitive: `2025-11-23-weekly-report.md`

**Documentation Standards**:
- Every doc must have frontmatter header with title, date, status
- Cross-references must use relative paths: `[See protocols](verification-protocols.md)`
- All docs must be linked from either README.md or another doc
- No orphaned documentation (docs not referenced anywhere)
- No duplicate content (similar topics should be consolidated)

## When to Use This Skill

**Automatic triggers**:
- Pre-commit hook detects loose .md files in root
- Pre-commit hook finds orphaned or duplicate docs
- Weekly docs audit (automated)

**Manual triggers**:
- User requests documentation organization
- After major refactoring or content extraction
- Before creating new documentation
- When docs/ feels messy or hard to navigate

## What This Skill Does

### 1. Scan Project Structure

**Check for violations**:
- ❌ Loose .md files in project root (except README.md)
- ❌ Files using wrong naming conventions (spaces, underscores, uppercase)
- ❌ Missing frontmatter headers
- ❌ Orphaned docs (not linked from anywhere)
- ❌ Duplicate content (similar topics in multiple files)
- ❌ Broken cross-references (links to non-existent files)
- ❌ Docs missing creation/update dates

**Scan locations**:
```bash
# Root directory (should only have README.md)
find . -maxdepth 1 -name "*.md" ! -name "README.md"

# docs/ directory (check structure)
find docs/ -type f -name "*.md"

# .claude/ directory (check CLAUDE.md size)
wc -c .claude/CLAUDE.md
```

### 2. Validate Documentation

**For each .md file in docs/, verify**:

#### Required Frontmatter
```markdown
---
title: Document Title
created: 2025-11-23
updated: 2025-11-23
status: active | archived | draft
---
```

**Status values**:
- `active`: Current, maintained documentation
- `archived`: Historical, kept for reference
- `draft`: Work in progress

#### Required Sections
- Title (H1 header)
- Purpose/Overview
- Content sections
- Related links (optional)
- Last updated date

#### Naming Convention Check
```python
# CORRECT
verification-protocols.md
r-and-d-phase.md
2025-11-23-weekly-report.md

# INCORRECT
Verification_Protocols.md  # Uppercase, underscore
r and d phase.md           # Spaces
verificationProtocols.md   # camelCase
vp.md                      # Too abbreviated
```

### 3. Check Cross-References

**Validate all markdown links**:
```markdown
# Internal links (must exist)
[See protocols](verification-protocols.md)  ✅
[See protocols](docs/verification-protocols.md)  ✅ (from root)
[See protocols](missing-doc.md)  ❌ Broken link

# External links (optional validation)
[GitHub](https://github.com)  ℹ️ External
```

**Link checking algorithm**:
1. Extract all `[text](link)` patterns
2. Identify internal vs external links
3. Resolve relative paths
4. Verify target files exist
5. Report broken links

### 4. Detect Duplicate Content

**Similarity checks**:
- Compare doc titles for similarity (>80% match)
- Check for repeated H1/H2 headers across docs
- Identify overlapping topics
- Flag potential consolidation opportunities

**Example duplicates**:
```
docs/verification-protocol.md
docs/show-dont-tell-protocol.md
→ Should be consolidated into docs/verification-protocols.md
```

### 5. Find Orphaned Documentation

**Orphan detection**:
1. Build graph of all docs and their links
2. Check if each doc is reachable from README.md
3. Flag docs with no incoming links

**Example orphan**:
```
docs/old-strategy-notes.md
→ Not linked from README.md or any other doc
→ Either archive or add link
```

### 6. Auto-Fix Common Issues

**Issues this skill can fix automatically**:

#### Move loose .md files to docs/
```bash
# Find loose files
loose_files=$(find . -maxdepth 1 -name "*.md" ! -name "README.md")

# Move to docs/
for file in $loose_files; do
  mv "$file" "docs/$(basename $file)"
  echo "Moved: $file → docs/$(basename $file)"
done
```

#### Rename files to follow conventions
```python
# BEFORE: Verification_Protocols.md
# AFTER: verification-protocols.md

import re

def fix_filename(filename):
    # Convert to lowercase
    name = filename.lower()
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    return name
```

#### Add missing frontmatter
```markdown
# If doc missing frontmatter, add:
---
title: [Extract from H1 or filename]
created: [File creation date]
updated: [File modification date]
status: active
---
```

#### Fix broken internal links
```markdown
# BEFORE: [See protocols](verification_protocols.md)
# AFTER: [See protocols](verification-protocols.md)

# Auto-fix if target exists with different name
```

### 7. Generate Documentation Map

**Create visual documentation structure**:
```markdown
# Documentation Map (Auto-Generated)

## Entry Point
- README.md → Project overview, links to all docs

## Core Documentation
- docs/verification-protocols.md → "Show, Don't Tell" protocol
  - Linked from: .claude/CLAUDE.md, README.md
- docs/r-and-d-phase.md → Current R&D phase strategy
  - Linked from: .claude/CLAUDE.md, README.md
- docs/research-findings.md → Enhancement roadmap
  - Linked from: .claude/CLAUDE.md, README.md
- docs/profit-optimization.md → Cost optimization strategies
  - Linked from: .claude/CLAUDE.md, README.md

## Status Summary
- Active docs: 4
- Archived docs: 0
- Draft docs: 0
- Orphaned docs: 0
- Total docs: 4

## Health Score: 100% ✅
```

## Output Format

After organization, report:

```markdown
## Documentation Organization Report

**Scan Date**: 2025-11-23 10:30:00 ET
**Total Files Scanned**: 12

### Issues Found

**Critical (Must Fix)**:
- ❌ 2 loose .md files in project root
  - CHANGELOG.md → Should move to docs/
  - NOTES.md → Should move to docs/
- ❌ 1 file with wrong naming convention
  - docs/Verification_Protocols.md → Should be verification-protocols.md
- ❌ 3 docs missing frontmatter
  - docs/old-notes.md
  - docs/temp-analysis.md
  - docs/draft-strategy.md

**Warnings (Should Fix)**:
- ⚠️ 1 orphaned doc (not linked anywhere)
  - docs/old-strategy-notes.md → Archive or link
- ⚠️ 2 potentially duplicate docs
  - docs/verification-protocol.md + docs/show-dont-tell-protocol.md → Consider consolidating
- ⚠️ 2 broken internal links
  - README.md links to docs/missing-doc.md (doesn't exist)
  - docs/research-findings.md links to docs/old-roadmap.md (doesn't exist)

**Info (Optional)**:
- ℹ️ 3 docs not updated in 30+ days
  - docs/research-findings.md (45 days old)

### Auto-Fixes Applied

✅ Moved 2 loose .md files to docs/
✅ Renamed 1 file to follow conventions
✅ Added frontmatter to 3 docs
✅ Fixed 2 broken links (found correct targets)

### Manual Actions Required

**High Priority**:
1. Review orphaned doc: docs/old-strategy-notes.md
   - Decision: Archive or add link from README.md?

2. Consolidate duplicate docs:
   - Merge docs/verification-protocol.md into docs/verification-protocols.md
   - Update all links to point to consolidated doc

**Low Priority**:
3. Update stale docs:
   - docs/research-findings.md (last updated 45 days ago)

### Documentation Health Score

**Before**: 58% (7 issues)
**After**: 88% (2 manual actions needed)

**Target**: 100% (zero violations)
```

## Pre-commit Integration

This skill integrates with `.claude/hooks/check-docs-organization.sh`:

```bash
#!/bin/bash
# .claude/hooks/check-docs-organization.sh

echo "Checking documentation organization..."

# Check for loose .md files (except README.md)
loose_files=$(find . -maxdepth 1 -name "*.md" ! -name "README.md")
if [ -n "$loose_files" ]; then
    echo "❌ ERROR: Found loose .md files in project root:"
    echo "$loose_files"
    echo "Run: claude 'Use docs-organizer skill to fix'"
    exit 1
fi

# Check for incorrect naming in docs/
bad_names=$(find docs/ -name "*.md" | grep -E '[A-Z_\s]')
if [ -n "$bad_names" ]; then
    echo "❌ ERROR: Found docs with incorrect naming:"
    echo "$bad_names"
    echo "Use lowercase-with-hyphens.md format"
    exit 1
fi

echo "✅ Documentation organization check passed"
exit 0
```

**Workflow**:
1. Developer creates new doc or modifies existing
2. Pre-commit hook runs docs organization check
3. If violations found → Commit blocked
4. Developer runs: `claude "Use docs-organizer skill"`
5. Skill fixes auto-fixable issues, reports manual actions
6. Developer addresses manual actions
7. Re-commit → Passes hook

## Maintenance Guidelines

### When Creating New Documentation

**Checklist**:
- [ ] Create in `docs/` directory (NOT root)
- [ ] Use lowercase-with-hyphens.md naming
- [ ] Add frontmatter header (title, dates, status)
- [ ] Link from README.md or relevant doc
- [ ] Keep docs focused (single topic)
- [ ] Use relative links for cross-references

### When Updating Existing Documentation

**Checklist**:
- [ ] Update `updated:` field in frontmatter
- [ ] Review and fix broken links
- [ ] Check for duplicate content
- [ ] Consolidate if doc becomes too long (>2000 lines)

### Weekly Docs Audit (Automated)

**Every Sunday 9:00 AM ET**:
1. Run docs-organizer skill
2. Generate health report
3. Email report to CEO if issues found
4. Auto-fix non-breaking issues
5. Create GitHub issue for manual actions

## Examples

### Example 1: Loose .md File in Root

**Before**:
```
project-root/
├── README.md
├── CHANGELOG.md  ❌ Should be in docs/
└── docs/
```

**After**:
```
project-root/
├── README.md
└── docs/
    └── changelog.md  ✅ Moved and renamed
```

**Action**:
```bash
mv CHANGELOG.md docs/changelog.md
# Update frontmatter
# Add link from README.md
```

### Example 2: Wrong Naming Convention

**Before**:
```
docs/Verification_Protocols.md  ❌ Uppercase + underscore
```

**After**:
```
docs/verification-protocols.md  ✅ Correct
```

**Action**:
```bash
mv docs/Verification_Protocols.md docs/verification-protocols.md
# Update all links to this file
```

### Example 3: Missing Frontmatter

**Before**:
```markdown
# Old Strategy Notes

Some content here...
```

**After**:
```markdown
---
title: Old Strategy Notes
created: 2025-10-15
updated: 2025-11-23
status: archived
---

# Old Strategy Notes

Some content here...
```

### Example 4: Orphaned Doc

**Before**:
```
docs/old-roadmap.md  ❌ Not linked anywhere
```

**Options**:
1. **Archive**: Add `status: archived` to frontmatter
2. **Link**: Add to README.md under "Historical Docs"
3. **Delete**: Remove if truly obsolete

**After**:
```markdown
# In README.md

## Historical Documentation
- [Old Roadmap](docs/old-roadmap.md) - Initial project roadmap (archived)
```

### Example 5: Duplicate Content

**Before**:
```
docs/verification-protocol.md (800 lines)
docs/show-dont-tell-protocol.md (600 lines)
→ 70% overlapping content
```

**After**:
```
docs/verification-protocols.md (1000 lines)
→ Consolidated, removed duplicates
→ Updated all incoming links
```

**Action**:
```bash
# Merge content
cat docs/verification-protocol.md docs/show-dont-tell-protocol.md > temp.md
# Manual deduplication and organization
# Save as docs/verification-protocols.md
# Update all links pointing to old files
# Delete old files
rm docs/verification-protocol.md docs/show-dont-tell-protocol.md
```

## Success Criteria

**Documentation is well-organized when**:
- ✅ No loose .md files in root (except README.md)
- ✅ All docs follow lowercase-with-hyphens.md naming
- ✅ All docs have proper frontmatter
- ✅ No orphaned docs (all linked from somewhere)
- ✅ No duplicate content (consolidated)
- ✅ No broken internal links
- ✅ All docs have creation/update dates
- ✅ Documentation map shows clear structure
- ✅ Health score 100%

## Related Files

- `.claude/CLAUDE.md` - Main project instructions (links to docs/)
- `README.md` - Project entry point (links to docs/)
- `docs/` - All detailed documentation
- `.claude/hooks/check-docs-organization.sh` - Pre-commit hook
- `.claude/skills/claude-md-optimizer.md` - CLAUDE.md optimization skill

## Integration with claude-md-optimizer

**Complementary skills**:
- **claude-md-optimizer**: Keeps `.claude/CLAUDE.md` under 40k chars
- **docs-organizer**: Ensures `docs/` structure is clean and organized

**Workflow**:
1. claude-md-optimizer extracts content → creates files in docs/
2. docs-organizer validates those files follow conventions
3. Both skills work together to maintain clean documentation structure

## Advanced Features

### Similarity Detection Algorithm

```python
from difflib import SequenceMatcher

def calculate_similarity(file1_content, file2_content):
    """Calculate similarity ratio between two documents."""
    ratio = SequenceMatcher(None, file1_content, file2_content).ratio()
    return ratio

# Flag if similarity > 0.70 (70% similar content)
if calculate_similarity(doc1, doc2) > 0.70:
    print(f"Potential duplicate: {doc1} and {doc2}")
```

### Link Graph Visualization

```python
import networkx as nx

# Build directed graph of docs and their links
G = nx.DiGraph()
G.add_node("README.md")
G.add_edge("README.md", "docs/verification-protocols.md")
G.add_edge("README.md", "docs/r-and-d-phase.md")
# ... add all links

# Find orphaned docs (no incoming edges except from self)
orphans = [node for node in G.nodes() if G.in_degree(node) == 0]
```

### Automated Consolidation Suggestions

```python
# Analyze doc titles and headers to suggest consolidations
related_docs = {
    "verification": [
        "docs/verification-protocol.md",
        "docs/show-dont-tell-protocol.md",
        "docs/verification-checklist.md"
    ],
    "r-and-d": [
        "docs/r-and-d-phase.md",
        "docs/research-phase.md"
    ]
}

# Suggest: Consolidate all "verification" docs into single doc
```

---

**Created**: November 23, 2025
**Last Updated**: November 23, 2025
**Skill Version**: 1.0.0
