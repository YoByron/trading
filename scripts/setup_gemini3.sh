#!/bin/bash
# Setup Gemini 3 Integration

echo "=" 
echo "🔧 GEMINI 3 SETUP"
echo "=" 

# Check for API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set"
    echo ""
    echo "To enable Gemini 3:"
    echo "1. Get API key from: https://makersuite.google.com/app/apikey"
    echo "2. Add to .env file:"
    echo "   echo 'GOOGLE_API_KEY=your_key_here' >> .env"
    echo ""
    echo "Optional: Disable Gemini 3"
    echo "   echo 'GEMINI3_ENABLED=false' >> .env"
    exit 1
fi

echo "✅ GOOGLE_API_KEY found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade langchain-google-genai google-generativeai --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "Gemini 3 is now integrated into:"
echo "  - CoreStrategy (Tier 1 trades)"
echo "  - Automatic trade validation"
echo "  - Multi-agent analysis"
echo ""
echo "To test: python3 scripts/gemini3_trading_analysis.py"

