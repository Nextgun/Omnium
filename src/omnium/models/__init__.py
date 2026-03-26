"""
omnium.models — Core Data Models
==================================

Dataclasses that mirror the database schema and define shared types
used across all modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ── Enums ──

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


# ── Database-Mapped Models ──

@dataclass
class Asset:
    """Maps to: ASSETS table."""
    id: int
    symbol: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Price:
    """Maps to: PRICES table (OHLCV bar)."""
    id: int | None
    asset_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Account:
    """Maps to: ACCOUNTS table."""
    id: int
    type: AccountType
    cash_balance: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trade:
    """Maps to: TRADES table."""
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
