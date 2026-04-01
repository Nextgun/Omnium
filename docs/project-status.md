# Omnium Project Status

**Team:** QuantumShell (7 people) | **Course:** COSC 3370, TAMUCC
**Deadline:** April 14, 2026 (~20 days from March 25)
**Last updated:** 2026-04-01

---

## What's Done

### Infrastructure
- [x] MariaDB database schema (4 tables: assets, prices, accounts, trades)
- [x] db.py — full abstraction layer (search, prices, accounts, trades, users, lockouts)
- [x] Database seeder (DJIA stocks from Yahoo Finance)
- [x] Project restructured into `src/omnium/` package layout
- [x] `.env` config for DB credentials (no more hardcoded passwords)
- [x] `.env.example` with setup instructions for new devs
- [x] requirements.txt updated for actual stack (flask, mariadb, python-dotenv)
- [x] `setup_dev.py` — detects Anaconda/Miniconda, creates conda env, installs deps
- [x] `setup_db.py` — installs MariaDB via winget, creates DB, runs schema, seeds data

### API (Flask)
- [x] `src/omnium/api.py` — app factory with all core routes
- [x] `GET /health` — health check
- [x] `GET /assets/search?q=` — search stocks
- [x] `GET /assets/<id>` — get asset by ID
- [x] `GET /prices/<asset_id>?limit=30` — price history
- [x] `GET /prices/<asset_id>/latest` — latest price
- [x] `GET /account/<id>` — account details
- [x] `GET /account/<id>/trades` — trade history
- [x] `GET /account/<id>/position/<asset_id>` — net shares held
- [x] `POST /auth/register` — user registration
- [x] `POST /auth/login` — user login
- [x] `POST /trading/tick` — run one algorithm cycle
- [x] `GET /trading/status/<account_id>/<asset_id>` — current position + signal
- [x] `POST /trading/config` / `GET /trading/config` — algorithm parameters
- [x] `POST /trading/switch` — switch active algorithm
- [x] `POST /backtest/run` — replay historical data
- [x] `GET /evaluation/compare?asset_id=X` — compare strategy configs
- [x] API documentation (`docs/api-guide.md`)

### Trading & Analysis
- [x] CS mean-reversion algorithm (`src/omnium/algorithms/cs_algorithm.py`)
- [x] Algorithm switcher (`src/omnium/algorithms/switcher.py`)
- [x] Orchestrator — connects algorithm to DB, executes trades (`src/omnium/orchestration/orchestrator.py`)
- [x] Backtesting engine (`src/omnium/backtesting/backtest.py`)
- [x] Evaluation / comparison module (`src/omnium/evaluation/compare.py`)

### WPF Desktop App
- [x] WPF shell layout — sidebar nav, ticker tabs, dashboard panels (`Omnium.UI/`)
- [x] WPF HttpClient wiring to Flask API (`Omnium.UI/Services/ApiClient.cs`)
- [x] Login/Register screen with tab toggle (`LoginWindow.xaml`)
- [x] Auto-refresh price/signal every 10s (DispatcherTimer)
- [x] Portfolio overview panel (positions, shares, value, cost basis)
- [x] Trade confirmation dialog (MessageBox before tick)
- [x] Backtest results DataGrid (bar/action/price/shares/cash)
- [x] Evaluation results DataGrid (strategy/return/value/trades)
- [x] Status bar (last refresh timestamp + version)
- [x] About/Help panel (team, version, features, architecture)
- [x] Error codes on all error messages (`docs/error-codes.md`)
- [x] Exe packaging — `build.bat`, `launch_omnium.bat`, single-file publish (v0.1.0)

### Auth
- [x] Registration with username/password validation
- [x] Login with lockout after 3 failed attempts
- [x] Password hashing (SHA-256)
- [x] User + lockout tables in MariaDB

### Search
- [x] Asset search by symbol or name (partial match)

### DevTools
- [x] setup_dev.py (conda env, PlantUML, VS Code extensions)
- [x] PlantUML watcher + renderer
- [x] Git pre-commit hooks (disabled — revisit post-deadline or move to CI)

---

## What's NOT Done (Priority Order)

### P0 — Must have for demo (by April 14)

1. ~~**Integrate trading algorithm**~~ DONE (2026-03-31)
   - CS mean-reversion algorithm in `src/omnium/algorithms/cs_algorithm.py`
   - Orchestrator in `src/omnium/orchestration/orchestrator.py`
   - All trading endpoints wired into `api.py`

2. ~~**Test the API end-to-end**~~ DONE (2026-04-01)
   - Flask server starts, /health and /assets/search verified with seeded DB

3. ~~**Connect WPF frontend to API**~~ DONE (2026-04-01)
   - Full HttpClient wiring in `ApiClient.cs`
   - Login, dashboard, trade, backtest, evaluate, portfolio, config panels all connected
   - Exe packaging with `build.bat` + `launch_omnium.bat` (v0.1.0)

4. **Switch to remote MariaDB (bane.tamucc.edu)**
   - Currently everyone uses localhost; need shared data for demo
   - Just a `.env` change, but need to verify bane access/credentials
   - Who: You | Effort: 30 min once creds are confirmed

### P1 — Should have

5. ~~**Algorithm switching endpoint**~~ DONE (2026-03-31)
   - `POST /trading/switch`, `POST /trading/config`, `GET /trading/config` all wired

6. **ML algorithm**
   - scikit-learn LinearRegression or Random Forest
   - Train on historical price data, predict next-day direction
   - Who: ML team member | Effort: 2-3 sessions

7. ~~**Backtesting**~~ DONE (2026-03-31)
   - `POST /backtest/run` in `src/omnium/backtesting/backtest.py`

8. ~~**Evaluation / comparison**~~ DONE (2026-03-31)
   - `GET /evaluation/compare` in `src/omnium/evaluation/compare.py`

### P2 — Nice to have

9. **Multi-user auth (JWT/sessions)**
   - Current auth stores `current_user` on the class — breaks with concurrent users
   - Only matters when deployed on shared server
   - Who: Brady | Effort: 1-2 sessions

10. **Email verification**
    - `email_service.py` exists somewhere but isn't integrated
    - Gmail SMTP creds need to go in `.env`
    - Who: Brady | Effort: 1 session

11. ~~**Automate dev setup**~~ DONE (2026-04-01)
    - `setup_db.py` — installs MariaDB, creates DB, runs schema, seeds data
    - `setup_dev.py` — detects Anaconda/Miniconda, creates conda env

12. **Fix SonarQube CI**
    - Failing after 10s on PRs; likely config mismatch after restructure
    - Who: Whoever set up SonarQube | Effort: 30 min

13. **Re-enable git hooks (or move to GitHub Actions CI)**
    - ruff linting + PlantUML rendering on commits
    - Who: You | Effort: 1 session

---

## Teammate Branches Not Yet Integrated

These remote branches may have work that needs to be pulled in:

| Branch | Description | Status |
|--------|-------------|--------|
| `11-create-interface-for-switching-between-decision-modules` | WPF UI + algorithm switching | Merged into integrate-gui |
| `9-implement-rule-based-trading-algorithm-cs-module` | CS trading algorithm | Integrated into finish-backend |
| `13-implement-logging-of-trades-and-portfolio-tracking` | Trade logging | Needs review |
| `14-design-account-interface-for-future-live-trading-integration` | Account interface | Already merged into database |
| `23-sonarqube` | SonarQube setup | Already merged into database |
| `security-search` | Search security fixes? | Needs review |
| `work-in-progress` | Unknown | Needs review |

---

## API Endpoints Still Needed

| Endpoint | Purpose | Depends On |
|----------|---------|------------|
| `POST /trading/tick` | Run one algorithm cycle on an asset | ~~Trading algorithm~~ DONE |
| `GET /trading/status/{account_id}/{asset_id}` | Current position + signal | ~~Trading algorithm~~ DONE |
| `POST /trading/config` | Update algorithm parameters | ~~Algorithm switcher~~ DONE |
| `GET /trading/config` | Get current algorithm config | ~~Algorithm switcher~~ DONE |
| `POST /trading/switch` | Switch active algorithm | ~~Algorithm switcher~~ DONE |
| `POST /backtest/run` | Replay historical data | ~~Backtesting module~~ DONE |
| `GET /evaluation/compare` | Compare algorithm results | ~~Evaluation module~~ DONE |

---

## Current Repo Structure (after restructure)

```
Omnium/
├── src/omnium/               # Python package
│   ├── __init__.py
│   ├── api.py                # Flask REST API (DONE)
│   ├── __main__.py           # Entry point placeholder
│   ├── data/
│   │   ├── db.py             # MariaDB abstraction (DONE)
│   │   ├── seed.py           # DJIA stock seeder (DONE)
│   │   └── schema.sql        # Database schema (DONE)
│   ├── authentication/
│   │   └── auth_system.py    # Login + registration (DONE)
│   ├── search/
│   │   └── search.py         # Asset search (DONE)
│   ├── algorithms/
│   │   ├── cs_algorithm.py   # Mean-reversion algorithm (DONE)
│   │   └── switcher.py       # Algorithm switching (DONE)
│   ├── orchestration/
│   │   └── orchestrator.py   # Connects algo to DB (DONE)
│   ├── backtesting/
│   │   └── backtest.py       # Historical replay (DONE)
│   ├── evaluation/
│   │   └── compare.py        # Strategy comparison (DONE)
│   ├── trading/              # Paper trading (via orchestrator) (DONE)
│   ├── models/               # Dataclasses: Asset, Price, Account, Trade
│   └── utils/                # EventBus, Config, logging
├── tests/
├── devtools/
├── Omnium.UI/                # WPF Desktop App (.NET 8)
│   ├── App.xaml              # App entry point
│   ├── LoginWindow.xaml      # Login/Register screen (DONE)
│   ├── MainWindow.xaml       # Main app shell (DONE)
│   └── Services/ApiClient.cs # HttpClient wrapper (DONE)
├── docs/
│   ├── api-guide.md          # How to use the API
│   ├── error-codes.md        # UI error code reference
│   └── project-status.md     # This file
├── .env.example
├── build.bat                 # Build exe (dotnet publish)
├── launch_omnium.bat         # Start MariaDB + Flask + WPF
├── requirements.txt
├── setup_dev.py
├── setup_db.py
├── sonar-project.properties
└── CLAUDE.md
```

---

## Key Decisions Made (2026-03-25)

- **Flask over FastAPI** — simpler, team doesn't need async
- **MariaDB connector over SQLAlchemy** — db.py already works, no reason to rewrite
- **`src/omnium/` over `omnium/`** — matches sonar-project.properties, standard Python layout
- **Git hooks disabled** — team members struggling with git; consider CI instead
- **Stub __init__.py files deleted** — were 2,600 lines of generated code that conflicted with actual implementations
- **`authentication/` over `auth/`** — user's naming choice during restructure
