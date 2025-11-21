#!/usr/bin/env python3
"""
Automated IPO Scraper - Strategy Expansion

Monitors IPOs from Google Sheets and alerts via Slack when they become tradable on Alpaca.

Features:
- Reads "Target IPOs" sheet from Google Sheets
- Checks if IPOs are tradable on Alpaca
- Sends Slack alerts when IPOs go live
- Tracks processed IPOs to avoid duplicate alerts
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Import MCP integrations
try:
    from mcp.servers.google_sheets import read_range
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  Google Sheets MCP not available - install dependencies")

# Slack is optional - only used if SLACK_BOT_TOKEN is set
SLACK_AVAILABLE = False
try:
    from mcp.servers.slack import send_message
    SLACK_AVAILABLE = True
except ImportError:
    pass

load_dotenv()

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
IPO_TRACKING_FILE = DATA_DIR / "ipo_tracking.json"
SLACK_CHANNEL = os.getenv("SLACK_IPO_CHANNEL", "#trading-alerts")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # Optional - IPO monitor works without it
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_IPO_SPREADSHEET_ID")
GOOGLE_SHEETS_RANGE = os.getenv("GOOGLE_SHEETS_IPO_RANGE", "Target IPOs!A2:E100")

# Alpaca API
ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_ipo_tracking() -> Dict[str, Any]:
    """Load IPO tracking data."""
    if IPO_TRACKING_FILE.exists():
        try:
            with open(IPO_TRACKING_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading IPO tracking: {e}")
    
    return {
        "processed_ipos": [],
        "last_check": None,
        "alerts_sent": []
    }


def save_ipo_tracking(tracking_data: Dict[str, Any]) -> None:
    """Save IPO tracking data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(IPO_TRACKING_FILE, 'w') as f:
        json.dump(tracking_data, f, indent=2)


def read_ipo_sheet() -> List[Dict[str, Any]]:
    """
    Read IPO data from Google Sheets.
    
    Expected columns:
    - Column A: Ticker Symbol
    - Column B: Company Name
    - Column C: Expected IPO Date
    - Column D: Status (Expected/Live)
    - Column E: Notes
    """
    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        logger.error("GOOGLE_SHEETS_IPO_SPREADSHEET_ID not set")
        return []
    
    if not MCP_AVAILABLE:
        logger.error("MCP integrations not available")
        return []
    
    try:
        result = read_range(GOOGLE_SHEETS_SPREADSHEET_ID, GOOGLE_SHEETS_RANGE)
        
        if not result.get("success"):
            logger.error(f"Failed to read Google Sheets: {result.get('error')}")
            return []
        
        values = result.get("values", [])
        ipos = []
        
        for row in values:
            if len(row) < 3:
                continue
            
            ticker = row[0].strip().upper() if row[0] else None
            company_name = row[1].strip() if len(row) > 1 and row[1] else ""
            expected_date = row[2].strip() if len(row) > 2 and row[2] else ""
            status = row[3].strip() if len(row) > 3 and row[3] else "Expected"
            notes = row[4].strip() if len(row) > 4 and row[4] else ""
            
            if ticker:
                ipos.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "expected_date": expected_date,
                    "status": status,
                    "notes": notes
                })
        
        logger.info(f"Read {len(ipos)} IPOs from Google Sheets")
        return ipos
        
    except Exception as e:
        logger.error(f"Error reading Google Sheets: {e}")
        return []


def check_tradable_on_alpaca(ticker: str, api: tradeapi.REST) -> bool:
    """
    Check if a ticker is tradable on Alpaca.
    
    Args:
        ticker: Stock ticker symbol
        api: Alpaca API client
        
    Returns:
        True if tradable, False otherwise
    """
    try:
        asset = api.get_asset(ticker)
        return asset.tradable and asset.status == 'active'
    except Exception as e:
        logger.debug(f"Ticker {ticker} not tradable: {e}")
        return False


def send_ipo_alert(ticker: str, company_name: str, notes: str = "") -> bool:
    """
    Send IPO alert via Slack (optional - only if SLACK_BOT_TOKEN is set).
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        notes: Additional notes
        
    Returns:
        True if alert sent successfully, False if Slack not configured
    """
    if not SLACK_AVAILABLE or not SLACK_BOT_TOKEN:
        logger.debug("Slack not configured - skipping alert (IPO monitor works without it)")
        return False
    
    try:
        message = f"🚀 IPO ALERT: {ticker} ({company_name}) is now LIVE on Alpaca!"
        if notes:
            message += f"\n📝 Notes: {notes}"
        
        # Create formatted blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"IPO Live: {ticker}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Company:* {company_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticker:* {ticker}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:* 🟢 LIVE"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        if notes:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Notes:* {notes}"
                }
            })
        
        result = send_message(SLACK_CHANNEL, message)
        
        if result.get("success"):
            logger.info(f"✅ IPO alert sent for {ticker}")
            return True
        else:
            logger.warning(f"Failed to send IPO alert: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.warning(f"Error sending IPO alert (non-critical): {e}")
        return False


def main():
    """Main IPO scraper execution."""
    print("\n" + "=" * 70)
    print("🚀 AUTOMATED IPO SCRAPER")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Validate configuration
    if not ALPACA_KEY or not ALPACA_SECRET:
        print("❌ ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY required")
        return 1
    
    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        print("❌ ERROR: GOOGLE_SHEETS_IPO_SPREADSHEET_ID required")
        print("   Set this to your Google Sheets spreadsheet ID")
        return 1
    
    # Initialize Alpaca API
    try:
        api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, base_url='https://paper-api.alpaca.markets' if PAPER_TRADING else 'https://api.alpaca.markets')
        print(f"✅ Alpaca API connected (Paper: {PAPER_TRADING})")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Alpaca API: {e}")
        return 1
    
    # Load tracking data
    tracking = load_ipo_tracking()
    processed_tickers = set(tracking.get("processed_ipos", []))
    
    # Read IPOs from Google Sheets
    print(f"\n📊 Reading IPOs from Google Sheets...")
    ipos = read_ipo_sheet()
    
    if not ipos:
        print("⚠️  No IPOs found in Google Sheets")
        return 0
    
    print(f"✅ Found {len(ipos)} IPOs to check")
    
    # Check each IPO
    new_live_ipos = []
    alerts_sent = []
    
    for ipo in ipos:
        ticker = ipo["ticker"]
        company_name = ipo["company_name"]
        status = ipo.get("status", "Expected")
        notes = ipo.get("notes", "")
        
        # Skip if already processed
        if ticker in processed_tickers:
            continue
        
        print(f"\n🔍 Checking {ticker} ({company_name})...")
        
        # Check if tradable on Alpaca
        is_tradable = check_tradable_on_alpaca(ticker, api)
        
        if is_tradable:
            print(f"✅ {ticker} is LIVE on Alpaca!")
            new_live_ipos.append(ipo)
            
            # Send Slack alert
            if send_ipo_alert(ticker, company_name, notes):
                alerts_sent.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "alerted_at": datetime.now().isoformat()
                })
            
            # Mark as processed
            processed_tickers.add(ticker)
        else:
            print(f"⏳ {ticker} not yet tradable (status: {status})")
    
    # Update tracking
    tracking["processed_ipos"] = list(processed_tickers)
    tracking["last_check"] = datetime.now().isoformat()
    tracking["alerts_sent"].extend(alerts_sent)
    
    # Keep only last 100 alerts
    if len(tracking["alerts_sent"]) > 100:
        tracking["alerts_sent"] = tracking["alerts_sent"][-100:]
    
    save_ipo_tracking(tracking)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"IPOs checked: {len(ipos)}")
    print(f"New live IPOs: {len(new_live_ipos)}")
    print(f"Alerts sent: {len(alerts_sent)}")
    
    if new_live_ipos:
        print("\n🚀 New Live IPOs:")
        for ipo in new_live_ipos:
            print(f"   ✅ {ipo['ticker']}: {ipo['company_name']}")
            if ipo.get('notes'):
                print(f"      Notes: {ipo['notes']}")
    
    if new_live_ipos and not alerts_sent:
        print("\n💡 Tip: Set SLACK_BOT_TOKEN to receive Slack alerts for new IPOs")
    
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

