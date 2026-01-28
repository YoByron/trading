# /delegate - Send Task to Cloud Agent

Delegates a task to run in GitHub Actions while you continue working locally.

## Usage

```
/delegate "Upgrade all dependencies and fix breaking changes"
/delegate "Run full test suite and fix any failures"
/delegate "Refactor src/utils/ to remove duplication"
```

## How It Works

1. **Package the task** - Creates `TASK_MANIFEST.json` with:
   - Task description
   - Current branch context
   - Relevant file paths
   - Expected outcome

2. **Create cloud branch** - Pushes to `claude/delegate/<task-hash>`

3. **Trigger workflow** - Dispatches `ralph-loop-ai.yml` with task manifest

4. **Return control** - You can continue working locally immediately

5. **Get notified** - Workflow creates PR when done with:
   - All changes made
   - Execution logs
   - Test results

## Implementation

When invoked, execute these steps:

```bash
# 1. Generate task hash
TASK_HASH=$(echo "$TASK_DESCRIPTION" | md5sum | cut -c1-8)
BRANCH_NAME="claude/delegate/${TASK_HASH}"

# 2. Create task manifest
cat > /tmp/TASK_MANIFEST.json << MANIFEST
{
  "task": "$TASK_DESCRIPTION",
  "source_branch": "$(git branch --show-current)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "delegated_by": "local-claude-code"
}
MANIFEST

# 3. Create and push branch
git checkout -b "$BRANCH_NAME"
cp /tmp/TASK_MANIFEST.json .claude/TASK_MANIFEST.json
git add .claude/TASK_MANIFEST.json
git commit -m "chore: Delegate task to cloud agent

Task: $TASK_DESCRIPTION"
git push -u origin "$BRANCH_NAME"

# 4. Trigger workflow
gh workflow run ralph-loop-ai.yml \
  --ref "$BRANCH_NAME" \
  -f task_manifest="$(cat /tmp/TASK_MANIFEST.json)"

# 5. Return to original branch
git checkout -
```

## When To Use

- **Large refactors** that touch many files
- **Dependency upgrades** with potential breaking changes
- **Test fixes** that require multiple iterations
- **Mechanical changes** (formatting, linting, cleanup)

## When NOT To Use

- Quick fixes (just do them locally)
- Tasks requiring human judgment at each step
- Anything needing immediate feedback
