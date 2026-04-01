"""
setup_db.py — One-command database setup for Omnium.

Creates the omnium_database if it doesn't exist, runs the schema,
and optionally seeds DJIA stock data.

Usage:
    python setup_db.py            # Create DB + schema only
    python setup_db.py --seed     # Create DB + schema + seed stock data

Requires:
    - MariaDB running on the host specified in .env (default: localhost:3306)
    - pip install mariadb python-dotenv
    - A .env file with OMNIUM_DB_USER and OMNIUM_DB_PASSWORD (see .env.example)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_config() -> dict:
    """Read DB connection info from .env."""
    return {
        "host": os.getenv("OMNIUM_DB_HOST", "localhost"),
        "port": int(os.getenv("OMNIUM_DB_PORT", "3306")),
        "user": os.getenv("OMNIUM_DB_USER", "root"),
        "password": os.getenv("OMNIUM_DB_PASSWORD", ""),
    }


def create_database(config: dict, db_name: str) -> None:
    """Create the database if it doesn't already exist."""
    import mariadb

    try:
        conn = mariadb.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        conn.commit()
        print(f"[setup_db] Database '{db_name}' ready.")
        conn.close()
    except mariadb.Error as e:
        print(f"[setup_db] Failed to create database: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is MariaDB running?")
        print(f"  2. Can user '{config['user']}' connect to {config['host']}:{config['port']}?")
        print("  3. Check your .env file (see .env.example)")
        sys.exit(1)


def run_schema(config: dict, db_name: str) -> None:
    """Execute schema.sql to create all tables."""
    import mariadb

    schema_path = Path(__file__).parent / "src" / "omnium" / "data" / "schema.sql"
    if not schema_path.exists():
        print(f"[setup_db] schema.sql not found at {schema_path}")
        sys.exit(1)

    sql = schema_path.read_text(encoding="utf-8")

    try:
        conn = mariadb.connect(**config, database=db_name)
        cursor = conn.cursor()

        # Execute each statement separately
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

        conn.commit()
        print("[setup_db] Schema applied (assets, prices, accounts, trades).")
        conn.close()
    except mariadb.Error as e:
        print(f"[setup_db] Failed to run schema: {e}")
        sys.exit(1)


def create_user_tables(config: dict, db_name: str) -> None:
    """Create users and lockouts tables (same as db.initialize_users_tables)."""
    import mariadb

    try:
        conn = mariadb.connect(**config, database=db_name)
        cursor = conn.cursor()
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
        print("[setup_db] User tables ready (users, lockouts).")
        conn.close()
    except mariadb.Error as e:
        print(f"[setup_db] Failed to create user tables: {e}")
        sys.exit(1)


def seed_data() -> None:
    """Run the stock seeder to populate assets and prices."""
    print("[setup_db] Seeding DJIA stock data (this may take a minute)...")
    try:
        from src.omnium.data.seed import main as seed_main
        seed_main()
        print("[setup_db] Seed complete.")
    except Exception as e:
        print(f"[setup_db] Seed failed: {e}")
        print("  You can run it manually later: python -m src.omnium.data.seed")


def main() -> None:
    db_name = os.getenv("OMNIUM_DB_NAME", "omnium_database")
    config = get_config()

    print(f"[setup_db] Connecting to MariaDB at {config['host']}:{config['port']}...")
    print(f"[setup_db] Target database: {db_name}")
    print()

    create_database(config, db_name)
    run_schema(config, db_name)
    create_user_tables(config, db_name)

    if "--seed" in sys.argv:
        seed_data()

    print()
    print("Done! You can now run the API:")
    print("  python -m flask --app src.omnium.api run")


if __name__ == "__main__":
    main()
