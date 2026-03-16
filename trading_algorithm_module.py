# configure_trading_algo.py

from dataclasses import dataclass


@dataclass
class TradingConfig:
    """
    Holds configuration for the trading algorithm.
    All percentage values are expressed as percentages (e.g., 5.0 = 5%).
    """
    buy_threshold: float = 5.0      # Buy if price drops 5% from reference
    sell_threshold: float = 10.0    # Sell if price rises 10% from purchase
    stop_loss: float = 8.0          # Sell if loss reaches 8%
    max_position: int = 100         # Maximum shares to hold of one asset


class TradingAlgorithm:
    def __init__(self, config: TradingConfig | None = None):
        self.config = config if config else TradingConfig()

    def update(
        self,
        buy_threshold: float | None = None,
        sell_threshold: float | None = None,
        stop_loss: float | None = None,
        max_position: int | None = None,
    ) -> bool:
        """
        Updates algorithm configuration values.
        Only provided arguments are updated.

        Returns:
            bool: True if at least one parameter was updated.
        """
        updated = False

        if buy_threshold is not None:
            self.config.buy_threshold = buy_threshold
            updated = True

        if sell_threshold is not None:
            self.config.sell_threshold = sell_threshold
            updated = True

        if stop_loss is not None:
            self.config.stop_loss = stop_loss
            updated = True

        if max_position is not None:
            self.config.max_position = max_position
            updated = True

        return updated

    def should_buy(self, reference_price: float, current_price: float) -> bool:
        """
        Determines whether the algorithm should buy.

        Buy if the current price has dropped by at least buy_threshold %
        from the reference price.

        Args:
            reference_price: Baseline price to compare against
            current_price: Current market price

        Returns:
            bool
        """
        if reference_price <= 0:
            return False

        drop_percent = ((reference_price - current_price) / reference_price) * 100
        return drop_percent >= self.config.buy_threshold

    def should_sell(self, current_price: float, purchase_price: float) -> bool:
        """
        Determines whether the algorithm should sell.

        Sell if:
        1. Profit target reached (sell_threshold % gain), OR
        2. Stop-loss reached (stop_loss % loss)

        Args:
            current_price: Current market price
            purchase_price: Price the asset was bought at

        Returns:
            bool
        """
        if purchase_price <= 0:
            return False

        change_percent = ((current_price - purchase_price) / purchase_price) * 100

        take_profit = change_percent >= self.config.sell_threshold
        stop_loss_hit = change_percent <= -self.config.stop_loss

        return take_profit or stop_loss_hit


# Example usage (optional test)
if __name__ == "__main__":
    algo = TradingAlgorithm()

    ref_price = 100
    current_price = 94

    print("Should Buy:", algo.should_buy(ref_price, current_price))

    purchase_price = 100
    current_price = 111

    print("Should Sell:", algo.should_sell(current_price, purchase_price))