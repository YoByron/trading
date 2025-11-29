#!/bin/bash
# Manual script to update GitHub wiki with latest dashboard
# This bypasses GitHub Actions and updates wiki directly

set -e

echo "📊 Generating progress dashboard..."
python3 scripts/generate_progress_dashboard.py

echo "📝 Updating GitHub Wiki..."

# Check if GH_TOKEN is set (GitHub CLI token)
if [ -z "$GH_TOKEN" ]; then
    echo "⚠️  GH_TOKEN not set. Using GitHub CLI authentication..."
    GH_TOKEN=$(gh auth token 2>/dev/null || echo "")
fi

if [ -z "$GH_TOKEN" ]; then
    echo "❌ ERROR: Cannot update wiki - no authentication token"
    echo "   Set GH_TOKEN environment variable or run: gh auth login"
    exit 1
fi

# Clone wiki repository
WIKI_DIR="wiki_repo_temp"
rm -rf "$WIKI_DIR"
git clone "https://x-access-token:${GH_TOKEN}@github.com/IgorGanapolsky/trading.wiki.git" "$WIKI_DIR" || {
    echo "⚠️  Wiki repository doesn't exist - creating..."
    mkdir -p "$WIKI_DIR"
    cd "$WIKI_DIR"
    git init
    git config user.name "GitHub Actions Bot"
    git config user.email "actions@github.com"
    git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/IgorGanapolsky/trading.wiki.git"
    cd ..
}

# Copy generated dashboard
cp wiki/Progress-Dashboard.md "$WIKI_DIR/Progress-Dashboard.md"
if [ -f wiki/Home.md ]; then
    cp wiki/Home.md "$WIKI_DIR/Home.md"
fi

# Commit and push
cd "$WIKI_DIR"
git config user.name "GitHub Actions Bot"
git config user.email "actions@github.com"
git add -A

if ! git diff --staged --quiet; then
    COMMIT_MSG="📊 Manual update progress dashboard - $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    git commit -m "$COMMIT_MSG"

    # Try master branch first (wiki default), then main
    if git push origin master 2>/dev/null; then
        echo "✅ Wiki updated successfully (master branch)!"
    elif git push origin main 2>/dev/null; then
        echo "✅ Wiki updated successfully (main branch)!"
    else
        # Try to create master branch
        git checkout -b master 2>/dev/null || git checkout master
        git push -u origin master && echo "✅ Wiki updated successfully (created master branch)!"
    fi
else
    echo "📋 No changes to dashboard"
fi

cd ..
rm -rf "$WIKI_DIR"

echo "✅ Wiki update complete!"
echo "📊 View dashboard: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard"
