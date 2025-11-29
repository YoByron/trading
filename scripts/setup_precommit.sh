#!/bin/bash
# Setup pre-commit hooks for dependency validation and code quality

set -e

echo "🚀 Setting up Pre-Commit Hooks"
echo "==============================="

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    python3 -m pip install pre-commit || {
        echo "⚠️  Failed to install pre-commit via pip"
        echo "   Try: brew install pre-commit (macOS) or pipx install pre-commit"
        exit 1
    }
else
    echo "✅ pre-commit already installed"
    pre-commit --version
fi

# Check if .pre-commit-config.yaml exists
if [ ! -f .pre-commit-config.yaml ]; then
    echo "⚠️  .pre-commit-config.yaml not found"
    echo "   Pre-commit hooks will use git hooks only"
else
    echo "✅ Found .pre-commit-config.yaml"
fi

# Install pre-commit hooks
echo ""
echo "📥 Installing pre-commit hooks..."
pre-commit install || {
    echo "⚠️  Failed to install pre-commit hooks"
    echo "   Hooks may still work via .git/hooks/pre-commit"
}

# Install commit-msg hook
pre-commit install --hook-type commit-msg || {
    echo "⚠️  Failed to install commit-msg hook"
}

echo ""
echo "✅ Pre-commit hooks installed!"
echo ""
echo "💡 Usage:"
echo "   - Hooks run automatically on 'git commit'"
echo "   - Test manually: pre-commit run --all-files"
echo "   - Skip hooks: git commit --no-verify (not recommended)"
echo ""
echo "🔍 Testing hooks..."
pre-commit run --all-files || {
    echo "⚠️  Some hooks failed (this is OK for first run)"
    echo "   Fix issues and hooks will pass on next commit"
}
