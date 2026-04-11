"""
Backtesting engine — replays historical price data through an algorithm
to evaluate performance without risking real trades.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.omnium.algorithms.cs_algorithm import CSAlgorithm, TradingConfig
from src.omnium.data import db

log = logging.getLogger(__name__)

TRADE_QUANTITY = 10


@dataclass
class BacktestResult:
    """Summary of a backtest run."""
    asset_id: int
    symbol: str
    algorithm: str
    starting_cash: float
    ending_cash: float
    shares_held: int
    total_value: float       # cash + shares * final price
    return_pct: float
    total_trades: int
    buys: int
    sells: int
    trade_log: list[dict] = field(default_factory=list)


def run_backtest(
    asset_id: int,
    algorithm: str = "rule_based",
    starting_cash: float = 100_000.0,
    limit: int = 90,
    config: dict[str, Any] | None = None,
) -> BacktestResult:
    """
    Replay historical prices through an algorithm.

    Args:
        asset_id: Which asset to backtest on
        algorithm: Algorithm name (currently only "rule_based")
        starting_cash: Starting cash balance
        limit: How many historical price bars to replay
        config: Optional algorithm config overrides
    """
    asset = db.get_asset_by_id(asset_id)
    symbol = asset["symbol"] if asset else "?"

    # Get price history oldest-first
    history = db.get_price_history(asset_id, limit=limit)
    history.reverse()

    if len(history) < 2:
        return BacktestResult(
            asset_id=asset_id, symbol=symbol, algorithm=algorithm,
            starting_cash=starting_cash, ending_cash=starting_cash,
            shares_held=0, total_value=starting_cash, return_pct=0.0,
            total_trades=0, buys=0, sells=0,
        )

    # Set up algorithm
    algo_config = TradingConfig(**(config or {}))
    algo = CSAlgorithm(algo_config)

    cash = starting_cash
    shares = 0
    avg_buy = 0.0
    trade_log: list[dict] = []

    for i, bar in enumerate(history):
        price = float(bar["close"])

        # Reference = average of previous 20 bars
        lookback = history[max(0, i - 20):i]
        ref_price = sum(float(b["close"]) for b in lookback) / len(lookback) if lookback else price

        purchase_price = avg_buy if shares > 0 else None
        action = algo.decide(price, ref_price, purchase_price, shares)

        if action == "BUY":
            cost = price * TRADE_QUANTITY
            if cash >= cost:
                total_cost = avg_buy * shares + cost
                shares += TRADE_QUANTITY
                avg_buy = total_cost / shares
                cash -= cost
                trade_log.append({"bar": i, "action": "BUY", "price": price, "qty": TRADE_QUANTITY})

        elif action == "SELL":
            sell_qty = min(TRADE_QUANTITY, shares)
            if sell_qty > 0:
                cash += price * sell_qty
                shares -= sell_qty
                if shares == 0:
                    avg_buy = 0.0
                trade_log.append({"bar": i, "action": "SELL", "price": price, "qty": sell_qty})

    final_price = float(history[-1]["close"])
    total_value = cash + shares * final_price
    return_pct = ((total_value - starting_cash) / starting_cash) * 100

    buys = sum(1 for t in trade_log if t["action"] == "BUY")
    sells = sum(1 for t in trade_log if t["action"] == "SELL")

    return BacktestResult(
        asset_id=asset_id, symbol=symbol, algorithm=algorithm,
        starting_cash=starting_cash, ending_cash=round(cash, 2),
        shares_held=shares, total_value=round(total_value, 2),
        return_pct=round(return_pct, 2), total_trades=len(trade_log),
        buys=buys, sells=sells, trade_log=trade_log,
    )
