# Lessons Learned — Omnium Project

Documenting what we learned building this project so future teams (and future us) can benefit.

---

## Database Optimization

### Indexes: What They Are and Why They Matter

Without indexes, every query does a **full table scan** — the database reads every single row
to find matches. With 30 stocks and 30 days of price history each, that's ~900 rows in `prices`.
Sounds small, but every API call (price lookup, trade history, position calculation) triggers
a scan, and the UI auto-refreshes every 10 seconds hitting multiple endpoints.

An **index** is like a book's table of contents. Instead of reading every page to find a topic,
you look it up in the index and jump straight to the right page. The database builds a sorted
data structure (usually a B-tree) on the indexed columns so lookups go from O(n) to O(log n).

**Trade-off:** indexes speed up reads but slightly slow down writes (the index must be updated
on every INSERT/UPDATE). For our app, reads vastly outnumber writes, so this is a clear win.

**What we should have added from the start:**

```sql
-- Fast symbol lookups (search, get_asset_by_symbol)
CREATE INDEX idx_assets_symbol ON assets(symbol);

-- Fast price queries (get_latest_price, get_price_history)
-- Composite index on (asset_id, timestamp) covers both filtering and sorting
CREATE INDEX idx_prices_asset_timestamp ON prices(asset_id, timestamp DESC);

-- Fast trade queries (get_trades, get_trades_for_asset, get_position)
CREATE INDEX idx_trades_account_asset ON trades(account_id, asset_id);
CREATE INDEX idx_trades_account_timestamp ON trades(account_id, timestamp DESC);
```

**Key concept — composite indexes:** `idx_prices_asset_timestamp` covers queries that filter
by `asset_id` AND sort by `timestamp` in a single index. The database walks the index to the
right `asset_id`, then reads timestamps in order without a separate sort step. Column order
matters: the most selective filter (asset_id) goes first.

### Connection Pooling: Reuse Instead of Recreate

Our original `db.py` opens a brand new database connection for every single function call,
then closes it when done. Opening a connection involves TCP handshake, authentication, and
session setup — typically 5-20ms each time. With the UI refreshing every 10 seconds and
hitting 3-4 endpoints per refresh, that's 12-16 unnecessary connection setups per cycle.

**Connection pooling** keeps a set of open connections ready to use. When a function needs
a connection, it borrows one from the pool. When it's done, it returns it instead of closing it.

```python
# Before: new connection every call (~10-20ms overhead each time)
def _get_connection():
    return mariadb.connect(**DB_CONFIG)

# After: borrow from pool (~0ms overhead)
pool = mariadb.ConnectionPool(pool_name="omnium", pool_size=5, **DB_CONFIG)

def _get_connection():
    return pool.get_connection()
```

The rest of the code doesn't change — `conn.close()` just returns the connection to the pool
instead of destroying it. MariaDB's Python connector handles this natively.

**Rule of thumb:** if your app makes more than a few DB calls per second, use pooling.

---

## Architecture & Design Patterns

### Strategy Pattern for Algorithm Switching

The `AlgorithmSwitcher` lets us swap between CS (mean-reversion) and ML (linear regression)
algorithms at runtime without changing any calling code. Both algorithms expose the same
interface (`decide()`, `update_config()`), so the switcher just routes to whichever is active.

**Lesson:** When you have multiple implementations of the same behavior, define a common
interface first. Adding a third algorithm later becomes trivial — just implement `decide()`
and register it in the switcher.

### Dual-Return Tuples Instead of Exceptions

Auth and email functions return `(bool, str)` — success flag and a human-readable message —
instead of raising exceptions. This makes error handling uniform and explicit:

```python
success, message = auth.login(username, password)
if not success:
    return jsonify({"error": message}), 401
```

**Lesson:** For expected failure cases (wrong password, duplicate username), return values
are cleaner than exceptions. Save exceptions for truly unexpected errors (DB down, network
failure).

### Graceful Degradation in Dev Mode

The email service checks for Gmail credentials on startup. If they're missing, it doesn't
crash — it generates verification codes and logs them to console instead of sending emails.
Production and development use the same code path; only the delivery mechanism differs.

**Lesson:** External dependencies (email, payment, SMS) should have a dev-mode fallback
so the team can work without configuring every service locally.

---

## Security

### Account Lockout with Database-Backed State

Lockout state (failed attempts, lockout expiration) is stored in the database, not in memory.
This means lockouts survive server restarts — an attacker can't just wait for a redeploy to
reset their attempts.

**Lesson:** Security state that matters (rate limits, lockouts, sessions) should be persisted.
In-memory state only works for single-process dev servers.

### Password Hashing with bcrypt

Passwords are hashed with bcrypt before storage. The `check_password` function compares
against the hash, never the plaintext. Even if the database is compromised, passwords
aren't exposed.

**Lesson:** Never store plaintext passwords. Use bcrypt (or argon2) — not SHA256 or MD5,
which are fast hashes designed for data integrity, not password storage.

---

## Frontend / UI

### Modal Login as App Gatekeeper

The WPF app sets `ShutdownMode = OnExplicitShutdown` before showing the login dialog.
If login fails, the app shuts down — the main window never gets created. This guarantees
no UI code runs without authentication.

**Lesson:** Authentication gates should be enforced at the app entry point, not inside
individual screens. One check at the door beats scattered checks everywhere.

### Defensive API Client

`ApiClient.cs` uses a single persistent `HttpClient` with a 10-second timeout and returns
empty collections or null on any network error instead of throwing. This prevents the UI
from crashing when the backend is down.

**Lesson:** UI code that calls external services should always have a fallback. Swallowing
errors trades diagnostic detail for stability — acceptable for a desktop app, but log the
errors somewhere.

### Auto-Refresh with Error Tolerance

The 10-second `DispatcherTimer` wraps all refresh calls in try-catch. If the API is down,
the status bar shows "refresh failed" but the app stays usable with stale data.

**Lesson:** Periodic background tasks should never crash the app. Catch errors, update
status, and try again next cycle.

---

## DevOps & Distribution

### Single-File Executable Packaging

The csproj uses `PublishSingleFile=true` and `SelfContained=true` to produce one .exe
with the .NET 8 runtime embedded. No install wizard, no framework dependency.

**Lesson:** For desktop apps targeting non-technical users, self-contained single-file
builds eliminate "it doesn't work on my machine" problems. The trade-off is a larger
file size (~150MB+).

### Launcher Script with Service Detection

`launch_omnium.bat` checks if MariaDB is running before trying to start it, and searches
multiple conda install locations before falling back to system Python.

**Lesson:** Setup/launch scripts should detect existing state rather than assuming a clean
environment. Different team members will have different setups.

### Version Sync Across Platforms

Version `0.1.0` is hardcoded in three places: the csproj, `__init__.py`, and the launcher.
If any one of these gets out of sync, the About panel shows a different version than the
backend reports.

**Lesson:** Keep version in a single source of truth (e.g., a `VERSION` file) and read it
at build time. Alternatively, document which files need updating and check them in code review.

---

## Code Organization

### Environment Variables with Structured Defaults

The `Config` class centralizes all `os.getenv()` calls with sensible defaults. Other modules
import `Config` instead of reading env vars directly.

**Lesson:** Scattering `os.getenv()` across the codebase makes configuration hard to audit.
A single config module documents what settings exist and what their defaults are.

### Type Hints and Dataclasses for Domain Models

`models/__init__.py` defines `Asset`, `Price`, `Account`, `Trade` as dataclasses with strict
type hints and enums for `Side`, `Action`, `AccountType`.

**Lesson:** Shared vocabulary matters. When every module uses the same `Trade` dataclass
instead of ad-hoc dicts, typos and type mismatches surface at development time, not runtime.

---

## Process

### Pre-Commit Hooks: Good Idea, Bad Timing

We set up ruff linting as a pre-commit hook early on, but disabled it because it blocked
teammates who weren't familiar with the linter. The friction slowed the team down more than
the quality benefit helped.

**Lesson:** Introduce linting gradually. Start with CI checks that warn but don't block,
then upgrade to blocking once the team is comfortable. Or use auto-fix (`ruff check --fix`)
in the hook so it corrects issues silently instead of rejecting commits.

### Git Branch Strategy

Our branch chain (`api-layer → finish-backend → integrate-gui → create-exe → expand-gui →
app-extras`) was linear and cumulative — each branch built on the last. This made merging
simple (just merge the tip) but meant every branch depended on its predecessor.

Meanwhile, teammate feature branches (issue-based like `9-implement-rule-based-...`) diverged
early and were never merged back, leading to duplicated/superseded work.

**Lesson:** Agree on a branching strategy early. Short-lived feature branches merged frequently
into main prevents divergence. Long-lived parallel branches almost always lead to wasted work.
