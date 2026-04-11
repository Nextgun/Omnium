"""
Evaluation — Compare algorithm performance side-by-side.

Runs backtests with different configurations and returns comparison metrics.
"""

from __future__ import annotations

from typing import Any

from src.omnium.backtesting.backtest import run_backtest


def compare_algorithms(
    asset_id: int,
    limit: int = 90,
    starting_cash: float = 100_000.0,
    configs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run multiple backtests on the same asset and compare results.

    Args:
        asset_id: Asset to backtest on
        limit: Price bars to replay
        starting_cash: Starting cash for each run
        configs: Optional dict of {name: config_overrides}.
                 Defaults to comparing default vs aggressive settings.
    """
    if configs is None:
        configs = {
            "conservative": {"buy_threshold": 7.0, "sell_threshold": 12.0, "stop_loss": 5.0},
            "default": {},
            "aggressive": {"buy_threshold": 3.0, "sell_threshold": 8.0, "stop_loss": 10.0},
        }

    results = {}
    for name, cfg in configs.items():
        bt = run_backtest(
            asset_id=asset_id,
            starting_cash=starting_cash,
            limit=limit,
            config=cfg,
        )
        results[name] = {
            "algorithm": bt.algorithm,
            "return_pct": bt.return_pct,
            "total_value": bt.total_value,
            "total_trades": bt.total_trades,
            "buys": bt.buys,
            "sells": bt.sells,
            "ending_cash": bt.ending_cash,
            "shares_held": bt.shares_held,
        }

    # Determine winner
    best = max(results.items(), key=lambda x: x[1]["return_pct"])

    return {
        "asset_id": asset_id,
        "bars_tested": limit,
        "starting_cash": starting_cash,
        "results": results,
        "best_strategy": best[0],
        "best_return_pct": best[1]["return_pct"],
    }
