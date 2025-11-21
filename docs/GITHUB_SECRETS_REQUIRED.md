# GitHub Secrets Required

## ✅ Already Configured (Daily Trading)

These secrets are already in use by your daily trading workflow:

| Secret Name | Purpose | Status |
|------------|---------|--------|
| `ALPACA_API_KEY` | Alpaca trading API key | ✅ Required |
| `ALPACA_SECRET_KEY` | Alpaca trading API secret | ✅ Required |
| `POLYGON_API_KEY` | Market data (primary source) | ⚠️ Recommended |
| `FINNHUB_API_KEY` | Economic calendar & earnings | ⚠️ Recommended |
| `ALPHA_VANTAGE_API_KEY` | Fallback market data | ❌ Optional |
| `OPENROUTER_API_KEY` | Multi-LLM sentiment analysis | ⚠️ Recommended |
| `GOOGLE_API_KEY` | ADK orchestrator (if enabled) | ❌ Optional |
| `DAILY_INVESTMENT` | Daily investment amount | ❌ Optional (defaults to 10.0) |

---

## 🆕 Required for IPO Monitor (New Feature)

These secrets are needed for the IPO scraper workflow:

| Secret Name | Purpose | Required? | How to Get |
|------------|---------|-----------|------------|
| `GOOGLE_SHEETS_IPO_SPREADSHEET_ID` | Google Sheets spreadsheet ID with IPO targets | ✅ **YES** | Copy from Google Sheets URL |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | Path to OAuth2 credentials JSON | ✅ **YES** | Download from Google Cloud Console |
| `SLACK_BOT_TOKEN` | Slack bot token for alerts | ✅ **YES** | Create Slack app, get bot token |
| `GOOGLE_SHEETS_TOKEN_PATH` | Path to store OAuth token | ❌ Optional | Defaults to `data/google_sheets_token.json` |
| `GOOGLE_SHEETS_IPO_RANGE` | Sheet range to read | ❌ Optional | Defaults to `Target IPOs!A2:E100` |
| `SLACK_IPO_CHANNEL` | Slack channel for alerts | ❌ Optional | Defaults to `#trading-alerts` |

**Note**: IPO Monitor workflow will skip gracefully if these secrets are missing (won't break daily trading).

---

## 🔧 Optional: MCP Integrations

These secrets enable full MCP functionality (Gmail, Slack, Google Sheets):

| Secret Name | Purpose | Required? | How to Get |
|------------|---------|-----------|------------|
| `GMAIL_CREDENTIALS_PATH` | Gmail OAuth2 credentials | ❌ Optional | Google Cloud Console |
| `GMAIL_TOKEN_PATH` | Gmail token storage path | ❌ Optional | Defaults to `data/gmail_token.json` |
| `SLACK_BOT_TOKEN` | Slack Web API token | ⚠️ If using Slack | Create Slack app |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | Google Sheets OAuth2 credentials | ⚠️ If using IPO Monitor | Google Cloud Console |
| `GOOGLE_SHEETS_TOKEN_PATH` | Google Sheets token path | ❌ Optional | Defaults to `data/google_sheets_token.json` |

---

## 📋 Quick Setup Guide

### For IPO Monitor (Minimum Required)

1. **Google Sheets Setup**:
   ```bash
   # 1. Create a Google Sheet with "Target IPOs" tab
   # 2. Add columns: Ticker (A), Company Name (B), Expected Date (C), Status (D), Notes (E)
   # 3. Get spreadsheet ID from URL: https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
   ```

2. **Google Cloud Console Setup**:
   ```bash
   # 1. Go to: https://console.cloud.google.com/
   # 2. Create project or select existing
   # 3. Enable "Google Sheets API" and "Google Drive API"
   # 4. Create OAuth 2.0 credentials (Desktop app)
   # 5. Download JSON credentials file
   # 6. Upload to GitHub Secrets as base64 or store securely
   ```

3. **Slack Setup**:
   ```bash
   # 1. Go to: https://api.slack.com/apps
   # 2. Create new app → "From scratch"
   # 3. Add bot token scopes: chat:write, channels:read, users:read
   # 4. Install app to workspace
   # 5. Copy "Bot User OAuth Token" (starts with xoxb-)
   ```

4. **Add to GitHub Secrets**:
   ```bash
   # Go to: https://github.com/IgorGanapolsky/trading/settings/secrets/actions
   # Add these secrets:
   GOOGLE_SHEETS_IPO_SPREADSHEET_ID=<your_spreadsheet_id>
   GOOGLE_SHEETS_CREDENTIALS_PATH=<path_or_base64_encoded_json>
   SLACK_BOT_TOKEN=xoxb-your-token-here
   ```

---

## 🎯 Priority Order

### Must Have (System Won't Work Without)
- ✅ `ALPACA_API_KEY`
- ✅ `ALPACA_SECRET_KEY`

### Should Have (Daily Trading Works Better)
- ⚠️ `POLYGON_API_KEY` (reliable market data)
- ⚠️ `FINNHUB_API_KEY` (economic calendar)
- ⚠️ `OPENROUTER_API_KEY` (sentiment analysis)

### Nice to Have (New Features)
- 📈 IPO Monitor: `GOOGLE_SHEETS_IPO_SPREADSHEET_ID`, `GOOGLE_SHEETS_CREDENTIALS_PATH`, `SLACK_BOT_TOKEN`
- 📧 Gmail Integration: `GMAIL_CREDENTIALS_PATH`
- 💬 Slack Integration: `SLACK_BOT_TOKEN` (shared with IPO Monitor)

---

## 🔍 How to Check What You Have

Run this in your repository:

```bash
# Check which secrets are configured (requires gh CLI)
gh secret list
```

Or check manually:
1. Go to: `https://github.com/IgorGanapolsky/trading/settings/secrets/actions`
2. View all configured secrets

---

## ⚠️ Important Notes

1. **IPO Monitor is Optional**: Daily trading will work fine without IPO monitor secrets
2. **MCP Integrations are Optional**: All MCP features gracefully degrade if secrets missing
3. **Secrets Never Expire**: Once set, they persist until you delete them
4. **Security**: Never commit secrets to code - always use GitHub Secrets

---

## 🚀 Quick Start (Minimum)

If you just want to get started quickly:

**Required** (already have):
- ✅ `ALPACA_API_KEY`
- ✅ `ALPACA_SECRET_KEY`

**For IPO Monitor** (add these):
- `GOOGLE_SHEETS_IPO_SPREADSHEET_ID`
- `GOOGLE_SHEETS_CREDENTIALS_PATH`  
- `SLACK_BOT_TOKEN`

Everything else is optional and can be added later!

