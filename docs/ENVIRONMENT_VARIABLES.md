# 🔐 Environment Variables Reference

**Last Updated**: November 19, 2025  
**Purpose**: Complete reference for all environment variables

---

## Required Variables

### Trading APIs

#### `ALPACA_API_KEY`
- **Required**: ✅ Yes
- **Purpose**: Alpaca API authentication
- **Where to Get**: https://app.alpaca.markets/paper/dashboard/overview → API Keys
- **Format**: String (e.g., `PK...`)
- **GitHub Secret**: ✅ Yes

#### `ALPACA_SECRET_KEY`
- **Required**: ✅ Yes
- **Purpose**: Alpaca API secret key
- **Where to Get**: Same as ALPACA_API_KEY
- **Format**: String (e.g., `...`)
- **GitHub Secret**: ✅ Yes

---

## Optional Variables (Recommended)

### Data Sources

#### `POLYGON_API_KEY`
- **Required**: ⚠️ Recommended (for reliable data)
- **Purpose**: Polygon.io API for market data
- **Where to Get**: https://polygon.io/dashboard/api-keys
- **Format**: String
- **GitHub Secret**: ✅ Yes
- **Priority**: Used as PRIMARY reliable data source (after Alpaca)

#### `ALPHA_VANTAGE_API_KEY`
- **Required**: ❌ Optional (fallback only)
- **Purpose**: Alpha Vantage API (last resort data source)
- **Where to Get**: https://www.alphavantage.co/support/#api-key
- **Format**: String
- **GitHub Secret**: ✅ Yes
- **Note**: Rate-limited, system avoids if possible

#### `FINNHUB_API_KEY`
- **Required**: ⚠️ Recommended (for economic calendar)
- **Purpose**: Finnhub API for earnings/economic calendar
- **Where to Get**: https://finnhub.io/register
- **Format**: String
- **GitHub Secret**: ✅ Yes

---

## AI/LLM APIs

#### `OPENROUTER_API_KEY`
- **Required**: ⚠️ Recommended (enables advanced LLM analysis)
- **Purpose**: Multi-LLM ensemble analysis (Gemini 3 Pro, Claude 3.5 Sonnet, GPT-4o)
- **Where to Get**: https://openrouter.ai/keys
- **Format**: String (e.g., `sk-or-v1-...`)
- **GitHub Secret**: ✅ Yes
- **Status**: ✅ **ENABLED** - System uses multi-LLM sentiment analysis
- **Benefits**: 
  - Advanced sentiment analysis with multi-model consensus
  - Better reasoning and market understanding
  - IPO analysis capabilities
  - Graceful fallback if unavailable (system continues without it)
- **Cost**: ~$15-60/month (within $100/month budget)

#### `GROK_API_KEY`
- **Required**: ⚠️ Recommended (enables real-time Twitter/X sentiment)
- **Purpose**: Real-time Twitter/X sentiment analysis via Grok API
- **Where to Get**: https://x.ai/api (X.ai developer portal)
- **Format**: String (API key from X.ai)
- **GitHub Secret**: ✅ Yes
- **Status**: ✅ **ENABLED** - Adds real-time FinTwit sentiment
- **Benefits**:
  - Real-time Twitter/X sentiment (faster than Reddit/Stocktwits)
  - FinTwit community analysis
  - Breaking news reactions
  - Influencer tracking (Elon, Cathie Wood, analysts)
- **Cost**: $30/month (within $100/month budget)

#### `GOOGLE_API_KEY`
- **Required**: ⚠️ If using ADK orchestrator or Google services
- **Purpose**: Google Cloud API key for various Google services
- **Format**: String (e.g., `AIzaSy...`)
- **GitHub Secret**: ✅ Yes

#### `GEMINI_API_KEY`
- **Required**: ⚠️ If using Gemini API directly
- **Purpose**: Google Gemini API for direct Gemini access
- **Format**: String (e.g., `AIzaSy...`)
- **GitHub Secret**: ✅ Yes

#### `GOOGLE_PROJECT_ID`
- **Required**: ⚠️ If using Google Cloud services
- **Purpose**: Google Cloud project ID
- **Format**: String
- **GitHub Secret**: ✅ Yes

#### `NOTIFICATION_CHANNELS`
- **Required**: ❌ Optional
- **Purpose**: Comma-separated list of notification channels
- **Default**: `email,dashboard,log`
- **Options**: `email`, `dashboard`, `log`, `slack` (if configured)
- **Note**: Slack removed from defaults - use email instead

#### `APPROVAL_NOTIFICATION_CHANNELS`
- **Required**: ❌ Optional
- **Purpose**: Channels for approval request notifications
- **Default**: `email`
- **Options**: `email`, `slack` (if configured)

---

## Configuration

#### `PAPER_TRADING`
- **Required**: ✅ Yes
- **Purpose**: Enable/disable paper trading mode
- **Values**: `"true"` or `"false"`
- **Default**: `"true"`
- **GitHub Secret**: ❌ No (hardcoded in workflow)

#### `DAILY_INVESTMENT`
- **Required**: ✅ Yes
- **Purpose**: Daily investment amount ($)
- **Format**: Float (e.g., `"10.0"`)
- **Default**: `"10.0"`
- **GitHub Secret**: ✅ Yes (optional, defaults to 10.0)

#### `ENVIRONMENT`
- **Required**: ❌ Optional
- **Purpose**: Environment name for Sentry
- **Values**: `"production"`, `"development"`, `"staging"`
- **Default**: `"production"`
- **GitHub Secret**: ❌ No

---

## Error Monitoring

#### `SENTRY_DSN`
- **Required**: ❌ Optional (recommended)
- **Purpose**: Sentry error tracking DSN
- **Where to Get**: https://sentry.io/settings/projects/ → Client Keys (DSN)
- **Format**: String (e.g., `https://...@...sentry.io/...`)
- **GitHub Secret**: ✅ Yes
- **Status**: Configured but optional (fails gracefully if not set)

---

## ADK Orchestrator (Optional)

#### `ADK_ENABLED`
- **Required**: ❌ Optional
- **Purpose**: Enable Go ADK orchestrator
- **Values**: `"1"` or `"0"`
- **Default**: `"0"` (disabled during R&D phase)

#### `ADK_BASE_URL`
- **Required**: ⚠️ If ADK_ENABLED=1
- **Purpose**: Go ADK service URL
- **Default**: `"http://127.0.0.1:8080/api"`

#### `ADK_APP_NAME`
- **Required**: ⚠️ If ADK_ENABLED=1
- **Purpose**: App name for ADK
- **Default**: `"trading_orchestrator"`

---

## Langchain (Optional)

#### `LANGCHAIN_MODEL`
- **Required**: ❌ Optional
- **Purpose**: Langchain model name
- **Default**: `"claude-3-5-sonnet-20241022"`

#### `LANGCHAIN_TEMPERATURE`
- **Required**: ❌ Optional
- **Purpose**: Langchain temperature
- **Default**: `"0.3"`

#### `LANGCHAIN_ENABLE_MCP`
- **Required**: ❌ Optional
- **Purpose**: Enable MCP tool bridge
- **Default**: `"true"`

---

## Alpha Vantage Timeout (Advanced)

#### `ALPHAVANTAGE_MAX_TOTAL_SECONDS`
- **Required**: ❌ Optional
- **Purpose**: Max total time for Alpha Vantage requests
- **Default**: `"90"` (90 seconds)
- **Note**: Prevents long waits on rate-limited API

---

## Setup Checklist

### Minimum Required (Basic Functionality)
- [ ] `ALPACA_API_KEY`
- [ ] `ALPACA_SECRET_KEY`
- [ ] `PAPER_TRADING` (defaults to "true")
- [ ] `DAILY_INVESTMENT` (defaults to "10.0")

### Recommended (Reliable Data)
- [ ] `POLYGON_API_KEY` (primary reliable data source)
- [ ] `FINNHUB_API_KEY` (economic calendar)

### Optional (Enhanced Features)
- [ ] `SENTRY_DSN` (error monitoring)
- [ ] `OPENROUTER_API_KEY` (multi-LLM analysis - disabled)
- [ ] `GOOGLE_API_KEY` (ADK orchestrator - disabled)

---

## GitHub Secrets Setup

To add secrets to GitHub:

1. Go to: Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each variable:
   - Name: `ALPACA_API_KEY`
   - Value: Your API key
4. Repeat for all required variables

**Required Secrets**:
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `POLYGON_API_KEY` (recommended)
- `FINNHUB_API_KEY` (recommended)
- `SENTRY_DSN` (optional)

---

## Local Development Setup

Create `.env` file in project root:

```bash
# Required
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
PAPER_TRADING=true
DAILY_INVESTMENT=10.0

# Recommended
POLYGON_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Optional
SENTRY_DSN=your_dsn_here
```

**Never commit `.env` file** - It's in `.gitignore`

---

## Verification

Test your configuration:

```bash
# Check required variables
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY']
for var in required:
    print(f'{var}: {\"✅\" if os.getenv(var) else \"❌\"}')
"
```

---

## Related Documentation

- `docs/TROUBLESHOOTING.md` - Troubleshooting guide
- `.claude/skills/error_handling_protocols/SKILL.md` - Error handling
- `docs/PLAN.md` - Infrastructure setup

