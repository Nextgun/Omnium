"""
==========================
db.py - abstraction layer for interacting with the database
author: Ayesha Khan
data created: 2/15/2026
date last modified: 3/6/2026
=====================================
All SQL lives here. 
Other modules calls these functions and gets back plain Python dicts.

Install the driver once with:  pip install mariadb
"""

import mariadb
import sys
from datetime import datetime

# mariaDB setup
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "omnom3",
    "database": "omnium_database",
}


def _get_connection():
    """
    internal helper used to open a MariaDB connection.
    Prefixed with _ so don't call this function directly.
    """
    try:
        return mariadb.connect(**DB_CONFIG)
    except mariadb.Error as e:
        print(f"[db] Connection error: {e}")
        sys.exit(1)


def _row_to_dict(cursor, row):
    """converts a row tuple into a dict using the cursor's column names."""
    return {desc[0]: value for desc, value in zip(cursor.description, row)}


# seeding helpers =================================================================

def truncate_all() -> None:
    """
    clears all tables in FK-safe order and resets auto-increment counters.
    called by seed.py before re-seeding.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ["trades", "prices", "accounts", "assets"]:
            cursor.execute(f"TRUNCATE TABLE {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    finally:
        conn.close()


def insert_asset(symbol: str, name: str) -> int:
    """inserts a row into ASSETS. returns the new row's auto-incremented id."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO assets (symbol, name) VALUES (?, ?)",
            (symbol, name)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_price(asset_id: int, timestamp: datetime, open: float,
                 high: float, low: float, close: float, volume: int) -> int:
    """inserts a row into PRICES. returns the new row's id."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO prices (asset_id, timestamp, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, timestamp, open, high, low, close, volume)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_account(account_type: str, cash_balance: float) -> int:
    """inserts a row into ACCOUNTS. returns the new account id."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO accounts (type, cash_balance) VALUES (?, ?)",
            (account_type, cash_balance)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_trade(account_id: int, asset_id: int, side: str,
                 quantity: int, price: float, timestamp: datetime) -> int:
    """inserts a row into TRADES. returns the new trade id."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO trades (account_id, asset_id, side, quantity, price, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (account_id, asset_id, side, quantity, price, timestamp)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# assets =================================================================

def search_assets(query: str) -> list[dict]:
    """
    returns all assets whose symbol or name partially matches `query`.
    each result: {"id", "symbol", "name"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        like_query = f"%{query}%"
        cursor.execute(
            """SELECT id, symbol, name FROM assets
               WHERE symbol LIKE ? OR name LIKE ?
               ORDER BY symbol
               LIMIT 20""",
            (like_query, like_query)
        )
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[db] search_assets error: {e}")
        return []
    finally:
        conn.close()


def get_asset_by_symbol(symbol: str) -> dict | None:
    """
    returns one asset matching the exact symbol, or None if not found.
    result: {"id", "symbol", "name"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, symbol, name FROM assets WHERE symbol = ?",
            (symbol,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_asset_by_symbol error: {e}")
        return None
    finally:
        conn.close()


def get_asset_by_id(asset_id: int) -> dict | None:
    """
    returns one asset by its primary key, or None if not found.
    result: {"id", "symbol", "name"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, symbol, name FROM assets WHERE id = ?",
            (asset_id,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_asset_by_id error: {e}")
        return None
    finally:
        conn.close()


# prices =================================================================

def get_latest_price(asset_id: int) -> dict | None:
    """
    returns the most recent price record for an asset, or None if unavailable.
    result: {"id", "asset_id", "timestamp", "open", "high", "low", "close", "volume"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT id, asset_id, timestamp, open, high, low, close, volume
               FROM prices
               WHERE asset_id = ?
               ORDER BY timestamp DESC
               LIMIT 1""",
            (asset_id,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_latest_price error: {e}")
        return None
    finally:
        conn.close()


def get_price_history(asset_id: int, limit: int = 30) -> list[dict]:
    """
    returns the most recent `limit` price records for an asset, newest first.
    each result: {"id", "asset_id", "timestamp", "open", "high", "low", "close", "volume"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT id, asset_id, timestamp, open, high, low, close, volume
               FROM prices
               WHERE asset_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (asset_id, limit)
        )
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[db] get_price_history error: {e}")
        return []
    finally:
        conn.close()


# ── ACCOUNTS ──────────────────────────────────────────────────────────────

def get_account(account_id: int) -> dict | None:
    """
    returns account details, or None if not found.
    result: {"id", "type", "cash_balance", "created_at"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, type, cash_balance, created_at FROM accounts WHERE id = ?",
            (account_id,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_account error: {e}")
        return None
    finally:
        conn.close()


def update_cash_balance(account_id: int, new_balance: float) -> bool:
    """
    sets the cash_balance for an account to `new_balance`.
    returns true on success; false if failure
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE accounts SET cash_balance = ? WHERE id = ?",
            (new_balance, account_id)
        )
        conn.commit()
        return cursor.rowcount > 0  # False if no row matched that id
    except Exception as e:
        conn.rollback()
        print(f"[db] update_cash_balance error: {e}")
        return False
    finally:
        conn.close()


# trades ────────────────────────────────────────────────────────────────

def log_trade(account_id: int, asset_id: int, side: str,
              quantity: int, price: float) -> bool:
    """
    inserts a new trade into TRADES using the current timestamp.
    returns true on success; false if failure
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO trades (account_id, asset_id, side, quantity, price, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (account_id, asset_id, side.upper(), quantity, price, datetime.now())
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[db] log_trade error: {e}")
        return False
    finally:
        conn.close()


def get_trades(account_id: int) -> list[dict]:
    """
    returns all trades for an account, newest first.
    each result: {"id", "account_id", "asset_id", "side", "quantity", "price", "timestamp"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT id, account_id, asset_id, side, quantity, price, timestamp
               FROM trades
               WHERE account_id = ?
               ORDER BY timestamp DESC""",
            (account_id,)
        )
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[db] get_trades error: {e}")
        return []
    finally:
        conn.close()


def get_trades_for_asset(account_id: int, asset_id: int) -> list[dict]:
    """
    returns all trades for an account filtered to one asset, newest first.
    each result: {"id", "account_id", "asset_id", "side", "quantity", "price", "timestamp"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT id, account_id, asset_id, side, quantity, price, timestamp
               FROM trades
               WHERE account_id = ? AND asset_id = ?
               ORDER BY timestamp DESC""",
            (account_id, asset_id)
        )
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[db] get_trades_for_asset error: {e}")
        return []
    finally:
        conn.close()


def get_position(account_id: int, asset_id: int) -> int:
    """
    returns the net shares held for an asset: total bought minus total sold.
    returns 0 if no trades exist.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT
                   SUM(CASE WHEN side = 'BUY'  THEN quantity ELSE 0 END) -
                   SUM(CASE WHEN side = 'SELL' THEN quantity ELSE 0 END) AS net_shares
               FROM trades
               WHERE account_id = ? AND asset_id = ?""",
            (account_id, asset_id)
        )
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print(f"[db] get_position error: {e}")
        return 0
    finally:
        conn.close()