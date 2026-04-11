"""
ML Algorithm — Machine-learning trading strategy using Linear Regression.

Trains on historical price data features (moving averages, momentum, volatility)
to predict next-day price direction. Outputs BUY/SELL/HOLD signals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LinearRegression

from src.omnium.data import db

log = logging.getLogger(__name__)


@dataclass
class MLConfig:
    """Configuration for the ML trading algorithm."""
    lookback: int = 30          # Number of historical bars to train on
    buy_threshold: float = 0.5  # Predicted % gain to trigger BUY
    sell_threshold: float = -0.3  # Predicted % loss to trigger SELL
    max_position: int = 100     # Maximum shares to hold


class MLAlgorithm:
    """Linear-regression predictor that forecasts next-day price movement."""

    def __init__(self, config: MLConfig | None = None) -> None:
        self.config = config or MLConfig()
        self._model = LinearRegression()
        self._is_trained = False

    def update_config(
        self,
        lookback: int | None = None,
        buy_threshold: float | None = None,
        sell_threshold: float | None = None,
        max_position: int | None = None,
    ) -> bool:
        """Update algorithm parameters. Returns True if anything changed."""
        updated = False
        for attr, val in [
            ("lookback", lookback),
            ("buy_threshold", buy_threshold),
            ("sell_threshold", sell_threshold),
            ("max_position", max_position),
        ]:
            if val is not None:
                setattr(self.config, attr, val)
                updated = True
        if updated:
            self._is_trained = False
        return updated

    def _build_features(self, closes: list[float]) -> np.ndarray:
        """
        Build feature matrix from a list of close prices.

        Features per row:
          0: 5-bar SMA ratio  (close / SMA5)
          1: 10-bar SMA ratio (close / SMA10)
          2: momentum (% change over 5 bars)
          3: volatility (std of last 5 closes / mean)
        """
        features = []
        for i in range(10, len(closes)):
            sma5 = np.mean(closes[i - 5 : i])
            sma10 = np.mean(closes[i - 10 : i])
            momentum = (closes[i] - closes[i - 5]) / closes[i - 5] * 100 if closes[i - 5] != 0 else 0
            vol = np.std(closes[i - 5 : i]) / np.mean(closes[i - 5 : i]) * 100 if np.mean(closes[i - 5 : i]) != 0 else 0
            features.append([
                closes[i] / sma5 if sma5 != 0 else 1,
                closes[i] / sma10 if sma10 != 0 else 1,
                momentum,
                vol,
            ])
        return np.array(features)

    def train(self, asset_id: int) -> bool:
        """
        Train the model on historical price data for the given asset.
        Returns True if training succeeded.
        """
        history = db.get_price_history(asset_id, limit=max(self.config.lookback + 20, 60))
        if len(history) < 20:
            log.warning("Not enough price data to train ML model (got %d)", len(history))
            self._is_trained = False
            return False

        # History comes newest-first; reverse for chronological order
        closes = [float(p["close"]) for p in reversed(history)]

        features = self._build_features(closes)
        if len(features) < 5:
            log.warning("Not enough feature rows to train (%d)", len(features))
            self._is_trained = False
            return False

        # Target: next-day % change
        targets = []
        for i in range(10, len(closes) - 1):
            pct_change = (closes[i + 1] - closes[i]) / closes[i] * 100 if closes[i] != 0 else 0
            targets.append(pct_change)

        # Align: features has one more row than targets (last row has no next-day)
        X = features[: len(targets)]
        y = np.array(targets)

        if len(X) < 3:
            self._is_trained = False
            return False

        self._model.fit(X, y)
        self._is_trained = True
        log.info("ML model trained on %d samples for asset %d", len(X), asset_id)
        return True

    def predict(self, asset_id: int) -> float:
        """
        Predict next-day % change for an asset.
        Returns 0.0 if model is not trained or data is insufficient.
        """
        if not self._is_trained:
            return 0.0

        history = db.get_price_history(asset_id, limit=15)
        if len(history) < 11:
            return 0.0

        closes = [float(p["close"]) for p in reversed(history)]
        features = self._build_features(closes)
        if len(features) == 0:
            return 0.0

        # Use the most recent feature row
        prediction = self._model.predict(features[-1:])
        return float(prediction[0])

    def decide(self, current_price: float, reference_price: float,
               purchase_price: float | None, shares_held: int,
               asset_id: int) -> str:
        """
        Make a trading decision using ML prediction.

        Returns: "BUY", "SELL", or "HOLD"
        """
        # Ensure model is trained
        if not self._is_trained:
            self.train(asset_id)

        predicted_change = self.predict(asset_id)
        log.info("ML predicted %.2f%% change for asset %d", predicted_change, asset_id)

        if predicted_change >= self.config.buy_threshold and shares_held < self.config.max_position:
            return "BUY"

        if predicted_change <= self.config.sell_threshold and shares_held > 0:
            return "SELL"

        return "HOLD"
