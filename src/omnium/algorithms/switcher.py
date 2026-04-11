"""
Algorithm Switcher — runtime switching between CS and ML algorithms.
"""

from __future__ import annotations

import logging
from typing import Any

from src.omnium.algorithms.cs_algorithm import CSAlgorithm, TradingConfig
from src.omnium.algorithms.ml_algorithm import MLAlgorithm, MLConfig

log = logging.getLogger(__name__)

# Registry of available algorithm names
AVAILABLE_ALGORITHMS = ["rule_based", "ml"]


class AlgorithmSwitcher:
    """Manages which trading algorithm is active and routes decisions through it."""

    def __init__(self) -> None:
        self._active_name: str = "rule_based"
        self._cs = CSAlgorithm()
        self._ml = MLAlgorithm()

    @property
    def active_algorithm(self) -> str:
        return self._active_name

    def switch(self, algorithm_name: str) -> bool:
        """Switch to a different algorithm. Returns True on success."""
        if algorithm_name not in AVAILABLE_ALGORITHMS:
            log.warning("Unknown algorithm: %s", algorithm_name)
            return False
        self._active_name = algorithm_name
        log.info("Switched to algorithm: %s", algorithm_name)
        return True

    def decide(self, current_price: float, reference_price: float,
               purchase_price: float | None, shares_held: int,
               asset_id: int = 0) -> str:
        """Route decision to the active algorithm."""
        if self._active_name == "ml":
            return self._ml.decide(current_price, reference_price,
                                   purchase_price, shares_held, asset_id)
        return self._cs.decide(current_price, reference_price, purchase_price, shares_held)

    def update_config(self, params: dict[str, Any]) -> bool:
        """Update configuration on the active algorithm."""
        if self._active_name == "ml":
            return self._ml.update_config(**params)
        return self._cs.update_config(**params)

    def get_config(self) -> dict[str, Any]:
        """Return current config as a dict."""
        if self._active_name == "ml":
            cfg = self._ml.config
            return {
                "algorithm": "ml",
                "lookback": cfg.lookback,
                "buy_threshold": cfg.buy_threshold,
                "sell_threshold": cfg.sell_threshold,
                "max_position": cfg.max_position,
            }
        cfg = self._cs.config
        return {
            "algorithm": self._active_name,
            "buy_threshold": cfg.buy_threshold,
            "sell_threshold": cfg.sell_threshold,
            "stop_loss": cfg.stop_loss,
            "max_position": cfg.max_position,
        }

    def train_ml(self, asset_id: int) -> bool:
        """Explicitly train the ML model on an asset's data."""
        return self._ml.train(asset_id)
