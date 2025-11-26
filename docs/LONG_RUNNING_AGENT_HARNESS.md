# Long-Running Agent Harness Analysis

**Date**: November 26, 2025  
**Reference**: [Anthropic's Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Executive Summary

We have **partial implementation** of Anthropic's recommended patterns for long-running agents. We have strong state management and context persistence, but are missing the structured harness components that enable agents to work effectively across multiple context windows.

## Current Implementation Status

### ✅ What We Have

1. **State Management** ✅
   - `data/system_state.json` - Complete system state persistence
   - `StateManager` class with staleness detection
   - State survives reboots and context windows

2. **Progress Tracking** ✅
   - Daily reports (`reports/daily_report_YYYY-MM-DD.txt`)
   - Notes in `system_state.json`
   - Git commits for state changes (automated in GitHub Actions)

3. **Context Management** ✅
   - `.claude/CLAUDE.md` with "Future Sessions - START HERE" section
   - Context engine for multi-agent systems (`src/agent_framework/context_engine.py`)
   - Memory persistence across sessions

4. **Feature Documentation** ✅
   - Feature specs in `docs/features/` (markdown format)
   - Feature status tracking (Complete/In Progress/Planned)

5. **Git Integration** ✅
   - Automated git commits in GitHub Actions workflows
   - State changes committed automatically

### ❌ What We're Missing

1. **Structured Progress File** ❌
   - Missing: `claude-progress.txt` for tracking agent progress across sessions
   - Current: Progress scattered across state.json notes and daily reports
   - Impact: Agents can't quickly understand what was done recently

2. **Feature List JSON** ❌
   - Missing: Structured `feature_list.json` with pass/fail status
   - Current: Markdown feature specs without pass/fail tracking
   - Impact: No clear feature-by-feature progress tracking

3. **Initialization Script** ❌
   - Missing: `init.sh` script for environment setup
   - Current: Various setup scripts but no unified initialization
   - Impact: No standardized way to verify environment is ready

4. **Session Orientation Pattern** ❌
   - Missing: Explicit "get bearings" steps for agents starting new sessions
   - Current: Instructions exist but not enforced as a pattern
   - Impact: Agents may skip context gathering steps

5. **Incremental Feature Workflow** ❌
   - Missing: Enforced "one feature at a time" workflow
   - Current: Agents can work on multiple things simultaneously
   - Impact: Risk of leaving features half-implemented

6. **End-to-End Testing Before Completion** ❌
   - Missing: Explicit requirement to test features end-to-end before marking complete
   - Current: Testing exists but not enforced as part of feature completion
   - Impact: Features may be marked complete without proper verification

## Recommended Implementation

### Pattern 1: Initializer Agent (First Session)

On the very first agent session, the agent should:

1. Create `init.sh` script for environment setup
2. Create `claude-progress.txt` file
3. Create `feature_list.json` with all features marked as `"passes": false`
4. Make initial git commit showing environment setup

### Pattern 2: Coding Agent (Subsequent Sessions)

Every subsequent agent session should:

1. **Get Bearings**:
   - Run `pwd` to see working directory
   - Read `claude-progress.txt` to understand recent work
   - Read `feature_list.json` to see feature status
   - Read git logs (`git log --oneline -20`) to see recent commits

2. **Verify Environment**:
   - Run `init.sh` (or equivalent) to start dev server/test environment
   - Run basic end-to-end test to verify system is working
   - Fix any bugs before starting new work

3. **Choose Feature**:
   - Select ONE feature from `feature_list.json` that is not passing
   - Work on that feature incrementally

4. **Complete Feature**:
   - Implement the feature
   - Test end-to-end (as a human user would)
   - Only mark `"passes": true` after successful end-to-end verification
   - Commit with descriptive message
   - Update `claude-progress.txt` with summary

5. **Leave Clean State**:
   - Ensure code is well-documented
   - No major bugs
   - Ready for next session to continue

## Implementation Plan

1. ✅ Create `claude-progress.txt` template
2. ✅ Create `feature_list.json` from existing feature specs
3. ✅ Create `init.sh` script
4. ✅ Update `.claude/CLAUDE.md` with session orientation steps
5. ✅ Document the initializer vs coding agent pattern

## Benefits

- **Consistency**: Agents always know how to start a session
- **Progress Tracking**: Clear visibility into what's done vs what's remaining
- **Incremental Work**: Prevents agents from trying to do too much at once
- **Clean State**: Each session ends with mergeable code
- **Context Bridging**: Progress file + git logs bridge context windows effectively

