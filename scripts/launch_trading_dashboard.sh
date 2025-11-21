#!/bin/bash
#
# Trading Control Center Dashboard Launcher
#
# Launches the Streamlit dashboard for real-time trading system monitoring
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Trading Control Center Dashboard${NC}"
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
    pip install streamlit>=1.29.0 --quiet
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Dashboard will work but API features require ALPACA_API_KEY and ALPACA_SECRET_KEY${NC}\n"
fi

# Get local IP address for mobile access
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

# Launch dashboard
echo -e "${GREEN}Launching Trading Control Center...${NC}\n"
echo -e "${BLUE}Dashboard will open at: http://localhost:8501${NC}"
echo -e "${BLUE}Access from iPhone: http://${LOCAL_IP}:8501${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}\n"

streamlit run dashboard/trading_dashboard.py --server.address=0.0.0.0 --server.port=8501

