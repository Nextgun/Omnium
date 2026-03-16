"""
==========================
seed.py - database seeder
author: Ayesha Khan
date created: 2/15/2026
date last modified: 3/6/2026
==========================

This function seeds the database with real stock data source from Yfinance (Yahoo! finance)
Also seeds with dummy accounts and plausible trades for testing.

run this once to set up your database for development:
    pip install yfinance
    python seed.py

safe to re-run; it will clear any existing data in it first
"""

import random
from datetime import datetime, timedelta
import yfinance as yf
import db

# configure which stocks you want in the database
SYMBOLS = [
    ("AAPL",  "Apple Inc."),
    ("MSFT",  "Microsoft Corporation"),
    ("GOOGL", "Alphabet Inc."),
    ("AMZN",  "Amazon.com Inc."),
    ("TSLA",  "Tesla Inc."),
]

# how many calendar days of price history to fetch for each stock
HISTORY_DAYS = 90

# initializing some dummys

ACCOUNTS = [
    {"type": "paper", "cash_balance": 10000.00},
    {"type": "paper", "cash_balance": 25000.00},
]

# how many random trades per account
TRADES_PER_ACCOUNT = 20


# FUNCTIONS FOR SEEDING ===================================================

def seed_assets_and_prices():
    """
    fetches real OHLCV price history from yfinance and inserts it
    into ASSETS and PRICES.

    OHLCV = open, high, low, close, volume
    """
    
    print("\n-------- Seeding assets and prices --------------------------------")

    end_date   = datetime.today()
    start_date = end_date - timedelta(days=HISTORY_DAYS)

    for symbol, name in SYMBOLS:
        print(f"  Fetching {symbol} ({name})...")

        asset_id = db.insert_asset(symbol=symbol, name=name)

        ticker  = yf.Ticker(symbol)
        history = ticker.history(start=start_date, end=end_date)

        price_rows_inserted = 0
        for timestamp, row in history.iterrows():
            db.insert_price(
                asset_id  = asset_id,
                timestamp = timestamp.to_pydatetime(),
                open      = round(float(row["Open"]),  2),
                high      = round(float(row["High"]),  2),
                low       = round(float(row["Low"]),   2),
                close     = round(float(row["Close"]), 2),
                volume    = int(row["Volume"]),
            )
            price_rows_inserted += 1

        print(f"     {price_rows_inserted} price rows inserted for {symbol}")


def seed_accounts():
    """inserts dummy trading accounts. returns the list of inserted account ids."""
    print("\n-------- Seeding accounts ----------------------------------------")

    account_ids = []
    for acct in ACCOUNTS:
        account_id = db.insert_account(
            account_type = acct["type"],
            cash_balance = acct["cash_balance"],
        )
        account_ids.append(account_id)
        print(f"Account {account_id} - {acct['type']}, ${acct['cash_balance']:,.2f}")

    return account_ids


def seed_trades(account_ids: list[int]):
    """
    Generates plausible random trades for each account using real prices
    from the PRICES table so trade prices look realistic.

    Rules applied:
      - Trade prices are always real historical close prices from PRICES.
      - BUY trades happen first; SELL trades only follow a BUY.
      - The account is never oversold (can't sell more than it bought).
    """
    print("\n------------ Seeding trades ------------------------")

    all_assets = [db.get_asset_by_symbol(s) for s, _ in SYMBOLS]

    for account_id in account_ids:
        print(f"\n  Account {account_id}:")

        # Track shares held per asset to avoid invalid sells
        positions = {asset["id"]: 0 for asset in all_assets}

        for _ in range(TRADES_PER_ACCOUNT):
            asset    = random.choice(all_assets)
            asset_id = asset["id"]

            price_history = db.get_price_history(asset_id, limit=HISTORY_DAYS)
            if not price_history:
                continue

            # Use a real historical close price and its timestamp
            price_record = random.choice(price_history)
            price        = price_record["close"]
            trade_time   = price_record["timestamp"]

            # Only allow SELL if shares are held
            if positions[asset_id] == 0:
                side = "BUY"
            else:
                side = random.choice(["BUY", "SELL"])

            if side == "BUY":
                quantity = random.randint(1, 20)
            else:
                quantity = random.randint(1, positions[asset_id])

            db.insert_trade(
                account_id = account_id,
                asset_id   = asset_id,
                side       = side,
                quantity   = quantity,
                price      = price,
                timestamp  = trade_time,
            )

            if side == "BUY":
                positions[asset_id] += quantity
            else:
                positions[asset_id] -= quantity

            print(f"    {side:4s} {quantity:3d} x {asset['symbol']:5s} @ ${price:.2f}")


def reset_all():
    """if re-seeding, then clear the database"""
    print("\n---- Resetting database ----------------------------------------")
    db.truncate_all()
    print("All tables cleared.")


# test the entry point here

if __name__ == "__main__":
    print("Starting database seed...")
    reset_all()
    seed_assets_and_prices()
    account_ids = seed_accounts()
    seed_trades(account_ids)
    print("\nSeed complete.\n")