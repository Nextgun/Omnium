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

## Repo Structure

```
Omnium/
├── src/omnium/                 # Python package
│   ├── __init__.py
│   ├── api.py                  # Flask REST API entry point (DONE)
│   ├── __main__.py             # Entry point placeholder
│   ├── data/
│   │   ├── db.py               # MariaDB abstraction layer (DONE)
│   │   ├── seed.py             # Seeds DJIA stocks from Yahoo Finance
│   │   └── schema.sql          # 4 tables: assets, prices, accounts, trades
│   ├── authentication/
│   │   └── auth_system.py      # Login, registration, lockout (DONE)
│   ├── search/
│   │   └── search.py           # Asset search by symbol/name (DONE)
│   ├── algorithms/             # TODO: integrate trading_algorithm.py
│   ├── orchestration/          # TODO: integrate orchestrator.py
│   ├── trading/                # TODO: paper trading logic
│   ├── models/__init__.py      # Dataclasses: Asset, Price, Account, Trade + enums
│   └── utils/__init__.py       # EventBus, Config, setup_logging
├── tests/
├── devtools/                   # PlantUML watcher, conda/vscode setup utils
├── docs/
│   ├── api-guide.md            # Comprehensive API usage guide
│   └── project-status.md       # Full project status + what's left
├── .env.example                # Template for local DB config
├── requirements.txt            # flask, mariadb, python-dotenv, yfinance, pytest, ruff
├── setup_dev.py                # One-time dev environment setup
└── sonar-project.properties    # SonarQube config (bane.tamucc.edu:9000)
```

## Database

- MariaDB on localhost:3306 (or bane.tamucc.edu for remote)
- Database name: omnium_database
- Config via .env file (see .env.example for setup)
- Key tables: assets, prices, accounts, trades, users, lockouts
- All queries use parameterized MariaDB connector

## API (Flask on localhost:5000)

Running endpoints (see docs/api-guide.md for full details):

Running endpoints (see docs/api-guide.md for full details):

- GET /health
- GET /assets/search?q={query}, GET /assets/{id}
- GET /prices/{asset_id}?limit=30, GET /prices/{asset_id}/latest
- GET /account/{id}, GET /account/{id}/trades, GET /account/{id}/position/{asset_id}
- POST /auth/register, POST /auth/login

Endpoints still needed:

- POST /trading/tick, GET /trading/status/{account_id}/{asset_id}
- POST /trading/config, POST /trading/switch
- POST /backtest/run
- GET /evaluation/compare

## Code Style

- Python 3.11+
- Linter: ruff (config in ruff.toml)
- Tests: pytest
- Type hints on all function signatures
- Docstrings on all public functions

## Important Notes

- DB credentials are in .env (never commit .env, use .env.example as template)
- The WPF UI is on branch 11-create-interface-for-switching-between-decision-modules
- Don't break existing db.py functions — other modules depend on them
- All API responses should be JSON with appropriate HTTP status codes
- trading_algorithm.py and orchestrator.py exist on other branches but aren't integrated yet
- Git pre-commit hooks are disabled (team friction) — config preserved in setup_dev.py
