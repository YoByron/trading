---
name: readme-sync-validator
description: Validates that README.md contains links to all documentation files in docs/ directory
location: project
---

# README Sync Validator Skill

## Purpose

This skill ensures that README.md maintains links to all documentation files in the `docs/` directory, preventing orphaned documentation and maintaining a single source of truth.

## Nov 2025 Best Standards

**Documentation Hierarchy**:
- `README.md`: Single source of truth at project root (ONLY .md file allowed at root)
- `docs/`: All other documentation files
- `docs/_archive/`: Historical/deprecated documentation
- README.md must link to ALL active docs (excluding _archive)

**Link Format**:
```markdown
- [Description](docs/FILENAME.md)
- [Feature: Topic](docs/features/SUBTOPIC.md)
```

**Validation Rules**:
1. Every .md file in `docs/` (excluding `_archive/`) must be linked from README.md
2. Links must use relative paths: `docs/FILENAME.md`
3. Links must not be broken (target file exists)
4. Archived files should NOT be linked (unless explicitly referenced as historical)

## When to Use This Skill

**Automatic triggers**:
- Pre-commit hook validation
- After creating new documentation in `docs/`
- After moving/renaming files in `docs/`
- Monthly documentation audit

**Manual triggers**:
- User requests README validation
- After major documentation reorganization
- Before releases or major milestones

## What This Skill Does

### 1. Scan Documentation Directory
- Find all `.md` files in `docs/` (recursively)
- Exclude `docs/_archive/` directory
- Build list of expected documentation files
- Identify subdirectories (e.g., `docs/features/`)

### 2. Parse README.md
- Extract all markdown links from README.md
- Identify links pointing to `docs/` directory
- Build list of currently linked documentation
- Check for broken links (404s)

### 3. Compare & Validate
- Cross-reference: docs/*.md vs README links
- Identify missing links (files not in README)
- Identify broken links (README links to non-existent files)
- Identify orphaned links (links to deleted files)

### 4. Generate Report
- List all validation issues
- Suggest which links to add
- Suggest which links to remove
- Provide ready-to-paste markdown snippets

### 5. Auto-Fix (Optional)
- Can automatically add missing links to README
- Preserves existing structure and formatting
- Adds new links under appropriate sections
- Updates commit with validation results

## Validation Rules

### Files to Include (MUST be linked)
✅ All `.md` files in `docs/` (excluding `_archive/`)
✅ Subdirectory files (e.g., `docs/features/README.md`)
✅ Recently created documentation
✅ Active project documentation

### Files to Exclude (should NOT be linked)
❌ Files in `docs/_archive/` directory
❌ README.md itself (already at root)
❌ Hidden files (`.filename.md`)
❌ Template files (`TEMPLATE.md`)

### Link Format Validation
✅ Relative paths: `docs/FILENAME.md`
✅ Descriptive text: `[Feature Name](docs/file.md)`
✅ Organized by category/section

❌ Absolute paths: `/Users/user/docs/FILENAME.md`
❌ Missing descriptions: `[](docs/file.md)`
❌ Broken links: `[Text](docs/nonexistent.md)`

## Output Format

### Validation Report (No Issues)
```markdown
## README Sync Validation: ✅ PASSED

**Scanned**: 45 documentation files in docs/
**Linked**: 45 files in README.md
**Missing**: 0 files
**Broken**: 0 links
**Orphaned**: 0 links

✅ All documentation properly linked
✅ No broken links detected
✅ No orphaned links found
```

### Validation Report (Issues Found)
```markdown
## README Sync Validation: ❌ FAILED

**Scanned**: 48 documentation files in docs/
**Linked**: 42 files in README.md
**Missing**: 6 files (not linked)
**Broken**: 2 links (404)
**Orphaned**: 1 link (file deleted)

---

### Missing Links (6 files not in README)

These files exist in docs/ but are not linked from README.md:

1. **docs/NEW_FEATURE.md** (created 2025-11-23)
   - Suggested section: Features
   - Suggested link: `- [New Feature Documentation](docs/NEW_FEATURE.md)`

2. **docs/API_REFERENCE.md** (created 2025-11-20)
   - Suggested section: Development
   - Suggested link: `- [API Reference](docs/API_REFERENCE.md)`

3. **docs/features/sentiment_analysis.md** (created 2025-11-18)
   - Suggested section: Features → Sentiment
   - Suggested link: `- [Sentiment Analysis](docs/features/sentiment_analysis.md)`

... (3 more)

---

### Broken Links (2 links point to non-existent files)

These links in README.md point to files that don't exist:

1. **Line 45**: `[Old Guide](docs/DEPRECATED_GUIDE.md)`
   - File not found: `docs/DEPRECATED_GUIDE.md`
   - **Action**: Remove link or fix path

2. **Line 78**: `[Setup Instructions](docs/SETUP.md)`
   - File not found: `docs/SETUP.md`
   - **Action**: File may have been moved to `docs/DEPLOYMENT_GUIDE.md`

---

### Orphaned Links (1 link to deleted file)

1. **Line 102**: `[Archived Feature](docs/old_feature.md)`
   - File deleted or moved to _archive
   - **Action**: Remove link or update to `docs/_archive/old_feature.md`

---

## Suggested Fixes

### Add Missing Links to README.md

Add these links under the appropriate sections:

```markdown
## Features
- [New Feature Documentation](docs/NEW_FEATURE.md)
- [Sentiment Analysis](docs/features/sentiment_analysis.md)

## Development
- [API Reference](docs/API_REFERENCE.md)
```

### Remove Broken/Orphaned Links

Remove or update these lines in README.md:
- Line 45: Remove `[Old Guide](docs/DEPRECATED_GUIDE.md)`
- Line 78: Update to `[Setup Instructions](docs/DEPLOYMENT_GUIDE.md)`
- Line 102: Remove `[Archived Feature](docs/old_feature.md)`
```

## Pre-commit Integration

This skill works with the pre-commit hook to prevent commits with orphaned documentation.

**Workflow**:
1. Developer creates new doc: `docs/NEW_FEATURE.md`
2. Developer forgets to link from README
3. Pre-commit hook runs: `readme-sync-validator`
4. Commit blocked with validation report
5. Developer adds link to README
6. Re-commit succeeds

**Hook Script** (`.claude/hooks/check-readme-sync.sh`):
```bash
#!/bin/bash
# Check README.md links to all docs

echo "Validating README.md documentation links..."
claude "Use readme-sync-validator skill"

if [ $? -ne 0 ]; then
    echo "❌ README validation failed"
    echo "Run: claude 'Use readme-sync-validator skill' to see issues"
    exit 1
fi

echo "✅ README validation passed"
exit 0
```

## Auto-Fix Mode

**When enabled**, this skill can automatically update README.md:

**Safe Auto-Fixes** (automatically applied):
- Add missing links under appropriate sections
- Fix relative path formatting
- Remove orphaned links to deleted files

**Manual Review Required**:
- Choosing which section to add new links
- Deciding if archived files should be referenced
- Merging duplicate links
- Reorganizing link structure

**Usage**:
```bash
# Validation only (no changes)
claude "Use readme-sync-validator skill"

# Validation + auto-fix
claude "Use readme-sync-validator skill with auto-fix enabled"
```

## Link Organization Guidelines

### Recommended README Structure
```markdown
# Project Name

## Quick Start
- [Quick Reference](docs/QUICK_REFERENCE.md)
- [Daily Operations Checklist](docs/DAILY_OPERATIONS_CHECKLIST.md)

## Architecture
- [Architecture Deep Dive](docs/ARCHITECTURE_DEEP_DIVE.md)
- [Multi-Agent System](docs/2025_MULTI_AGENT_SYSTEM.md)

## Features
- [Feature Overview](docs/features/README.md)
- [Sentiment Analysis](docs/features/sentiment_analysis.md)

## Development
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [TDD Approach](docs/TDD_APPROACH.md)

## Troubleshooting
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Common Mistakes](docs/MISTAKES_AND_LEARNINGS.md)
```

### Link Categorization Rules
- **Quick Start**: User-facing operational docs
- **Architecture**: System design and technical specs
- **Features**: Feature-specific documentation
- **Development**: Developer guides and workflows
- **Troubleshooting**: Debugging and problem-solving

## Edge Cases

### Subdirectories
- `docs/features/README.md` → Link as `[Features Overview](docs/features/README.md)`
- `docs/features/topic.md` → Link as `[Feature: Topic](docs/features/topic.md)`

### Archived Files
- Files in `docs/_archive/` should NOT be linked (unless explicitly referenced)
- If referencing historical context, use footnote: "See `docs/_archive/OLD.md` for historical context"

### Private/Draft Files
- Prefix with `_` or `.` to exclude from validation: `docs/_DRAFT.md`
- Or use `.gitignore` patterns

### Auto-Generated Files
- If docs are auto-generated, mark with comment: `<!-- AUTO-GENERATED -->`
- Validator can skip these if configured

## Success Criteria

**Validation passes when**:
- ✅ All active docs (excluding `_archive/`) are linked in README
- ✅ All README links point to existing files
- ✅ No orphaned links (to deleted files)
- ✅ Links use relative paths (`docs/...`)
- ✅ Links are organized logically by section
- ✅ No duplicate links to same file

## Related Files

- `README.md` - Project root documentation hub
- `docs/` - All project documentation
- `docs/_archive/` - Historical/deprecated docs (excluded)
- `.claude/hooks/check-readme-sync.sh` - Pre-commit hook
- `.git/hooks/pre-commit` - Git pre-commit hook

## Implementation Details

**Validation Algorithm**:
```python
# Pseudo-code for validation logic
def validate_readme_sync():
    # 1. Scan docs directory
    docs_files = glob("docs/**/*.md", exclude="docs/_archive/**")

    # 2. Parse README.md
    readme_links = extract_markdown_links("README.md", filter="docs/")

    # 3. Compare
    missing = docs_files - readme_links  # Files not linked
    broken = readme_links - docs_files   # Links to non-existent files

    # 4. Report
    if missing or broken:
        generate_report(missing, broken)
        return FAIL
    else:
        return PASS
```

**Auto-Fix Algorithm**:
```python
def auto_fix_readme(missing_files):
    # Group by directory
    by_category = group_by_directory(missing_files)

    # Find appropriate README section
    for category, files in by_category:
        section = find_or_create_section(category)

        # Add links
        for file in files:
            link = generate_markdown_link(file)
            insert_link_in_section(section, link)

    # Save updated README
    save_readme()
```

## Maintenance Guidelines

**Weekly**:
- Run validation manually: `claude "Use readme-sync-validator skill"`
- Review any new docs added to `docs/`
- Ensure README organization still makes sense

**Monthly**:
- Audit link organization (consolidate duplicates)
- Update section headers if needed
- Archive obsolete documentation

**Before Releases**:
- Full validation pass
- Ensure all new features documented and linked
- Clean up broken/orphaned links

## Examples

### Example 1: New Feature Added
```bash
# Developer creates new doc
$ touch docs/NEW_FEATURE.md

# Pre-commit catches missing link
$ git commit -m "Add new feature"
❌ README validation failed: docs/NEW_FEATURE.md not linked

# Fix by adding link to README
$ vim README.md
# Add: - [New Feature](docs/NEW_FEATURE.md)

# Commit succeeds
$ git commit -m "Add new feature"
✅ README validation passed
```

### Example 2: File Renamed
```bash
# Developer renames file
$ git mv docs/OLD_NAME.md docs/NEW_NAME.md

# Pre-commit catches broken link
$ git commit -m "Rename file"
❌ README validation failed: docs/OLD_NAME.md link broken

# Fix by updating link in README
$ vim README.md
# Change: [Old Name](docs/OLD_NAME.md)
# To: [New Name](docs/NEW_NAME.md)

# Commit succeeds
$ git commit -m "Rename file and update README"
✅ README validation passed
```

### Example 3: Auto-Fix Mode
```bash
# Run validator with auto-fix
$ claude "Use readme-sync-validator skill with auto-fix enabled"

## README Sync Validation: ⚙️ AUTO-FIXING

**Found Issues**: 3 missing links
**Auto-Fixed**: 3 links added to README.md

**Changes Made**:
- Added [New Feature](docs/NEW_FEATURE.md) under Features section
- Added [API Docs](docs/API_REFERENCE.md) under Development section
- Added [Sentiment](docs/features/sentiment.md) under Features section

✅ README.md updated successfully
```

## Future Enhancements

**Potential Additions**:
1. **Link Description Quality Check**: Ensure link text is descriptive, not generic
2. **Section Recommendations**: AI-powered section placement suggestions
3. **Duplicate Detection**: Find multiple links to same file
4. **Broken Anchor Links**: Validate `#section` anchors within docs
5. **Cross-Reference Validation**: Check docs that reference each other
6. **GitHub Actions Integration**: Run on every PR
7. **Metrics Tracking**: Monitor documentation coverage over time

---

**Created**: November 23, 2025
**Last Updated**: November 23, 2025
**Skill Version**: 1.0.0
