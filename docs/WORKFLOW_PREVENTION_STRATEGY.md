# 🛡️ Workflow Prevention Strategy

**Purpose**: Prevent GitHub Actions workflows from being disabled and ensure continuous operation

**Last Updated**: January 2025

---

## Root Causes Analysis

### Why Workflows Get Disabled

1. **GitHub Auto-Disable (60-Day Rule)**
   - GitHub automatically disables scheduled workflows after 60 days of repository inactivity
   - This is a security feature to prevent abandoned workflows from running
   - **Impact**: Trading stops without warning

2. **Manual Disabling**
   - Workflows can be manually disabled via GitHub UI
   - May happen during troubleshooting or maintenance
   - **Impact**: Trading stops until manually re-enabled

3. **Workflow Failures**
   - Repeated failures can lead to manual disabling
   - Timeout issues, API errors, or configuration problems
   - **Impact**: Trading stops until issues are resolved

---

## Prevention Mechanisms

### 1. Automated Health Check ✅

**Workflow**: `.github/workflows/workflow-health-check.yml`

**Schedule**: Every Monday at 8:00 AM UTC (before trading starts)

**What It Does**:
- Checks status of all critical workflows
- Detects disabled workflows automatically
- Creates GitHub issue if workflows are disabled
- Optionally auto-re-enables (if `AUTO_ENABLE_WORKFLOWS=true` secret is set)

**Critical Workflows Monitored**:
- `daily-trading.yml` - Main trading execution
- `weekend-crypto-trading.yml` - Weekend crypto trading
- `youtube-analysis.yml` - YouTube analysis pipeline

### 2. Keep Repository Active

**Strategy**: Ensure regular commits/activity to prevent 60-day inactivity

**Methods**:
- Daily trading execution creates commits (system_state.json updates)
- Regular code improvements and updates
- Weekly health checks create activity
- Documentation updates

**Monitoring**:
```bash
# Check last commit date
git log -1 --format="%cd" --date=short

# Check repository activity
gh api repos/IgorGanapolsky/trading --jq '.pushed_at'
```

### 3. Workflow Failure Prevention

**Best Practices**:
- ✅ Comprehensive error handling in scripts
- ✅ Timeout protection (30-minute limit)
- ✅ Health checks before execution
- ✅ Fallback mechanisms for API failures
- ✅ Proper secret management

**Monitoring**:
- `notify-on-failure.yml` workflow sends alerts on failures
- Weekly health check detects patterns
- Logs stored in GitHub Actions artifacts

### 4. Duplicate Issue Prevention

**Problem**: Multiple issues created for same problem (#9, #10, #11)

**Solution**: Health check checks for existing issues before creating new ones

**Implementation**:
```javascript
// Check for existing issues before creating
const hasExistingIssue = existingIssues.some(issue => 
  issue.title.toLowerCase().includes('workflow') && 
  issue.title.toLowerCase().includes('disabled')
);
```

---

## Quick Recovery Procedures

### If Workflow is Disabled

**Option 1: Manual Re-enable (2 minutes)**
1. Go to: `https://github.com/IgorGanapolsky/trading/actions/workflows/daily-trading.yml`
2. Click **"Enable workflow"** button
3. Click **"Run workflow"** to trigger immediately

**Option 2: GitHub CLI**
```bash
# List workflows
gh workflow list

# Enable workflow
gh workflow enable daily-trading.yml

# Trigger run
gh workflow run daily-trading.yml
```

**Option 3: Auto-Enable (if configured)**
- Set `AUTO_ENABLE_WORKFLOWS=true` secret
- Health check will auto-enable on next run

---

## Monitoring & Alerts

### Weekly Health Check

**Schedule**: Every Monday 8:00 AM UTC

**Checks**:
- ✅ Workflow enabled status
- ✅ Recent run success/failure
- ✅ Workflow configuration validity

**Alerts**:
- Creates GitHub issue if workflows disabled
- Reports status in Actions summary

### Failure Notifications

**Workflow**: `.github/workflows/notify-on-failure.yml`

**Triggers**: On workflow failure

**Notifications**:
- GitHub issue creation
- Email (if configured)
- Status checks

---

## Configuration

### Required Secrets

**For Health Check**:
- `GITHUB_TOKEN` - Auto-provided by GitHub Actions
- `AUTO_ENABLE_WORKFLOWS` (optional) - Set to `true` to enable auto-re-enable

### Workflow Settings

**Recommended Settings**:
- ✅ Keep workflows enabled
- ✅ Allow manual triggers
- ✅ Enable failure notifications
- ✅ Store logs for 30+ days

---

## Best Practices

### 1. Regular Activity
- ✅ Daily commits from trading execution
- ✅ Weekly code improvements
- ✅ Regular documentation updates

### 2. Monitoring
- ✅ Check Actions tab weekly
- ✅ Review health check results
- ✅ Monitor failure rates

### 3. Documentation
- ✅ Keep this guide updated
- ✅ Document workflow changes
- ✅ Record recovery procedures

### 4. Testing
- ✅ Test workflow changes before merging
- ✅ Verify manual triggers work
- ✅ Test recovery procedures

---

## Metrics & Tracking

### Key Metrics

**Workflow Uptime**:
- Target: 99.9% (1 failure per 1000 runs)
- Current: Monitor via Actions tab

**Detection Time**:
- Target: < 24 hours
- Current: Weekly health check (7 days max)

**Recovery Time**:
- Target: < 5 minutes
- Current: Manual (2 minutes) or auto (instant)

---

## Future Improvements

### Planned Enhancements

1. **Daily Health Check** (instead of weekly)
   - More frequent detection
   - Faster recovery

2. **Auto-Re-Enable by Default**
   - Remove manual intervention
   - Faster recovery

3. **Slack/Discord Notifications**
   - Real-time alerts
   - Better visibility

4. **Workflow Status Dashboard**
   - Visual monitoring
   - Historical trends

---

## Troubleshooting

### Health Check Not Running

**Check**:
```bash
# Verify workflow exists
gh workflow list

# Check recent runs
gh run list --workflow=workflow-health-check.yml
```

**Fix**: Ensure workflow is enabled and scheduled correctly

### Auto-Enable Not Working

**Check**:
- Secret `AUTO_ENABLE_WORKFLOWS` is set to `true`
- GitHub token has `actions:write` permission

**Fix**: Update workflow permissions or secret

### False Positives

**Issue**: Health check reports disabled but workflow is enabled

**Fix**: Check GitHub API response, verify workflow ID

---

## Summary

**Prevention Strategy**:
1. ✅ Weekly health check detects disabled workflows
2. ✅ Regular repository activity prevents 60-day disable
3. ✅ Comprehensive error handling prevents failures
4. ✅ Duplicate issue prevention reduces noise

**Recovery**:
- Manual: 2 minutes
- Auto: Instant (if configured)

**Monitoring**:
- Weekly health checks
- Failure notifications
- Status reporting

---

**Status**: ✅ Active Prevention System Implemented

**Next Review**: February 2025

