# ACT - Local GitHub Actions Testing

**ACT** allows you to run GitHub Actions workflows locally, catching CI failures before pushing.

## Quick Start

### 1. Install ACT

```bash
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or use our setup script
./scripts/setup_act.sh
```

### 2. Configure Secrets

```bash
# Copy example secrets file
cp .github/local-secrets.env.example .github/local-secrets.env

# Edit and add your API keys
nano .github/local-secrets.env
```

**⚠️ IMPORTANT**: Never commit `.github/local-secrets.env` to git!

### 3. Test CI Locally

```bash
# Test adk-ci workflow
./scripts/test_ci_locally.sh adk-ci.yml

# Or use ACT directly
act -W .github/workflows/adk-ci.yml --secret-file .github/local-secrets.env
```

## Usage Examples

### Test Specific Workflow

```bash
# Test dependency check
act -W .github/workflows/dependency-check.yml

# Test daily trading (requires secrets)
act -W .github/workflows/daily-trading.yml --secret-file .github/local-secrets.env
```

### List Available Workflows

```bash
act -l
```

### Run with Verbose Output

```bash
act -W .github/workflows/adk-ci.yml --verbose
```

## Benefits

✅ **Catch CI failures before pushing**
✅ **Faster feedback loop** (no need to push and wait)
✅ **Test with real secrets** (local secrets file)
✅ **Debug workflow issues** locally
✅ **Save GitHub Actions minutes**

## Workflow

1. **Make changes** to code or requirements.txt
2. **Run validation**: `python3 scripts/validate_dependencies.py`
3. **Test locally**: `./scripts/test_ci_locally.sh adk-ci.yml`
4. **If tests pass**: Push to GitHub
5. **If tests fail**: Fix issues locally first

## Troubleshooting

### ACT not found
```bash
./scripts/setup_act.sh
```

### Secrets not loading
- Check `.github/local-secrets.env` exists
- Verify secrets file format (KEY=value, one per line)
- Use `--secret-file .github/local-secrets.env` flag

### Docker issues
ACT requires Docker. Make sure Docker is running:
```bash
docker ps
```

### Workflow not found
List available workflows:
```bash
act -l
```

## Integration with Pre-commit

The pre-commit hook automatically validates dependencies when `requirements.txt` changes, but you can also test full CI workflows with ACT.
