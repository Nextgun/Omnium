"""
omnium.utils — Shared Utilities
=================================

EventBus:    Decoupled pub/sub for inter-module communication.
Config:      Load settings from environment variables.
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


# ── Logging Setup ──

def setup_logging(level: str = "INFO") -> None:
    """Configure consistent logging for the entire application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)-7s] %(name)-30s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ── Event Bus ──

@dataclass
class Event:
    """Base event with a name, payload, and timestamp."""
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """
    Simple publish/subscribe event bus for decoupled module communication.

    Usage:
        bus = EventBus()
        bus.subscribe("price_updated", my_callback)
        bus.emit("price_updated", {"symbol": "AAPL", "price": 185.42})
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable) -> None:
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        with self._lock:
            if event_name in self._subscribers:
                self._subscribers[event_name] = [
                    cb for cb in self._subscribers[event_name] if cb is not callback
                ]

    def emit(self, event_name: str, data: dict[str, Any] | None = None) -> None:
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
        with self._lock:
            self._subscribers.clear()


# ── Config ──

class Config:
    """
    Central configuration — reads from environment variables with defaults.

    Values match the existing db.py DB_CONFIG and MariaDB setup.
    """

    def __init__(self) -> None:
        # ── Database (MariaDB) ──
        self.db_host: str = os.getenv("OMNIUM_DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("OMNIUM_DB_PORT", "3306"))
        self.db_name: str = os.getenv("OMNIUM_DB_NAME", "omnium_database")
        self.db_user: str = os.getenv("OMNIUM_DB_USER", "root")
        self.db_password: str = os.getenv("OMNIUM_DB_PASSWORD", "")

        # ── Trading ──
        self.account_type: str = os.getenv("OMNIUM_ACCOUNT_TYPE", "paper")
        self.starting_cash: float = float(os.getenv("OMNIUM_STARTING_CASH", "100000"))
        self.active_algorithm: str = os.getenv("OMNIUM_ACTIVE_ALGO", "rule_based")
        self.tracked_symbols: list[str] = os.getenv(
            "OMNIUM_SYMBOLS", "AAPL,MSFT,TSLA"
        ).split(",")

        # ── Email (Gmail SMTP) ──
        self.email_address: str = os.getenv("OMNIUM_EMAIL_ADDRESS", "")
        self.email_password: str = os.getenv("OMNIUM_EMAIL_PASSWORD", "")

    def __repr__(self) -> str:
        return (
            f"Config(db={self.db_host}:{self.db_port}/{self.db_name}, "
            f"algo={self.active_algorithm})"
        )
