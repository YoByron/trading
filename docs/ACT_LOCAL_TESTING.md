# ACT Local CI Testing Guide

**Prevent workflow failures by testing GitHub Actions locally before pushing!**

## What is ACT?

[ACT](https://github.com/nektos/act) runs your GitHub Actions workflows locally using Docker. This lets you:
- ✅ Catch syntax errors before pushing
- ✅ Test workflow logic locally
- ✅ Debug issues faster
- ✅ Save GitHub Actions minutes

## Quick Start

### 1. Install ACT

```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or download from: https://github.com/nektos/act/releases
```

### 2. Install Docker

ACT requires Docker to run workflows:
- **macOS**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: `sudo apt install docker.io` (or equivalent)

### 3. Test Workflows Locally

```bash
# Quick syntax check (fast, no Docker needed)
./scripts/test-workflows-local.sh

# Full workflow test (runs actual steps)
./scripts/test-workflow-full.sh .github/workflows/daily-trading.yml
```

## Usage

### Quick Syntax Validation

Tests all workflows for syntax errors (fast, ~10 seconds):

```bash
./scripts/test-workflows-local.sh
```

**Output:**
```
🧪 Testing GitHub Actions Workflows Locally

📋 Found 12 workflow(s) to test

✅ daily-trading.yml: Syntax valid
✅ weekend-crypto-trading.yml: Syntax valid
⏭️  Skipping notify-on-failure.yml (requires GitHub API)
...

✅ All tested workflows passed!
```

### Full Workflow Test

Runs a complete workflow with Docker (slower, ~2-5 minutes):

```bash
# Test specific workflow
./scripts/test-workflow-full.sh .github/workflows/ipo-monitor.yml

# Test with secrets
echo "ALPACA_API_KEY=test_key" > .secrets
./scripts/test-workflow-full.sh .github/workflows/daily-trading.yml
```

### Manual ACT Commands

```bash
# List all workflows
act -l

# Run workflow with workflow_dispatch event
act workflow_dispatch -W .github/workflows/daily-trading.yml

# Run specific job
act -j execute-trading -W .github/workflows/daily-trading.yml

# Run with secrets
act -s ALPACA_API_KEY=your_key -s ALPACA_SECRET_KEY=your_secret

# Dry run (syntax check only)
act workflow_dispatch --dryrun
```

## Configuration

### `.actrc` File

Configuration is in `.actrc`:
- Uses `catthehacker/ubuntu:act-latest` for Ubuntu workflows
- Reuses containers for faster runs
- Verbose output for debugging

### Secrets File

Create `.secrets` file (gitignored) for local testing:

```bash
# .secrets (DO NOT COMMIT!)
ALPACA_API_KEY=your_test_key
ALPACA_SECRET_KEY=your_test_secret
ANTHROPIC_API_KEY=your_test_key
```

**Important**: `.secrets` is in `.gitignore` - never commit secrets!

## Pre-Commit Hook (Optional)

Add to `.git/hooks/pre-commit` to test workflows before every commit:

```bash
#!/bin/bash
# Test workflows if workflow files changed
if git diff --cached --name-only | grep -q ".github/workflows/"; then
    echo "🧪 Testing modified workflows..."
    ./scripts/test-workflows-local.sh || exit 1
fi
```

Or use Husky (if installed):

```bash
npx husky add .husky/pre-commit "./scripts/test-workflows-local.sh"
```

## Troubleshooting

### "ACT is not installed"
```bash
brew install act
```

### "Docker is not running"
Start Docker Desktop, then retry.

### "Workflow requires secrets"
Create `.secrets` file with required secrets, or use:
```bash
act -s SECRET_NAME=value
```

### "macOS workflows not supported"
ACT has limited macOS support. Most workflows use `ubuntu-latest` which works fine.

### "Workflow times out"
Some workflows are designed for GitHub's environment. Test individual jobs:
```bash
act -j job-name -W .github/workflows/workflow.yml
```

## Best Practices

1. **Always test before pushing workflow changes**
   ```bash
   ./scripts/test-workflows-local.sh
   ```

2. **Test critical workflows fully before major changes**
   ```bash
   ./scripts/test-workflow-full.sh .github/workflows/daily-trading.yml
   ```

3. **Use secrets file for local testing** (never commit it!)

4. **Run syntax check in CI** (already configured in `test-workflows.yml`)

5. **Test workflow changes in PRs** (GitHub Actions will validate)

## Integration with Development Workflow

### Before Committing Workflow Changes

```bash
# 1. Quick syntax check
./scripts/test-workflows-local.sh

# 2. If passing, commit
git add .github/workflows/
git commit -m "fix: update workflow configuration"
```

### Before Merging PRs

The `test-workflows.yml` workflow automatically validates syntax on PRs.

### Weekly Health Check

The `workflow-health-check.yml` workflow runs weekly to detect disabled workflows.

## Limitations

- **macOS workflows**: Limited support (most use Ubuntu anyway)
- **Self-hosted runners**: Not supported
- **GitHub API calls**: Some workflows need GitHub API (skipped in local tests)
- **External services**: Workflows that call external APIs may behave differently

## Resources

- [ACT GitHub](https://github.com/nektos/act)
- [ACT Documentation](https://github.com/nektos/act#example-commands)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

---

**Remember**: Test locally, push confidently! 🚀
