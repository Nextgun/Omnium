"""
==========================
orchestrator.py 
author: 
date created: 3/16/2026
date last modified: 3/16/2026
==========================

connects trading algo logic with database values

"""


from datetime import datetime
import database.db as db
from trading_logic.trading_algorithm import TradingAlgorithm

algo = TradingAlgorithm()


def _get_reference_price(asset_id: int) -> float | None:
    """Uses the oldest price in history as the reference baseline."""
    history = db.get_price_history(asset_id, limit=30)
    if not history:
        return None
    return history[-1]["close"]  # oldest entry

# THREE OPTIONS: CALLABLE FROM MENU

# run_tick = evaluates and executes a trade 
def run_tick(account_id: int, asset_id: int) -> str:
    """
    Evaluates current price and executes a BUY or SELL if conditions are met.
    Returns a status string for the menu to display.
    """
    price_row = db.get_latest_price(asset_id)
    if not price_row:
        return "No price data available."

    current_price = price_row["close"]
    position      = db.get_position(account_id, asset_id)
    account       = db.get_account(account_id)
    if not account:
        return "Account not found."

    # BUY LOGIC ------------------------
    # this adds a guard to prevent buying beyond max allowed shares 
    if position < algo.config.max_position:
        ref = _get_reference_price(asset_id)
        if ref and algo.should_buy(ref, current_price):

            # prevents buying more than is affordable
            affordable = int(account["cash_balance"] // current_price)

            shares = min(algo.config.max_position - position, affordable)
            if shares > 0:
                db.log_trade(account_id, asset_id, "BUY", shares, current_price)
                db.update_cash_balance(account_id, account["cash_balance"] - shares * current_price)
                return f"BUY {shares} shares @ ${current_price:.2f}"

    # SELL LOGIC -------------------------
    # this prevents selling shares that you don't own
    if position > 0:
        avg_cost = db.get_avg_buy_price(account_id, asset_id)
        if avg_cost and algo.should_sell(current_price, avg_cost):
            db.log_trade(account_id, asset_id, "SELL", position, current_price)
            db.update_cash_balance(account_id, account["cash_balance"] + position * current_price)
            return f"SELL {position} shares @ ${current_price:.2f}"

    return f"No action. Price: ${current_price:.2f}, Position: {position} shares."

# not implementing this in the terminal UI yet but it will be in Andrew's UI
def update_algorithm(
    buy_threshold:  float | None = None,
    sell_threshold: float | None = None,
    stop_loss:      float | None = None,
    max_position:   int   | None = None,
) -> str:
    """Updates algorithm config. Returns a status string for the menu to display."""
    changed = algo.update(buy_threshold, sell_threshold, stop_loss, max_position)
    if changed:
        cfg = algo.config
        return (f"Config updated — Buy: {cfg.buy_threshold}%, "
                f"Sell: {cfg.sell_threshold}%, "
                f"Stop-loss: {cfg.stop_loss}%, "
                f"Max position: {cfg.max_position}")
    return "No changes made."


def get_status(account_id: int, asset_id: int) -> str:
    """Returns a summary of account balance, position, and latest price."""
    account   = db.get_account(account_id)
    position  = db.get_position(account_id, asset_id)
    price_row = db.get_latest_price(asset_id)
    asset     = db.get_asset_by_id(asset_id)

    if not account or not price_row or not asset:
        return "Could not retrieve status — check account/asset IDs."

    market_value = position * price_row["close"]
    return (f"Account #{account_id} | Cash: ${account['cash_balance']:.2f} | "
            f"{asset['symbol']}: {position} shares @ ${price_row['close']:.2f} "
            f"(Market value: ${market_value:.2f})")