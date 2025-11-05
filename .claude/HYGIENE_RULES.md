# 📋 Repository Hygiene Rules - ENFORCED

## Critical Rule for CTO

**ALL .md files MUST be in `docs/` directory and linked from `README.md`**

Exception: `README.md` stays in root

## File Organization Standards

### Root Directory (MINIMAL)

**Allowed files ONLY:**
- `README.md` - Main documentation (ONLY .md file in root)
- `LICENSE` - Project license
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker build configuration
- `docker-compose.yml` - Docker orchestration
- `.gitignore` - Git ignore rules
- `.env.example` - Environment variable template
- `.pre-commit-config.yaml` - Pre-commit hook configuration

**EVERYTHING ELSE goes in subdirectories:**
- `.md` files → `docs/`
- `.py` test files → `tests/`
- `.py` script files → `scripts/`
- `.json` data files → `data/`
- `.txt` documentation → `docs/`
- `.log` files → `logs/`

### Directory Structure

```
trading/
├── README.md              ← ONLY .md file in root
├── requirements.txt       ← Python dependencies
├── Dockerfile             ← Docker config
├── docker-compose.yml     ← Docker orchestration
├── LICENSE                ← License file
│
├── docs/                  ← ALL other .md files go here
│   ├── *.md               ← All documentation
│   └── status/            ← Status reports
│
├── scripts/               ← All executable scripts
│   └── *.py, *.sh
│
├── src/                   ← Source code
│   ├── core/
│   ├── strategies/
│   └── utils/
│
├── tests/                 ← All test files
│   └── test_*.py
│
├── data/                  ← Data files (gitignored)
│   └── *.json, *.csv
│
├── logs/                  ← Log files (gitignored)
│   └── *.log
│
└── reports/               ← Generated reports
    └── daily_report_*.txt
```

## Pre-Commit Hook Rules

The pre-commit hook will automatically:

1. **Check for misplaced .md files**
   - Error if any .md file (except README.md) is in root
   - Suggest moving to docs/

2. **Check for test files in root**
   - Error if test_*.py files are in root
   - Suggest moving to tests/

3. **Check for data files in root**
   - Error if *.json files are in root
   - Suggest moving to data/

4. **Check for script files in root**
   - Error if standalone .py files are in root
   - Suggest moving to scripts/

5. **Update README.md links**
   - Remind to link new docs/ files from README.md
   - Ensure single source of truth

## Enforcement

### Manual Check
```bash
# Run hygiene check
python .claude/skills/precommit_hygiene/scripts/precommit_hygiene.py check_file_organization
```

### Auto-Fix
```bash
# Organize automatically
python .claude/skills/precommit_hygiene/scripts/precommit_hygiene.py check_file_organization --fix
```

### Pre-Commit Hook
```bash
# Automatically runs on git commit
git add .
git commit -m "your message"
# Hook runs automatically, prevents commit if issues found
```

## CTO Commitment

**I, Claude (CTO), commit to:**
1. ✅ Never create .md files in root (except README.md)
2. ✅ Always move documentation to docs/
3. ✅ Always link new docs from README.md
4. ✅ Follow 2025 best practices for repository organization
5. ✅ Run pre-commit hook before every commit
6. ✅ Keep root directory minimal and clean

**If I break these rules, the pre-commit hook will catch it.**

## README.md Structure

README.md must have a "Complete Documentation Index" section linking to all docs:

```markdown
## 📚 Complete Documentation Index

### 🚀 Start Here
- [START_HERE.md](docs/START_HERE.md)
- ...

### 🎯 System Status & Planning
- [PLAN.md](docs/PLAN.md)
- ...

### 📊 Status Reports
- [AUTOMATION_STATUS.md](docs/status/AUTOMATION_STATUS.md)
- ...
```

## Violations and Fixes

| Violation | Fix |
|-----------|-----|
| Created `NEW_FEATURE.md` in root | Move to `docs/NEW_FEATURE.md`, link from README |
| Created `test_new.py` in root | Move to `tests/test_new.py` |
| Created `data.json` in root | Move to `data/data.json` |
| Created `script.py` in root | Move to `scripts/script.py` |

## Reminder

**If you see a .md file in root (except README.md), it's wrong.**
**If you see a test_*.py file in root, it's wrong.**
**If you see a *.json file in root, it's wrong.**

**Always organize files properly BEFORE committing.**

---

**Enforced by:** Pre-commit hook (`.git/hooks/pre-commit`)
**Last Updated:** November 5, 2025
**Committed by:** Claude (CTO)

