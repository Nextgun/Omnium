# Omnium Project Status

**Team:** QuantumShell (7 people) | **Course:** COSC 3370, TAMUCC
**Deadline:** April 14, 2026 (~20 days from March 25)
**Last updated:** 2026-03-25

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
- [x] API documentation (`docs/api-guide.md`)

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

1. **Test the API end-to-end**
   - Start Flask server, hit every endpoint, verify DB connection
   - Who: You | Effort: 1 session

2. **Integrate trading algorithm**
   - `trading_algorithm.py` (mean-reversion) exists on another branch but isn't in `src/omnium/algorithms/` yet
   - Wire into API: `POST /trading/tick`
   - Who: You + algorithm owner | Effort: 1-2 sessions

3. **Connect WPF frontend to API**
   - WPF app is on branch `11-create-interface-for-switching-between-decision-modules`
   - Needs to call Flask API endpoints via HttpClient
   - Who: WPF developer(s) | Effort: 2-3 sessions

4. **Switch to remote MariaDB (bane.tamucc.edu)**
   - Currently everyone uses localhost; need shared data for demo
   - Just a `.env` change, but need to verify bane access/credentials
   - Who: You | Effort: 30 min once creds are confirmed

### P1 — Should have

5. **Algorithm switching endpoint**
   - `POST /trading/switch` — switch between CS and ML algorithms at runtime
   - `POST /trading/config` — update algorithm parameters
   - Who: Algorithm team | Effort: 1 session

6. **ML algorithm**
   - scikit-learn LinearRegression or Random Forest
   - Train on historical price data, predict next-day direction
   - Who: ML team member | Effort: 2-3 sessions

7. **Backtesting**
   - `POST /backtest/run` — replay historical prices through an algorithm
   - Compare algorithm performance on past data
   - Who: TBD | Effort: 2 sessions

8. **Evaluation / comparison**
   - `GET /evaluation/compare` — side-by-side metrics for CS vs ML
   - Who: TBD | Effort: 1 session

### P2 — Nice to have

9. **Multi-user auth (JWT/sessions)**
   - Current auth stores `current_user` on the class — breaks with concurrent users
   - Only matters when deployed on shared server
   - Who: Brady | Effort: 1-2 sessions

10. **Email verification**
    - `email_service.py` exists somewhere but isn't integrated
    - Gmail SMTP creds need to go in `.env`
    - Who: Brady | Effort: 1 session

11. **Automate dev setup**
    - `setup_db.py` — create database, run schema, seed data in one command
    - Update `setup_dev.py` to ask local vs remote DB
    - Who: You | Effort: 1 session

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
| `11-create-interface-for-switching-between-decision-modules` | WPF UI + algorithm switching | Needs review |
| `13-implement-logging-of-trades-and-portfolio-tracking` | Trade logging | Needs review |
| `14-design-account-interface-for-future-live-trading-integration` | Account interface | Already merged into database |
| `23-sonarqube` | SonarQube setup | Already merged into database |
| `security-search` | Search security fixes? | Needs review |
| `work-in-progress` | Unknown | Needs review |

---

## API Endpoints Still Needed

| Endpoint | Purpose | Depends On |
|----------|---------|------------|
| `POST /trading/tick` | Run one algorithm cycle on an asset | Trading algorithm |
| `GET /trading/status/{account_id}/{asset_id}` | Current position + signal | Trading algorithm |
| `POST /trading/config` | Update algorithm parameters | Algorithm switcher |
| `POST /trading/switch` | Switch active algorithm | Algorithm switcher |
| `POST /backtest/run` | Replay historical data | Backtesting module |
| `GET /evaluation/compare` | Compare algorithm results | Evaluation module |

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
│   ├── algorithms/           # EMPTY — needs trading_algorithm.py
│   ├── orchestration/        # EMPTY — needs orchestrator.py
│   ├── trading/              # EMPTY — needs paper trading logic
│   ├── models/               # Dataclasses: Asset, Price, Account, Trade
│   └── utils/                # EventBus, Config, logging
├── tests/
├── devtools/
├── docs/
│   ├── api-guide.md          # How to use the API
│   └── project-status.md     # This file
├── .env.example
├── requirements.txt
├── setup_dev.py
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
