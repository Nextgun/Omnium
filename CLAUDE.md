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
│   ├── algorithms/
│   │   ├── cs_algorithm.py     # Mean-reversion buy/sell algorithm (DONE)
│   │   └── switcher.py         # Runtime algorithm switching (DONE)
│   ├── orchestration/
│   │   └── orchestrator.py     # Connects algorithm to DB, executes trades (DONE)
│   ├── backtesting/
│   │   └── backtest.py         # Replay historical prices through algorithm (DONE)
│   ├── evaluation/
│   │   └── compare.py          # Compare strategy configurations (DONE)
│   ├── trading/                # Paper trading (handled by orchestrator for now)
│   ├── models/__init__.py      # Dataclasses: Asset, Price, Account, Trade + enums
│   └── utils/__init__.py       # EventBus, Config, setup_logging
├── Omnium.UI/                  # WPF Desktop App (C#/.NET 8)
│   ├── MainWindow.xaml         # Main app shell (sidebar, nav, dashboard panels)
│   ├── MainWindow.xaml.cs      # Code-behind (needs API wiring)
│   ├── Dashboard/Panels/       # Reusable dashboard panel components
│   ├── App.xaml                # WPF app entry point
│   └── Omnium.UI.sln           # Visual Studio solution file
├── tests/
├── devtools/                   # PlantUML watcher, conda/vscode setup utils
├── docs/
│   ├── api-guide.md            # Comprehensive API usage guide
│   └── project-status.md       # Full project status + what's left
├── .env.example                # Template for local DB config
├── requirements.txt            # flask, mariadb, python-dotenv, yfinance, pytest, ruff
├── setup_dev.py                # One-time dev environment setup (conda env + deps)
├── setup_db.py                 # One-time DB setup (installs MariaDB + schema + seed)
└── sonar-project.properties    # SonarQube config (bane.tamucc.edu:9000)
```

## Database

- MariaDB on localhost:3306 (or bane.tamucc.edu for remote)
- Database name: omnium_database
- Config via .env file (see .env.example for setup)
- Key tables: assets, prices, accounts, trades, users, lockouts
- All queries use parameterized MariaDB connector

## API (Flask on localhost:5000)

All endpoints (see docs/api-guide.md for full details):

- GET /health
- GET /assets/search?q={query}, GET /assets/{id}
- GET /prices/{asset_id}?limit=30, GET /prices/{asset_id}/latest
- GET /account/{id}, GET /account/{id}/trades, GET /account/{id}/position/{asset_id}
- POST /auth/register, POST /auth/login
- POST /trading/tick, GET /trading/status/{account_id}/{asset_id}
- POST /trading/config, GET /trading/config, POST /trading/switch
- POST /backtest/run
- GET /evaluation/compare?asset_id={id}

## Code Style

- Python 3.11+
- Linter: ruff (config in ruff.toml)
- Tests: pytest
- Type hints on all function signatures
- Docstrings on all public functions

## Delivery Plan (v0.1.0)

### Branch: `create-exe` (off `integrate-gui`)
Goal: Package Omnium as a distributable desktop app that runs on localhost.

1. **WPF publish config** — add `PublishSingleFile`, `SelfContained`, version 0.1.0 to csproj
2. **Launcher script** (`launch_omnium.bat`) — starts MariaDB service, Flask API in background, then launches WPF exe
3. **Build script** (`build.bat`) — runs `dotnet publish` to produce the exe in a `dist/` folder
4. **Update .gitignore** — add `dist/` folder
5. **Version info** — set 0.1.0 in csproj, `__init__.py`, and launcher

### Branch: `expand-gui` (off `create-exe`)
Goal: Polish the GUI for end-user demo. Team can continue iterating on this branch.

1. **Login/Register screen** — show before main window, call /auth/register and /auth/login
2. **Real-time price refresh** — auto-refresh selected asset price every 10s
3. **Portfolio overview panel** — show all positions across assets with total P&L
4. **Trade confirmation dialog** — confirm before executing a trade tick
5. **Backtest results table** — show trade log in a DataGrid instead of plain text
6. **Evaluation results table** — DataGrid with strategy comparison columns
7. **Error handling UX** — show user-friendly messages when API is down or requests fail
8. **Status bar** — bottom bar showing connection status, last action, and timestamp
9. **About/Help panel** — team name, version, course info

## Important Notes

- DB credentials are in .env (never commit .env, use .env.example as template)
- The WPF UI is merged into integrate-gui branch; code-behind needs HttpClient wiring to API
- Setup: `python setup_dev.py` (conda env) → `python setup_db.py --seed` (DB) → `python -m flask --app src.omnium.api run` (API)
- MariaDB service may need admin start: `net start MariaDB` in admin PowerShell
- Don't break existing db.py functions — other modules depend on them
- All API responses should be JSON with appropriate HTTP status codes
- CS trading algorithm and orchestrator are integrated; ML algorithm is a future addition
- Git pre-commit hooks are disabled (team friction) — config preserved in setup_dev.py
