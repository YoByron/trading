"""
Google Sheets MCP Server - Spreadsheet operations

Provides tools for:
- Reading spreadsheet data
- Writing data to spreadsheets
- Creating reports
- Updating cells/ranges
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Mapping, Optional, List
from datetime import datetime

try:
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    SHEETS_API_AVAILABLE = True
except ImportError:
    SHEETS_API_AVAILABLE = False

from mcp.client import default_client
from mcp.utils import ensure_env_var, run_sync

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

_sheets_service = None
_gspread_client = None


def _get_sheets_client():
    """Get Google Sheets API client with OAuth2 authentication."""
    global _sheets_service, _gspread_client
    
    if not SHEETS_API_AVAILABLE:
        logger.warning("Google Sheets API libraries not installed")
        return None, None
    
    if _sheets_service is not None and _gspread_client is not None:
        return _sheets_service, _gspread_client
    
    # Check for credentials file path
    credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    token_path = os.getenv("GOOGLE_SHEETS_TOKEN_PATH", "data/google_sheets_token.json")
    
    # Default to data/google_sheets_credentials.json if not specified
    if not credentials_path:
        default_path = "data/google_sheets_credentials.json"
        if os.path.exists(default_path):
            credentials_path = default_path
            logger.info(f"Using default credentials path: {default_path}")
        else:
            logger.warning("GOOGLE_SHEETS_CREDENTIALS_PATH not set and default file not found - Sheets MCP will be limited")
            return None, None
    
    try:
        creds = None
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    logger.error(f"Google Sheets credentials file not found: {credentials_path}")
                    return None, None
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build Google Sheets service
        _sheets_service = build('sheets', 'v4', credentials=creds)
        _gspread_client = gspread.authorize(creds)
        
        logger.info("Google Sheets API client initialized successfully")
        return _sheets_service, _gspread_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {e}")
        return None, None


async def read_range_async(
    spreadsheet_id: str,
    range_name: str
) -> Dict[str, Any]:
    """
    Read data from spreadsheet range.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        range_name: Range to read (e.g., "Sheet1!A1:C10")
        
    Returns:
        Data from range
    """
    logger.info(f"Reading range {range_name} from spreadsheet {spreadsheet_id}")
    
    service, _ = _get_sheets_client()
    if not service:
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "values": [],
            "error": "Google Sheets API client not available - check credentials"
        }
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "values": values,
            "rows": len(values),
            "columns": len(values[0]) if values else 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "values": [],
            "error": f"Google Sheets API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error reading range: {e}")
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "values": [],
            "error": str(e)
        }


def read_range(
    spreadsheet_id: str,
    range_name: str
) -> Dict[str, Any]:
    """Sync wrapper for read_range_async."""
    return run_sync(read_range_async(spreadsheet_id, range_name))


async def write_range_async(
    spreadsheet_id: str,
    range_name: str,
    values: List[List[Any]]
) -> Dict[str, Any]:
    """
    Write data to spreadsheet range.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        range_name: Range to write to (e.g., "Sheet1!A1")
        values: 2D array of values to write
        
    Returns:
        Write result
    """
    logger.info(f"Writing to range {range_name} in spreadsheet {spreadsheet_id}")
    
    service, _ = _get_sheets_client()
    if not service:
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "rows_written": 0,
            "error": "Google Sheets API client not available - check credentials"
        }
    
    try:
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        rows_written = result.get('updatedRows', len(values))
        
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "rows_written": rows_written,
            "cells_updated": result.get('updatedCells', 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "rows_written": 0,
            "error": f"Google Sheets API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error writing range: {e}")
        return {
            "success": False,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "rows_written": 0,
            "error": str(e)
        }


def write_range(
    spreadsheet_id: str,
    range_name: str,
    values: List[List[Any]]
) -> Dict[str, Any]:
    """Sync wrapper for write_range_async."""
    return run_sync(write_range_async(spreadsheet_id, range_name, values))


async def create_report_async(
    spreadsheet_id: str,
    report_name: str,
    data: List[Dict[str, Any]],
    sheet_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a formatted report in spreadsheet.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        report_name: Name of the report
        data: List of dictionaries with report data
        sheet_name: Optional sheet name (creates new if not exists)
        
    Returns:
        Creation result
    """
    logger.info(f"Creating report {report_name} in spreadsheet {spreadsheet_id}")
    
    service, gspread_client = _get_sheets_client()
    if not service or not gspread_client:
        return {
            "success": False,
            "error": "Google Sheets API client not available - check credentials"
        }
    
    if not data:
        return {
            "success": False,
            "error": "No data provided"
        }
    
    try:
        # Open spreadsheet
        spreadsheet = gspread_client.open_by_key(spreadsheet_id)
        target_sheet_name = sheet_name or report_name
        
        # Check if sheet exists, create if not
        try:
            worksheet = spreadsheet.worksheet(target_sheet_name)
            # Clear existing data
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=target_sheet_name,
                rows=len(data) + 1,
                cols=len(data[0].keys()) if data else 10
            )
        
        # Extract headers from first row
        headers = list(data[0].keys())
        
        # Convert data to 2D array
        values = [headers]
        for row in data:
            values.append([row.get(h, "") for h in headers])
        
        # Write data to sheet
        worksheet.update(range_name=f'A1:{chr(64 + len(headers))}{len(values)}', values=values)
        
        # Format header row (bold)
        worksheet.format('A1:{}1'.format(chr(64 + len(headers))), {
            'textFormat': {'bold': True}
        })
        
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "report_name": report_name,
            "sheet_name": target_sheet_name,
            "rows": len(values),
            "columns": len(headers),
            "timestamp": datetime.now().isoformat()
        }
        
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        return {
            "success": False,
            "error": f"Google Sheets API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error creating report: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def create_report(
    spreadsheet_id: str,
    report_name: str,
    data: List[Dict[str, Any]],
    sheet_name: Optional[str] = None
) -> Dict[str, Any]:
    """Sync wrapper for create_report_async."""
    return run_sync(create_report_async(spreadsheet_id, report_name, data, sheet_name))

