#!/bin/bash
# Setup ACT (Local GitHub Actions Runner) for testing CI workflows locally

set -e

echo "🚀 Setting up ACT (Local GitHub Actions Runner)"
echo "================================================"

# Check if ACT is installed
if ! command -v act &> /dev/null; then
    echo "📦 Installing ACT..."

    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install act
        else
            echo "❌ Homebrew not found. Install ACT manually:"
            echo "   brew install act"
            exit 1
        fi
    # Linux
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "📥 Downloading ACT for Linux..."
        curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
    else
        echo "❌ Unsupported OS. Install ACT manually:"
        echo "   https://github.com/nektos/act#installation"
        exit 1
    fi
else
    echo "✅ ACT already installed"
    act --version
fi

# Create local secrets file if it doesn't exist
if [ ! -f .github/local-secrets.env ]; then
    echo ""
    echo "📝 Creating .github/local-secrets.env from example..."
    cp .github/local-secrets.env.example .github/local-secrets.env
    echo "⚠️  Edit .github/local-secrets.env and add your API keys"
    echo "   DO NOT commit this file to git!"
else
    echo "✅ .github/local-secrets.env exists"
fi

# Create .actrc if it doesn't exist
if [ ! -f .actrc ]; then
    echo "✅ .actrc configuration file created"
else
    echo "✅ .actrc already exists"
fi

echo ""
echo "✅ ACT setup complete!"
echo ""
echo "💡 Usage:"
echo "   # Test adk-ci workflow locally:"
echo "   act -W .github/workflows/adk-ci.yml"
echo ""
echo "   # Test with secrets:"
echo "   act --secret-file .github/local-secrets.env -W .github/workflows/adk-ci.yml"
echo ""
echo "   # List available workflows:"
echo "   act -l"
echo ""
