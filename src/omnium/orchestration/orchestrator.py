"""
Orchestrator — connects the trading algorithm to the database.

Reads prices and positions from db.py, runs the algorithm, executes trades.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.omnium.algorithms.switcher import AlgorithmSwitcher
from src.omnium.data import db

log = logging.getLogger(__name__)

TRADE_QUANTITY = 10  # Shares per trade (simple fixed-size for now)


@dataclass
class TickResult:
    """Result of one algorithm tick on a single asset."""
    asset_id: int
    symbol: str
    action: str          # BUY, SELL, or HOLD
    price: float
    shares_held: int
    trade_executed: bool
    message: str


def tick(account_id: int, asset_id: int, switcher: AlgorithmSwitcher) -> TickResult:
    """
    Run one trading cycle for an asset:
    1. Get latest price
    2. Get current position and average buy price
    3. Get reference price (average of last 20 closes)
    4. Ask algorithm for decision
    5. Execute trade if BUY/SELL
    """
    # Get latest price
    price_data = db.get_latest_price(asset_id)
    if not price_data:
        return TickResult(asset_id, "?", "HOLD", 0, 0, False, "No price data")

    current_price = float(price_data["close"])
    asset = db.get_asset_by_id(asset_id)
    symbol = asset["symbol"] if asset else "?"

    # Current position
    shares_held = db.get_position(account_id, asset_id)
    purchase_price = _get_avg_buy_price(account_id, asset_id)

    # Reference price = average of last 20 closes
    history = db.get_price_history(asset_id, limit=20)
    if history:
        reference_price = sum(float(p["close"]) for p in history) / len(history)
    else:
        reference_price = current_price

    # Algorithm decision
    action = switcher.decide(current_price, reference_price, purchase_price, shares_held)

    # Execute
    trade_executed = False
    message = f"{action} signal for {symbol} at ${current_price:.2f}"

    if action == "BUY":
        account = db.get_account(account_id)
        if not account:
            message = "Account not found"
        else:
            cost = current_price * TRADE_QUANTITY
            if float(account["cash_balance"]) >= cost:
                db.log_trade(account_id, asset_id, "BUY", TRADE_QUANTITY, current_price)
                db.update_cash_balance(account_id, float(account["cash_balance"]) - cost)
                trade_executed = True
                shares_held += TRADE_QUANTITY
                message = f"Bought {TRADE_QUANTITY} shares of {symbol} at ${current_price:.2f}"
            else:
                message = f"Insufficient funds for {symbol} (need ${cost:.2f})"

    elif action == "SELL":
        sell_qty = min(TRADE_QUANTITY, shares_held)
        if sell_qty > 0:
            db.log_trade(account_id, asset_id, "SELL", sell_qty, current_price)
            account = db.get_account(account_id)
            if account:
                proceeds = current_price * sell_qty
                db.update_cash_balance(account_id, float(account["cash_balance"]) + proceeds)
            trade_executed = True
            shares_held -= sell_qty
            message = f"Sold {sell_qty} shares of {symbol} at ${current_price:.2f}"

    log.info(message)
    return TickResult(asset_id, symbol, action, current_price, shares_held, trade_executed, message)


def get_status(account_id: int, asset_id: int, switcher: AlgorithmSwitcher) -> dict[str, Any]:
    """Get current position + what the algorithm would signal (without executing)."""
    price_data = db.get_latest_price(asset_id)
    current_price = float(price_data["close"]) if price_data else 0
    asset = db.get_asset_by_id(asset_id)
    symbol = asset["symbol"] if asset else "?"

    shares_held = db.get_position(account_id, asset_id)
    purchase_price = _get_avg_buy_price(account_id, asset_id)

    history = db.get_price_history(asset_id, limit=20)
    reference_price = sum(float(p["close"]) for p in history) / len(history) if history else current_price

    signal = switcher.decide(current_price, reference_price, purchase_price, shares_held)

    return {
        "account_id": account_id,
        "asset_id": asset_id,
        "symbol": symbol,
        "current_price": current_price,
        "reference_price": round(reference_price, 2),
        "shares_held": shares_held,
        "avg_buy_price": purchase_price,
        "signal": signal,
        "algorithm": switcher.active_algorithm,
    }


def _get_avg_buy_price(account_id: int, asset_id: int) -> float | None:
    """Calculate average buy price from trade history."""
    trades = db.get_trades_for_asset(account_id, asset_id)
    buys = [t for t in trades if t["side"] == "BUY"]
    if not buys:
        return None
    total_cost = sum(float(t["price"]) * int(t["quantity"]) for t in buys)
    total_shares = sum(int(t["quantity"]) for t in buys)
    return round(total_cost / total_shares, 2) if total_shares > 0 else None
