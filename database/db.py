"""
All SQL lives here.
Other modules call these functions and get back plain Python dicts.

Install the driver once with:  pip install mariadb
"""

# db.py

import mariadb
import sys
from datetime import datetime

# mariaDB setup. change this if needed
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "Johncenagoat",
    "database": "omnium_database",
}


def _get_connection():
    """
    Internal helper used to open a MariaDB connection.
    Prefixed with _ so don't call this function directly.
    """
    try:
        return mariadb.connect(**DB_CONFIG)
    except mariadb.Error as e:
        print(f"[db] Connection error: {e}")
        sys.exit(1)


def _row_to_dict(cursor, row):
    """Converts a row tuple into a dict using the cursor's column names."""
    return {desc[0]: value for desc, value in zip(cursor.description, row)}


# seeding helpers =================================================================

def truncate_all() -> None:
    """
    Clears all tables in FK-safe order and resets auto-increment counters.
    Called by seed.py before re-seeding.
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
    """Inserts a row into ASSETS. Returns the new row's auto-incremented id."""
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
    """Inserts a row into PRICES. Returns the new row's id."""
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
    """Inserts a row into ACCOUNTS. Returns the new account id."""
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
    """Inserts a row into TRADES. Returns the new trade id."""
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
    Returns all assets whose symbol or name partially matches `query`.
    Each result: {"id", "symbol", "name"}
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
    Returns one asset matching the exact symbol, or None if not found.
    Result: {"id", "symbol", "name"}
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
    Returns one asset by its primary key, or None if not found.
    Result: {"id", "symbol", "name"}
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
    Returns the most recent price record for an asset, or None if unavailable.
    Result: {"id", "asset_id", "timestamp", "open", "high", "low", "close", "volume"}
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
    Returns the most recent `limit` price records for an asset, newest first.
    Each result: {"id", "asset_id", "timestamp", "open", "high", "low", "close", "volume"}
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


# accounts ────────────────────────────────────────────────────────────────

def get_account(account_id: int) -> dict | None:
    """
    Returns account details, or None if not found.
    Result: {"id", "type", "cash_balance", "created_at"}
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
    Sets the cash_balance for an account to `new_balance`.
    Returns True on success, False on failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE accounts SET cash_balance = ? WHERE id = ?",
            (new_balance, account_id)
        )
        conn.commit()
        return cursor.rowcount > 0
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
    Inserts a new trade into TRADES using the current timestamp.
    Returns True on success, False on failure.
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
    Returns all trades for an account, newest first.
    Each result: {"id", "account_id", "asset_id", "side", "quantity", "price", "timestamp"}
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
    Returns all trades for an account filtered to one asset, newest first.
    Each result: {"id", "account_id", "asset_id", "side", "quantity", "price", "timestamp"}
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
    Returns the net shares held for an asset: total bought minus total sold.
    Returns 0 if no trades exist.
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


# user accounts ----------------------------------------------------------------

def initialize_users_tables() -> None:
    """
    Creates the users, lockouts, and verification_codes tables if they don't
    already exist. Also adds email columns to users if missing (safe for
    existing installations). Safe to call on every startup.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username       VARCHAR(255) PRIMARY KEY,
                display_name   VARCHAR(255) NOT NULL,
                password       VARCHAR(255) NOT NULL,
                email          VARCHAR(255) DEFAULT NULL,
                email_verified TINYINT(1)   DEFAULT 0
            )
        """)

        # Safely add email columns for existing installations that pre-date them.
        for col, definition in [
            ("email",          "VARCHAR(255) DEFAULT NULL"),
            ("email_verified", "TINYINT(1)   DEFAULT 0"),
        ]:
            try:
                cursor.execute(
                    f"ALTER TABLE users ADD COLUMN {col} {definition}"
                )
            except mariadb.Error:
                pass  # Column already exists — that's fine.

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockouts (
                username        VARCHAR(255) PRIMARY KEY,
                failed_attempts INT      DEFAULT 0,
                lockout_until   DATETIME DEFAULT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_codes (
                username VARCHAR(255) PRIMARY KEY,
                code     VARCHAR(10)  NOT NULL,
                expiry   DATETIME     NOT NULL,
                attempts INT          DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)

        conn.commit()
    except Exception as e:
        print(f"[db] initialize_users_tables error: {e}")
    finally:
        conn.close()


def create_user(username: str, display_name: str, password_hash: str,
                email: str | None = None) -> bool:
    """
    Inserts a new row into USERS.
    Username is stored lowercase; display_name preserves original casing.
    Returns True on success, False on failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO users (username, display_name, password, email, email_verified)
               VALUES (?, ?, ?, ?, 0)""",
            (username.lower(), display_name, password_hash, email)
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
    Returns one user by username (case-insensitive), or None if not found.
    Result: {"username", "display_name", "password", "email", "email_verified"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT username, display_name, password, email, email_verified
               FROM users WHERE username = ?""",
            (username.lower(),)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_user error: {e}")
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """
    Returns one user by email address (case-insensitive), or None if not found.
    Result: {"username", "display_name", "password", "email", "email_verified"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT username, display_name, password, email, email_verified
               FROM users WHERE LOWER(email) = LOWER(?)""",
            (email,)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_user_by_email error: {e}")
        return None
    finally:
        conn.close()


def set_email_verified(username: str, verified: bool = True) -> bool:
    """
    Sets the email_verified flag for a user.
    Returns True on success, False on failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET email_verified = ? WHERE username = ?",
            (1 if verified else 0, username.lower())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[db] set_email_verified error: {e}")
        return False
    finally:
        conn.close()


# user lockouts ------------------------------------------------------------------

def initialize_user_lockout(username: str) -> None:
    """
    Inserts a lockout row for a user if one doesn't already exist.
    Safe to call multiple times.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT IGNORE INTO lockouts (username, failed_attempts, lockout_until) VALUES (?, 0, NULL)",
            (username.lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"[db] initialize_user_lockout error: {e}")
    finally:
        conn.close()


def get_lockout(username: str) -> dict | None:
    """
    Returns lockout info for a user, or None if not found.
    Result: {"username", "failed_attempts", "lockout_until"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, failed_attempts, lockout_until FROM lockouts WHERE username = ?",
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
    Increments failed_attempts by 1 for a user.
    If lockout_until is provided, sets it at the same time (account is being locked).
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE lockouts
               SET failed_attempts = failed_attempts + 1,
                   lockout_until   = ?
               WHERE username = ?""",
            (lockout_until, username.lower())
        )
        conn.commit()
    except Exception as e:
        print(f"[db] increment_failed_attempt error: {e}")
    finally:
        conn.close()


def reset_lockout(username: str) -> None:
    """
    Resets failed_attempts to 0 and clears lockout_until for a user.
    Called after a successful login or when a lockout period expires.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE lockouts SET failed_attempts = 0, lockout_until = NULL WHERE username = ?",
            (username.lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"[db] reset_lockout error: {e}")
    finally:
        conn.close()


# verification codes -------------------------------------------------------------

def upsert_verification_code(username: str, code: str, expiry: datetime) -> bool:
    """
    Inserts or replaces a verification code for a user.
    Returns True on success, False on failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO verification_codes (username, code, expiry, attempts)
               VALUES (?, ?, ?, 0)
               ON DUPLICATE KEY UPDATE code = VALUES(code),
                                       expiry = VALUES(expiry),
                                       attempts = 0""",
            (username.lower(), code, expiry)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[db] upsert_verification_code error: {e}")
        return False
    finally:
        conn.close()


def get_verification_code(username: str) -> dict | None:
    """
    Returns the active verification code record for a user, or None if not found.
    Result: {"username", "code", "expiry", "attempts"}
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username, code, expiry, attempts FROM verification_codes WHERE username = ?",
            (username.lower(),)
        )
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row else None
    except Exception as e:
        print(f"[db] get_verification_code error: {e}")
        return None
    finally:
        conn.close()


def increment_code_attempts(username: str) -> int | None:
    """
    Increments the attempt counter for a user's verification code.
    Returns the new attempt count, or None on error.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE verification_codes SET attempts = attempts + 1 WHERE username = ?",
            (username.lower(),)
        )
        conn.commit()
        cursor.execute(
            "SELECT attempts FROM verification_codes WHERE username = ?",
            (username.lower(),)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"[db] increment_code_attempts error: {e}")
        return None
    finally:
        conn.close()


def delete_verification_code(username: str) -> None:
    """Deletes the verification code record for a user."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM verification_codes WHERE username = ?",
            (username.lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"[db] delete_verification_code error: {e}")
    finally:
        conn.close()


# trading algorithm logic --------------------------------------------------------

def get_avg_buy_price(account_id: int, asset_id: int) -> float | None:
    """Returns average cost basis for all BUY trades on an asset."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT SUM(price * quantity) / SUM(quantity)
               FROM trades
               WHERE account_id = ? AND asset_id = ? AND side = 'BUY'""",
            (account_id, asset_id)
        )
        row = cursor.fetchone()
        return float(row[0]) if row and row[0] is not None else None
    except Exception as e:
        print(f"[db] get_avg_buy_price error: {e}")
        return None
    finally:
        conn.close()