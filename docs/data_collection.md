# Historical Data Collection System

## Overview

The `DataCollector` class provides systematic archival of OHLCV (Open, High, Low, Close, Volume) data for machine learning training and backtesting.

## Features

- **Multi-Symbol Support**: Fetch data for multiple symbols (SPY, QQQ, VOO, NVDA, GOOGL)
- **Automatic Deduplication**: Prevents saving duplicate dates
- **Lookback Periods**: Configurable history (default: 30 days)
- **CSV Storage**: Human-readable format for analysis
- **Error Handling**: Robust network failure handling
- **CLI Interface**: Standalone command-line tool

## File Structure

```
data/historical/
├── SPY_2025-11-02.csv
├── QQQ_2025-11-02.csv
├── VOO_2025-11-02.csv
├── NVDA_2025-11-02.csv
└── GOOGL_2025-11-02.csv
```

Each CSV contains:
- **Date**: Trading date (index)
- **Open**: Opening price
- **High**: Highest price
- **Low**: Lowest price
- **Close**: Closing price
- **Volume**: Trading volume

## Usage

### 1. Command Line Interface

**Collect data for default symbols (SPY, QQQ, VOO, NVDA, GOOGL):**
```bash
python src/utils/data_collector.py
```

**Custom symbols and lookback:**
```bash
python src/utils/data_collector.py --symbols AAPL,MSFT,TSLA --lookback 60
```

**List existing data files:**
```bash
python src/utils/data_collector.py --list
```

**Load and display historical data:**
```bash
python src/utils/data_collector.py --load SPY
```

### 2. Python Integration

**Basic usage:**
```python
from src.utils.data_collector import DataCollector

# Initialize collector
collector = DataCollector(data_dir="data/historical")

# Collect 30 days of data
symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL"]
collector.collect_daily_data(symbols, lookback_days=30)
```

**Load historical data:**
```python
# Load all historical data for a symbol
data = collector.load_historical_data("SPY")

print(f"Total rows: {len(data)}")
print(f"Date range: {data.index.min()} to {data.index.max()}")
print(data.tail(10))  # Show latest 10 days
```

**List existing files:**
```python
# List all files
all_files = collector.get_existing_files()

# List files for specific symbol
spy_files = collector.get_existing_files(symbol="SPY")
```

### 3. Integration with Autonomous Trader

The data collector is automatically integrated into `scripts/autonomous_trader.py`:

```python
# At the end of daily trading execution
collector = DataCollector(data_dir="data/historical")
symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL"]
collector.collect_daily_data(symbols, lookback_days=30)
```

This runs automatically after each trading day to ensure continuous data archival.

## Data Format

**CSV Structure:**
```csv
Price,Close,High,Low,Open,Volume
Ticker,SPY,SPY,SPY,SPY,SPY
Date,,,,,
2025-10-23,671.76,672.71,667.80,668.12,65604500
2025-10-24,677.25,678.47,675.65,676.46,74356500
...
```

**Loading with pandas:**
```python
import pandas as pd

data = pd.read_csv("data/historical/SPY_2025-11-02.csv",
                   index_col=0,
                   parse_dates=True)

# Access columns
close_prices = data['Close']
volume = data['Volume']

# Date filtering
recent = data['2025-10-01':]
```

## Configuration

**Default Settings:**
- **Data Directory**: `data/historical/`
- **Lookback Days**: 30
- **Symbols**: SPY, QQQ, VOO, NVDA, GOOGL
- **Interval**: 1 day

**Customization:**
```python
# Custom data directory
collector = DataCollector(data_dir="custom/path")

# Custom lookback period
collector.collect_daily_data(symbols, lookback_days=90)

# Add more symbols
symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL", "AAPL", "MSFT"]
```

## Error Handling

The system handles common errors gracefully:

- **Network failures**: Logs error, continues with next symbol
- **Invalid symbols**: Warns and skips
- **Missing data**: Logs warning, no file created
- **Duplicate dates**: Automatically deduplicates when merging

**Example log output:**
```
2025-11-02 21:24:29 - INFO - DataCollector initialized: data/historical
2025-11-02 21:24:29 - INFO - Collecting data for 5 symbols with 30 days lookback
2025-11-02 21:24:29 - INFO - Fetching data for SPY...
2025-11-02 21:24:30 - INFO - Saved 25 rows for SPY to data/historical/SPY_2025-11-02.csv
```

## ML Training Integration (Future)

Once sufficient data is collected (30+ days), use for:

1. **Momentum Indicators**: MACD, RSI, Volume analysis
2. **RL Training**: State representations, reward calculations
3. **Backtesting**: Historical performance validation
4. **Pattern Recognition**: Entry/exit signal detection

**Example ML loading:**
```python
from src.utils.data_collector import DataCollector

collector = DataCollector()

# Load multi-symbol dataset
symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL"]
datasets = {}

for symbol in symbols:
    datasets[symbol] = collector.load_historical_data(symbol)

# Build training dataset
import pandas as pd
combined = pd.concat(datasets, axis=1)

# Calculate features
combined['SPY_returns'] = combined['SPY']['Close'].pct_change()
combined['NVDA_volume_ma'] = combined['NVDA']['Volume'].rolling(10).mean()
```

## Maintenance

**Daily Automatic Collection:**
- Runs after autonomous trader execution
- Collects 30 days of data (rolling window)
- Deduplicates with existing data
- No manual intervention needed

**Manual Collection:**
```bash
# Backfill missing data
python src/utils/data_collector.py --lookback 90

# Collect specific date range (future enhancement)
# python src/utils/data_collector.py --start 2025-10-01 --end 2025-11-01
```

## Dependencies

- **pandas**: DataFrame operations
- **yfinance**: Yahoo Finance API client
- **pathlib**: File system operations

All dependencies are in `requirements.txt`.

## Troubleshooting

**Issue: "No data returned for symbol"**
- Check symbol is valid (use Yahoo Finance ticker)
- Verify market is open (weekends return no data)
- Check network connection

**Issue: "Module not found: pandas/yfinance"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: CSV format incorrect**
- Delete corrupted file: `rm data/historical/SYMBOL_DATE.csv`
- Re-run collection: `python src/utils/data_collector.py`

## Next Steps

1. **Phase 1 (Now - Day 30)**: Collect 30 days baseline
2. **Phase 2 (Month 2)**: Build momentum indicators
3. **Phase 3 (Month 3)**: Integrate with RL system
4. **Phase 4 (Month 4+)**: Real-time feature engineering
