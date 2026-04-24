# Omnium REST API Guide

This document explains what the API is, how to run it, and how to use every
endpoint. No prior Flask knowledge is assumed.

---

## What is this API?

The Omnium API is a **web server** that runs on your computer at
`http://localhost:5000`. It exposes **endpoints** (URLs) that accept HTTP
requests and return JSON data.

Our WPF desktop app (C#) talks to this API to get data from the database.
Instead of the C# app connecting to MariaDB directly, it sends HTTP requests
to the API, and the API handles the database work.

```
WPF Desktop App  ──HTTP request──>  Flask API  ──SQL query──>  MariaDB
                  <──JSON response──           <──rows────────
```

**Why not connect to the DB directly from C#?**
- Keeps all database logic in one place (Python)
- The API can be tested independently with simple tools
- Multiple clients (WPF, web, mobile) can share the same API

---

## Prerequisites

1. **Python 3.11+** installed
2. **MariaDB** installed and running (see `.env.example` for setup steps)
3. **Dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```
4. **`.env` file configured** (copy from `.env.example` and set your DB password)

---

## How to Start the API

From the project root (`Omnium/`), run one of these:

```bash
# Option 1 — simplest
python src/omnium/api.py

# Option 2 — using Flask's built-in runner
flask --app src.omnium.api run

# Option 3 — with auto-reload (restarts when you edit code)
flask --app src.omnium.api run --debug
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
```

The API is now running. Leave this terminal open — it needs to stay running
while you use the API. Press `Ctrl+C` to stop it.

---

## How to Test Endpoints

You do not need the WPF app to test. Use any of these tools:

### Using your browser (GET requests only)
Just paste the URL into your browser's address bar:
```
http://localhost:5000/health
http://localhost:5000/assets/search?q=apple
```

### Using curl (command line)
```bash
# GET request
curl http://localhost:5000/health

# POST request with JSON body
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Pass123"}'
```

### Using Postman or Insomnia (GUI tools)
These are free apps that let you build and send HTTP requests with a visual
interface. Good if you prefer not to use the command line.

### Using Python
```python
import requests

# GET
response = requests.get("http://localhost:5000/assets/search?q=apple")
print(response.json())

# POST
response = requests.post("http://localhost:5000/auth/login", json={
    "username": "testuser",
    "password": "Pass123"
})
print(response.json())
```

---

## Endpoint Reference

Every endpoint returns JSON. Error responses include an `"error"` field.

### Health Check

| | |
|---|---|
| **URL** | `GET /health` |
| **Purpose** | Check if the API is running |
| **Parameters** | None |

**Response:**
```json
{"status": "ok"}
```

---

### Search Assets

| | |
|---|---|
| **URL** | `GET /assets/search?q={query}` |
| **Purpose** | Search stocks by symbol or name |
| **Parameters** | `q` (required) — search term |

**Example:** `GET /assets/search?q=apple`

**Response:**
```json
[
  {"id": 1, "symbol": "AAPL", "name": "Apple Inc."},
  {"id": 15, "symbol": "APLE", "name": "Apple Hospitality REIT Inc."}
]
```

**Errors:**
- `400` — missing `q` parameter

---

### Get Asset by ID

| | |
|---|---|
| **URL** | `GET /assets/{asset_id}` |
| **Purpose** | Get a single asset by its database ID |
| **Parameters** | `asset_id` (in URL) — integer |

**Example:** `GET /assets/1`

**Response:**
```json
{"id": 1, "symbol": "AAPL", "name": "Apple Inc."}
```

**Errors:**
- `404` — asset not found

---

### Get Price History

| | |
|---|---|
| **URL** | `GET /prices/{asset_id}?limit={n}` |
| **Purpose** | Get recent OHLCV price bars for an asset |
| **Parameters** | `asset_id` (in URL) — integer, `limit` (optional, default 30) — number of bars |

**Example:** `GET /prices/1?limit=5`

**Response:**
```json
[
  {
    "id": 150,
    "asset_id": 1,
    "timestamp": "2026-03-24 16:00:00",
    "open": 184.50,
    "high": 186.20,
    "low": 183.80,
    "close": 185.90,
    "volume": 52340000
  }
]
```

---

### Get Latest Price

| | |
|---|---|
| **URL** | `GET /prices/{asset_id}/latest` |
| **Purpose** | Get the most recent price for an asset |
| **Parameters** | `asset_id` (in URL) — integer |

**Example:** `GET /prices/1/latest`

**Response:** Same format as price history, but a single object (not an array).

**Errors:**
- `404` — no price data found

---

### Get Account

| | |
|---|---|
| **URL** | `GET /account/{account_id}` |
| **Purpose** | Get account details (type, cash balance) |
| **Parameters** | `account_id` (in URL) — integer |

**Example:** `GET /account/1`

**Response:**
```json
{
  "id": 1,
  "type": "paper",
  "cash_balance": 100000.00,
  "created_at": "2026-03-20 10:30:00"
}
```

**Errors:**
- `404` — account not found

---

### Get Account Trades

| | |
|---|---|
| **URL** | `GET /account/{account_id}/trades` |
| **Purpose** | Get all trades for an account (newest first) |
| **Parameters** | `account_id` (in URL) — integer |

**Example:** `GET /account/1/trades`

**Response:**
```json
[
  {
    "id": 5,
    "account_id": 1,
    "asset_id": 1,
    "side": "BUY",
    "quantity": 10,
    "price": 185.50,
    "timestamp": "2026-03-24 14:30:00"
  }
]
```

---

### Get Position

| | |
|---|---|
| **URL** | `GET /account/{account_id}/position/{asset_id}` |
| **Purpose** | Get net shares held for a specific asset |
| **Parameters** | `account_id` and `asset_id` (in URL) — integers |

**Example:** `GET /account/1/position/1`

**Response:**
```json
{
  "account_id": 1,
  "asset_id": 1,
  "shares": 10
}
```

---

### Register

| | |
|---|---|
| **URL** | `POST /auth/register` |
| **Purpose** | Create a new user account |
| **Body** | JSON with `username` and `password` |

**Example request body:**
```json
{
  "username": "testuser",
  "password": "MyPass123"
}
```

**Password requirements:**
- At least 6 characters
- At least one uppercase letter
- At least one digit

**Success response (201):**
```json
{
  "success": true,
  "message": "Successfully registered and logged in as testuser"
}
```

**Error response (400):**
```json
{
  "success": false,
  "message": "Password validation failed: Password must contain at least one digit"
}
```

---

### Login

| | |
|---|---|
| **URL** | `POST /auth/login` |
| **Purpose** | Authenticate an existing user |
| **Body** | JSON with `username` and `password` |

**Example request body:**
```json
{
  "username": "testuser",
  "password": "MyPass123"
}
```

**Success response (200):**
```json
{
  "success": true,
  "message": "Successfully logged in as testuser"
}
```

**Error responses (401):**
```json
{
  "success": false,
  "message": "Incorrect password. 2 attempts remaining."
}
```
```json
{
  "success": false,
  "message": "Account locked. Try again in 0m 58s"
}
```

**Lockout rules:**
- 3 failed attempts locks the account for 60 seconds
- Counter resets after successful login or lockout expiry

---

## Common Issues

### "Connection refused" when calling the API
The API server isn't running. Start it with `python src/omnium/api.py`.

### "Connection error" on startup
MariaDB isn't running or your `.env` credentials are wrong. Check:
1. MariaDB service is running
2. `.env` file exists with correct `OMNIUM_DB_PASSWORD`
3. The `omnium_database` database exists (run `schema.sql`)

### "Table doesn't exist" errors
You need to create the tables. Run:
```bash
mysql -u root -p omnium_database < src/omnium/data/schema.sql
```

### POST request returns "415 Unsupported Media Type"
You forgot the `Content-Type: application/json` header. Add it:
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "Pass123"}'
```

### Datetime values look weird in responses
MariaDB returns datetime objects. Flask serializes them as strings like
`"2026-03-24 16:00:00"`. If the WPF app needs a different format, we can
add a custom JSON serializer later.

---

## For C# / WPF Developers

In C#, use `HttpClient` to call the API:

```csharp
using System.Net.Http;
using System.Net.Http.Json;

var client = new HttpClient { BaseAddress = new Uri("http://localhost:5000") };

// GET request
var assets = await client.GetFromJsonAsync<List<Asset>>("/assets/search?q=apple");

// POST request
var loginRequest = new { username = "testuser", password = "Pass123" };
var response = await client.PostAsJsonAsync("/auth/login", loginRequest);
var result = await response.Content.ReadFromJsonAsync<LoginResult>();
```

Make sure the Flask API is running before starting the WPF app.
