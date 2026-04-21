"""
==========================
db.py - abstraction layer for interacting with the database
author: 
data created: 2/15/2026
date last modified: 3/6/2026
=====================================
All SQL lives here. 
Other modules calls these functions and gets back plain Python dicts.

Install the driver once with:  pip install pymysql
"""

from __future__ import annotations

import os
import pymysql
import sys
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# mariaDB setup — reads from .env file, falls back to defaults.
# Each developer creates their own .env from .env.example.
# See .env.example for setup instructions.
DB_CONFIG = {
    "host":     os.getenv("OMNIUM_DB_HOST", "localhost"),
    "port":     int(os.getenv("OMNIUM_DB_PORT", "3306")),
    "user":     os.getenv("OMNIUM_DB_USER", "root"),
    "password": os.getenv("OMNIUM_DB_PASSWORD", ""),
    "database": os.getenv("OMNIUM_DB_NAME", "omnium_database"),
}

def _get_connection():
    """
    internal helper used to get a MariaDB connection via pymysql.
    Prefixed with _ so don't call this function directly.
    """
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
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
            "INSERT INTO assets (symbol, name) VALUES (%s, %s)",
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
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
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
            "INSERT INTO accounts (type, cash_balance) VALUES (%s, %s)",
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
               VALUES (%s, %s, %s, %s, %s, %s)""",
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
               WHERE symbol LIKE %s OR name LIKE %s
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
            "SELECT id, symbol, name FROM assets WHERE symbol = %s",
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
            "SELECT id, symbol, name FROM assets WHERE id = %s",
            (asset_id,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_asset_by_id error: {e}")
        return None
    finally:
        conn.close()


def get_assets_paginated(page: int = 1, per_page: int = 10) -> dict:
    """
    returns a paginated list of all assets.
    result: {"assets": [...], "page", "per_page", "total", "total_pages"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM assets")
        total = cursor.fetchone()[0]

        offset = (page - 1) * per_page
        cursor.execute(
            "SELECT id, symbol, name FROM assets ORDER BY symbol LIMIT %s OFFSET %s",
            (per_page, offset)
        )
        assets = [_row_to_dict(cursor, row) for row in cursor.fetchall()]

        total_pages = (total + per_page - 1) // per_page
        return {
            "assets": assets,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
    except Exception as e:
        print(f"[db] get_assets_paginated error: {e}")
        return {"assets": [], "page": page, "per_page": per_page, "total": 0, "total_pages": 0}
    finally:
        conn.close()


# cached queries =============================================================

@lru_cache(maxsize=1)
def get_all_assets_cached() -> tuple[dict, ...]:
    """
    returns all assets as a tuple of dicts (cached after first call).
    Call invalidate_asset_cache() after inserting new assets.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, symbol, name FROM assets ORDER BY symbol")
        return tuple(_row_to_dict(cursor, row) for row in cursor.fetchall())
    except Exception as e:
        print(f"[db] get_all_assets_cached error: {e}")
        return ()
    finally:
        conn.close()


def invalidate_asset_cache() -> None:
    """clears the cached asset list. Call after seeding or inserting assets."""
    get_all_assets_cached.cache_clear()


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
               WHERE asset_id = %s
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
               WHERE asset_id = %s
               ORDER BY timestamp DESC
               LIMIT %s""",
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
            "SELECT id, type, cash_balance, created_at FROM accounts WHERE id = %s",
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
            "UPDATE accounts SET cash_balance = %s WHERE id = %s",
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
               VALUES (%s, %s, %s, %s, %s, %s)""",
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
               WHERE account_id = %s
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
               WHERE account_id = %s AND asset_id = %s
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
               WHERE account_id = %s AND asset_id = %s""",
            (account_id, asset_id)
        )
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        print(f"[db] get_position error: {e}")
        return 0
    finally:
        conn.close()

# user accounts ----------------------------------------------------------------

def initialize_users_tables() -> None:
    """
    creates the users and lockouts tables if they don't already exist.
    safe to call on every startup.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username     VARCHAR(255) PRIMARY KEY,
                display_name VARCHAR(255) NOT NULL,
                password     VARCHAR(255) NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockouts (
                username        VARCHAR(255) PRIMARY KEY,
                failed_attempts INT      DEFAULT 0,
                lockout_until   DATETIME DEFAULT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"[db] initialize_users_tables error: {e}")
    finally:
        conn.close()


def create_user(username: str, display_name: str, password_hash: str) -> bool:
    """
    inserts a new row into USERS.
    username is stored lowercase; display_name preserves original casing.
    returns true on success; false if failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, display_name, password) VALUES (%s, %s, %s)",
            (username.lower(), display_name, password_hash)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[db] create_user error: {e}")
        return False
    finally:
        conn.close()


def get_user(username: str) -> dict | None:
    """
    returns one user by username (case-insensitive), or None if not found.
    result: {"username", "display_name", "password"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, display_name, password FROM users WHERE username = %s",
            (username.lower(),)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_user error: {e}")
        return None
    finally:
        conn.close()


# USER LOCKOUTS ------------------------------------------------------------------

def initialize_user_lockout(username: str) -> None:
    """
    inserts a lockout row for a user if one doesn't already exist.
    safe to call multiple times.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT IGNORE INTO lockouts (username, failed_attempts, lockout_until) VALUES (%s, 0, NULL)",
            (username.lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"[db] initialize_user_lockout error: {e}")
    finally:
        conn.close()


def get_lockout(username: str) -> dict | None:
    """
    returns lockout info for a user, or None if not found.
    result: {"username", "failed_attempts", "lockout_until"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, failed_attempts, lockout_until FROM lockouts WHERE username = %s",
            (username.lower(),)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_lockout error: {e}")
        return None
    finally:
        conn.close()


def increment_failed_attempt(username: str, lockout_until: datetime | None = None) -> None:
    """
    increments failed_attempts by 1 for a user.
    if lockout_until is provided, sets it at the same time (account is being locked).
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE lockouts
               SET failed_attempts = failed_attempts + 1,
                   lockout_until   = %s
               WHERE username = %s""",
            (lockout_until, username.lower())
        )
        conn.commit()
    except Exception as e:
        print(f"[db] increment_failed_attempt error: {e}")
    finally:
        conn.close()


def reset_lockout(username: str) -> None:
    """
    resets failed_attempts to 0 and clears lockout_until for a user.
    called after a successful login or when a lockout period expires.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE lockouts SET failed_attempts = 0, lockout_until = NULL WHERE username = %s",
            (username.lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"[db] reset_lockout error: {e}")
    finally:
        conn.close()
