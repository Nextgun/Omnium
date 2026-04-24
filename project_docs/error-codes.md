# Omnium — Error Code Reference

## Login (E-1xx)

| Code   | Message                          | Cause                                      | Fix                                                       |
|--------|----------------------------------|--------------------------------------------|------------------------------------------------------------|
| E-101  | Please enter username and password | Username or password field is empty        | Fill in both fields                                        |
| E-102  | Could not connect to API         | Flask API is not running on localhost:5000  | Start the API: `python -m flask --app src.omnium.api run`  |

## Connection / General (E-2xx)

| Code   | Message                          | Cause                                      | Fix                                                       |
|--------|----------------------------------|--------------------------------------------|------------------------------------------------------------|
| E-201  | API Offline / Refresh failed     | API unreachable or went down mid-session   | Check Flask is running; check MariaDB is running           |
| E-202  | Could not load account           | `/account/{id}` endpoint failed            | Verify API is running and DB has accounts seeded           |
| E-203  | Could not load config            | `/trading/config` endpoint failed          | Verify API is running                                      |
| E-204  | Could not load portfolio         | `/account/{id}` endpoint failed            | Verify API is running and DB has accounts seeded           |

## Actions (E-3xx)

| Code   | Message                          | Cause                                      | Fix                                                       |
|--------|----------------------------------|--------------------------------------------|------------------------------------------------------------|
| E-300  | Select an asset first            | No asset selected before action            | Search for a stock and select it from results              |
| E-301  | Trade failed                     | `/trading/tick` endpoint failed             | Verify API is running and asset/account exist in DB        |
| E-302  | Backtest failed                  | `/backtest/run` endpoint failed             | Verify API is running and asset has price history          |
| E-303  | Evaluation failed                | `/evaluation/compare` endpoint failed       | Verify API is running and asset has price history          |

## Common Fixes

- **Start MariaDB**: Run `net start MariaDB` in an admin PowerShell
- **Start Flask API**: `conda activate omnium-dev && python -m flask --app src.omnium.api run`
- **Seed the database**: `python setup_db.py --seed`
- **Full setup from scratch**: `python setup_dev.py` → `python setup_db.py --seed` → start API → launch app
