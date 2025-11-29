#!/bin/bash
# Automatically fix security alerts using GitHub CLI
# This script reviews and fixes security alerts autonomously

set -e

echo "🔒 Security Alert Auto-Fix Script"
echo "===================================="
echo ""

# Check GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found. Install: brew install gh"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated. Run: gh auth login"
    exit 1
fi

REPO="IgorGanapolsky/trading"

echo "📊 Checking security status..."
echo ""

# Check current security features status
echo "Security Features Status:"
gh api repos/$REPO --jq '.security_and_analysis | to_entries[] | "  \(.key): \(.value.status)"' 2>&1
echo ""

# Check Dependabot alerts
echo "🔍 Checking Dependabot alerts..."
DEPENDABOT_COUNT=$(gh api repos/$REPO/dependabot/alerts --jq 'length' 2>&1 || echo "0")
echo "  Found: $DEPENDABOT_COUNT alerts"
echo ""

if [ "$DEPENDABOT_COUNT" -gt 0 ]; then
    echo "📋 Dependabot Alerts (first 10):"
    gh api repos/$REPO/dependabot/alerts --jq '[.[] | select(.state == "open") | {
        number: .number,
        severity: .security_vulnerability.severity,
        package: .dependency.package.name,
        vulnerable_version: .security_vulnerability.vulnerable_version_range,
        summary: .security_advisory.summary
    }] | .[0:10] | .[] | "  [\(.severity)] \(.package) - \(.summary)"' 2>&1 || echo "  (Could not fetch alerts)"
    echo ""
fi

# Check CodeQL alerts
echo "🔍 Checking CodeQL alerts..."
CODEQL_COUNT=$(gh api repos/$REPO/code-scanning/alerts --jq 'length' 2>&1 || echo "0")
echo "  Found: $CODEQL_COUNT alerts"
echo ""

if [ "$CODEQL_COUNT" -gt 0 ]; then
    echo "📋 CodeQL Alerts (first 10):"
    gh api repos/$REPO/code-scanning/alerts --jq '[.[] | select(.state == "open") | {
        number: .number,
        rule: .rule.id,
        severity: .rule.severity,
        message: .rule.description
    }] | .[0:10] | .[] | "  [\(.severity)] \(.rule) - \(.message)"' 2>&1 || echo "  (Could not fetch alerts)"
    echo ""
fi

# Check secret scanning alerts
echo "🔍 Checking Secret Scanning alerts..."
SECRET_COUNT=$(gh api repos/$REPO/secret-scanning/alerts --jq 'length' 2>&1 || echo "0")
echo "  Found: $SECRET_COUNT alerts"
echo ""

if [ "$SECRET_COUNT" -gt 0 ]; then
    echo "⚠️  WARNING: Secret scanning alerts found!"
    echo "  Review manually: https://github.com/$REPO/security/secret-scanning"
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Security Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dependabot alerts: $DEPENDABOT_COUNT"
echo "  CodeQL alerts: $CODEQL_COUNT"
echo "  Secret scanning alerts: $SECRET_COUNT"
echo ""

# Recommendations
if [ "$DEPENDABOT_COUNT" -gt 0 ] || [ "$CODEQL_COUNT" -gt 0 ]; then
    echo "💡 Recommendations:"
    echo ""

    if [ "$DEPENDABOT_COUNT" -gt 0 ]; then
        echo "  1. Review Dependabot PRs: https://github.com/$REPO/pulls?q=is:pr+is:open+label:dependencies"
        echo "  2. Merge security updates automatically (if safe)"
    fi

    if [ "$CODEQL_COUNT" -gt 0 ]; then
        echo "  3. Review CodeQL alerts: https://github.com/$REPO/security/code-scanning"
        echo "  4. Fix or dismiss false positives"
    fi

    echo ""
    echo "🔗 View all alerts: https://github.com/$REPO/security"
else
    echo "✅ No open security alerts found!"
fi

echo ""
