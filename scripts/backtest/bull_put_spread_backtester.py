import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np

class BullPutSpreadBacktester:
    def __init__(self, options_data: pd.DataFrame):
        self.options_data = options_data
        self.trades: List[Dict] = []
        self.results: Dict = {}
    
    def calculate_spread_premium(self, underlying_price: float, 
                                strike_short: float, strike_long: float, 
                                dte: int) -> float:
        """Calculate the premium for a bull put spread."""
        short_premium = self._calculate_option_premium(
            underlying_price, strike_short, dte, "put"
        )
        long_premium = self._calculate_option_premium(
            underlying_price, strike_long, dte, "put"
        )
        return short_premium - long_premium
    
    def _calculate_option_premium(self, underlying_price: float, 
                                 strike: float, dte: int, 
                                 option_type: str) -> float:
        """Calculate option premium using simplified Black-Scholes."""
        if dte <= 0:
            if option_type == "put":
                return max(strike - underlying_price, 0)
            else:
                return max(underlying_price - strike, 0)
        
        # Simplified premium calculation
        time_value = max(0.01 * dte / 365, 0.001)
        intrinsic = 0
        
        if option_type == "put":
            intrinsic = max(strike - underlying_price, 0)
        else:
            intrinsic = max(underlying_price - strike, 0)
        
        return intrinsic + time_value
    
    def find_optimal_strikes(self, underlying_price: float, 
                           target_delta: float = 0.30) -> Tuple[float, float]:
        """Find optimal strike prices for the spread."""
        # Simple strike selection based on percentage of underlying
        short_strike = underlying_price * (1 - target_delta * 0.1)
        long_strike = short_strike * 0.95  # 5% below short strike
        
        # Round to nearest dollar
        short_strike = round(short_strike)
        long_strike = round(long_strike)
        
        return short_strike, long_strike
    
    def backtest_strategy(self, start_date: str, end_date: str, 
                         dte_entry: int = 45, dte_exit: int = 21) -> Dict:
        """Run the backtest for the bull put spread strategy."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        current_date = start_dt
        total_trades = 0
        winning_trades = 0
        total_pnl = 0
        
        while current_date <= end_dt:
            # Simulate weekly entries (every 7 days)
            if self._should_enter_trade(current_date):
                trade_result = self._execute_trade(current_date, dte_entry, dte_exit)
                if trade_result:
                    total_trades += 1
                    total_pnl += trade_result['pnl']
                    if trade_result['pnl'] > 0:
                        winning_trades += 1
                    self.trades.append(trade_result)
            
            current_date += timedelta(days=1)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        self.results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_pnl': total_pnl / total_trades if total_trades > 0 else 0,
            'trades': self.trades
        }
        
        return self.results
    
    def _should_enter_trade(self, date: datetime) -> bool:
        """Determine if we should enter a trade on this date."""
        # Enter trades on Mondays (weekday 0)
        return date.weekday() == 0
    
    def _execute_trade(self, entry_date: datetime, 
                      dte_entry: int, dte_exit: int) -> Optional[Dict]:
        """Execute a single bull put spread trade."""
        # Simulate underlying price (this would come from real data)
        underlying_price = 4000 + np.random.normal(0, 100)  # SPX-like price
        
        # Find optimal strikes
        short_strike, long_strike = self.find_optimal_strikes(underlying_price)
        
        # Calculate entry premium
        entry_premium = self.calculate_spread_premium(
            underlying_price, short_strike, long_strike, dte_entry
        )
        
        # Simulate price movement over holding period
        days_held = dte_entry - dte_exit
        exit_date = entry_date + timedelta(days=days_held)
        
        # Simple price evolution
        price_change = np.random.normal(0, underlying_price * 0.01 * np.sqrt(days_held / 365))
        exit_underlying_price = underlying_price + price_change
        
        # Calculate exit premium
        exit_premium = self.calculate_spread_premium(
            exit_underlying_price, short_strike, long_strike, dte_exit
        )
        
        # Calculate P&L (we sold the spread, so profit when premium decreases)
        pnl = (entry_premium - exit_premium) * 100  # Assume 1 contract = 100 multiplier
        
        return {
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'exit_date': exit_date.strftime('%Y-%m-%d'),
            'underlying_entry': underlying_price,
            'underlying_exit': exit_underlying_price,
            'short_strike': short_strike,
            'long_strike': long_strike,
            'entry_premium': entry_premium,
            'exit_premium': exit_premium,
            'pnl': pnl,
            'days_held': days_held
        }
    
    def print_results(self):
        """Print backtest results summary."""
        if not self.results:
            print("No backtest results available. Run backtest_strategy() first.")
            return
        
        print(f"=== Bull Put Spread Backtest Results ===")
        print(f"Total Trades: {self.results['total_trades']}")
        print(f"Winning Trades: {self.results['winning_trades']}")
        print(f"Win Rate: {self.results['win_rate']:.2%}")
        print(f"Total P&L: ${self.results['total_pnl']:,.2f}")
        print(f"Average P&L per Trade: ${self.results['average_pnl']:,.2f}")
        
        if self.results['total_trades'] > 0:
            print(f"✅ Initialized {self.results['total_trades']} trades successfully")