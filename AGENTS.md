# Agent Guidelines

## Core Principles

Never tell the user to do any manual work. You as the AI agent can do all the work yourself.

## Git Workflow

**ALWAYS use git worktrees instead of switching branches locally.**

- This prevents conflicts when multiple agents work on the same repository
- Use `git worktree add ../trading-feature feature-branch` for new features
- Work in the worktree directory, commit, and push from there
- Clean up worktrees when done: `git worktree remove ../trading-feature`

Example workflow:
```bash
# Create worktree for new feature
git worktree add ../trading-fix-ci fix-ci-issues
cd ../trading-fix-ci

# Do work, commit, push
git add .
git commit -m "fix: improve CI reliability"
git push origin fix-ci-issues

# Clean up when done
cd ../trading
git worktree remove ../trading-fix-ci
```

## Commands Reference

### Testing
- `python3 tests/test_smoke.py` - Quick smoke tests
- `./scripts/local_ci_test.sh` - Full local CI validation with ACT
- `pre-commit run --all-files` - Code quality checks

### CI/CD
- `gh workflow list` - List workflows
- `gh run list --workflow="Daily Trading Execution"` - Check recent runs
- `gh workflow run daily-trading.yml` - Trigger manual run

### Build & Dependencies
- `python3 -m pip install -r requirements.txt` - Install dependencies
- `go mod download && go mod verify` - Go dependencies (ADK)
- `python3 scripts/validate_secrets.py` - Check required secrets
