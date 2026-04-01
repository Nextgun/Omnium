"""
CS Algorithm — Rule-based mean-reversion trading strategy.

Original code by teammate on branch 9-implement-rule-based-trading-algorithm-cs-module,
integrated into src/omnium/algorithms/ package.
"""

from dataclasses import dataclass


@dataclass
class TradingConfig:
    """
    Configuration for the rule-based trading algorithm.
    All percentage values are expressed as percentages (e.g., 5.0 = 5%).
    """
    buy_threshold: float = 5.0      # Buy if price drops 5% from reference
    sell_threshold: float = 10.0    # Sell if price rises 10% from purchase
    stop_loss: float = 8.0          # Sell if loss reaches 8%
    max_position: int = 100         # Maximum shares to hold of one asset


class CSAlgorithm:
    """Mean-reversion buy/sell algorithm using configurable thresholds."""

    def __init__(self, config: TradingConfig | None = None) -> None:
        self.config = config or TradingConfig()

    def update_config(
        self,
        buy_threshold: float | None = None,
        sell_threshold: float | None = None,
        stop_loss: float | None = None,
        max_position: int | None = None,
    ) -> bool:
        """Update algorithm parameters. Returns True if anything changed."""
        updated = False
        for attr, val in [
            ("buy_threshold", buy_threshold),
            ("sell_threshold", sell_threshold),
            ("stop_loss", stop_loss),
            ("max_position", max_position),
        ]:
            if val is not None:
                setattr(self.config, attr, val)
                updated = True
        return updated

    def should_buy(self, reference_price: float, current_price: float) -> bool:
        """Buy if current price dropped >= buy_threshold% from reference."""
        if reference_price <= 0:
            return False
        drop_pct = ((reference_price - current_price) / reference_price) * 100
        return drop_pct >= self.config.buy_threshold

    def should_sell(self, current_price: float, purchase_price: float) -> bool:
        """Sell if profit >= sell_threshold% OR loss >= stop_loss%."""
        if purchase_price <= 0:
            return False
        change_pct = ((current_price - purchase_price) / purchase_price) * 100
        return change_pct >= self.config.sell_threshold or change_pct <= -self.config.stop_loss

    def decide(self, current_price: float, reference_price: float,
               purchase_price: float | None, shares_held: int) -> str:
        """
        Make a trading decision for one asset.

        Returns: "BUY", "SELL", or "HOLD"
        """
        if shares_held > 0 and purchase_price is not None:
            if self.should_sell(current_price, purchase_price):
                return "SELL"

        if shares_held < self.config.max_position:
            if self.should_buy(reference_price, current_price):
                return "BUY"

        return "HOLD"
