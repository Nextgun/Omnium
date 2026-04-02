# Lessons Learned: Database Indexing

**Date Identified:** April 2, 2026
**Status:** Documented, pending implementation and benchmarking

---

## Problem

All queries on the `prices` and `trades` tables perform **full table scans** because
there are no indexes on frequently-queried columns. Only the auto-increment `id`
primary keys are indexed.

### Current Schema (no indexes)

```sql
-- prices: queried by asset_id + timestamp on nearly every API call
CREATE TABLE IF NOT EXISTS prices (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    asset_id  INT            NOT NULL,      -- NO INDEX
    timestamp DATETIME       NOT NULL,      -- NO INDEX
    open      FLOAT          NOT NULL,
    high      FLOAT          NOT NULL,
    low       FLOAT          NOT NULL,
    close     FLOAT          NOT NULL,
    volume    INT            NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- trades: queried by account_id + asset_id on portfolio, position, and status calls
CREATE TABLE IF NOT EXISTS trades (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT            NOT NULL,     -- NO INDEX
    asset_id   INT            NOT NULL,     -- NO INDEX
    side       VARCHAR(4)     NOT NULL,
    quantity   INT            NOT NULL,
    price      FLOAT          NOT NULL,
    timestamp  DATETIME       NOT NULL,     -- NO INDEX
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (asset_id)   REFERENCES assets(id)
);
```

### Affected Queries (from db.py)

| Function | Query Pattern | Impact |
|----------|--------------|--------|
| `get_latest_price()` | `WHERE asset_id = ? ORDER BY timestamp DESC LIMIT 1` | Full scan of all prices, sorts entire result |
| `get_price_history()` | `WHERE asset_id = ? ORDER BY timestamp DESC LIMIT ?` | Full scan of all prices |
| `get_trades()` | `WHERE account_id = ? ORDER BY timestamp DESC` | Full scan of all trades |
| `get_trades_for_asset()` | `WHERE account_id = ? AND asset_id = ? ORDER BY timestamp DESC` | Full scan of all trades |
| `get_position()` | `WHERE account_id = ? AND asset_id = ?` with SUM aggregation | Full scan of all trades |
| `search_assets()` | `WHERE symbol LIKE ? OR name LIKE ?` | Full scan of assets (minor, small table) |

### How This Cascades

The WPF auto-refresh timer fires **every 10 seconds** and calls:
1. `GET /prices/{id}/latest` -> `get_latest_price()` -> full table scan
2. `GET /trading/status/{acct}/{asset}` -> `get_latest_price()` + `get_position()` + `get_trades_for_asset()` + `get_price_history()` -> **4 full table scans**
3. `GET /account/{id}` -> `get_account()` -> PK lookup (fast, no issue)

That's **5 full table scans every 10 seconds per connected user**.

The Portfolio view is worse: it calls `GET /prices/{id}/latest` once **per asset held**,
creating an N+1 query pattern (1 call to get trades + N calls for prices).

---

## Proposed Fix

Add these indexes to `schema.sql`:

```sql
-- Covers get_latest_price() and get_price_history()
-- Composite index on (asset_id, timestamp DESC) lets the DB jump to
-- the right asset and walk timestamps in order without sorting.
CREATE INDEX idx_prices_asset_time ON prices (asset_id, timestamp DESC);

-- Covers get_trades(), get_trades_for_asset(), and get_position()
-- Composite index on (account_id, asset_id, timestamp DESC) covers
-- all three query patterns with a single index.
CREATE INDEX idx_trades_acct_asset_time ON trades (account_id, asset_id, timestamp DESC);
```

For existing databases, run as a migration:

```sql
ALTER TABLE prices ADD INDEX idx_prices_asset_time (asset_id, timestamp DESC);
ALTER TABLE trades ADD INDEX idx_trades_acct_asset_time (account_id, asset_id, timestamp DESC);
```

---

## Expected Impact

| Metric | Before (no index) | After (with index) |
|--------|-------------------|-------------------|
| `get_latest_price()` | O(n) scan + sort | O(log n) seek + 1 row |
| `get_price_history(limit=30)` | O(n) scan + sort | O(log n) seek + 30 rows |
| `get_trades_for_asset()` | O(n) scan + sort | O(log n) seek |
| `get_position()` (SUM) | O(n) scan | O(log n) seek + aggregate subset |
| Storage overhead | None | ~2 small B-tree indexes |

With 5 stocks x 90 days = 450 price rows, the difference is modest. But as data
grows (more stocks, more trading days, more trades), unindexed queries degrade
linearly while indexed queries stay logarithmic.

---

## Benchmarking Plan

**Record these before and after adding indexes:**

### Test 1: Single endpoint latency
```bash
# Start the API, then measure:
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:5000/prices/1/latest
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:5000/trading/status/1/1
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:5000/account/1/trades
```

### Test 2: Query execution plans
```sql
-- Run in MariaDB console before and after:
EXPLAIN SELECT * FROM prices WHERE asset_id = 1 ORDER BY timestamp DESC LIMIT 1;
EXPLAIN SELECT * FROM trades WHERE account_id = 1 AND asset_id = 1 ORDER BY timestamp DESC;
```
Look for `type: ALL` (bad, full scan) changing to `type: ref` or `type: range` (good, index used).

### Test 3: Bulk data stress test
```sql
-- Insert 10,000 dummy price rows, then re-run Test 1 and Test 2
-- This makes the difference between indexed and unindexed much more visible
```

### Results (fill in after testing)

| Test | Endpoint | Before (ms) | After (ms) | Improvement |
|------|----------|-------------|------------|-------------|
| 1 | `/prices/1/latest` | | | |
| 1 | `/trading/status/1/1` | | | |
| 1 | `/account/1/trades` | | | |
| 2 | EXPLAIN prices query | type: | type: | |
| 2 | EXPLAIN trades query | type: | type: | |

---

## Other Bottlenecks Identified (not in scope for this fix)

| Issue | Impact | Fix |
|-------|--------|-----|
| **No connection pooling** — `db.py` opens a new MariaDB connection per query call | 1-5ms overhead per call | Use `mariadb.ConnectionPool` or SQLAlchemy pool |
| **Portfolio N+1 queries** — WPF calls `/prices/{id}/latest` once per asset held | Extra round trips | Add a batch endpoint like `/prices/latest?ids=1,2,3` |
| **Seed inserts one row at a time** — 450 individual INSERTs | Slow initial setup | Use batch INSERT with multiple value tuples |

These are documented for future optimization but not required for v0.1.0.
