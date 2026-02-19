"""
omnium.algorithms — Trading Algorithms
=========================================

Strategy pattern: all algorithms implement BaseTradingAlgorithm.
The AlgorithmSwitcher manages registration and hot-swapping.

    BaseTradingAlgorithm  (ABC)    — Common interface for all algorithms
    RuleBasedAlgorithm    (#9)     — SMA crossover, RSI, MACD, volume
    MLTradingAlgorithm    (#10)    — Feature extraction → ML model → signal
    FeatureExtractor      (#10)    — Converts price history into model features
    AlgorithmSwitcher     (#11)    — Registry + runtime switching

All classes below are STUBS. Interfaces are final and match the UML.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from omnium.models import Action, Price, TradingSignal

log = logging.getLogger(__name__)

_STUB = "⚠️  STUB"


# ═══════════════════════════════════════════════════════════════════
#  BaseTradingAlgorithm — Issue #9 sub-task 9.1
# ═══════════════════════════════════════════════════════════════════

class BaseTradingAlgorithm(ABC):
    """
    Abstract base class for all trading algorithms.

    Every algorithm — whether rule-based, ML, or future additions —
    implements this interface. The Orchestrator only ever talks to this
    interface (via AlgorithmSwitcher), never to concrete classes.

    Subclasses MUST implement:
        analyze(prices) → TradingSignal

    Issue: #9 sub-task 9.1 (Define BaseTradingAlgorithm abstract class)
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        self._name = name
        self._config = config or {}
        log.info("Algorithm '%s' initialized with config: %s", name, self._config)

    @abstractmethod
    def analyze(self, prices: list[Price]) -> TradingSignal:
        """
        Analyze price history and produce a trading signal.

        This is THE core method. Given a window of historical prices,
        return a recommendation: BUY, SELL, or HOLD with a confidence score.

        Args:
            prices: List of Price objects, ordered oldest → newest.
                    Length is determined by Config.price_lookback (default 50).

        Returns:
            TradingSignal with action, quantity, confidence, and metadata.

        Raises:
            ValueError: If prices list is too short for the algorithm's needs.
        """
        ...

    def get_name(self) -> str:
        """Return the algorithm's display name."""
        return self._name

    def get_config(self) -> dict[str, Any]:
        """Return the algorithm's current configuration."""
        return dict(self._config)

    def update_config(self, params: dict[str, Any]) -> None:
        """
        Update algorithm parameters at runtime.

        Args:
            params: Dict of parameter names → new values.
                    Only known keys are updated; unknown keys are ignored.
        """
        for key, value in params.items():
            if key in self._config:
                old = self._config[key]
                self._config[key] = value
                log.info("Algorithm '%s': %s = %s → %s", self._name, key, old, value)
            else:
                log.warning("Algorithm '%s': unknown config key '%s'", self._name, key)


# ═══════════════════════════════════════════════════════════════════
#  RuleBasedAlgorithm — Issue #9
# ═══════════════════════════════════════════════════════════════════

class RuleBasedAlgorithm(BaseTradingAlgorithm):
    """
    Classical technical analysis: SMA crossover + RSI + MACD + volume.

    Combines multiple indicators into a weighted composite signal.
    Each indicator returns a value in {-1, 0, +1}, and the weighted
    sum determines the final action.

    Config defaults:
        sma_short_period:  20
        sma_long_period:   50
        rsi_period:        14
        rsi_overbought:    70.0
        rsi_oversold:      30.0
        volume_threshold:  1.5  (ratio vs 20-day avg volume)

    Issue: #9 (Implement rule-based trading algorithm)
    Sub-tasks: 9.3 (SMA), 9.4 (RSI), 9.5 (MACD), 9.6 (aggregation), 9.7 (tests)
    """

    DEFAULT_CONFIG = {
        "sma_short_period": 20,
        "sma_long_period": 50,
        "rsi_period": 14,
        "rsi_overbought": 70.0,
        "rsi_oversold": 30.0,
        "volume_threshold": 1.5,
        "indicator_weights": {
            "sma": 0.30,
            "rsi": 0.25,
            "macd": 0.30,
            "volume": 0.15,
        },
    }

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        merged = {**self.DEFAULT_CONFIG, **(config or {})}
        super().__init__(name="rule_based", config=merged)

    def analyze(self, prices: list[Price]) -> TradingSignal:
        """
        Run all technical indicators and produce a composite signal.

        Flow:
            1. calc_sma() → SMA crossover signal
            2. calc_rsi() → Overbought/oversold signal
            3. calc_macd() → MACD crossover signal
            4. check_volume_surge() → Volume confirmation
            5. Weighted sum → composite score → TradingSignal

        TODO (#9.3–9.6):
            - Implement each indicator method below
            - Aggregate signals with configurable weights
            - Map composite score to BUY/SELL/HOLD
            - Set confidence = abs(composite_score) normalized to 0.0–1.0

        CURRENT STUB: Returns HOLD with 0.0 confidence.
        """
        symbol = prices[-1].asset_id if prices else 0
        log.warning(
            "%s RuleBasedAlgorithm.analyze() — returning HOLD (need %d prices, got %d)",
            _STUB,
            self._config["sma_long_period"],
            len(prices),
        )
        return TradingSignal(
            symbol=str(symbol),
            action=Action.HOLD,
            quantity=0,
            confidence=0.0,
            metadata={"algorithm": "rule_based", "stub": True},
        )

    def _calc_sma(self, prices: list[Price], period: int) -> float:
        """
        Calculate Simple Moving Average over the last `period` closing prices.

        Formula: SMA = sum(close[-period:]) / period

        TODO (#9.3):
            - Extract closing prices from Price objects
            - Return the arithmetic mean of the last `period` values
            - Raise ValueError if len(prices) < period

        Returns:
            The SMA value as a float.
        """
        log.warning("%s _calc_sma(period=%d) — returning 0.0", _STUB, period)
        return 0.0

    def _calc_rsi(self, prices: list[Price], period: int) -> float:
        """
        Calculate Relative Strength Index.

        Formula:
            gains = [max(0, close[i] - close[i-1]) for i in range(1, len)]
            losses = [max(0, close[i-1] - close[i]) for i in range(1, len)]
            RS = avg(gains[-period:]) / avg(losses[-period:])
            RSI = 100 - (100 / (1 + RS))

        TODO (#9.4):
            - Calculate period gains and losses
            - Handle division by zero (if avg_loss == 0, RSI = 100)
            - Return float in range 0–100

        Returns:
            RSI value (0.0 – 100.0)
        """
        log.warning("%s _calc_rsi(period=%d) — returning 50.0", _STUB, period)
        return 50.0  # Neutral

    def _calc_macd(self, prices: list[Price]) -> tuple[float, float, float]:
        """
        Calculate MACD Line, Signal Line, and Histogram.

        Uses 12/26/9 EMA periods (standard).

        Formula:
            macd_line = EMA(12) - EMA(26)
            signal_line = EMA(9, of macd_line)
            histogram = macd_line - signal_line

        TODO (#9.5):
            - Implement EMA calculation helper
            - Calculate all three components
            - Return (macd_line, signal_line, histogram)

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        log.warning("%s _calc_macd() — returning (0, 0, 0)", _STUB)
        return (0.0, 0.0, 0.0)

    def _check_volume_surge(self, prices: list[Price]) -> bool:
        """
        Check if current volume is significantly above the 20-day average.

        A volume surge confirms that a price move has conviction behind it.

        TODO (#9.6):
            - Calculate 20-day average volume
            - Compare latest volume to average
            - Return True if latest > average * volume_threshold

        Returns:
            True if volume surge detected.
        """
        log.warning("%s _check_volume_surge() — returning False", _STUB)
        return False


# ═══════════════════════════════════════════════════════════════════
#  FeatureExtractor — Issue #10 sub-task 10.1
# ═══════════════════════════════════════════════════════════════════

class FeatureExtractor:
    """
    Converts raw price history into a numerical feature vector for ML models.

    Features include:
        - Price returns (1d, 5d, 20d)
        - Volatility (std dev of returns)
        - Technical indicators (SMA, RSI, MACD values)
        - Volume features (ratio to average)
        - Lag features (previous closes)

    Issue: #10 sub-task 10.1 (Implement FeatureExtractor)
    """

    def extract(self, prices: list[Price]) -> list[float]:
        """
        Extract a feature vector from price history.

        Args:
            prices: Ordered list of Price objects (oldest → newest)

        Returns:
            List of floats (feature vector). In production, use numpy array.

        TODO (#10.1):
            - Call _calc_technical_indicators()
            - Call _calc_price_momentum()
            - Call _calc_volatility()
            - Concatenate all features
            - Call _normalize()
            - Return as ndarray
        """
        log.warning(
            "%s FeatureExtractor.extract() — returning empty feature vector", _STUB,
        )
        return []

    def _calc_technical_indicators(self, prices: list[Price]) -> dict[str, float]:
        """
        Compute SMA, RSI, MACD as features.

        TODO (#10.1): Reuse indicator logic from RuleBasedAlgorithm or share a utils module.
        """
        log.warning("%s _calc_technical_indicators() — returning {}", _STUB)
        return {}

    def _calc_price_momentum(self, prices: list[Price]) -> list[float]:
        """
        Calculate returns over different lookback periods.

        TODO (#10.1):
            - 1-day return = (close[-1] - close[-2]) / close[-2]
            - 5-day, 10-day, 20-day returns
        """
        log.warning("%s _calc_price_momentum() — returning []", _STUB)
        return []

    def _calc_volatility(self, prices: list[Price]) -> float:
        """
        Calculate rolling standard deviation of daily returns.

        TODO (#10.1): std(daily_returns[-20:])
        """
        log.warning("%s _calc_volatility() — returning 0.0", _STUB)
        return 0.0

    def _normalize(self, features: list[float]) -> list[float]:
        """
        Normalize feature vector (z-score or min-max scaling).

        TODO (#10.1): Use sklearn StandardScaler or manual normalization.
        """
        log.warning("%s _normalize() — returning features unchanged", _STUB)
        return features


# ═══════════════════════════════════════════════════════════════════
#  MLTradingAlgorithm — Issue #10
# ═══════════════════════════════════════════════════════════════════

class MLTradingAlgorithm(BaseTradingAlgorithm):
    """
    Machine learning-based trading algorithm.

    Uses FeatureExtractor to convert prices → features, then feeds
    features into a trained model (e.g. Random Forest, Gradient Boosting)
    to predict the next price movement direction.

    Issue: #10 (Implement ML-based trading algorithm)
    Sub-tasks: 10.1–10.6
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="ml_based", config=config or {"lookback_window": 50})
        self._model = None  # TODO (#10.3): Trained sklearn model
        self._feature_extractor = FeatureExtractor()
        log.info("%s MLTradingAlgorithm created (model=None, needs training)", _STUB)

    def analyze(self, prices: list[Price]) -> TradingSignal:
        """
        Extract features → predict → map to TradingSignal.

        TODO (#10.4):
            - features = self._feature_extractor.extract(prices)
            - prediction, probability = self._predict(features)
            - Map prediction to Action (BUY/SELL/HOLD)
            - Use probability as confidence
            - Return TradingSignal

        CURRENT STUB: Returns HOLD with 0.0 confidence.
        """
        symbol = prices[-1].asset_id if prices else 0
        log.warning(
            "%s MLTradingAlgorithm.analyze() — returning HOLD (model not trained)",
            _STUB,
        )
        return TradingSignal(
            symbol=str(symbol),
            action=Action.HOLD,
            quantity=0,
            confidence=0.0,
            metadata={"algorithm": "ml_based", "stub": True},
        )

    def train(self, training_data: list[Price]) -> None:
        """
        Train the ML model on historical price data.

        IMPORTANT: Use time-series split — never shuffle. Train on older data,
        test on newer data. See Financial Reference Guide Section 7.

        TODO (#10.2, #10.3):
            - Extract features for each window in training_data
            - Label each window (next-day return > threshold = BUY)
            - Time-series train/test split
            - Fit model (Random Forest recommended as starting point)
            - Store trained model in self._model
            - Log training accuracy
        """
        log.warning(
            "%s MLTradingAlgorithm.train() — no-op (%d prices provided)",
            _STUB, len(training_data),
        )

    def evaluate(self, test_data: list[Price]) -> dict[str, float]:
        """
        Evaluate model performance on test data.

        Returns dict with: accuracy, precision, recall, sharpe_ratio

        TODO (#10.5):
            - Run predictions on test_data
            - Calculate classification metrics
            - Simulate trades for Sharpe ratio
            - Return metrics dict
        """
        log.warning("%s MLTradingAlgorithm.evaluate() — returning zeros", _STUB)
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "sharpe_ratio": 0.0,
        }

    def _predict(self, features: list[float]) -> tuple[str, float]:
        """
        Run the trained model on a feature vector.

        Returns:
            Tuple of (predicted_action, probability)

        TODO (#10.4):
            - self._model.predict_proba(features)
            - Map class to action string
        """
        log.warning("%s _predict() — returning ('hold', 0.0)", _STUB)
        return ("hold", 0.0)


# ═══════════════════════════════════════════════════════════════════
#  AlgorithmSwitcher — Issue #11
# ═══════════════════════════════════════════════════════════════════

class AlgorithmSwitcher:
    """
    Registry and runtime switcher for trading algorithms.

    The Orchestrator holds one AlgorithmSwitcher instance and calls
    switcher.analyze(prices). The Switcher delegates to whichever
    algorithm is currently active.

    Supports hot-swapping: switch algorithms without restarting the system.

    Issue: #11 (Create interface for switching between decision modules)
    Sub-tasks: 11.1 (registry), 11.2 (hot-swap), 11.3 (A/B mode), 11.4 (API)
    """

    def __init__(self) -> None:
        self._algorithms: dict[str, BaseTradingAlgorithm] = {}
        self._active_algorithm: str = ""
        log.info("AlgorithmSwitcher initialized (no algorithms registered yet)")

    def register(self, name: str, algorithm: BaseTradingAlgorithm) -> None:
        """
        Register an algorithm instance under a name.

        Args:
            name:      Unique identifier (e.g. "rule_based", "ml_based")
            algorithm: An instance of BaseTradingAlgorithm

        If this is the first algorithm registered, it becomes active by default.
        """
        self._algorithms[name] = algorithm
        if not self._active_algorithm:
            self._active_algorithm = name
            log.info("Registered and activated algorithm: '%s'", name)
        else:
            log.info(
                "Registered algorithm: '%s' (active: '%s')", name, self._active_algorithm,
            )

    def switch_to(self, name: str) -> None:
        """
        Switch the active algorithm at runtime.

        Args:
            name: Name of a previously registered algorithm.

        Raises:
            KeyError: If the name is not registered.

        Thread-safety note for implementer (#11.2):
            The current analysis (if running) should complete before the
            switch takes effect. Consider using a threading lock.
        """
        if name not in self._algorithms:
            available = list(self._algorithms.keys())
            raise KeyError(
                f"Algorithm '{name}' not registered. Available: {available}"
            )
        old = self._active_algorithm
        self._active_algorithm = name
        log.info("Switched algorithm: '%s' → '%s'", old, name)

    def get_active(self) -> BaseTradingAlgorithm:
        """
        Return the currently active algorithm instance.

        Raises:
            RuntimeError: If no algorithms are registered.
        """
        if not self._active_algorithm:
            raise RuntimeError("No algorithms registered in AlgorithmSwitcher")
        return self._algorithms[self._active_algorithm]

    def list_available(self) -> list[str]:
        """Return names of all registered algorithms."""
        return list(self._algorithms.keys())

    def analyze(self, prices: list[Price]) -> TradingSignal:
        """
        Delegate analysis to the currently active algorithm.

        This is the method the Orchestrator calls. It transparently
        routes to whichever algorithm is active.

        Args:
            prices: Price history (oldest → newest)

        Returns:
            TradingSignal from the active algorithm.
        """
        algo = self.get_active()
        log.debug("Delegating analyze() to '%s'", self._active_algorithm)
        return algo.analyze(prices)
