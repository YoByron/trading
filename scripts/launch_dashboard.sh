#!/bin/bash
#
# Sentiment RAG Dashboard Launcher
#
# This script activates the virtual environment and launches the Streamlit dashboard
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Sentiment RAG Dashboard Launcher${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if Streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}Streamlit not found. Installing dependencies...${NC}"
    pip install -r requirements.txt --quiet
fi

# Check if sentiment data exists
if [ ! -f "data/sentiment/reddit_2025-11-09.json" ]; then
    echo -e "${YELLOW}Warning: No sentiment data found in data/sentiment/${NC}"
    echo -e "${YELLOW}Run sentiment collection scripts first:${NC}"
    echo -e "  python scripts/collect_reddit_sentiment.py"
    echo -e "  python scripts/collect_news_sentiment.py\n"
fi

# Get local IP address for mobile access
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

# Launch dashboard
echo -e "${GREEN}Launching dashboard...${NC}\n"
echo -e "${BLUE}Dashboard will open at: http://localhost:8501${NC}"
echo -e "${BLUE}Access from iPhone: http://${LOCAL_IP}:8501${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}\n"

streamlit run dashboard/sentiment_dashboard.py --server.address=0.0.0.0 --server.port=8501
