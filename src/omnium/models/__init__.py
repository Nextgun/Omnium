"""
omnium.models — Core Data Models
==================================

These dataclasses define the shared types that flow between all modules.
They are the "contracts" that every component agrees on.

Corresponds to:
    - ASSETS, PRICES, ACCOUNTS, TRADES tables in the DB schema
    - TradingSignal, TradeResult used by algorithms and executor
    - Portfolio, Position used by the trading engine and dashboard

Usage:
    from omnium.models import Price, TradingSignal, TradeResult, Portfolio
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════════════

class Side(str, Enum):
    """Trade side — buy or sell."""
    BUY = "buy"
    SELL = "sell"


class Action(str, Enum):
    """Algorithm decision action."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class AccountType(str, Enum):
    """Account mode — paper or live."""
    PAPER = "paper"
    LIVE = "live"


# ═══════════════════════════════════════════════════════════════════
#  Database-Mapped Models
#  (Mirror the DB schema — will become SQLAlchemy models in #6/#7)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Asset:
    """
    A tradable asset (stock).

    Maps to: ASSETS table
    Fields: id, symbol (e.g. 'AAPL'), name (e.g. 'Apple Inc.')
    """
    id: int
    symbol: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Price:
    """
    A single OHLCV price bar for an asset at a point in time.

    Maps to: PRICES table
    Used by: HistoricalDataLoader, LiveMarketFetcher, algorithms, charts

    Validation rules (enforced by DataValidator):
        - high >= max(open, close)
        - low  <= min(open, close)
        - volume >= 0
        - open, high, low, close > 0
    """
    id: int | None
    asset_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def is_bullish(self) -> bool:
        """True if close > open (green candle)."""
        return self.close > self.open

    @property
    def body_size(self) -> float:
        """Absolute difference between open and close."""
        return abs(self.close - self.open)


@dataclass
class Account:
    """
    A trading account (paper or live).

    Maps to: ACCOUNTS table
    """
    id: int
    type: AccountType
    cash_balance: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trade:
    """
    A record of an executed trade.

    Maps to: TRADES table
    Created by: OrderExecutor → PaperTradingAccount
    Logged by: TradeLogger
    """
    id: int | None
    account_id: int
    asset_id: int
    side: Side
    quantity: int
    price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_cost(self) -> float:
        """Total dollar amount of this trade."""
        return self.quantity * self.price


# ═══════════════════════════════════════════════════════════════════
#  Algorithm / Trading Models
#  (Not DB-mapped — used for inter-module communication)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class TradingSignal:
    """
    Output from a trading algorithm — a recommendation to act.

    Produced by: BaseTradingAlgorithm.analyze()
    Consumed by: Orchestrator → OrderExecutor

    Fields:
        symbol:     Ticker to trade (e.g. "AAPL")
        action:     BUY, SELL, or HOLD
        quantity:   Suggested number of shares
        confidence: 0.0 to 1.0 — how confident the algorithm is
        timestamp:  When the signal was generated
        metadata:   Algorithm-specific context (indicator values, rationale)
    """
    symbol: str
    action: Action
    quantity: int
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0–1.0, got {self.confidence}")
        if self.quantity < 0:
            raise ValueError(f"Quantity must be >= 0, got {self.quantity}")


@dataclass
class TradeResult:
    """
    Result of an attempted trade execution.

    Returned by: PaperTradingAccount.execute_trade()
    Consumed by: Orchestrator, TradeLogger

    Fields:
        success:       Whether the trade was filled
        fill_price:    Actual execution price (may differ from signal due to slippage)
        fill_quantity: Actual number of shares filled
        fees:          Commission/slippage cost
        trade:         The Trade record (if successful)
        error_message: Why it failed (if unsuccessful)
    """
    success: bool
    fill_price: float = 0.0
    fill_quantity: int = 0
    fees: float = 0.0
    trade: Trade | None = None
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Position:
    """
    An active holding in a specific asset.

    Managed by: PaperTradingAccount, AccountManager
    Displayed by: PortfolioComponent

    The avg_cost tracks what was paid on average per share.
    current_price is updated on each price tick.
    """
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0

    def unrealized_pnl(self) -> float:
        """Paper profit/loss if sold right now."""
        return (self.current_price - self.avg_cost) * self.quantity

    def market_value(self) -> float:
        """Current dollar value of this position."""
        return self.current_price * self.quantity


@dataclass
class Portfolio:
    """
    Complete snapshot of an account: cash + all positions.

    Managed by: AccountManager
    Displayed by: PortfolioComponent, dashboard

    portfolio_value = cash + sum(position.market_value)
    """
    account_id: int
    positions: dict[str, Position] = field(default_factory=dict)
    cash: float = 0.0

    def total_value(self) -> float:
        """Total portfolio value: cash + all position market values."""
        position_value = sum(p.market_value() for p in self.positions.values())
        return self.cash + position_value

    def unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return sum(p.unrealized_pnl() for p in self.positions.values())


@dataclass
class PortfolioSnapshot:
    """
    A point-in-time record of portfolio state (for historical tracking).

    Stored by: TradeLogger (periodic snapshots)
    Displayed by: portfolio value chart over time
    """
    account_id: int
    timestamp: datetime
    cash: float
    total_value: float
    unrealized_pnl: float
    realized_pnl: float
