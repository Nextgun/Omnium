"""
omnium.trading — Trading Engine
==================================

Handles order execution, account management, and trade logging.

    TradingAccount     (ABC)  — Shared interface for paper + live accounts (#14)
    PaperTradingAccount (#12) — Simulated execution with fake money
    LiveTradingAccount  (#14) — Future: real broker API integration (stub only)
    AccountManager             — Manages accounts and portfolios
    OrderExecutor       (#16) — Validates and routes orders to accounts
    TradeLogger         (#13) — Records trades, signals, and portfolio snapshots

All classes below are STUBS. Interfaces are final and match the UML.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from omnium.data import DatabaseManager
from omnium.models import (
    Account,
    AccountType,
    Action,
    Portfolio,
    PortfolioSnapshot,
    Position,
    Side,
    Trade,
    TradeResult,
    TradingSignal,
)

log = logging.getLogger(__name__)

_STUB = "⚠️  STUB"


# ═══════════════════════════════════════════════════════════════════
#  TradingAccount — Abstract Interface (#14)
# ═══════════════════════════════════════════════════════════════════

class TradingAccount(ABC):
    """
    Abstract interface shared by PaperTradingAccount and LiveTradingAccount.

    Both account types expose the exact same methods. This means the
    OrderExecutor can route to either one without knowing or caring
    which type it's talking to. Switching from paper to live is a
    config change, not a code change.

    Issue: #14 (Design account interface for future live trading)
    Sub-tasks: 14.1 (abstract interface), 14.4 (factory pattern)
    """

    @abstractmethod
    def execute_trade(self, signal: TradingSignal) -> TradeResult:
        """
        Execute a trade based on a TradingSignal.

        BUY: deduct cash, add/increase position.
        SELL: add cash, reduce/close position.

        Returns:
            TradeResult with success/failure and fill details.
        """
        ...

    @abstractmethod
    def get_portfolio_value(self) -> float:
        """Return total portfolio value (cash + positions)."""
        ...

    @abstractmethod
    def get_positions(self) -> dict[str, Position]:
        """Return all current positions keyed by symbol."""
        ...

    @abstractmethod
    def get_unrealized_pnl(self) -> float:
        """Return total unrealized P&L across all positions."""
        ...

    @abstractmethod
    def get_cash_balance(self) -> float:
        """Return current cash balance."""
        ...


# ═══════════════════════════════════════════════════════════════════
#  PaperTradingAccount — Issue #12
# ═══════════════════════════════════════════════════════════════════

class PaperTradingAccount(TradingAccount):
    """
    Simulated trading account with fake money.

    Executes trades at current market price (+ optional slippage).
    Tracks positions, cash balance, and P&L. No real money moves.

    Issue: #12 (Implement paper trading account logic)
    Sub-tasks: 12.1 (core class), 12.2 (position tracking),
               12.3 (portfolio), 12.4 (validation), 12.5 (slippage/fees)
    """

    def __init__(
        self,
        starting_cash: float = 100_000.0,
        slippage_pct: float = 0.001,
        commission: float = 0.0,
    ) -> None:
        self._cash: float = starting_cash
        self._positions: dict[str, Position] = {}
        self._slippage_pct = slippage_pct
        self._commission = commission
        log.info(
            "%s PaperTradingAccount created (cash=$%.2f, slippage=%.3f%%)",
            _STUB, starting_cash, slippage_pct * 100,
        )

    def execute_trade(self, signal: TradingSignal) -> TradeResult:
        """
        Simulate trade execution.

        BUY flow:
            1. Calculate fill price = market_price * (1 + slippage_pct)
            2. Calculate total cost = fill_price * quantity + commission
            3. Check cash balance >= total cost
            4. Deduct cash
            5. Update position (add shares, recalculate avg cost)
            6. Return TradeResult(success=True)

        SELL flow:
            1. Check we own enough shares
            2. Calculate fill price = market_price * (1 - slippage_pct)
            3. Calculate proceeds = fill_price * quantity - commission
            4. Add proceeds to cash
            5. Reduce position (remove shares, close if quantity = 0)
            6. Return TradeResult(success=True)

        TODO (#12.1, #12.4, #12.5):
            - Implement the full BUY and SELL flows above
            - Handle edge cases: HOLD signal → no-op, insufficient balance,
              selling more than owned, zero quantity

        CURRENT STUB: Returns a successful dummy result.
        """
        log.warning(
            "%s PaperTradingAccount.execute_trade(%s %s × %d) — returning dummy result",
            _STUB, signal.action.value, signal.symbol, signal.quantity,
        )
        return TradeResult(
            success=True,
            fill_price=0.0,
            fill_quantity=signal.quantity,
            fees=0.0,
            trade=None,
            error_message="STUB — no actual execution",
        )

    def get_portfolio_value(self) -> float:
        """
        Total value: cash + sum of all position market values.

        TODO (#12.3):
            - Sum position.market_value() for all positions
            - Add self._cash
        """
        log.warning(
            "%s PaperTradingAccount.get_portfolio_value() — returning cash only", _STUB,
        )
        return self._cash

    def get_positions(self) -> dict[str, Position]:
        """Return all current positions keyed by symbol."""
        return dict(self._positions)

    def get_unrealized_pnl(self) -> float:
        """
        Sum of unrealized P&L across all positions.

        TODO (#12.3): return sum(p.unrealized_pnl() for p in self._positions.values())
        """
        log.warning("%s get_unrealized_pnl() — returning 0.0", _STUB)
        return 0.0

    def get_cash_balance(self) -> float:
        """Return current cash balance."""
        return self._cash


# ═══════════════════════════════════════════════════════════════════
#  LiveTradingAccount — Issue #14 (Stub / Future)
# ═══════════════════════════════════════════════════════════════════

class LiveTradingAccount(TradingAccount):
    """
    PLACEHOLDER for future live broker integration.

    When implemented, this will connect to a real broker API (e.g. Alpaca,
    Interactive Brokers) and execute real orders with real money.

    All methods currently raise NotImplementedError with guidance on
    what needs to be built.

    Issue: #14 sub-task 14.3 (Create LiveTradingAccount stub)
    """

    def __init__(self) -> None:
        log.warning(
            "LiveTradingAccount instantiated — THIS IS A PLACEHOLDER. "
            "Real broker integration is not yet implemented (Issue #14)."
        )

    def execute_trade(self, signal: TradingSignal) -> TradeResult:
        raise NotImplementedError(
            "LiveTradingAccount.execute_trade() is not yet implemented. "
            "Requires broker API client (e.g. Alpaca SDK). See Issue #14."
        )

    def get_portfolio_value(self) -> float:
        raise NotImplementedError("LiveTradingAccount — not yet implemented")

    def get_positions(self) -> dict[str, Position]:
        raise NotImplementedError("LiveTradingAccount — not yet implemented")

    def get_unrealized_pnl(self) -> float:
        raise NotImplementedError("LiveTradingAccount — not yet implemented")

    def get_cash_balance(self) -> float:
        raise NotImplementedError("LiveTradingAccount — not yet implemented")


# ═══════════════════════════════════════════════════════════════════
#  AccountManager
# ═══════════════════════════════════════════════════════════════════

class AccountManager:
    """
    Manages trading accounts and provides portfolio views.

    Uses the Factory pattern: creates the right account type based on config.

    Issue: #14 sub-task 14.4 (Account factory pattern)
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._accounts: dict[str, TradingAccount] = {}
        log.info("%s AccountManager created", _STUB)

    def create_account(
        self,
        account_type: str = "paper",
        starting_cash: float = 100_000.0,
        **kwargs: Any,
    ) -> TradingAccount:
        """
        Factory method — create an account of the specified type.

        Args:
            account_type: "paper" or "live"
            starting_cash: Initial cash balance (paper only)

        Returns:
            A TradingAccount instance (Paper or Live).

        TODO (#14.4):
            - Store created account in self._accounts
            - Persist to DB via Account model
        """
        if account_type == "paper":
            account = PaperTradingAccount(starting_cash=starting_cash, **kwargs)
        elif account_type == "live":
            account = LiveTradingAccount()
        else:
            raise ValueError(f"Unknown account type: {account_type}")

        self._accounts[account_type] = account
        log.info("Created %s account (cash=$%.2f)", account_type, starting_cash)
        return account

    def get_account(self, account_type: str = "paper") -> TradingAccount:
        """
        Retrieve an existing account by type.

        Raises:
            KeyError: If no account of that type exists.
        """
        if account_type not in self._accounts:
            raise KeyError(
                f"No '{account_type}' account exists. Call create_account() first."
            )
        return self._accounts[account_type]

    def get_portfolio(self, account_type: str = "paper") -> Portfolio:
        """
        Build a Portfolio snapshot from the account's current state.

        TODO:
            - Read positions and cash from the account
            - Construct Portfolio dataclass
        """
        account = self.get_account(account_type)
        return Portfolio(
            account_id=0,
            positions=account.get_positions(),
            cash=account.get_cash_balance(),
        )


# ═══════════════════════════════════════════════════════════════════
#  OrderExecutor — Issue #16
# ═══════════════════════════════════════════════════════════════════

class OrderExecutor:
    """
    Validates trading signals and routes them to the appropriate account.

    Acts as a gatekeeper: checks balance, position limits, and symbol
    validity before forwarding to PaperTradingAccount or LiveTradingAccount.

    Issue: #16 (Collect decisions and send orders to trading account module)
    Sub-tasks: 16.1 (executor class), 16.2 (rate limiting),
               16.3 (TradeResult), 16.4 (integration)
    """

    def __init__(
        self,
        account_manager: AccountManager,
        max_position_pct: float = 0.20,
    ) -> None:
        self._account_manager = account_manager
        self._max_position_pct = max_position_pct
        self._last_trade_time: dict[str, datetime] = {}  # symbol → last trade time
        log.info(
            "%s OrderExecutor created (max_position_pct=%.0f%%)",
            _STUB, max_position_pct * 100,
        )

    def execute(self, signal: TradingSignal) -> TradeResult:
        """
        Validate and execute a trading signal.

        Flow:
            1. validate_order(signal) — check all preconditions
            2. If invalid → return TradeResult(success=False)
            3. Get account from AccountManager
            4. account.execute_trade(signal)
            5. Return the TradeResult

        TODO (#16.1):
            - Call validate_order()
            - Route to the correct account type
            - Update self._last_trade_time for cooldown tracking
            - Return TradeResult

        CURRENT STUB: Delegates to account directly without validation.
        """
        if signal.action == Action.HOLD:
            log.debug("OrderExecutor: HOLD signal, skipping execution")
            return TradeResult(success=True, error_message="HOLD — no action")

        log.warning(
            "%s OrderExecutor.execute(%s %s × %d, conf=%.2f) — skipping validation",
            _STUB, signal.action.value, signal.symbol, signal.quantity, signal.confidence,
        )

        try:
            account = self._account_manager.get_account()
            result = account.execute_trade(signal)
            return result
        except Exception as e:
            log.error("OrderExecutor.execute() failed: %s", e)
            return TradeResult(success=False, error_message=str(e))

    def validate_order(self, signal: TradingSignal) -> bool:
        """
        Check all preconditions before allowing a trade.

        Checks:
            1. check_balance() — enough cash for BUY?
            2. check_position_limits() — within concentration limits?
            3. Symbol exists in tracked assets?
            4. Quantity > 0?
            5. Not on cooldown for this symbol?

        TODO (#16.1):
            - Implement each check method
            - Return True only if ALL checks pass
            - Log which check failed if any
        """
        log.warning(
            "%s OrderExecutor.validate_order() — returning True (no checks)", _STUB,
        )
        return True

    def _check_balance(self, signal: TradingSignal) -> bool:
        """
        For BUY orders: does the account have enough cash?

        TODO (#16.1):
            - Get current cash from account
            - Estimate cost = signal.quantity * latest_price * (1 + slippage)
            - Return cash >= cost
        """
        log.warning("%s _check_balance() — returning True", _STUB)
        return True

    def _check_position_limits(self, signal: TradingSignal) -> bool:
        """
        Would this trade exceed the max concentration per symbol?

        Rule: no single position should exceed max_position_pct of portfolio.

        TODO (#16.1):
            - Get portfolio value and current position in this symbol
            - Calculate post-trade position value
            - Return post_trade_value / portfolio_value <= max_position_pct
        """
        log.warning("%s _check_position_limits() — returning True", _STUB)
        return True


# ═══════════════════════════════════════════════════════════════════
#  TradeLogger — Issue #13
# ═══════════════════════════════════════════════════════════════════

class TradeLogger:
    """
    Records trades, algorithm signals, and portfolio snapshots to the database.

    This is the audit trail — every decision and execution is logged for
    display in the dashboard and for post-hoc analysis.

    Issue: #13 (Implement logging of trades and portfolio tracking)
    Sub-tasks: 13.1 (log methods), 13.2 (snapshots), 13.3 (daily P&L), 13.4 (queries)
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        log.info("%s TradeLogger created", _STUB)

    def log_trade(self, trade: Trade) -> None:
        """
        Record a completed trade to the database.

        TODO (#13.1):
            - INSERT INTO trades (account_id, asset_id, side, quantity, price, timestamp)
            - Log: "Trade logged: {side} {quantity} {symbol} @ ${price}"
        """
        log.warning(
            "%s TradeLogger.log_trade(%s %d shares @ $%.2f) — not persisted",
            _STUB, trade.side.value, trade.quantity, trade.price,
        )

    def log_signal(self, signal: TradingSignal) -> None:
        """
        Record an algorithm signal (even if not executed) for analysis.

        TODO (#13.1):
            - INSERT INTO signals table (or a JSON log)
            - Include algorithm name, confidence, metadata
        """
        log.warning(
            "%s TradeLogger.log_signal(%s %s, conf=%.2f) — not persisted",
            _STUB, signal.action.value, signal.symbol, signal.confidence,
        )

    def get_trade_history(
        self,
        account_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Trade]:
        """
        Query trade history with optional filters and pagination.

        TODO (#13.4):
            - Query TRADES table with filters
            - ORDER BY timestamp DESC
            - LIMIT/OFFSET for pagination
        """
        log.warning(
            "%s TradeLogger.get_trade_history(account=%d) — returning []",
            _STUB, account_id,
        )
        return []

    def get_portfolio_snapshots(
        self, account_id: int, start: datetime | None = None, end: datetime | None = None,
    ) -> list[PortfolioSnapshot]:
        """
        Get historical portfolio snapshots for charting portfolio value over time.

        TODO (#13.2):
            - Query portfolio_snapshots table
            - Return ordered by timestamp
        """
        log.warning(
            "%s TradeLogger.get_portfolio_snapshots() — returning []", _STUB,
        )
        return []

    def take_snapshot(self, portfolio: Portfolio) -> None:
        """
        Capture current portfolio state and persist it.

        Called periodically by the Scheduler (every 5 minutes during market hours)
        and after every trade execution.

        TODO (#13.2):
            - Build PortfolioSnapshot from current Portfolio
            - INSERT INTO portfolio_snapshots table
        """
        log.warning(
            "%s TradeLogger.take_snapshot(value=$%.2f) — not persisted",
            _STUB, portfolio.total_value(),
        )

    def calc_daily_pnl(self, account_id: int, date: datetime) -> float:
        """
        Calculate realized + unrealized P&L for a specific date.

        TODO (#13.3):
            - Get portfolio snapshot at start of day
            - Get portfolio snapshot at end of day (or current)
            - Return difference in total_value
        """
        log.warning(
            "%s TradeLogger.calc_daily_pnl() — returning 0.0", _STUB,
        )
        return 0.0
