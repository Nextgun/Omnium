"""
omnium.utils — Shared Utilities
=================================

EventBus:    Decoupled pub/sub for inter-module communication.
Config:      Load settings from YAML/env vars.
Logging:     Consistent log formatting across all modules.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  Logging Setup
# ═══════════════════════════════════════════════════════════════════

def setup_logging(level: str = "INFO") -> None:
    """
    Configure consistent logging for the entire application.

    Call once at startup (in main.py).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)-7s] %(name)-30s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


# ═══════════════════════════════════════════════════════════════════
#  Event Bus — Decoupled Communication (#15 sub-task 15.4)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """Base event with a name, payload, and timestamp."""
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """
    Simple publish/subscribe event bus for decoupled module communication.

    Modules emit events without knowing who listens. Other modules subscribe
    to event names they care about. This prevents circular imports and tight
    coupling between (for example) LiveMarketFetcher and the UI.

    Events:
        "price_updated"     — new price tick arrived
        "signal_generated"  — algorithm produced a TradingSignal
        "trade_executed"    — a trade was filled
        "portfolio_updated" — positions or cash changed

    Usage:
        bus = EventBus()
        bus.subscribe("price_updated", my_callback)
        bus.emit("price_updated", {"symbol": "AAPL", "price": 185.42})

    Thread-safety:
        All operations are protected by a threading lock so the bus
        can be shared across the Orchestrator and async data fetchers.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()
        log.info("EventBus initialized")

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Register a callback for a specific event name."""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)
            log.debug(
                "Subscribed %s to '%s' (%d listeners)",
                callback.__qualname__, event_name, len(self._subscribers[event_name])
            )

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Remove a callback from a specific event."""
        with self._lock:
            if event_name in self._subscribers:
                self._subscribers[event_name] = [
                    cb for cb in self._subscribers[event_name] if cb is not callback
                ]

    def emit(self, event_name: str, data: dict[str, Any] | None = None) -> None:
        """
        Emit an event to all subscribers.

        Callbacks are invoked synchronously in registration order.
        If a callback raises, the error is logged but other callbacks
        still execute (fail-safe).
        """
        event = Event(name=event_name, data=data or {})

        with self._lock:
            callbacks = list(self._subscribers.get(event_name, []))

        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                log.exception(
                    "Error in subscriber %s for event '%s'",
                    callback.__qualname__, event_name,
                )

    def clear(self) -> None:
        """Remove all subscriptions (useful for testing)."""
        with self._lock:
            self._subscribers.clear()


# ═══════════════════════════════════════════════════════════════════
#  Config Loader
# ═══════════════════════════════════════════════════════════════════

class Config:
    """
    Central configuration — reads from environment variables with defaults.

    Every configurable value in Omnium lives here. Modules receive a Config
    instance rather than reading env vars directly, making testing easy
    (just pass a Config with overridden values).

    In production, set env vars. In development, defaults are sensible.
    Future: load from a YAML file (config/omnium.yaml).
    """

    def __init__(self) -> None:
        # ── Database ──
        self.db_host: str = os.getenv("OMNIUM_DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("OMNIUM_DB_PORT", "5432"))
        self.db_name: str = os.getenv("OMNIUM_DB_NAME", "omnium")
        self.db_user: str = os.getenv("OMNIUM_DB_USER", "omnium")
        self.db_password: str = os.getenv("OMNIUM_DB_PASSWORD", "omnium")

        # ── Market Data ──
        self.market_data_api_key: str = os.getenv("OMNIUM_API_KEY", "")
        self.market_data_provider: str = os.getenv("OMNIUM_DATA_PROVIDER", "alpaca")
        self.tracked_symbols: list[str] = os.getenv(
            "OMNIUM_SYMBOLS", "AAPL,MSFT,TSLA"
        ).split(",")

        # ── Trading ──
        self.account_type: str = os.getenv("OMNIUM_ACCOUNT_TYPE", "paper")
        self.starting_cash: float = float(os.getenv("OMNIUM_STARTING_CASH", "100000"))
        self.slippage_pct: float = float(os.getenv("OMNIUM_SLIPPAGE_PCT", "0.001"))
        self.commission_per_trade: float = float(os.getenv("OMNIUM_COMMISSION", "0.0"))
        self.max_position_pct: float = float(os.getenv("OMNIUM_MAX_POSITION_PCT", "0.20"))
        self.min_confidence_threshold: float = float(os.getenv("OMNIUM_MIN_CONFIDENCE", "0.6"))
        self.trade_cooldown_seconds: int = int(os.getenv("OMNIUM_TRADE_COOLDOWN", "60"))

        # ── Algorithm ──
        self.active_algorithm: str = os.getenv("OMNIUM_ACTIVE_ALGO", "rule_based")
        self.price_lookback: int = int(os.getenv("OMNIUM_LOOKBACK", "50"))

        # ── Scheduler ──
        self.market_open: str = os.getenv("OMNIUM_MARKET_OPEN", "09:30")
        self.market_close: str = os.getenv("OMNIUM_MARKET_CLOSE", "16:00")
        self.market_timezone: str = os.getenv("OMNIUM_TIMEZONE", "US/Eastern")

        # ── Cache ──
        self.cache_ttl_seconds: int = int(os.getenv("OMNIUM_CACHE_TTL", "30"))
        self.cache_max_size: int = int(os.getenv("OMNIUM_CACHE_MAX_SIZE", "1000"))

    @property
    def db_connection_string(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def __repr__(self) -> str:
        return (
            f"Config(provider={self.market_data_provider}, "
            f"symbols={self.tracked_symbols}, "
            f"account={self.account_type}, "
            f"algo={self.active_algorithm})"
        )
