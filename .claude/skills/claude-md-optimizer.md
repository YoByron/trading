---
name: claude-md-optimizer
description: Optimizes .claude/CLAUDE.md file size by extracting detailed content to docs/ directory
location: project
---

# Claude CLAUDE.md Optimizer Skill

## Purpose

This skill automatically optimizes the `.claude/CLAUDE.md` file to stay under 40,000 characters (Claude Code performance threshold) while maintaining all critical project instructions and context.

## Nov 2025 Best Standards

**File Size Limits**:
- `.claude/CLAUDE.md`: 40,000 characters maximum (warning at 80% = 32,000 chars)
- Target: 10,000-15,000 characters for optimal performance
- Detailed content should live in `docs/` directory

**Structure**:
```
.claude/CLAUDE.md (concise, high-level, links to docs)
└── docs/
    ├── verification-protocols.md (detailed protocols)
    ├── r-and-d-phase.md (current phase status)
    ├── research-findings.md (enhancement roadmap)
    ├── profit-optimization.md (cost-benefit analysis)
    └── [other-detailed-docs].md
```

## When to Use This Skill

**Automatic triggers**:
- `/memory` shows warning about large CLAUDE.md file
- Pre-commit hook fails due to file size
- File size exceeds 32,000 characters (80% threshold)

**Manual triggers**:
- User requests CLAUDE.md optimization
- Adding substantial new content to CLAUDE.md
- Refactoring project documentation

## What This Skill Does

### 1. Analyze Current File
- Check `.claude/CLAUDE.md` character count
- Identify sections that can be extracted to docs/
- Determine optimal extraction strategy

### 2. Extract Detailed Content
**Content to Extract** (move to docs/):
- Detailed protocols (>500 words)
- Historical context and examples
- Research findings and roadmaps
- Detailed cost-benefit analyses
- Implementation timelines
- Technical specifications
- Long code examples

**Content to Keep** (in CLAUDE.md):
- Critical mandates (chain of command, anti-lying, anti-manual)
- Quick reference protocols
- Current project status
- North Star goals
- Links to detailed docs
- Memory management instructions

### 3. Create Extracted Documentation
For each extracted section:
- Create standalone markdown file in `docs/`
- Add proper headers and context
- Make self-contained (no external dependencies)
- Update README.md if needed

### 4. Refactor CLAUDE.md
- Replace detailed sections with concise summaries
- Add links to extracted docs: `See docs/[filename].md for details`
- Maintain logical flow and readability
- Update "Last Optimized" timestamp

### 5. Verify Results
- Confirm file size <40,000 characters
- Test that all links work
- Ensure no critical information lost
- Validate markdown formatting

## Extraction Strategy

### Priority 1: Extract First (Highest Impact)
1. Research findings and enhancement roadmaps
2. Historical context and past failures
3. Detailed cost-benefit analyses
4. Implementation timelines and roadmaps
5. Long examples and code snippets

### Priority 2: Condense (Medium Impact)
1. Repeated concepts (consolidate)
2. Verbose explanations (tighten)
3. Multiple examples (keep best one, link to others)
4. Redundant sections (merge or remove)

### Priority 3: Keep Intact (Critical)
1. Chain of command rules
2. Anti-lying mandate
3. Anti-manual mandate
4. Verification protocols (summary)
5. Current project status
6. North Star goal

## File Naming Conventions

**Extracted docs should use**:
- Lowercase with hyphens: `verification-protocols.md`
- Descriptive names: `r-and-d-phase.md` not `phase.md`
- Topical organization: `profit-optimization.md`

## Output Format

After optimization, report:

```markdown
## CLAUDE.md Optimization Complete

**Before**: 43,500 characters
**After**: 12,159 characters
**Reduction**: 72%

**Files Created**:
- docs/verification-protocols.md (6,234 chars)
- docs/r-and-d-phase.md (4,821 chars)
- docs/research-findings.md (8,932 chars)
- docs/profit-optimization.md (5,612 chars)

**CLAUDE.md Changes**:
- Extracted 4 major sections
- Added links to detailed docs
- Maintained all critical mandates
- Updated "Last Optimized" timestamp

**Verification**:
✅ File size under 40k limit (30% of limit)
✅ All links functional
✅ No critical information lost
✅ Markdown validated
```

## Pre-commit Integration

This skill works with the pre-commit hook (`.claude/hooks/check-file-sizes.sh`) to prevent oversized files from being committed.

**Workflow**:
1. Developer modifies CLAUDE.md
2. Pre-commit hook detects size >40k
3. Commit blocked with error message
4. Developer runs: `claude "Use claude-md-optimizer skill"`
5. Skill extracts content, refactors file
6. Developer re-commits (passes hook)

## Maintenance Guidelines

**When adding new content**:
- Start by asking: "Does this belong in CLAUDE.md or docs/?"
- If >500 words: Create separate doc
- If <500 words but detailed: Consider extraction
- If critical mandate: Keep in CLAUDE.md

**Monthly review**:
- Check CLAUDE.md file size
- Identify stale content
- Update extracted docs
- Consolidate similar topics

## Examples

### Before Optimization
```markdown
## PROFIT OPTIMIZATION STRATEGIES 💰

### 1. Alpaca High-Yield Cash (3.56% APY)

**Discovered**: October 30, 2025 (Alpaca rate update email)

**Key Features**:
- **APY**: 3.56% (nearly 10x national average of 0.40%)
- **FDIC Insurance**: Up to $1M
...
[5,000 more characters of detailed analysis]
```

### After Optimization
```markdown
## Optimization Strategies 💰

### 1. Alpaca High-Yield Cash (3.56% APY)
- Passive income on idle cash (nearly 10x national average)
- Available after going live (NOT during paper trading)
- Full liquidity - can use as buying power anytime

**See docs/profit-optimization.md for full cost-benefit analysis**
```

## Success Criteria

**Optimization is successful when**:
- ✅ CLAUDE.md <40,000 characters
- ✅ Target: 10,000-15,000 characters
- ✅ All critical mandates intact
- ✅ Links to extracted docs work
- ✅ No information loss
- ✅ Logical flow maintained
- ✅ Pre-commit hook passes

## Related Files

- `.claude/CLAUDE.md` - Main project instructions
- `.claude/hooks/check-file-sizes.sh` - Pre-commit hook
- `docs/` - Detailed documentation directory
- `.git/hooks/pre-commit` - Git pre-commit hook

---

**Created**: November 23, 2025
**Last Updated**: November 23, 2025
**Skill Version**: 1.0.0
