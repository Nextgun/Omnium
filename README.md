# Omnium — Day Trading Platform

> Automated day-trading system with rule-based and ML-driven algorithms, paper trading, and a real-time dashboard.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│                                                              │
│  LiveMarketFetcher ──→ on_price_update() ──→ Algorithm       │
│                              │                    │          │
│                        DataPipeline          AlgorithmSwitcher│
│                       (cache → DB)          (CS ←→ ML)       │
│                              │                    │          │
│                        OrderExecutor ←──── TradingSignal     │
│                              │                               │
│                    PaperTradingAccount                        │
│                              │                               │
│                        TradeLogger ──→ DB                    │
│                              │                               │
│                         EventBus ──→ Dashboard UI            │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure

```
omnium/                          ← repo root
├── src/
│   └── omnium/                  ← Python package (what gets shipped)
│       ├── __init__.py
│       ├── __main__.py          # Entry point (python -m omnium)
│       ├── models/              # Price, Trade, TradingSignal, Portfolio
│       ├── data/                # DatabaseManager, DataValidator, Cache,
│       │                        # HistoricalDataLoader, LiveMarketFetcher
│       ├── algorithms/          # BaseTradingAlgorithm, RuleBasedAlgorithm,
│       │                        # MLTradingAlgorithm, AlgorithmSwitcher
│       ├── trading/             # TradingAccount, PaperTradingAccount,
│       │                        # OrderExecutor, TradeLogger, AccountManager
│       ├── orchestration/       # Orchestrator, DataPipeline, Scheduler (IMPL)
│       └── utils/               # EventBus, Config, setup_logging
├── devtools/                    ← developer setup utilities (NOT shipped)
│   ├── utils/
│   │   ├── conda.py             # Miniconda installation & env management
│   │   ├── plantuml.py          # PlantUML jar download & rendering
│   │   ├── git_hooks.py         # Pre-commit hook management
│   │   └── vscode.py            # VS Code extension installation
│   ├── watcher.py               # Auto-render .puml files on change
│   └── render_changed_puml.py   # Git hook: render staged .puml files
├── tests/
│   ├── test_integration.py      # Full pipeline integration tests
│   ├── benchmarks/
│   │   ├── test_function_benchmarks.py   # Per-function speed tests
│   │   └── test_pipeline_benchmarks.py   # End-to-end scenario benchmarks
│   └── devtools/                # Tests for developer setup utilities
├── config/
│   └── .env.example             # Environment variable template
├── .github/
│   └── workflows/
│       └── pr-checks.yml        # CI: lint → test → SonarQube on every PR
├── setup_dev.py                 # Run this first after cloning
├── pyproject.toml               # Package config, pytest, ruff settings
├── requirements.txt             # All dependencies (dev + app)
├── sonar-project.properties     # SonarQube configuration
└── README.md
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/omnium.git
cd omnium

# 2. Run the developer setup (installs everything)
python setup_dev.py

# 3. Activate the environment
conda activate omnium-dev

# 4. Verify everything works
pytest

# 5. Run the app
python -m omnium
```

### What `setup_dev.py` Does

The setup script is idempotent — safe to run multiple times. It:

1. Installs Miniconda (if not already installed)
2. Creates the `omnium-dev` conda environment with Python 3.11
3. Installs all dependencies from `requirements.txt`
4. Installs the `omnium` package in editable mode (`pip install -e .`)
5. Downloads the PlantUML jar to `lib/`
6. Installs a git pre-commit hook that:
   - Re-renders any staged `.puml` files
   - Lints staged Python files with `ruff`
7. Installs recommended VS Code extensions

## Testing

```bash
# Run all tests
pytest

# Run only integration tests
pytest tests/test_integration.py -v

# Run only benchmarks
pytest tests/benchmarks/ --benchmark-only -v

# Run benchmarks grouped by scenario
pytest tests/benchmarks/ --benchmark-only --benchmark-group-by=group -v

# Run benchmarks and save results to JSON
pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark-results.json

# Run tests with coverage report
pytest --cov=omnium --cov-report=html
```

### Benchmark Types

**Function Benchmarks** (`test_function_benchmarks.py`):
Measures individual function speed across all modules — Price creation,
cache lookups, algorithm analysis, order execution, EventBus fan-out, etc.

**Pipeline Benchmarks** (`test_pipeline_benchmarks.py`):
Measures complete operational scenarios end-to-end:
- **Tick → Signal**: Price tick arrives → algorithm produces signal
- **Signal → Trade**: Signal qualifies → order executed → trade logged
- **Full Hot Path**: Complete cycle from tick to logged trade
- **Portfolio Snapshot**: Periodic snapshot cycle
- **Multi-Symbol Burst**: 10 symbols updating simultaneously

## Linting

```bash
# Check for issues
ruff check src/ tests/ devtools/

# Auto-fix what's possible
ruff check --fix src/ tests/ devtools/

# Format code (optional)
ruff format src/ tests/ devtools/
```

Ruff configuration is in `pyproject.toml` under `[tool.ruff]`.

## CI/CD Pipeline

On every Pull Request to `main` or `develop`:

1. **Lint** — `ruff check` catches syntax/import/style issues
2. **Test** — Full test suite with coverage report
3. **Benchmark** — Performance tests (non-blocking)
4. **SonarQube** — Code quality analysis on `bane.tamucc.edu:9000`

SonarQube requires `SONAR_TOKEN` and `SONAR_HOST_URL` in GitHub repo secrets.

## How to Fill In a Stub

Every stub module has the interface fully defined: method signatures, type
hints, docstrings with step-by-step TODOs, and a `⚠️ STUB` log warning.

```python
# BEFORE (stub):
def connect(self) -> None:
    log.warning("⚠️  STUB DatabaseManager.connect()")

# AFTER (implemented):
def connect(self) -> None:
    self._engine = create_engine(self._connection_string, pool_size=5)
    self._session_factory = scoped_session(sessionmaker(bind=self._engine))
    log.info("Database connected: %s", self._connection_string)
```

Workflow:
1. Open the stub file (e.g., `src/omnium/data/__init__.py`)
2. Find the method (look for `⚠️ STUB`)
3. Read the docstring — it describes what the method should do
4. Read the TODO comments — they give step-by-step instructions
5. Replace the TODO block with your implementation
6. Remove the STUB log warning
7. Run `pytest` to verify the integration tests still pass

## PlantUML Diagrams

```bash
# Watch for .puml changes and auto-render
python devtools/watcher.py --watch-dir . --jar lib/plantuml.jar

# Manual render
java -jar lib/plantuml.jar path/to/diagram.puml
```

## Environment Variables

Copy `config/.env.example` to `.env` at the repo root and fill in your values.
See the file for all available settings (database, API keys, trading config).
