"""
tests/benchmarks/test_function_benchmarks.py
================================================

Per-function performance benchmarks using pytest-benchmark.

Measures the execution time of individual functions across all modules.
Results are grouped by module so you can see which areas are fast/slow.

Run:
    pytest tests/benchmarks/test_function_benchmarks.py --benchmark-only -v
    pytest tests/benchmarks/ --benchmark-only --benchmark-json=results.json

Output includes: min, max, mean, median, stddev, rounds, iterations.

NOTE: These benchmarks test the STUB implementations initially. As stubs
get filled in with real logic, the benchmarks will reflect actual performance.
This is intentional — you establish a baseline now, and catch regressions later.
"""

from datetime import datetime, timedelta

from omnium.algorithms import (
    AlgorithmSwitcher,
    MLTradingAlgorithm,
    RuleBasedAlgorithm,
)
from omnium.data import (
    DatabaseManager,
    DataCache,
    DataValidator,
    HistoricalDataLoader,
    LiveMarketFetcher,
)
from omnium.models import (
    Action,
    Portfolio,
    Position,
    Price,
    TradingSignal,
)
from omnium.orchestration import DataPipeline
from omnium.trading import (
    AccountManager,
    OrderExecutor,
    TradeLogger,
)
from omnium.utils import Config, EventBus

# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def make_prices(n: int = 50) -> list[Price]:
    """Generate a list of n dummy Price objects."""
    base_time = datetime.utcnow() - timedelta(minutes=n)
    return [
        Price(
            id=i,
            asset_id=1,
            timestamp=base_time + timedelta(minutes=i),
            open=180.0 + i * 0.1,
            high=181.0 + i * 0.1,
            low=179.0 + i * 0.1,
            close=180.5 + i * 0.1,
            volume=1_000_000 + i * 1000,
        )
        for i in range(n)
    ]


def make_signal() -> TradingSignal:
    """Create a dummy trading signal."""
    return TradingSignal(
        symbol="AAPL",
        action=Action.BUY,
        quantity=10,
        confidence=0.85,
        metadata={"algorithm": "rule_based", "reason": "sma_crossover"},
    )


# ═══════════════════════════════════════════════════════════════════
#  Module: models
# ═══════════════════════════════════════════════════════════════════

class TestModelsBenchmarks:
    """Benchmark core data model operations."""

    def test_price_creation(self, benchmark):
        """How fast can we create Price objects (hot path — happens every tick)."""
        benchmark(
            Price,
            id=1, asset_id=1,
            timestamp=datetime.utcnow(),
            open=180.0, high=181.0, low=179.0, close=180.5,
            volume=1_000_000,
        )

    def test_trading_signal_creation(self, benchmark):
        """TradingSignal creation speed."""
        benchmark(
            TradingSignal,
            symbol="AAPL", action=Action.BUY,
            quantity=10, confidence=0.85,
            metadata={"reason": "test"},
        )

    def test_portfolio_total_value(self, benchmark):
        """Portfolio value calculation with multiple positions."""
        positions = {
            f"SYM{i}": Position(
                symbol=f"SYM{i}", quantity=100,
                avg_cost=150.0 + i, current_price=155.0 + i,
            )
            for i in range(20)
        }
        portfolio = Portfolio(
            account_id=1, cash=50_000.0, positions=positions,
        )
        benchmark(portfolio.total_value)

    def test_position_unrealized_pnl(self, benchmark):
        """Single position P&L calculation."""
        pos = Position(
            symbol="AAPL", quantity=100,
            avg_cost=150.0, current_price=185.0,
        )
        benchmark(pos.unrealized_pnl)


# ═══════════════════════════════════════════════════════════════════
#  Module: data
# ═══════════════════════════════════════════════════════════════════

class TestDataBenchmarks:
    """Benchmark data layer operations."""

    def test_cache_store_and_retrieve(self, benchmark):
        """Cache write + read cycle (should be very fast — in-memory)."""
        cache = DataCache(ttl_seconds=30, max_size=1000)
        price = Price(
            id=1, asset_id=1, timestamp=datetime.utcnow(),
            open=180.0, high=181.0, low=179.0, close=180.5, volume=1_000_000,
        )

        def store_and_get():
            cache.set("prices:AAPL:latest", [price])
            return cache.get_latest_prices("AAPL")

        benchmark(store_and_get)

    def test_data_validator(self, benchmark):
        """Validation speed for a single price record."""
        validator = DataValidator()
        price = Price(
            id=1, asset_id=1, timestamp=datetime.utcnow(),
            open=180.0, high=181.0, low=179.0, close=180.5, volume=1_000_000,
        )
        benchmark(validator.validate_price, price)

    def test_data_pipeline_get_prices(self, benchmark):
        """DataPipeline.get_prices() — cache lookup path."""
        config = Config()
        db = DatabaseManager(config.db_connection_string)
        validator = DataValidator()
        cache = DataCache(ttl_seconds=30, max_size=1000)
        historical = HistoricalDataLoader(db=db, validator=validator)
        live = LiveMarketFetcher(db=db, validator=validator)
        pipeline = DataPipeline(
            live_fetcher=live, historical_loader=historical, cache=cache,
        )
        # Note: cache is a stub — get_prices will exercise the lookup path
        # but return empty. Once cache is implemented, this benchmark
        # measures real cache performance.
        benchmark(pipeline.get_prices, "AAPL", 50)


# ═══════════════════════════════════════════════════════════════════
#  Module: algorithms
# ═══════════════════════════════════════════════════════════════════

class TestAlgorithmBenchmarks:
    """Benchmark algorithm analysis speed."""

    def test_rule_based_analyze(self, benchmark):
        """RuleBasedAlgorithm.analyze() with 50-bar window."""
        algo = RuleBasedAlgorithm()
        prices = make_prices(50)
        benchmark(algo.analyze, prices)

    def test_ml_based_analyze(self, benchmark):
        """MLTradingAlgorithm.analyze() with 50-bar window."""
        algo = MLTradingAlgorithm()
        prices = make_prices(50)
        benchmark(algo.analyze, prices)

    def test_algorithm_switcher_routing(self, benchmark):
        """AlgorithmSwitcher routing overhead (delegation cost)."""
        switcher = AlgorithmSwitcher()
        switcher.register("rule_based", RuleBasedAlgorithm())
        switcher.register("ml_based", MLTradingAlgorithm())
        switcher.switch_to("rule_based")
        prices = make_prices(50)
        benchmark(switcher.analyze, prices)


# ═══════════════════════════════════════════════════════════════════
#  Module: trading
# ═══════════════════════════════════════════════════════════════════

class TestTradingBenchmarks:
    """Benchmark trading engine operations."""

    def test_order_executor_execute(self, benchmark):
        """OrderExecutor.execute() — full order processing."""
        config = Config()
        db = DatabaseManager(config.db_connection_string)
        account_mgr = AccountManager(db=db)
        account_mgr.create_account(
            account_type="paper", starting_cash=100_000.0,
        )
        executor = OrderExecutor(
            account_manager=account_mgr, max_position_pct=0.2,
        )
        signal = make_signal()
        benchmark(executor.execute, signal)

    def test_trade_logger_log_signal(self, benchmark):
        """TradeLogger.log_signal() — signal recording speed."""
        config = Config()
        db = DatabaseManager(config.db_connection_string)
        logger = TradeLogger(db=db)
        signal = make_signal()
        benchmark(logger.log_signal, signal)


# ═══════════════════════════════════════════════════════════════════
#  Module: utils
# ═══════════════════════════════════════════════════════════════════

class TestUtilsBenchmarks:
    """Benchmark utility operations."""

    def test_event_bus_emit(self, benchmark):
        """EventBus.emit() with 5 subscribers (fan-out cost)."""
        bus = EventBus()
        received = []
        for _ in range(5):
            bus.subscribe("price_updated", lambda data: received.append(data))

        benchmark(
            bus.emit, "price_updated",
            {"symbol": "AAPL", "price": 185.42},
        )

    def test_event_bus_emit_no_subscribers(self, benchmark):
        """EventBus.emit() with no subscribers (baseline overhead)."""
        bus = EventBus()
        benchmark(
            bus.emit, "price_updated",
            {"symbol": "AAPL", "price": 185.42},
        )

    def test_config_creation(self, benchmark):
        """Config object creation (env var parsing)."""
        benchmark(Config)
