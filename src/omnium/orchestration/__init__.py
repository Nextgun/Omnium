"""
omnium.orchestration — The Central Nervous System
====================================================

This is the Orchestrator module — the spine that connects everything.

Unlike other modules (which are stubs), this module is substantially
implemented because it's the integration point. Stub modules plug into
it as they get built.

    Orchestrator  (#15, #17) — Main control loop: data → algorithm → executor
    DataPipeline  (#15)      — Unified interface over live + historical + cache
    Scheduler     (#17)      — Time-based job scheduling (market hours, backfill)

Flow:
    1. LiveMarketFetcher emits a price tick
    2. Orchestrator.on_price_update() receives it
    3. DataPipeline.get_prices() returns a full price window
    4. AlgorithmSwitcher.analyze(prices) returns a TradingSignal
    5. If confidence > threshold → OrderExecutor.execute(signal)
    6. TradeLogger records everything
    7. EventBus notifies the UI
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from omnium.algorithms import AlgorithmSwitcher, MLTradingAlgorithm, RuleBasedAlgorithm
from omnium.data import DatabaseManager, DataCache, HistoricalDataLoader, LiveMarketFetcher
from omnium.models import Action, Price, TradingSignal
from omnium.trading import (
    AccountManager,
    OrderExecutor,
    PaperTradingAccount,
    TradeLogger,
)
from omnium.utils import Config, EventBus

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  DataPipeline — Issue #15 sub-task 15.1
# ═══════════════════════════════════════════════════════════════════

class DataPipeline:
    """
    Unified data interface for the Orchestrator.

    Wraps LiveMarketFetcher + HistoricalDataLoader + DataCache into one
    clean API. The Orchestrator never talks to data sources directly —
    it always goes through the pipeline.

    get_prices(symbol, lookback) → tries cache first, then DB, then API.
    """

    def __init__(
        self,
        live_fetcher: LiveMarketFetcher,
        historical_loader: HistoricalDataLoader,
        cache: DataCache,
    ) -> None:
        self._live_fetcher = live_fetcher
        self._historical_loader = historical_loader
        self._cache = cache
        self._is_live = False
        log.info("DataPipeline initialized")

    def get_prices(self, symbol: str, lookback: int = 50) -> list[Price]:
        """
        Get the most recent `lookback` price bars for a symbol.

        Resolution order:
            1. Check DataCache (fastest)
            2. Fall back to database query
            3. If insufficient data, trigger historical backfill

        Args:
            symbol:   Ticker symbol (e.g. "AAPL")
            lookback: Number of recent bars to return

        Returns:
            List of Price objects, ordered oldest → newest.
            May return fewer than `lookback` if insufficient data exists.
        """
        # Try cache first
        cached = self._cache.get_latest_prices(symbol)
        if cached and len(cached) >= lookback:
            log.debug("DataPipeline: cache hit for '%s' (%d bars)", symbol, len(cached))
            return cached[-lookback:]

        # Cache miss — would query DB here
        log.debug(
            "DataPipeline: cache miss for '%s', would query DB for %d bars",
            symbol, lookback,
        )
        # TODO: Query PriceRepository.get_range() when DB is implemented
        # For now, return whatever cache has (may be empty)
        return cached[-lookback:] if cached else []

    def is_live(self) -> bool:
        """Return True if live data streaming is active."""
        return self._is_live

    def start_live(self, symbols: list[str]) -> None:
        """
        Start live data streaming for the given symbols.

        Connects the LiveMarketFetcher and subscribes to each symbol.
        """
        self._live_fetcher.connect()
        for symbol in symbols:
            self._live_fetcher.subscribe(symbol)
        self._is_live = True
        log.info("DataPipeline: live streaming started for %s", symbols)

    def stop_live(self) -> None:
        """Stop live data streaming."""
        self._live_fetcher.stop_streaming()
        self._is_live = False
        log.info("DataPipeline: live streaming stopped")


# ═══════════════════════════════════════════════════════════════════
#  Scheduler — Issue #17
# ═══════════════════════════════════════════════════════════════════

class ScheduledJob:
    """A single scheduled job with metadata."""

    _next_id = 0

    def __init__(
        self,
        func: Callable,
        interval_seconds: float | None = None,
        run_at: str | None = None,
        name: str = "",
    ) -> None:
        ScheduledJob._next_id += 1
        self.id = ScheduledJob._next_id
        self.func = func
        self.interval_seconds = interval_seconds
        self.run_at = run_at
        self.name = name or func.__qualname__
        self.last_run: datetime | None = None
        self.is_active = True

    def __repr__(self) -> str:
        if self.interval_seconds:
            return f"Job('{self.name}', every {self.interval_seconds}s)"
        return f"Job('{self.name}', at {self.run_at})"


class Scheduler:
    """
    Simple job scheduler for time-based tasks.

    Manages recurring tasks (e.g. "take portfolio snapshot every 5 min")
    and one-time scheduled tasks (e.g. "start streaming at market open").

    Runs in a background thread and checks jobs every second.

    Issue: #17 (Add configurable scheduling)
    Sub-tasks: 17.1 (scheduler class), 17.2 (market hours), 17.3 (nightly backfill)
    """

    def __init__(self, timezone: str = "US/Eastern") -> None:
        self._jobs: list[ScheduledJob] = []
        self._timezone = timezone
        self._running = False
        self._thread: threading.Thread | None = None
        log.info("Scheduler initialized (timezone=%s)", timezone)

    def schedule_recurring(
        self, func: Callable, interval_seconds: float, name: str = "",
    ) -> int:
        """
        Schedule a function to run at a fixed interval.

        Args:
            func:             Callable with no arguments
            interval_seconds: How often to run (in seconds)
            name:             Human-readable name for logging

        Returns:
            Job ID (for cancellation).
        """
        job = ScheduledJob(func=func, interval_seconds=interval_seconds, name=name)
        self._jobs.append(job)
        log.info("Scheduled recurring job: %s (every %.0fs)", job.name, interval_seconds)
        return job.id

    def schedule_at(self, func: Callable, time_str: str, name: str = "") -> int:
        """
        Schedule a function to run at a specific time daily.

        Args:
            func:     Callable with no arguments
            time_str: Time in "HH:MM" format (e.g. "09:30")
            name:     Human-readable name

        Returns:
            Job ID.

        TODO (#17.2):
            - Parse time_str into hour/minute
            - Check against current time each tick
            - Handle timezone conversion
        """
        job = ScheduledJob(func=func, run_at=time_str, name=name)
        self._jobs.append(job)
        log.info("Scheduled daily job: %s (at %s %s)", job.name, time_str, self._timezone)
        return job.id

    def cancel(self, job_id: int) -> None:
        """Cancel a scheduled job by ID."""
        for job in self._jobs:
            if job.id == job_id:
                job.is_active = False
                log.info("Cancelled job #%d: %s", job_id, job.name)
                return
        log.warning("Job #%d not found for cancellation", job_id)

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            log.warning("Scheduler is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="Scheduler")
        self._thread.start()
        log.info("Scheduler started (%d jobs)", len(self._jobs))

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        log.info("Scheduler stopped")

    def _run_loop(self) -> None:
        """
        Background loop that checks and executes due jobs.

        Runs every 1 second. For each active recurring job, checks if
        enough time has passed since the last run. Executes and logs.
        """
        while self._running:
            now = datetime.utcnow()
            for job in self._jobs:
                if not job.is_active:
                    continue
                if job.interval_seconds and self._is_recurring_due(job, now):
                    self._execute_job(job, now)
                # TODO (#17.2): Check time-based jobs (market open/close)
            time.sleep(1)

    def _is_recurring_due(self, job: ScheduledJob, now: datetime) -> bool:
        """Check if a recurring job should run now."""
        if job.last_run is None:
            return True
        elapsed = (now - job.last_run).total_seconds()
        return elapsed >= job.interval_seconds

    def _execute_job(self, job: ScheduledJob, now: datetime) -> None:
        """Execute a job and update its last_run timestamp."""
        try:
            log.debug("Executing job: %s", job.name)
            job.func()
            job.last_run = now
        except Exception:
            log.exception("Error executing job '%s'", job.name)


# ═══════════════════════════════════════════════════════════════════
#  Orchestrator — Issues #15, #17
# ═══════════════════════════════════════════════════════════════════

class Orchestrator:
    """
    The central controller that wires all Omnium components together.

    This is the "main brain" of the system. It:
        1. Receives price ticks from the DataPipeline
        2. Routes price windows to the active algorithm
        3. Filters signals by confidence threshold
        4. Routes qualifying signals to the OrderExecutor
        5. Logs everything via TradeLogger
        6. Emits events via EventBus for the UI

    The Orchestrator does NOT contain business logic for any specific
    module — it only routes data between modules. Each module handles
    its own logic internally.

    Issues: #15 (routing), #17 (scheduling)
    Sub-tasks: 15.1–15.4, 17.1–17.4
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._is_running = False

        # ── Event Bus (shared communication channel) ──
        self.event_bus = EventBus()

        # ── Data Layer ──
        self._db = DatabaseManager(config.db_connection_string)
        validator = DataCache()  # DataValidator would be injected here
        from omnium.data import DataValidator
        self._validator = DataValidator()

        self._cache = DataCache(
            ttl_seconds=config.cache_ttl_seconds,
            max_size=config.cache_max_size,
        )
        self._historical_loader = HistoricalDataLoader(
            db=self._db, validator=self._validator,
        )
        self._live_fetcher = LiveMarketFetcher(
            db=self._db, validator=self._validator,
        )

        # Wire the live fetcher to route ticks through us
        self._live_fetcher.on_price_update(self.on_price_update)

        self._data_pipeline = DataPipeline(
            live_fetcher=self._live_fetcher,
            historical_loader=self._historical_loader,
            cache=self._cache,
        )

        # ── Algorithm Layer ──
        self._algorithm_switcher = AlgorithmSwitcher()
        self._algorithm_switcher.register("rule_based", RuleBasedAlgorithm())
        self._algorithm_switcher.register("ml_based", MLTradingAlgorithm())

        # Set active algorithm from config
        if config.active_algorithm in self._algorithm_switcher.list_available():
            self._algorithm_switcher.switch_to(config.active_algorithm)

        # ── Trading Layer ──
        self._account_manager = AccountManager(db=self._db)
        self._account_manager.create_account(
            account_type=config.account_type,
            starting_cash=config.starting_cash,
            slippage_pct=config.slippage_pct,
            commission=config.commission_per_trade,
        )

        self._order_executor = OrderExecutor(
            account_manager=self._account_manager,
            max_position_pct=config.max_position_pct,
        )

        self._trade_logger = TradeLogger(db=self._db)

        # ── Scheduler ──
        self._scheduler = Scheduler(timezone=config.market_timezone)

        # ── Cooldown tracking ──
        self._last_signal_time: dict[str, datetime] = {}

        log.info(
            "Orchestrator initialized:\n"
            "    Account:    %s ($%.2f)\n"
            "    Algorithm:  %s\n"
            "    Symbols:    %s\n"
            "    Confidence: >= %.0f%%\n"
            "    Cooldown:   %ds",
            config.account_type,
            config.starting_cash,
            config.active_algorithm,
            config.tracked_symbols,
            config.min_confidence_threshold * 100,
            config.trade_cooldown_seconds,
        )

    # ── Public API ──────────────────────────────────────────────

    def start(self) -> None:
        """
        Start the Omnium trading system.

        Sequence:
            1. Connect to database
            2. Start scheduler (background jobs)
            3. Start live data streaming
            4. Enter running state
        """
        if self._is_running:
            log.warning("Orchestrator is already running")
            return

        log.info("═" * 60)
        log.info("  OMNIUM STARTING")
        log.info("═" * 60)

        # 1. Database
        self._db.connect()
        log.info("Step 1/4: Database connected (%s)", "OK" if self._db.health_check() else "FAIL")

        # 2. Scheduler — set up recurring jobs
        self._setup_scheduled_jobs()
        self._scheduler.start()
        log.info("Step 2/4: Scheduler started")

        # 3. Live data
        self._data_pipeline.start_live(self._config.tracked_symbols)
        log.info("Step 3/4: Live data streaming started")

        # 4. Running
        self._is_running = True
        self.event_bus.emit("system_started", {"timestamp": datetime.utcnow().isoformat()})
        log.info("Step 4/4: Orchestrator is RUNNING")
        log.info("═" * 60)

    def stop(self) -> None:
        """
        Gracefully shut down all components.

        Sequence: stop scheduler → stop streaming → take final snapshot → disconnect DB
        """
        if not self._is_running:
            log.warning("Orchestrator is not running")
            return

        log.info("═" * 60)
        log.info("  OMNIUM SHUTTING DOWN")
        log.info("═" * 60)

        self._is_running = False
        self._scheduler.stop()
        self._data_pipeline.stop_live()

        # Final portfolio snapshot
        try:
            portfolio = self._account_manager.get_portfolio(self._config.account_type)
            self._trade_logger.take_snapshot(portfolio)
            log.info("Final portfolio value: $%.2f", portfolio.total_value())
        except Exception:
            log.exception("Failed to take final portfolio snapshot")

        self._db.disconnect()
        self.event_bus.emit("system_stopped", {"timestamp": datetime.utcnow().isoformat()})
        log.info("Orchestrator stopped cleanly")

    def on_price_update(self, price: Price) -> None:
        """
        Callback invoked by LiveMarketFetcher on every new price tick.

        This is the main hot path — called potentially hundreds of times
        per minute during market hours. Keep it fast.

        Flow:
            1. Emit "price_updated" event (for UI)
            2. Get full price window from DataPipeline
            3. Route to algorithm for analysis
            4. Check confidence threshold and cooldown
            5. If qualifying → route to OrderExecutor
            6. Log signal (always) and trade (if executed)
        """
        if not self._is_running:
            return

        symbol = str(price.asset_id)  # TODO: resolve to ticker symbol

        # 1. Notify UI
        self.event_bus.emit("price_updated", {
            "symbol": symbol,
            "price": price.close,
            "timestamp": price.timestamp.isoformat(),
        })

        # 2. Get price window
        prices = self._data_pipeline.get_prices(symbol, self._config.price_lookback)
        if not prices:
            log.debug("No price history for '%s', skipping analysis", symbol)
            return

        # 3. Analyze
        signal = self._route_to_algorithm(prices)

        # 4. Log signal (always — even HOLD signals, for analysis)
        self._trade_logger.log_signal(signal)
        self.event_bus.emit("signal_generated", {
            "symbol": signal.symbol,
            "action": signal.action.value,
            "confidence": signal.confidence,
            "algorithm": self._algorithm_switcher.get_active().get_name(),
        })

        # 5. Check if we should execute
        if signal.action == Action.HOLD:
            return

        if signal.confidence < self._config.min_confidence_threshold:
            log.debug(
                "Signal for '%s' below threshold (%.2f < %.2f), skipping",
                symbol, signal.confidence, self._config.min_confidence_threshold,
            )
            return

        if self._is_on_cooldown(symbol):
            log.debug("Symbol '%s' is on cooldown, skipping", symbol)
            return

        # 6. Execute
        self._route_to_executor(signal)

    # ── Private Methods ─────────────────────────────────────────

    def _route_to_algorithm(self, prices: list[Price]) -> TradingSignal:
        """
        Send price data to the active algorithm and get a signal back.

        Delegates to AlgorithmSwitcher, which transparently routes to
        whichever algorithm is currently active (rule_based or ml_based).
        """
        try:
            signal = self._algorithm_switcher.analyze(prices)
            log.debug(
                "Algorithm '%s' → %s (conf=%.2f)",
                self._algorithm_switcher.get_active().get_name(),
                signal.action.value,
                signal.confidence,
            )
            return signal
        except Exception:
            log.exception("Algorithm analysis failed, returning HOLD")
            return TradingSignal(
                symbol="unknown",
                action=Action.HOLD,
                quantity=0,
                confidence=0.0,
                metadata={"error": "algorithm_exception"},
            )

    def _route_to_executor(self, signal: TradingSignal) -> None:
        """
        Send a qualifying signal to the OrderExecutor for trade execution.

        After execution:
            - Log the trade
            - Take a portfolio snapshot
            - Update cooldown timer
            - Emit events for UI
        """
        log.info(
            "Executing: %s %d × %s (confidence=%.2f)",
            signal.action.value.upper(), signal.quantity, signal.symbol, signal.confidence,
        )

        result = self._order_executor.execute(signal)

        if result.success:
            log.info(
                "Trade filled: %d × %s @ $%.2f (fees=$%.2f)",
                result.fill_quantity, signal.symbol, result.fill_price, result.fees,
            )

            # Log the trade
            if result.trade:
                self._trade_logger.log_trade(result.trade)

            # Snapshot portfolio after trade
            try:
                portfolio = self._account_manager.get_portfolio(self._config.account_type)
                self._trade_logger.take_snapshot(portfolio)
            except Exception:
                log.exception("Failed to snapshot portfolio after trade")

            # Update cooldown
            self._last_signal_time[signal.symbol] = datetime.utcnow()

            # Notify UI
            self.event_bus.emit("trade_executed", {
                "symbol": signal.symbol,
                "action": signal.action.value,
                "quantity": result.fill_quantity,
                "price": result.fill_price,
                "fees": result.fees,
            })
        else:
            log.warning(
                "Trade failed for %s: %s", signal.symbol, result.error_message,
            )
            self.event_bus.emit("trade_failed", {
                "symbol": signal.symbol,
                "reason": result.error_message,
            })

    def _is_on_cooldown(self, symbol: str) -> bool:
        """
        Check if we've traded this symbol too recently.

        Prevents rapid-fire trades on the same symbol from noisy signals.
        """
        if symbol not in self._last_signal_time:
            return False
        elapsed = (datetime.utcnow() - self._last_signal_time[symbol]).total_seconds()
        return elapsed < self._config.trade_cooldown_seconds

    def _setup_scheduled_jobs(self) -> None:
        """
        Register all recurring and time-based jobs with the Scheduler.

        Jobs:
            - Portfolio snapshot every 5 minutes
            - Nightly historical backfill after market close

        TODO (#17.2, #17.3):
            - schedule_at(start_live, market_open)
            - schedule_at(stop_live, market_close)
            - schedule_at(nightly_backfill, "16:30")
        """
        # Snapshot every 5 minutes
        self._scheduler.schedule_recurring(
            func=self._take_periodic_snapshot,
            interval_seconds=300,
            name="portfolio_snapshot",
        )

        # TODO: Add market-hours scheduling (#17.2)
        # self._scheduler.schedule_at(
        #     func=lambda: self._data_pipeline.start_live(self._config.tracked_symbols),
        #     time_str=self._config.market_open,
        #     name="market_open_start_live",
        # )

        log.info("Scheduled jobs registered")

    def _take_periodic_snapshot(self) -> None:
        """Take a portfolio snapshot (called by scheduler)."""
        try:
            portfolio = self._account_manager.get_portfolio(self._config.account_type)
            self._trade_logger.take_snapshot(portfolio)
            log.debug("Periodic snapshot: $%.2f", portfolio.total_value())
        except Exception:
            log.exception("Periodic snapshot failed")

    # ── Accessors for UI / API ──────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def algorithm_switcher(self) -> AlgorithmSwitcher:
        """Expose the AlgorithmSwitcher for the UI to switch algorithms."""
        return self._algorithm_switcher

    @property
    def account_manager(self) -> AccountManager:
        """Expose the AccountManager for the UI to read portfolio data."""
        return self._account_manager

    @property
    def trade_logger(self) -> TradeLogger:
        """Expose the TradeLogger for the UI to query trade history."""
        return self._trade_logger

    @property
    def data_pipeline(self) -> DataPipeline:
        """Expose the DataPipeline for the UI to fetch price data."""
        return self._data_pipeline
