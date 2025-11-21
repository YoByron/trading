# CI Failure Prevention Strategy

**Last Updated**: November 21, 2025  
**Purpose**: Prevent dependency conflicts and CI failures before they reach GitHub

---

## 🎯 Multi-Layer Prevention Strategy

### Layer 1: Pre-Commit Hook (Local)
**When**: Before every commit  
**What**: Validates dependencies if `requirements.txt` changed

```bash
# Automatic - runs on every commit
git commit -m "Update requirements.txt"
# → Pre-commit hook runs validate_dependencies.py
# → Blocks commit if conflicts detected
```

**Benefits**:
- ✅ Catches issues before commit
- ✅ Instant feedback
- ✅ No wasted commits

### Layer 2: ACT Local CI Testing (Local)
**When**: Before pushing to GitHub  
**What**: Run full CI workflows locally

```bash
# Test CI workflows locally
./scripts/test_ci_locally.sh adk-ci.yml

# Or use ACT directly
act -W .github/workflows/adk-ci.yml --secret-file .github/local-secrets.env
```

**Benefits**:
- ✅ Test exact CI environment locally
- ✅ Catch workflow failures before push
- ✅ Save GitHub Actions minutes
- ✅ Faster debugging

### Layer 3: GitHub Actions Dependency Check (CI)
**When**: On every PR that changes dependencies  
**What**: Automatic dependency validation

**Workflow**: `.github/workflows/dependency-check.yml`
- Runs on PRs that modify `requirements.txt`
- Validates dependencies in clean Python 3.11 environment
- Blocks merge if conflicts detected

**Benefits**:
- ✅ Catches issues missed locally
- ✅ Validates in exact CI environment
- ✅ Prevents broken code from merging

### Layer 4: Full CI Suite (CI)
**When**: On every push/PR  
**What**: Full test suite runs

**Workflows**:
- `adk-ci.yml`: Go + Python tests
- `daily-trading.yml`: Trading system validation
- Other workflow-specific tests

---

## 📋 Prevention Checklist

Before pushing changes to `requirements.txt`:

- [ ] Run `python3 scripts/validate_dependencies.py`
- [ ] Run `./scripts/test_ci_locally.sh adk-ci.yml` (if ACT installed)
- [ ] Verify no dependency conflicts
- [ ] Commit changes
- [ ] Push to GitHub
- [ ] Monitor CI status

---

## 🔧 Tools & Scripts

### Dependency Validation
```bash
# Validate dependencies
python3 scripts/validate_dependencies.py

# Check specific requirements file
python3 scripts/validate_dependencies.py requirements-minimal.txt
```

### ACT Local CI Testing
```bash
# Setup ACT (first time)
./scripts/setup_act.sh

# Test CI workflow locally
./scripts/test_ci_locally.sh adk-ci.yml

# List available workflows
act -l
```

### Pre-Commit Hook
```bash
# Already installed in .git/hooks/pre-commit
# Automatically runs on every commit
# Validates dependencies if requirements.txt changed
```

---

## 🚨 What Each Layer Catches

| Layer | Catches | Example |
|-------|---------|---------|
| **Pre-Commit** | Dependency conflicts | `numpy==1.25.0` vs `pandas 2.1.0` requiring `numpy>=1.25.0` |
| **ACT Local** | Workflow syntax errors, test failures | Missing environment variables, broken tests |
| **GitHub Dependency Check** | Environment-specific conflicts | Python 3.11 vs 3.14 differences |
| **Full CI** | Integration issues, runtime errors | API connection failures, import errors |

---

## 💡 Best Practices

### 1. Always Validate Before Committing
```bash
# Before committing requirements.txt changes
python3 scripts/validate_dependencies.py
```

### 2. Test Locally with ACT
```bash
# Before pushing
./scripts/test_ci_locally.sh adk-ci.yml
```

### 3. Use Version Constraints
```python
# Good: Flexible version constraint
numpy>=1.25.0,<2.0.0

# Bad: Exact version (can cause conflicts)
numpy==1.25.0
```

### 4. Check Dependency Compatibility
```bash
# Check what versions are compatible
pip install pip-tools
pip-compile requirements.in  # Creates requirements.txt with resolved versions
```

---

## 🔍 Troubleshooting

### Pre-Commit Hook Not Running
```bash
# Reinstall hook
chmod +x .git/hooks/pre-commit
```

### ACT Not Working
```bash
# Install ACT
./scripts/setup_act.sh

# Check Docker is running
docker ps
```

### Dependency Conflicts Persist
```bash
# Use pip-tools to resolve
pip install pip-tools
pip-compile requirements.in
```

---

## 📊 Success Metrics

**Goal**: Zero dependency-related CI failures

**Current Status**:
- ✅ Pre-commit hook: Active
- ✅ ACT setup: Available
- ✅ GitHub dependency check: Active
- ✅ Full CI suite: Active

**Next Steps**:
- Monitor CI failure rate
- Improve validation scripts based on failures
- Add more comprehensive dependency checking

