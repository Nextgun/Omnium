"""
tests/benchmarks/test_pipeline_benchmarks.py
================================================

End-to-End Scenario Benchmarks — Operational Use Cases.

Instead of testing functions A, B, C separately, these tests measure
the full sequential pipeline as it would run in production:

    Scenario 1: Price Tick → Signal
        LiveMarketFetcher delivers tick → DataPipeline builds window →
        Algorithm analyzes → TradingSignal produced

    Scenario 2: Signal → Trade Execution
        TradingSignal → OrderExecutor validates → Account executes →
        TradeLogger records → EventBus notifies

    Scenario 3: Full Hot Path (Tick → Trade → Log)
        Combines Scenarios 1 + 2: the complete path from receiving
        a price tick to having a logged, executed trade.

    Scenario 4: Portfolio Snapshot Cycle
        AccountManager builds portfolio → TradeLogger snapshots →
        EventBus emits portfolio_updated

These benchmarks answer: "How long does an actual operational cycle take?"
as opposed to function benchmarks which answer "How fast is each piece?"

Run:
    pytest tests/benchmarks/test_pipeline_benchmarks.py --benchmark-only -v
    pytest tests/benchmarks/ --benchmark-only --benchmark-group-by=group -v
"""

from datetime import datetime, timedelta
from typing import Any

import pytest

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
#  Shared Setup
# ═══════════════════════════════════════════════════════════════════

def make_prices(n: int = 50) -> list[Price]:
    """Generate n dummy Price objects simulating a price window."""
    base_time = datetime.utcnow() - timedelta(minutes=n)
    return [
        Price(
            id=i, asset_id=1,
            timestamp=base_time + timedelta(minutes=i),
            open=180.0 + i * 0.1,
            high=181.0 + i * 0.1,
            low=179.0 + i * 0.1,
            close=180.5 + i * 0.1,
            volume=1_000_000 + i * 1000,
        )
        for i in range(n)
    ]


def build_system() -> dict[str, Any]:
    """
    Build a complete Omnium system (without starting it).

    Returns a dict of all components, wired together the same way
    the Orchestrator does it — but exposed individually so scenarios
    can measure specific sub-pipelines.
    """
    config = Config()
    event_bus = EventBus()

    # Data layer
    db = DatabaseManager(config.db_connection_string)
    validator = DataValidator()
    cache = DataCache(ttl_seconds=30, max_size=1000)
    historical = HistoricalDataLoader(db=db, validator=validator)
    live = LiveMarketFetcher(db=db, validator=validator)
    pipeline = DataPipeline(
        live_fetcher=live, historical_loader=historical, cache=cache,
    )

    # Algorithm layer
    switcher = AlgorithmSwitcher()
    switcher.register("rule_based", RuleBasedAlgorithm())
    switcher.register("ml_based", MLTradingAlgorithm())
    switcher.switch_to("rule_based")

    # Trading layer
    account_mgr = AccountManager(db=db)
    account_mgr.create_account(account_type="paper", starting_cash=100_000.0)
    executor = OrderExecutor(account_manager=account_mgr, max_position_pct=0.2)
    trade_logger = TradeLogger(db=db)

    # Pre-populate cache with price data
    # NOTE: DataCache is a stub — set() is a no-op until implemented.
    # Once cache is real, this pre-populates it so benchmarks measure
    # the "hot" (cached) path. Until then, benchmarks measure stub overhead.
    prices = make_prices(50)
    cache.set("prices:AAPL:latest", prices)

    return {
        "config": config,
        "event_bus": event_bus,
        "db": db,
        "cache": cache,
        "pipeline": pipeline,
        "switcher": switcher,
        "account_mgr": account_mgr,
        "executor": executor,
        "trade_logger": trade_logger,
    }


# ═══════════════════════════════════════════════════════════════════
#  Scenario 1: Price Tick → Trading Signal
#  Simulates: new price arrives, system analyzes it
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.benchmark(group="scenario-tick-to-signal")
class TestTickToSignal:
    """
    Measures the latency from receiving a price tick to producing
    a trading signal. This is the "thinking" part of the hot path.
    """

    def test_tick_to_signal_rule_based(self, benchmark):
        """Full tick→signal pipeline using rule-based algorithm."""
        system = build_system()
        system["switcher"].switch_to("rule_based")

        def tick_to_signal():
            # 1. DataPipeline fetches price window
            prices = system["pipeline"].get_prices("AAPL", 50)
            # 2. Algorithm produces signal
            signal = system["switcher"].analyze(prices)
            return signal

        result = benchmark(tick_to_signal)
        assert result is not None

    def test_tick_to_signal_ml_based(self, benchmark):
        """Full tick→signal pipeline using ML algorithm."""
        system = build_system()
        system["switcher"].switch_to("ml_based")

        def tick_to_signal():
            prices = system["pipeline"].get_prices("AAPL", 50)
            signal = system["switcher"].analyze(prices)
            return signal

        result = benchmark(tick_to_signal)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════
#  Scenario 2: Trading Signal → Executed Trade
#  Simulates: signal qualifies, gets executed and logged
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.benchmark(group="scenario-signal-to-trade")
class TestSignalToTrade:
    """
    Measures the latency from having a trading signal to completing
    the trade execution, logging, and event emission.
    """

    def test_signal_to_trade_with_logging(self, benchmark):
        """Signal → execute → log trade → log signal → emit events."""
        system = build_system()
        events_received = []
        system["event_bus"].subscribe("trade_executed", lambda d: events_received.append(d))
        system["event_bus"].subscribe("signal_generated", lambda d: events_received.append(d))

        signal = TradingSignal(
            symbol="AAPL", action=Action.BUY,
            quantity=10, confidence=0.85,
            metadata={"algorithm": "rule_based"},
        )

        def signal_to_trade():
            # 1. Log the signal
            system["trade_logger"].log_signal(signal)
            # 2. Execute the trade
            result = system["executor"].execute(signal)
            # 3. Log the trade result
            if result.success and result.trade:
                system["trade_logger"].log_trade(result.trade)
            # 4. Emit events
            system["event_bus"].emit("signal_generated", {
                "symbol": signal.symbol,
                "action": signal.action.value,
                "confidence": signal.confidence,
            })
            system["event_bus"].emit("trade_executed", {
                "symbol": signal.symbol,
                "action": signal.action.value,
            })
            return result

        benchmark(signal_to_trade)


# ═══════════════════════════════════════════════════════════════════
#  Scenario 3: Full Hot Path (Tick → Trade → Log)
#  The complete operational cycle — the most important benchmark
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.benchmark(group="scenario-full-hot-path")
class TestFullHotPath:
    """
    Measures the COMPLETE cycle: price tick arrives → system analyzes →
    decides to trade → executes → logs → emits events.

    This is the single most important performance number. It represents
    the worst-case latency a user would experience per price tick
    when the system decides to act on it.
    """

    def test_full_cycle_buy(self, benchmark):
        """Complete hot path for a BUY decision."""
        system = build_system()
        events = []
        system["event_bus"].subscribe("price_updated", lambda d: events.append(d))
        system["event_bus"].subscribe("signal_generated", lambda d: events.append(d))
        system["event_bus"].subscribe("trade_executed", lambda d: events.append(d))

        new_price = Price(
            id=999, asset_id=1, timestamp=datetime.utcnow(),
            open=195.0, high=196.0, low=194.5, close=195.5,
            volume=2_000_000,
        )

        def full_cycle():
            # 1. Price arrives — emit event
            system["event_bus"].emit("price_updated", {
                "symbol": "AAPL", "price": new_price.close,
            })

            # 2. Cache the new price
            system["cache"].set("prices:AAPL:latest", [new_price])

            # 3. Get price window
            prices = system["pipeline"].get_prices("AAPL", 50)

            # 4. Analyze
            signal = system["switcher"].analyze(prices)

            # 5. Log signal
            system["trade_logger"].log_signal(signal)
            system["event_bus"].emit("signal_generated", {
                "symbol": signal.symbol,
                "action": signal.action.value,
                "confidence": signal.confidence,
            })

            # 6. Execute (if actionable)
            if signal.action != Action.HOLD and signal.confidence >= 0.6:
                result = system["executor"].execute(signal)
                if result.success and result.trade:
                    system["trade_logger"].log_trade(result.trade)
                    system["event_bus"].emit("trade_executed", {
                        "symbol": signal.symbol,
                        "quantity": result.fill_quantity,
                        "price": result.fill_price,
                    })
                return result
            return signal

        benchmark(full_cycle)

    def test_full_cycle_hold(self, benchmark):
        """Complete hot path when algorithm says HOLD (no trade)."""
        system = build_system()

        def full_cycle_hold():
            # Same pipeline but we don't execute (HOLD path)
            prices = system["pipeline"].get_prices("AAPL", 50)
            signal = system["switcher"].analyze(prices)
            system["trade_logger"].log_signal(signal)
            system["event_bus"].emit("signal_generated", {
                "symbol": "AAPL",
                "action": signal.action.value,
                "confidence": signal.confidence,
            })
            # HOLD — no execution
            return signal

        benchmark(full_cycle_hold)


# ═══════════════════════════════════════════════════════════════════
#  Scenario 4: Portfolio Snapshot Cycle
#  Simulates: the periodic snapshot the Scheduler triggers
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.benchmark(group="scenario-portfolio-snapshot")
class TestPortfolioSnapshot:
    """
    Measures the portfolio snapshot cycle that runs every 5 minutes.
    Not on the hot path, but important for system overhead.
    """

    def test_snapshot_cycle(self, benchmark):
        """Build portfolio → calculate value → snapshot → emit event."""
        system = build_system()
        events = []
        system["event_bus"].subscribe("portfolio_updated", lambda d: events.append(d))

        def snapshot_cycle():
            # 1. Get portfolio from account manager
            portfolio = system["account_mgr"].get_portfolio("paper")
            # 2. Calculate total value
            value = portfolio.total_value()
            # 3. Take snapshot
            system["trade_logger"].take_snapshot(portfolio)
            # 4. Emit event
            system["event_bus"].emit("portfolio_updated", {
                "total_value": value,
                "timestamp": datetime.utcnow().isoformat(),
            })
            return value

        benchmark(snapshot_cycle)


# ═══════════════════════════════════════════════════════════════════
#  Scenario 5: Multi-Symbol Tick Burst
#  Simulates: multiple symbols updating in rapid succession
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.benchmark(group="scenario-multi-symbol-burst")
class TestMultiSymbolBurst:
    """
    Measures throughput when multiple symbols fire ticks simultaneously.
    Answers: "Can we handle 10 symbols updating at once?"
    """

    def test_10_symbol_burst(self, benchmark):
        """Process 10 different symbols in sequence (simulated burst)."""
        system = build_system()
        symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN",
                    "META", "NVDA", "JPM", "V", "WMT"]

        # Pre-populate caches for all symbols
        for sym in symbols:
            cache_prices = make_prices(50)
            system["cache"].set(f"prices:{sym}:latest", cache_prices)

        def process_burst():
            results = []
            for sym in symbols:
                prices = system["pipeline"].get_prices(sym, 50)
                signal = system["switcher"].analyze(prices)
                system["trade_logger"].log_signal(signal)
                results.append(signal)
            return results

        result = benchmark(process_burst)
        assert len(result) == 10
