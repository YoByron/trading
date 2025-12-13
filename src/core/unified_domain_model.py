"""
Unified Domain Model (UDM) for Trading System
Inspired by Netflix's Upper Metamodel & UDA Architecture

"Model Once, Represent Everywhere"
- Single authoritative definition for all trading concepts
- Auto-generates schemas for different representations
- Ensures consistency across strategies, data sources, and storage

References:
- Netflix UDA: blog.thewitslab.com
- Upper Metamodel: infoq.com/news/2025/12/netflix-upper-uda-architecture
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import json


# =============================================================================
# CORE DOMAIN ENUMS (Single Source of Truth)
# =============================================================================

class AssetClass(str, Enum):
    """All supported asset classes"""
    EQUITY = "equity"
    CRYPTO = "crypto"
    OPTION = "option"
    ETF = "etf"
    BOND = "bond"


class TradeAction(str, Enum):
    """Trade action types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderStatus(str, Enum):
    """Order status states"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalStrength(str, Enum):
    """Signal confidence levels"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class StrategyTier(str, Enum):
    """Trading strategy tiers"""
    TIER1_SAFE = "tier1_safe"           # Low risk, high probability
    TIER2_MOMENTUM = "tier2_momentum"   # Momentum plays
    TIER3_SWING = "tier3_swing"         # Swing trades
    TIER4_OPTIONS = "tier4_options"     # Options strategies
    TIER5_CRYPTO = "tier5_crypto"       # Crypto trading


class DataSource(str, Enum):
    """Data source identifiers"""
    ALPACA = "alpaca"
    POLYGON = "polygon"
    YFINANCE = "yfinance"
    NEWS_API = "news_api"
    REDDIT = "reddit"
    TWITTER = "twitter"
    GEMINI_RESEARCH = "gemini_research"


# =============================================================================
# CORE DOMAIN MODELS (Netflix Upper Pattern)
# =============================================================================

@dataclass
class Symbol:
    """Unified symbol representation"""
    ticker: str                          # e.g., "BTCUSD", "AAPL"
    asset_class: AssetClass
    exchange: Optional[str] = None       # e.g., "NASDAQ", "CRYPTO"
    name: Optional[str] = None           # e.g., "Bitcoin", "Apple Inc."
    
    def to_alpaca(self) -> str:
        """Project to Alpaca format"""
        if self.asset_class == AssetClass.CRYPTO:
            return self.ticker.replace("/", "")
        return self.ticker
    
    def to_yfinance(self) -> str:
        """Project to yfinance format"""
        if self.asset_class == AssetClass.CRYPTO:
            return f"{self.ticker[:3]}-USD"
        return self.ticker


@dataclass
class Price:
    """Unified price representation"""
    value: float
    currency: str = "USD"
    timestamp: Optional[datetime] = None
    source: Optional[DataSource] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "currency": self.currency,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source.value if self.source else None
        }


@dataclass
class Signal:
    """Unified trading signal"""
    symbol: Symbol
    action: TradeAction
    strength: SignalStrength
    confidence: float                    # 0.0 - 1.0
    source: str                          # Strategy or model that generated it
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol.ticker,
            "asset_class": self.symbol.asset_class.value,
            "action": self.action.value,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def is_actionable(self, min_confidence: float = 0.6) -> bool:
        """Check if signal meets minimum confidence threshold"""
        return (
            self.action != TradeAction.HOLD and 
            self.confidence >= min_confidence
        )


@dataclass
class Trade:
    """Unified trade representation (the core domain object)"""
    id: str                              # Unique trade ID
    symbol: Symbol
    action: TradeAction
    quantity: float
    price: Price
    notional: float                      # Dollar amount
    strategy: StrategyTier
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None       # Broker order ID
    signal: Optional[Signal] = None      # Original signal
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON storage)"""
        return {
            "id": self.id,
            "symbol": self.symbol.ticker,
            "asset_class": self.symbol.asset_class.value,
            "action": self.action.value,
            "quantity": self.quantity,
            "price": self.price.value,
            "notional": self.notional,
            "strategy": self.strategy.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "order_id": self.order_id,
            "metadata": self.metadata
        }
    
    def to_alpaca_order(self) -> Dict[str, Any]:
        """Project to Alpaca order format"""
        return {
            "symbol": self.symbol.to_alpaca(),
            "side": self.action.value.lower(),
            "type": "market",
            "notional": str(self.notional),
            "time_in_force": "day"
        }
    
    def to_performance_record(self) -> Dict[str, Any]:
        """Project to performance log format"""
        return {
            "date": self.timestamp.strftime("%Y-%m-%d"),
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol.ticker,
            "action": self.action.value,
            "notional": self.notional,
            "price": self.price.value,
            "strategy": self.strategy.value,
            "status": self.status.value
        }


@dataclass
class Position:
    """Unified position representation"""
    symbol: Symbol
    quantity: float
    avg_entry_price: Price
    current_price: Price
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol.ticker,
            "asset_class": self.symbol.asset_class.value,
            "quantity": self.quantity,
            "avg_entry_price": self.avg_entry_price.value,
            "current_price": self.current_price.value,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct
        }


@dataclass
class Portfolio:
    """Unified portfolio state"""
    equity: float
    cash: float
    buying_power: float
    positions: List[Position] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions)
    
    @property
    def position_count(self) -> int:
        return len(self.positions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "equity": self.equity,
            "cash": self.cash,
            "buying_power": self.buying_power,
            "total_pnl": self.total_pnl,
            "position_count": self.position_count,
            "positions": [p.to_dict() for p in self.positions],
            "timestamp": self.timestamp.isoformat()
        }


# =============================================================================
# SCHEMA GENERATOR (Model Once, Represent Everywhere)
# =============================================================================

class SchemaGenerator:
    """
    Generates consistent schemas from domain models.
    Netflix's "Upper" pattern - single source generates all representations.
    """
    
    @staticmethod
    def to_json_schema(model_class) -> Dict[str, Any]:
        """Generate JSON Schema from dataclass"""
        # This would use dataclass introspection to generate full schema
        return {
            "type": "object",
            "title": model_class.__name__,
            "description": model_class.__doc__,
        }
    
    @staticmethod
    def to_avro_schema(model_class) -> Dict[str, Any]:
        """Generate Avro schema for Kafka/streaming"""
        return {
            "type": "record",
            "name": model_class.__name__,
            "namespace": "com.trading.domain",
        }
    
    @staticmethod
    def to_sql_ddl(model_class) -> str:
        """Generate SQL DDL for database tables"""
        return f"CREATE TABLE {model_class.__name__.lower()} (...);"


# =============================================================================
# DOMAIN FACTORY (Consistent Object Creation)
# =============================================================================

class DomainFactory:
    """
    Factory for creating domain objects with validation.
    Ensures all objects conform to unified model.
    """
    
    @staticmethod
    def create_crypto_symbol(ticker: str) -> Symbol:
        """Create a crypto symbol"""
        return Symbol(
            ticker=ticker,
            asset_class=AssetClass.CRYPTO,
            exchange="CRYPTO"
        )
    
    @staticmethod
    def create_equity_symbol(ticker: str, exchange: str = "NASDAQ") -> Symbol:
        """Create an equity symbol"""
        return Symbol(
            ticker=ticker,
            asset_class=AssetClass.EQUITY,
            exchange=exchange
        )
    
    @staticmethod
    def create_trade_from_alpaca(alpaca_order: Dict, strategy: StrategyTier) -> Trade:
        """Create Trade from Alpaca order response"""
        symbol_str = alpaca_order.get("symbol", "")
        is_crypto = "USD" in symbol_str and len(symbol_str) > 4
        
        symbol = Symbol(
            ticker=symbol_str,
            asset_class=AssetClass.CRYPTO if is_crypto else AssetClass.EQUITY
        )
        
        return Trade(
            id=alpaca_order.get("id", ""),
            symbol=symbol,
            action=TradeAction(alpaca_order.get("side", "buy").upper()),
            quantity=float(alpaca_order.get("qty", 0)),
            price=Price(value=float(alpaca_order.get("filled_avg_price", 0))),
            notional=float(alpaca_order.get("notional", 0)),
            strategy=strategy,
            status=OrderStatus.FILLED if alpaca_order.get("status") == "filled" else OrderStatus.PENDING,
            order_id=alpaca_order.get("id")
        )
    
    @staticmethod
    def create_signal(
        symbol: Symbol,
        action: TradeAction,
        confidence: float,
        source: str
    ) -> Signal:
        """Create a trading signal"""
        if confidence >= 0.8:
            strength = SignalStrength.STRONG_BUY if action == TradeAction.BUY else SignalStrength.STRONG_SELL
        elif confidence >= 0.6:
            strength = SignalStrength.BUY if action == TradeAction.BUY else SignalStrength.SELL
        else:
            strength = SignalStrength.HOLD
        
        return Signal(
            symbol=symbol,
            action=action,
            strength=strength,
            confidence=confidence,
            source=source
        )


# Singleton factory instance
factory = DomainFactory()


if __name__ == "__main__":
    # Test the unified domain model
    print("=== Unified Domain Model Test ===\n")
    
    # Create a crypto symbol
    btc = factory.create_crypto_symbol("BTCUSD")
    print(f"Symbol: {btc.ticker}")
    print(f"  Alpaca format: {btc.to_alpaca()}")
    print(f"  yfinance format: {btc.to_yfinance()}")
    
    # Create a signal
    signal = factory.create_signal(
        symbol=btc,
        action=TradeAction.BUY,
        confidence=0.85,
        source="text_analyzer"
    )
    print(f"\nSignal: {signal.action.value}")
    print(f"  Strength: {signal.strength.value}")
    print(f"  Actionable: {signal.is_actionable()}")
    
    # Create a trade
    trade = Trade(
        id="trade_001",
        symbol=btc,
        action=TradeAction.BUY,
        quantity=0.00011,
        price=Price(value=90125.56),
        notional=10.0,
        strategy=StrategyTier.TIER5_CRYPTO,
        signal=signal
    )
    print(f"\nTrade: {json.dumps(trade.to_dict(), indent=2)}")
    print(f"\nAlpaca Order: {json.dumps(trade.to_alpaca_order(), indent=2)}")
