# Omnium — Project Context for Claude Code

## What This Project Is
Omnium is a modular day-trading platform built by a 7-person student team (QuantumShell)
for COSC 3370 at TAMUCC. Deadline: April 14, 2026. It has a Python backend and a
C# WPF desktop frontend that communicate via a Flask REST API on localhost:5000.

## Architecture
```
WPF Desktop App (C#/.NET 8) ──HTTP/JSON──> Flask REST API (Python) ──> MariaDB
```

The Python backend handles: database CRUD, trading algorithms (CS + ML),
orchestration, backtesting, and evaluation. The WPF app is the user-facing GUI.

## Current Repo Structure (being restructured)
```
Omnium/
├── database/db.py          # 724-line MariaDB abstraction (DONE)
├── database/schema.sql     # 4 tables: assets, prices, accounts, trades
├── database/seed.py        # Seeds DJIA stocks from Yahoo Finance
├── trading_logic/
│   ├── trading_algorithm.py  # CS algorithm: mean-reversion buy/sell
│   └── orchestrator.py       # Connects algorithm to DB (3 functions)
├── registration/auth_system.py  # Login, registration, email verification
├── search.py               # Asset search by symbol/name
├── email_service.py        # Gmail SMTP (creds need to move to .env)
├── Omnium.UI/              # WPF app (C#/.NET 8, on separate branch)
└── tests/                  # Needs pytest setup
```

## Target Structure (what we're building toward)
```
src/omnium/                 # Python package
├── __init__.py
├── api.py                  # Flask REST API entry point
├── data/db.py              # Existing database module
├── algorithms/
│   ├── cs_algorithm.py     # Existing rule-based algorithm
│   ├── ml_algorithm.py     # NEW: scikit-learn LinearRegression
│   └── switcher.py         # NEW: runtime algorithm switching
├── orchestration/
│   └── orchestrator.py     # Existing + enhanced
├── backtesting/            # NEW: replay historical prices
├── evaluation/             # NEW: compare algorithm performance
├── auth/                   # Existing auth + email
└── search/                 # Existing search
```

## Database
- MariaDB on localhost:3306 (or bane.tamucc.edu for remote)
- Database name: omnium_database
- Config in db.py DB_CONFIG dict (moving to .env)
- Key tables: assets, prices, accounts, trades
- All queries use parameterized MariaDB connector

## Key db.py Functions (already implemented)
- search_assets(query) → list[dict]
- get_latest_price(asset_id) → dict | None
- get_price_history(asset_id, limit=30) → list[dict]
- get_account(account_id) → dict | None
- log_trade(account_id, asset_id, side, quantity, price) → int
- get_trades(account_id) → list[dict]
- get_position(account_id, asset_id) → int
- get_avg_buy_price(account_id, asset_id) → float | None
- update_cash_balance(account_id, new_balance) → bool

## API Endpoints to Build
- POST /auth/register, POST /auth/login
- GET /assets/search?q={query}
- GET /prices/{asset_id}?limit=30
- POST /trading/tick, GET /trading/status/{account_id}/{asset_id}
- POST /trading/config, POST /trading/switch
- GET /account/{id}
- POST /backtest/run
- GET /evaluation/compare

## Code Style
- Python 3.11+
- Linter: ruff (config in ruff.toml)
- Tests: pytest
- Type hints on all function signatures
- Docstrings on all public functions

## Important Notes
- email_service.py has hardcoded Gmail creds — these must move to .env
- The WPF UI is on a separate branch (11-create-interface-for-switching-between-decision-modules)
- Don't break existing db.py functions — other modules depend on them
- All API responses should be JSON with appropriate HTTP status codes
