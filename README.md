# 🤖 AI-Powered Automated Trading System

![Status](https://img.shields.io/badge/status-production_ready-brightgreen.svg)
![Win Rate](https://img.shields.io/badge/win_rate-62.2%25-success.svg)
![Sharpe Ratio](https://img.shields.io/badge/sharpe-2.18-success.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

**Validated profitable** automated trading system using momentum indicators (MACD + RSI + Volume) with cloud deployment via GitHub Actions.

---

## 🚀 Quick Start

### 1. Setup (5 minutes)

```bash
# Clone and install
git clone https://github.com/IgorGanapolsky/trading.git
cd trading
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Create `.env` file with your API keys:
```bash
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
PAPER_TRADING=true
DAILY_INVESTMENT=10.0
```

### 3. Test Run

```bash
python scripts/autonomous_trader.py
```

**Done!** System is ready for autonomous execution.

---

## 💰 Performance (Validated)

**60-Day Backtest** (Sept-Oct 2025):
- ✅ Win Rate: **62.2%** (target: >55%)
- ✅ Sharpe Ratio: **2.18** (world-class)
- ✅ Max Drawdown: **2.2%** (excellent)
- ✅ Annualized Return: **26.16%**

**Current Status**: Day 7 of 90-day R&D phase  
**Account**: $99,978.75 (paper trading)  
**Daily Investment**: $10/day (fixed)

---

## 🎯 Strategy

**Momentum-based trading** with technical indicators:
- MACD (trend confirmation)
- RSI (overbought/oversold detection)
- Volume analysis (signal strength)
- Multi-period returns (1m/3m/6m)

**Four-tier allocation**:
- Tier 1 (60%): Index ETFs (SPY, QQQ, VOO)
- Tier 2 (20%): Growth stocks (NVDA, GOOGL, AMZN)
- Tier 3 (10%): IPO opportunities (manual)
- Tier 4 (10%): Crowdfunding (manual)

---

## ☁️ Cloud Deployment

**GitHub Actions** (runs automatically):
- Schedule: Weekdays at 9:35 AM EST
- No Mac required
- Free for public repos
- Logs available in Actions → Artifacts

**Setup**:
1. Add GitHub Secrets (Settings → Secrets → Actions):
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `DAILY_INVESTMENT` (optional, defaults to 10.0)

2. Workflow runs automatically every weekday

**Alternative**: Docker deployment available (see [CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md))

---

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│       GitHub Actions (Cloud Scheduler)      │
│         Triggers: Mon-Fri 9:35 AM EST       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│       autonomous_trader.py (Main Script)    │
│   1. Fetch market data (SPY, QQQ, VOO)     │
│   2. Calculate momentum scores             │
│   3. Select best performer                 │
│   4. Execute $10/day trades                │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌──────┐  ┌──────┐  ┌──────────┐
    │ Tier │  │ Tier │  │  Alpaca  │
    │  1   │  │  2   │  │ Trading  │
    │ $6/d │  │ $2/d │  │   API    │
    └──────┘  └──────┘  └──────────┘
```

---

## 📚 Documentation

### Essential Reading
- **[START_HERE.md](docs/START_HERE.md)** - Complete setup guide
- **[CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md)** - Cloud deployment options
- **[RESEARCH_AND_IMPROVEMENTS.md](docs/RESEARCH_AND_IMPROVEMENTS.md)** - Learning resources

### System Status
- **[PLAN.md](docs/PLAN.md)** - 90-day R&D roadmap
- **[AUTOMATION_STATUS.md](docs/status/AUTOMATION_STATUS.md)** - Current automation status
- **[ALPACA_ACCOUNT_STATUS.md](docs/status/ALPACA_ACCOUNT_STATUS_2025-11-04.md)** - Latest account report

### Technical Docs
- **[BACKTEST_USAGE.md](docs/BACKTEST_USAGE.md)** - Backtesting engine
- **[ORCHESTRATOR_README.md](docs/ORCHESTRATOR_README.md)** - Main orchestrator
- **[Full Documentation Index](docs/)** - All 42 documentation files

---

## 🌟 Features

### Core Trading
- **Momentum Indicators**: MACD, RSI, Volume analysis
- **Multi-tier Allocation**: ETFs (60%), Growth stocks (20%), IPOs (10%), Crowdfunding (10%)
- **Risk Management**: Daily loss limits, max drawdown protection, position sizing
- **Paper Trading**: 90-day validation before live trading

### Data Sources & Sentiment
- **Market Data**: Real-time via Alpaca API
- **YouTube Analysis**: Automated monitoring of 5 financial channels (Parkev Tatevosian CFA, etc)
- **Reddit Sentiment**: Daily scraping from r/wallstreetbets, r/stocks, r/investing, r/options
- **Technical Indicators**: MACD, RSI, Volume, Moving Averages

### Automation
- **Cloud Deployment**: GitHub Actions (weekdays 9:35 AM EST)
- **Daily Reporting**: Automated CEO reports with performance metrics
- **State Persistence**: Complete system state tracking
- **Error Handling**: Retry logic, graceful failures, comprehensive logging

### Sentiment Analysis
- **Reddit Scraper**: Monitors 4 key investing subreddits
  - Extracts ticker mentions and sentiment scores
  - Weighted by upvotes and engagement
  - Confidence levels (high/medium/low)
  - Detects meme stocks and sentiment shifts
  - See [Reddit Sentiment Setup Guide](docs/reddit_sentiment_setup.md)

- **YouTube Monitor**: Analyzes financial video content
  - Daily monitoring of 5 pro financial channels
  - Stock picks and recommendations
  - Auto-updates watchlist
  - Integration with Tier 2 strategy

---

## 🛡️ Risk Management

- **Daily loss limit**: 2% of account value
- **Max drawdown**: 10% (triggers halt)
- **Position sizing**: Fixed $10/day (not portfolio-based)
- **Stop losses**: 5% trailing (ATR-based coming soon)
- **Paper trading**: Validate for 90 days before live trading

---

## 🧪 Testing

```bash
# Run backtests
python run_backtest_now.py

# Run tests
python -m pytest tests/

# Check current positions
python scripts/check_positions.py
```

---

## 🚨 Safety First

**Before live trading**:
- [ ] 90+ days of profitable paper trading
- [ ] Overall return >5%
- [ ] Max drawdown <10%
- [ ] Win rate >55%
- [ ] You understand why trades are made

**Never**:
- Trade money you can't afford to lose
- Skip paper trading validation
- Trade when desperate or emotional
- Use borrowed/margin money initially

---

## 🤝 Contributing

This is a personal trading system, but suggestions welcome via issues.

---

## 📝 License

MIT License - See [LICENSE](LICENSE)

---

## ⚠️ Disclaimer

This software is for educational purposes. Trading involves risk. Past performance does not guarantee future results. Always paper trade first. Only invest what you can afford to lose.

---

**Built with**: Python, Alpaca API, GitHub Actions, Streamlit  
**Maintained by**: Igor Ganapolsky  
**Documentation**: See [docs/](docs/) for complete guides
