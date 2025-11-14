"""
Finnhub API client for economic calendar and earnings calendar.

Finnhub provides:
- Economic calendar (Fed meetings, GDP, CPI, Employment)
- Earnings calendar (upcoming earnings dates)
- Company fundamentals (financials, earnings)
- Real-time news
"""
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class FinnhubClient:
    """Client for Finnhub API."""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Finnhub client.
        
        Args:
            api_key: Finnhub API key (reads from FINNHUB_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY not set. Finnhub features will be unavailable.")
        self.session = requests.Session()
        self.session.headers.update({"X-Finnhub-Token": self.api_key})
    
    def get_economic_calendar(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Get economic calendar events.
        
        Args:
            start_date: Start date (defaults to today)
            end_date: End date (defaults to today)
        
        Returns:
            List of economic events
        """
        if not self.api_key:
            logger.warning("Finnhub API key not available")
            return []
        
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today()
        
        try:
            url = f"{self.BASE_URL}/calendar/economic"
            params = {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("economicCalendar", [])
            logger.info(f"Retrieved {len(events)} economic events from Finnhub")
            return events
        except Exception as e:
            logger.warning(f"Failed to fetch economic calendar from Finnhub: {e}")
            return []
    
    def has_major_event_today(self) -> bool:
        """
        Check if there's a major economic event today.
        
        Major events include:
        - Fed FOMC meetings
        - GDP releases
        - CPI releases
        - Employment data (NFP)
        
        Returns:
            True if major event today, False otherwise
        """
        events = self.get_economic_calendar()
        
        major_keywords = ["FOMC", "Fed", "GDP", "CPI", "Employment", "NFP", "Non-Farm Payrolls"]
        
        for event in events:
            event_name = event.get("event", "").upper()
            if any(keyword.upper() in event_name for keyword in major_keywords):
                logger.info(f"Major economic event detected: {event.get('event')}")
                return True
        
        return False
    
    def get_earnings_calendar(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Get earnings calendar.
        
        Args:
            start_date: Start date (defaults to today)
            end_date: End date (defaults to 7 days from today)
        
        Returns:
            List of earnings events
        """
        if not self.api_key:
            logger.warning("Finnhub API key not available")
            return []
        
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=7)
        
        try:
            url = f"{self.BASE_URL}/calendar/earnings"
            params = {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            earnings = data.get("earningsCalendar", [])
            logger.info(f"Retrieved {len(earnings)} earnings events from Finnhub")
            return earnings
        except Exception as e:
            logger.warning(f"Failed to fetch earnings calendar from Finnhub: {e}")
            return []
    
    def is_earnings_week(self, symbol: str) -> bool:
        """
        Check if symbol has earnings coming up this week.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            True if earnings this week, False otherwise
        """
        earnings = self.get_earnings_calendar()
        
        for earning in earnings:
            if earning.get("symbol", "").upper() == symbol.upper():
                logger.info(f"{symbol} has earnings: {earning.get('date')}")
                return True
        
        return False
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get company profile and fundamentals.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Company profile data or None
        """
        if not self.api_key:
            logger.warning("Finnhub API key not available")
            return None
        
        try:
            url = f"{self.BASE_URL}/stock/profile2"
            params = {"symbol": symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and "name" in data:
                logger.debug(f"Retrieved company profile for {symbol} from Finnhub")
                return data
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch company profile for {symbol} from Finnhub: {e}")
            return None

