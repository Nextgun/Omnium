"""
setup_db.py — One-command database setup for Omnium.

Installs MariaDB if not found, creates the omnium_database,
runs the schema, and optionally seeds DJIA stock data.

Usage:
    python setup_db.py            # Create DB + schema only
    python setup_db.py --seed     # Create DB + schema + seed stock data

Requires:
    - pip install mariadb python-dotenv
    - A .env file with OMNIUM_DB_USER and OMNIUM_DB_PASSWORD (see .env.example)
"""

import os
import platform
import shutil
import subprocess
import sys
import time
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


# ── MariaDB Installation ──


def _is_mariadb_running(config: dict) -> bool:
    """Try to connect to MariaDB. Returns True if reachable."""
    import mariadb

    # Try with .env password
    try:
        conn = mariadb.connect(**config)
        conn.close()
        return True
    except Exception:
        pass

    # Try with empty password (fresh install)
    try:
        conn = mariadb.connect(
            host=config["host"], port=config["port"],
            user=config["user"], password="",
        )
        conn.close()
        return True
    except Exception:
        return False


def _find_mariadb_install() -> str | None:
    """Find MariaDB install directory on disk."""
    if platform.system() != "Windows":
        if shutil.which("mysqld") or shutil.which("mariadbd"):
            return "system"
        return None

    # Check common install paths
    program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    for entry in program_files.iterdir() if program_files.exists() else []:
        if entry.is_dir() and entry.name.lower().startswith("mariadb"):
            mariadbd = entry / "bin" / "mariadbd.exe"
            if mariadbd.exists():
                return str(entry)
    return None


def _find_mariadb_service() -> bool:
    """Check if MariaDB is registered as a Windows service."""
    if platform.system() != "Windows":
        return shutil.which("mysqld") is not None or shutil.which("mariadbd") is not None

    result = subprocess.run(
        ["sc", "query", "MariaDB"],
        capture_output=True, text=True,
    )
    return "MariaDB" in result.stdout


def _register_and_start_service(install_dir: str) -> bool:
    """Register MariaDB as a Windows service and start it."""
    mariadbd = Path(install_dir) / "bin" / "mariadbd.exe"

    print(f"[setup_db] Registering MariaDB service from {install_dir}...")
    # Try to register the service (needs admin)
    result = subprocess.run(
        [str(mariadbd), "--install", "MariaDB"],
        capture_output=True, text=True,
    )

    if result.returncode != 0 and "exists" not in result.stderr.lower():
        print("[setup_db] Could not register MariaDB service (needs admin).")
        print()
        print("  Run these commands in an admin PowerShell:")
        print(f'    & "{mariadbd}" --install MariaDB')
        print('    net start MariaDB')
        print()
        print("  Then re-run: python setup_db.py --seed")
        return False

    return _start_mariadb_service()


def _start_mariadb_service() -> bool:
    """Try to start the MariaDB service (Windows)."""
    if platform.system() != "Windows":
        print("[setup_db] On Linux/Mac, start MariaDB with: sudo systemctl start mariadb")
        return False

    print("[setup_db] Starting MariaDB service...")
    result = subprocess.run(
        ["net", "start", "MariaDB"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("[setup_db] MariaDB service started.")
        time.sleep(2)  # Give it a moment to accept connections
        return True

    print("[setup_db] Could not start MariaDB service (needs admin).")
    print()
    print("  Run this in an admin PowerShell:")
    print("    net start MariaDB")
    print()
    print("  Then re-run: python setup_db.py --seed")
    return False


def install_mariadb(config: dict) -> None:
    """Install MariaDB using winget (Windows) if not already installed."""
    if _is_mariadb_running(config):
        print("[setup_db] MariaDB is already running.")
        _set_root_password(config)
        return

    # Check if service exists and just needs starting
    if _find_mariadb_service():
        print("[setup_db] MariaDB service found but not running.")
        if _start_mariadb_service():
            return
        sys.exit(1)

    # Check if installed on disk but service not registered
    install_dir = _find_mariadb_install()
    if install_dir and install_dir != "system":
        print(f"[setup_db] MariaDB found at {install_dir} but service not registered.")
        if _register_and_start_service(install_dir):
            return
        sys.exit(1)

    # Not installed — install via winget
    if platform.system() != "Windows":
        print("[setup_db] MariaDB is not installed.")
        print("  Install it with your package manager:")
        print("    Ubuntu/Debian: sudo apt install mariadb-server")
        print("    Mac:           brew install mariadb")
        sys.exit(1)

    if not shutil.which("winget"):
        print("[setup_db] MariaDB is not installed and winget is not available.")
        print("  Please install MariaDB manually from: https://mariadb.org/download/")
        sys.exit(1)

    password = config["password"]
    print("[setup_db] Installing MariaDB via winget...")
    print("  This may take a few minutes and require admin approval.")
    print()

    # winget install with root password
    cmd = [
        "winget", "install", "MariaDB.Server",
        "--accept-package-agreements",
        "--accept-source-agreements",
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print()
        print("[setup_db] winget install failed or was cancelled.")
        print("  You can install MariaDB manually from: https://mariadb.org/download/")
        print(f"  Set the root password to: {password}")
        sys.exit(1)

    print()
    print("[setup_db] MariaDB installed.")

    # Wait for service to be available
    print("[setup_db] Waiting for MariaDB service to start...")
    _start_mariadb_service()

    # After winget install, the root password may be empty.
    # Try to set it to match .env
    _set_root_password(config)


def _set_root_password(config: dict) -> None:
    """After fresh install, set root password to match .env."""
    password = config["password"]
    if not password:
        return

    try:
        import mariadb

        # Try connecting with no password (fresh install default)
        try:
            conn = mariadb.connect(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password="",
            )
            cursor = conn.cursor()
            cursor.execute(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{password}'")
            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()
            conn.close()
            print(f"[setup_db] Root password set to match .env.")
        except mariadb.Error:
            # Already has a password or can't connect — try with .env password
            pass
    except Exception:
        pass


# ── Database Setup ──


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
        print("  1. Is MariaDB running? Check Services (Win+R -> services.msc)")
        print(f"  2. Can user '{config['user']}' connect to {config['host']}:{config['port']}?")
        print("  3. Does the password in .env match your MariaDB root password?")
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
        from src.omnium.data import seed
        seed.reset_all()
        seed.seed_assets_and_prices()
        account_ids = seed.seed_accounts()
        seed.seed_trades(account_ids)
        print("[setup_db] Seed complete.")
    except Exception as e:
        print(f"[setup_db] Seed failed: {e}")
        print("  You can run it manually later: python -m src.omnium.data.seed")


def main() -> None:
    db_name = os.getenv("OMNIUM_DB_NAME", "omnium_database")
    config = get_config()

    print("[setup_db] Omnium Database Setup")
    print(f"[setup_db] Target: {config['host']}:{config['port']} / {db_name}")
    print()

    # Step 0: Ensure MariaDB is installed and running
    install_mariadb(config)

    # Step 1: Create database
    create_database(config, db_name)

    # Step 2: Run schema
    run_schema(config, db_name)

    # Step 3: Create user/lockout tables
    create_user_tables(config, db_name)

    # Step 4: Seed data (optional)
    if "--seed" in sys.argv:
        seed_data()

    print()
    print("Done! You can now run the API:")
    print("  python -m flask --app src.omnium.api run")


if __name__ == "__main__":
    main()
