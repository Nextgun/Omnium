"""
tests/test_integration.py — Full Pipeline Integration Test
=============================================================

This test runs the entire Omnium pipeline end-to-end using STUBS.
As each real component replaces a stub, this test keeps passing.
If someone's implementation breaks the contract, this catches it.

Run:
    pytest tests/ -v
    pytest tests/test_integration.py -v -s   # with print output
"""

from datetime import datetime, timedelta

import pytest

from omnium.algorithms import (
    AlgorithmSwitcher,
    MLTradingAlgorithm,
    RuleBasedAlgorithm,
)
from omnium.data import (
    DatabaseManager,
)
from omnium.models import (
    Action,
    Portfolio,
    Position,
    Price,
    Side,
    Trade,
    TradeResult,
    TradingSignal,
)
from omnium.orchestration import Orchestrator, Scheduler
from omnium.trading import (
    AccountManager,
    OrderExecutor,
    PaperTradingAccount,
)
from omnium.utils import Config, EventBus

# ═══════════════════════════════════════════════════════════════════
#  Helpers — Fake data generators
# ═══════════════════════════════════════════════════════════════════

def make_price(
    asset_id: int = 1,
    close: float = 185.0,
    minutes_ago: int = 0,
) -> Price:
    """Create a dummy Price object for testing."""
    ts = datetime.utcnow() - timedelta(minutes=minutes_ago)
    return Price(
        id=None,
        asset_id=asset_id,
        timestamp=ts,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=100_000,
    )


def make_prices(n: int = 50, base_price: float = 180.0) -> list[Price]:
    """Generate a list of n prices with slight uptrend."""
    return [
        make_price(close=base_price + i * 0.1, minutes_ago=n - i)
        for i in range(n)
    ]


# ═══════════════════════════════════════════════════════════════════
#  SECTION 1: Model Tests (These work NOW, no stubs involved)
# ═══════════════════════════════════════════════════════════════════

class TestModels:
    """Tests for the shared data models — these should always pass."""

    def test_price_is_bullish(self):
        p = make_price(close=185.0)
        # open is close - 0.5 = 184.5, so close > open = bullish
        assert p.is_bullish is True

    def test_price_body_size(self):
        p = make_price(close=185.0)
        assert p.body_size == pytest.approx(0.5)

    def test_trading_signal_validation(self):
        sig = TradingSignal(symbol="AAPL", action=Action.BUY, quantity=10, confidence=0.85)
        assert sig.confidence == 0.85
        assert sig.action == Action.BUY

    def test_trading_signal_rejects_bad_confidence(self):
        with pytest.raises(ValueError, match="Confidence"):
            TradingSignal(symbol="AAPL", action=Action.BUY, quantity=10, confidence=1.5)

    def test_trading_signal_rejects_negative_quantity(self):
        with pytest.raises(ValueError, match="Quantity"):
            TradingSignal(symbol="AAPL", action=Action.BUY, quantity=-5, confidence=0.5)

    def test_position_unrealized_pnl(self):
        pos = Position(symbol="AAPL", quantity=10, avg_cost=180.0, current_price=190.0)
        assert pos.unrealized_pnl() == pytest.approx(100.0)

    def test_position_market_value(self):
        pos = Position(symbol="AAPL", quantity=10, avg_cost=180.0, current_price=190.0)
        assert pos.market_value() == pytest.approx(1900.0)

    def test_portfolio_total_value(self):
        portfolio = Portfolio(
            account_id=1,
            positions={
                "AAPL": Position("AAPL", 10, 180.0, 190.0),
                "TSLA": Position("TSLA", 5, 200.0, 210.0),
            },
            cash=50_000.0,
        )
        # 10*190 + 5*210 + 50000 = 1900 + 1050 + 50000 = 52950
        assert portfolio.total_value() == pytest.approx(52_950.0)

    def test_portfolio_unrealized_pnl(self):
        portfolio = Portfolio(
            account_id=1,
            positions={
                "AAPL": Position("AAPL", 10, 180.0, 190.0),  # +100
                "TSLA": Position("TSLA", 5, 200.0, 195.0),   # -25
            },
            cash=50_000.0,
        )
        assert portfolio.unrealized_pnl() == pytest.approx(75.0)

    def test_trade_total_cost(self):
        trade = Trade(
            id=None, account_id=1, asset_id=1,
            side=Side.BUY, quantity=10, price=185.0,
        )
        assert trade.total_cost == pytest.approx(1850.0)


# ═══════════════════════════════════════════════════════════════════
#  SECTION 2: EventBus Tests (Fully implemented, should pass)
# ═══════════════════════════════════════════════════════════════════

class TestEventBus:
    """Tests for the event bus — this is fully implemented."""

    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda e: received.append(e))
        bus.emit("test_event", {"value": 42})
        assert len(received) == 1
        assert received[0].data["value"] == 42

    def test_multiple_subscribers(self):
        bus = EventBus()
        results = []
        bus.subscribe("evt", lambda e: results.append("a"))
        bus.subscribe("evt", lambda e: results.append("b"))
        bus.emit("evt")
        assert results == ["a", "b"]

    def test_unsubscribe(self):
        bus = EventBus()
        results = []
        cb = lambda e: results.append("hit")
        bus.subscribe("evt", cb)
        bus.unsubscribe("evt", cb)
        bus.emit("evt")
        assert results == []

    def test_error_in_subscriber_doesnt_break_others(self):
        bus = EventBus()
        results = []
        bus.subscribe("evt", lambda e: 1 / 0)  # Raises ZeroDivisionError
        bus.subscribe("evt", lambda e: results.append("survived"))
        bus.emit("evt")
        assert results == ["survived"]

    def test_emit_unknown_event_is_safe(self):
        bus = EventBus()
        bus.emit("nonexistent_event")  # Should not raise


# ═══════════════════════════════════════════════════════════════════
#  SECTION 3: Algorithm Switcher Tests (Fully implemented)
# ═══════════════════════════════════════════════════════════════════

class TestAlgorithmSwitcher:
    """Tests for algorithm registration and switching."""

    def test_register_first_algorithm_activates_it(self):
        switcher = AlgorithmSwitcher()
        algo = RuleBasedAlgorithm()
        switcher.register("rule_based", algo)
        assert switcher.get_active() is algo

    def test_switch_to_different_algorithm(self):
        switcher = AlgorithmSwitcher()
        rb = RuleBasedAlgorithm()
        ml = MLTradingAlgorithm()
        switcher.register("rule_based", rb)
        switcher.register("ml_based", ml)
        switcher.switch_to("ml_based")
        assert switcher.get_active() is ml

    def test_switch_to_unknown_raises(self):
        switcher = AlgorithmSwitcher()
        switcher.register("rule_based", RuleBasedAlgorithm())
        with pytest.raises(KeyError, match="not registered"):
            switcher.switch_to("deep_learning")

    def test_list_available(self):
        switcher = AlgorithmSwitcher()
        switcher.register("rule_based", RuleBasedAlgorithm())
        switcher.register("ml_based", MLTradingAlgorithm())
        available = switcher.list_available()
        assert "rule_based" in available
        assert "ml_based" in available

    def test_analyze_delegates_to_active(self):
        switcher = AlgorithmSwitcher()
        switcher.register("rule_based", RuleBasedAlgorithm())
        prices = make_prices(50)
        signal = switcher.analyze(prices)
        # Stub returns HOLD
        assert isinstance(signal, TradingSignal)
        assert signal.action == Action.HOLD


# ═══════════════════════════════════════════════════════════════════
#  SECTION 4: Account & Executor Tests (Stub behavior)
# ═══════════════════════════════════════════════════════════════════

class TestPaperAccount:
    """Tests for PaperTradingAccount — stub behavior for now."""

    def test_initial_cash_balance(self):
        account = PaperTradingAccount(starting_cash=100_000.0)
        assert account.get_cash_balance() == pytest.approx(100_000.0)

    def test_execute_trade_returns_trade_result(self):
        account = PaperTradingAccount()
        signal = TradingSignal(
            symbol="AAPL", action=Action.BUY, quantity=10, confidence=0.9,
        )
        result = account.execute_trade(signal)
        assert isinstance(result, TradeResult)
        # Stub always returns success
        assert result.success is True

    def test_get_positions_returns_dict(self):
        account = PaperTradingAccount()
        positions = account.get_positions()
        assert isinstance(positions, dict)


class TestOrderExecutor:
    """Tests for OrderExecutor — routing and HOLD handling."""

    def _make_executor(self):
        db = DatabaseManager("stub://")
        mgr = AccountManager(db=db)
        mgr.create_account(account_type="paper", starting_cash=100_000.0)
        return OrderExecutor(account_manager=mgr)

    def test_hold_signal_returns_success_no_action(self):
        executor = self._make_executor()
        signal = TradingSignal(
            symbol="AAPL", action=Action.HOLD, quantity=0, confidence=0.0,
        )
        result = executor.execute(signal)
        assert result.success is True
        assert "HOLD" in result.error_message

    def test_buy_signal_delegates_to_account(self):
        executor = self._make_executor()
        signal = TradingSignal(
            symbol="AAPL", action=Action.BUY, quantity=10, confidence=0.9,
        )
        result = executor.execute(signal)
        assert isinstance(result, TradeResult)


# ═══════════════════════════════════════════════════════════════════
#  SECTION 5: Full Pipeline Integration (end-to-end with stubs)
# ═══════════════════════════════════════════════════════════════════

class TestFullPipeline:
    """
    End-to-end integration test.

    Boots the Orchestrator with default config and simulates a price tick
    flowing through the entire system. With all stubs, the algorithm returns
    HOLD and no trade executes — but the wiring is validated.

    As real components replace stubs, this test keeps passing. If someone's
    implementation breaks the contract (e.g. wrong return type), this fails.
    """

    def test_orchestrator_initializes(self):
        config = Config()
        orch = Orchestrator(config)
        assert orch.is_running is False

    def test_orchestrator_start_and_stop(self):
        config = Config()
        orch = Orchestrator(config)
        orch.start()
        assert orch.is_running is True
        orch.stop()
        assert orch.is_running is False

    def test_price_update_flows_through_pipeline(self):
        """Simulate a price tick and verify events fire."""
        config = Config()
        orch = Orchestrator(config)
        orch.start()

        # Track emitted events
        events_received = []
        orch.event_bus.subscribe("price_updated", lambda e: events_received.append(e))
        orch.event_bus.subscribe("signal_generated", lambda e: events_received.append(e))

        # Simulate a price tick
        price = make_price(close=185.0)
        orch.on_price_update(price)

        orch.stop()

        # We should have received at least a price_updated event
        event_names = [e.name for e in events_received]
        assert "price_updated" in event_names

    def test_algorithm_switching_during_runtime(self):
        config = Config()
        orch = Orchestrator(config)
        orch.start()

        assert orch.algorithm_switcher.get_active().get_name() == "rule_based"
        orch.algorithm_switcher.switch_to("ml_based")
        assert orch.algorithm_switcher.get_active().get_name() == "ml_based"

        orch.stop()

    def test_portfolio_accessible(self):
        config = Config()
        orch = Orchestrator(config)
        orch.start()

        portfolio = orch.account_manager.get_portfolio("paper")
        assert portfolio.cash == pytest.approx(100_000.0)
        assert portfolio.total_value() == pytest.approx(100_000.0)

        orch.stop()


# ═══════════════════════════════════════════════════════════════════
#  SECTION 6: Scheduler Tests (Fully implemented)
# ═══════════════════════════════════════════════════════════════════

class TestScheduler:
    """Tests for the Scheduler."""

    def test_schedule_recurring_returns_id(self):
        scheduler = Scheduler()
        job_id = scheduler.schedule_recurring(lambda: None, 60, name="test")
        assert isinstance(job_id, int)
        assert job_id > 0

    def test_cancel_job(self):
        scheduler = Scheduler()
        job_id = scheduler.schedule_recurring(lambda: None, 60, name="test")
        scheduler.cancel(job_id)
        # Job should be marked inactive
        for job in scheduler._jobs:
            if job.id == job_id:
                assert job.is_active is False

    def test_start_and_stop(self):
        scheduler = Scheduler()
        scheduler.schedule_recurring(lambda: None, 60)
        scheduler.start()
        assert scheduler._running is True
        scheduler.stop()
        assert scheduler._running is False


# ═══════════════════════════════════════════════════════════════════
#  SECTION 7: Config Tests
# ═══════════════════════════════════════════════════════════════════

class TestConfig:
    """Tests for the configuration system."""

    def test_default_values(self):
        config = Config()
        assert config.starting_cash == 100_000.0
        assert config.account_type == "paper"
        assert config.active_algorithm == "rule_based"
        assert "AAPL" in config.tracked_symbols

    def test_db_connection_string(self):
        config = Config()
        assert config.db_connection_string.startswith("postgresql://")
