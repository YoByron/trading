#!/bin/bash

echo "=========================================="
echo "Sentiment Aggregator Verification"
echo "=========================================="
echo ""

echo "1. Checking file structure..."
echo ""

files=(
    "src/utils/news_sentiment.py"
    "test_sentiment_demo.py"
    "docs/NEWS_SENTIMENT_AGGREGATOR.md"
    "SENTIMENT_AGGREGATOR_SUMMARY.md"
    "data/sentiment"
)

for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file exists"
        if [ -f "$file" ]; then
            size=$(wc -c < "$file" | tr -d ' ')
            echo "   Size: $size bytes"
        fi
    else
        echo "❌ $file NOT FOUND"
    fi
done

echo ""
echo "2. Checking dependencies..."
echo ""

source venv/bin/activate 2>/dev/null || echo "⚠️  venv not activated"

python3 -c "import yfinance; print('✅ yfinance installed')" 2>/dev/null || echo "❌ yfinance NOT installed"
python3 -c "import requests; print('✅ requests installed')" 2>/dev/null || echo "❌ requests NOT installed"
python3 -c "from alpha_vantage.timeseries import TimeSeries; print('✅ alpha-vantage installed')" 2>/dev/null || echo "❌ alpha-vantage NOT installed"

echo ""
echo "3. Checking .env configuration..."
echo ""

if [ -f ".env" ]; then
    echo "✅ .env file exists"
    if grep -q "ALPHA_VANTAGE_API_KEY" .env; then
        key=$(grep "ALPHA_VANTAGE_API_KEY" .env | cut -d'=' -f2)
        if [ -n "$key" ] && [ "$key" != "your_key_here" ]; then
            echo "✅ ALPHA_VANTAGE_API_KEY configured"
        else
            echo "⚠️  ALPHA_VANTAGE_API_KEY needs to be set"
        fi
    else
        echo "⚠️  ALPHA_VANTAGE_API_KEY not found in .env"
    fi
else
    echo "❌ .env file NOT FOUND"
fi

echo ""
echo "4. Testing module import..."
echo ""

python3 -c "from src.utils.news_sentiment import NewsSentimentAggregator; print('✅ Module imports successfully')" 2>/dev/null || echo "❌ Module import FAILED"

echo ""
echo "5. Checking output directory..."
echo ""

if [ -d "data/sentiment" ]; then
    count=$(ls -1 data/sentiment/*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ data/sentiment/ directory exists"
    echo "   Reports found: $count"
    if [ $count -gt 0 ]; then
        echo "   Latest reports:"
        ls -lt data/sentiment/*.json | head -3 | awk '{print "   - " $9 " (" $5 " bytes)"}'
    fi
else
    echo "❌ data/sentiment/ directory NOT FOUND"
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add ALPHA_VANTAGE_API_KEY to .env (if not already set)"
echo "2. Run: python3 -m src.utils.news_sentiment --test"
echo "3. Run: python3 test_sentiment_demo.py"
echo "4. Check output: cat data/sentiment/news_*.json"
echo ""
