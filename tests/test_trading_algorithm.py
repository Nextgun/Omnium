"""
==========================
test_trading_algorithm.py
Comprehensive test suite for TradingAlgorithm
==========================

Tests cover:
- Default configuration behavior
- Configuration customization
- Buy signal logic
- Sell signal logic
- Edge cases and invalid inputs
- Integration scenarios
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_logic.trading_algorithm import TradingAlgorithm, TradingConfig


class TestDefaultConfiguration:
    """Test default TradingConfig values and behavior."""

    def test_default_config_values(self):
        """Verify all default configuration values are correct."""
        config = TradingConfig()
        assert config.buy_threshold == 5.0
        assert config.sell_threshold == 10.0
        assert config.stop_loss == 8.0
        assert config.max_position == 100

    def test_algorithm_initializes_with_default_config(self):
        """Verify TradingAlgorithm creates default config when none provided."""
        algo = TradingAlgorithm()
        assert algo.config is not None
        assert algo.config.buy_threshold == 5.0
        assert algo.config.sell_threshold == 10.0

    def test_algorithm_uses_provided_config(self):
        """Verify TradingAlgorithm uses provided config instead of creating default."""
        custom_config = TradingConfig(buy_threshold=3.0, sell_threshold=15.0)
        algo = TradingAlgorithm(custom_config)
        assert algo.config is custom_config
        assert algo.config.buy_threshold == 3.0

    def test_default_buy_signal_with_default_config(self):
        """Test buy signal triggers with default 5% threshold."""
        algo = TradingAlgorithm()
        ref_price = 100.0
        current_price = 94.99  # 5.01% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_default_sell_signal_with_default_config(self):
        """Test sell signal triggers with default 10% threshold."""
        algo = TradingAlgorithm()
        purchase_price = 100.0
        current_price = 111.0  # 11% gain
        assert algo.should_sell(current_price, purchase_price) is True


class TestConfigurationUpdates:
    """Test configuration update functionality."""

    def test_update_single_parameter(self):
        """Test updating a single parameter."""
        algo = TradingAlgorithm()
        result = algo.update(buy_threshold=2.5)
        assert result is True
        assert algo.config.buy_threshold == 2.5
        assert algo.config.sell_threshold == 10.0  # unchanged

    def test_update_multiple_parameters(self):
        """Test updating multiple parameters at once."""
        algo = TradingAlgorithm()
        result = algo.update(
            buy_threshold=1.0,
            sell_threshold=20.0,
            stop_loss=5.0,
            max_position=50
        )
        assert result is True
        assert algo.config.buy_threshold == 1.0
        assert algo.config.sell_threshold == 20.0
        assert algo.config.stop_loss == 5.0
        assert algo.config.max_position == 50

    def test_update_returns_false_when_no_changes(self):
        """Test update returns False when no parameters provided."""
        algo = TradingAlgorithm()
        result = algo.update()
        assert result is False
        # Config should remain unchanged
        assert algo.config.buy_threshold == 5.0

    def test_update_returns_false_with_all_none(self):
        """Test update returns False when all parameters are None."""
        algo = TradingAlgorithm()
        result = algo.update(
            buy_threshold=None,
            sell_threshold=None,
            stop_loss=None,
            max_position=None
        )
        assert result is False

    def test_sequential_updates_accumulate(self):
        """Test that sequential updates persist and accumulate."""
        algo = TradingAlgorithm()
        algo.update(buy_threshold=3.0)
        algo.update(sell_threshold=15.0)
        algo.update(max_position=75)
        
        assert algo.config.buy_threshold == 3.0
        assert algo.config.sell_threshold == 15.0
        assert algo.config.stop_loss == 8.0  # unchanged
        assert algo.config.max_position == 75

    def test_update_with_zero_values(self):
        """Test updating with zero values."""
        algo = TradingAlgorithm()
        result = algo.update(buy_threshold=0.0, max_position=0)
        assert result is True
        assert algo.config.buy_threshold == 0.0
        assert algo.config.max_position == 0

    def test_update_with_negative_values(self):
        """Test updating with negative values (should be allowed at config level)."""
        algo = TradingAlgorithm()
        result = algo.update(buy_threshold=-5.0, stop_loss=-10.0)
        assert result is True
        assert algo.config.buy_threshold == -5.0
        assert algo.config.stop_loss == -10.0

    def test_update_with_large_values(self):
        """Test updating with very large threshold values."""
        algo = TradingAlgorithm()
        result = algo.update(buy_threshold=1000.0, max_position=10000)
        assert result is True
        assert algo.config.buy_threshold == 1000.0
        assert algo.config.max_position == 10000


class TestBuySignalLogic:
    """Test buy signal determination."""

    def test_buy_signal_triggers_at_threshold(self):
        """Test buy signal triggers when price drops exactly to threshold."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 100.0
        current_price = 95.0  # exactly 5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_buy_signal_triggers_below_threshold(self):
        """Test buy signal triggers when price drops below threshold."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 100.0
        current_price = 94.0  # 6% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_buy_signal_does_not_trigger_above_threshold(self):
        """Test buy signal does not trigger when price drop is below threshold."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 100.0
        current_price = 95.5  # 4.5% drop
        assert algo.should_buy(ref_price, current_price) is False

    def test_buy_signal_with_no_price_drop(self):
        """Test buy signal when price equals reference (0% drop)."""
        algo = TradingAlgorithm()
        ref_price = 100.0
        current_price = 100.0
        assert algo.should_buy(ref_price, current_price) is False

    def test_buy_signal_when_price_rises(self):
        """Test buy signal when price rises (negative drop)."""
        algo = TradingAlgorithm()
        ref_price = 100.0
        current_price = 110.0
        assert algo.should_buy(ref_price, current_price) is False

    def test_buy_signal_with_zero_reference_price(self):
        """Test buy signal returns False with zero reference price."""
        algo = TradingAlgorithm()
        assert algo.should_buy(0.0, 50.0) is False

    def test_buy_signal_with_negative_reference_price(self):
        """Test buy signal returns False with negative reference price."""
        algo = TradingAlgorithm()
        assert algo.should_buy(-100.0, 50.0) is False

    def test_buy_signal_with_custom_threshold(self):
        """Test buy signal with custom threshold."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=2.0))
        ref_price = 100.0
        current_price = 97.5  # 2.5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_buy_signal_with_zero_threshold(self):
        """Test buy signal with 0% threshold (any drop triggers buy)."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=0.0))
        ref_price = 100.0
        current_price = 99.99  # 0.01% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_buy_signal_with_very_small_prices(self):
        """Test buy signal with very small price values."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 0.01
        current_price = 0.0095  # 5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_buy_signal_with_fractional_prices(self):
        """Test buy signal with fractional prices."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 50.25
        current_price = 47.7375  # 5% drop
        assert algo.should_buy(ref_price, current_price) is True


class TestSellSignalLogic:
    """Test sell signal determination."""

    def test_sell_signal_on_profit_target(self):
        """Test sell signal triggers on profit target."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=10.0))
        purchase_price = 100.0
        current_price = 111.0  # 11% gain
        assert algo.should_sell(current_price, purchase_price) is True

    def test_sell_signal_on_profit_target_at_threshold(self):
        """Test sell signal triggers at exactly profit threshold."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=10.0))
        purchase_price = 100.0
        current_price = 110.0  # exactly 10% gain
        assert algo.should_sell(current_price, purchase_price) is True

    def test_sell_signal_on_stop_loss(self):
        """Test sell signal triggers on stop-loss."""
        algo = TradingAlgorithm(TradingConfig(stop_loss=8.0))
        purchase_price = 100.0
        current_price = 91.5  # 8.5% loss
        assert algo.should_sell(current_price, purchase_price) is True

    def test_sell_signal_on_stop_loss_at_threshold(self):
        """Test sell signal triggers at exactly stop-loss threshold."""
        algo = TradingAlgorithm(TradingConfig(stop_loss=8.0))
        purchase_price = 100.0
        current_price = 92.0  # exactly 8% loss
        assert algo.should_sell(current_price, purchase_price) is True

    def test_no_sell_signal_on_small_gain(self):
        """Test no sell signal when gain is below profit target."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=10.0))
        purchase_price = 100.0
        current_price = 105.0  # 5% gain
        assert algo.should_sell(current_price, purchase_price) is False

    def test_no_sell_signal_on_small_loss(self):
        """Test no sell signal when loss is smaller than stop-loss."""
        algo = TradingAlgorithm(TradingConfig(stop_loss=8.0))
        purchase_price = 100.0
        current_price = 96.0  # 4% loss
        assert algo.should_sell(current_price, purchase_price) is False

    def test_no_sell_signal_at_breakeven(self):
        """Test no sell signal when price equals purchase price."""
        algo = TradingAlgorithm()
        purchase_price = 100.0
        current_price = 100.0
        assert algo.should_sell(current_price, purchase_price) is False

    def test_sell_signal_with_zero_purchase_price(self):
        """Test sell signal returns False with zero purchase price."""
        algo = TradingAlgorithm()
        assert algo.should_sell(50.0, 0.0) is False

    def test_sell_signal_with_negative_purchase_price(self):
        """Test sell signal returns False with negative purchase price."""
        algo = TradingAlgorithm()
        assert algo.should_sell(50.0, -100.0) is False

    def test_sell_signal_with_custom_thresholds(self):
        """Test sell signal with custom profit and stop-loss thresholds."""
        algo = TradingAlgorithm(
            TradingConfig(sell_threshold=5.0, stop_loss=3.0)
        )
        # Test profit target
        assert algo.should_sell(105.0, 100.0) is True  # 5% gain
        # Test stop-loss
        assert algo.should_sell(96.5, 100.0) is True  # 3.5% loss

    def test_sell_signal_with_very_small_prices(self):
        """Test sell signal with very small price values."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=10.0, stop_loss=8.0))
        purchase_price = 0.01
        # Test profit - use 0.01101 to ensure > 10% (avoids floating-point issues)
        assert algo.should_sell(0.01101, purchase_price) is True  # >10% gain
        # Test loss - use 0.00919 to ensure < -8% (avoids floating-point issues)
        assert algo.should_sell(0.00919, purchase_price) is True  # >8% loss

    def test_sell_signal_priority_profit_over_loss(self):
        """Test that both profit and loss are evaluated (OR logic)."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=10.0, stop_loss=8.0))
        purchase_price = 100.0
        # Either condition triggers sell
        assert algo.should_sell(111.0, purchase_price) is True  # profit
        assert algo.should_sell(91.5, purchase_price) is True  # loss

    def test_sell_signal_with_zero_thresholds(self):
        """Test sell signal with 0% thresholds (any change triggers sell)."""
        algo = TradingAlgorithm(TradingConfig(sell_threshold=0.0, stop_loss=0.0))
        purchase_price = 100.0
        # Any price change should trigger sell
        assert algo.should_sell(100.01, purchase_price) is True  # 0.01% gain
        assert algo.should_sell(99.99, purchase_price) is True  # 0.01% loss


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_price_values(self):
        """Test with very large price values."""
        algo = TradingAlgorithm()
        ref_price = 1_000_000.0
        current_price = 950_000.0  # 5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_very_small_price_values(self):
        """Test with very small price values (penny stocks)."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 0.001
        current_price = 0.00095  # 5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_floating_point_precision(self):
        """Test floating-point precision in percentage calculations."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
        ref_price = 100.0 / 3  # 33.333...
        current_price = (100.0 / 3) * 0.95  # 5% drop
        assert algo.should_buy(ref_price, current_price) is True

    def test_negative_config_values_in_logic(self):
        """Test algorithm behavior with negative threshold values."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=-5.0))
        ref_price = 100.0
        current_price = 105.0  # price rose 5%
        # With negative threshold (-5%), any price >= reference should trigger
        # Because drop_percent = (100 - 105)/100 * 100 = -5%, and -5% >= -5% is True
        assert algo.should_buy(ref_price, current_price) is True

    def test_max_position_with_zero_value(self):
        """Test that max_position can be set to zero."""
        algo = TradingAlgorithm()
        algo.update(max_position=0)
        assert algo.config.max_position == 0

    def test_max_position_with_large_value(self):
        """Test max_position with very large value."""
        algo = TradingAlgorithm()
        algo.update(max_position=1_000_000)
        assert algo.config.max_position == 1_000_000


class TestIntegrationScenarios:
    """Test real-world trading scenarios."""

    def test_buy_then_sell_profit_scenario(self):
        """Test a complete buy-then-sell-at-profit scenario."""
        algo = TradingAlgorithm(
            TradingConfig(buy_threshold=5.0, sell_threshold=10.0)
        )
        ref_price = 100.0
        
        # Check buy at 5% drop
        assert algo.should_buy(ref_price, 95.0) is True
        
        # Simulate purchase at 95
        purchase_price = 95.0
        
        # Check sell at 10% profit from purchase
        current_price = 104.5  # 10% gain from 95
        assert algo.should_sell(current_price, purchase_price) is True

    def test_buy_then_sell_stoploss_scenario(self):
        """Test a buy-then-sell-at-stoploss scenario."""
        algo = TradingAlgorithm(
            TradingConfig(buy_threshold=5.0, stop_loss=8.0)
        )
        ref_price = 100.0
        
        # Check buy at 5% drop
        assert algo.should_buy(ref_price, 95.0) is True
        
        # Simulate purchase at 95
        purchase_price = 95.0
        
        # Check sell at >8% loss from purchase (use 87.0 to avoid floating-point issues)
        # (87.0 - 95.0) / 95.0 * 100 = -8.42% which is > 8% loss
        current_price = 87.0  # ~8.4% loss from 95
        assert algo.should_sell(current_price, purchase_price) is True

    def test_dynamic_reconfiguration_during_trading(self):
        """Test reconfiguring algorithm during trading."""
        algo = TradingAlgorithm()
        
        # Initial config: 5% buy, 10% sell
        assert algo.should_buy(100.0, 95.0) is True
        
        # Tighten thresholds
        algo.update(buy_threshold=3.0, sell_threshold=5.0)
        
        # Should buy at 4% drop with new 3% threshold
        assert algo.should_buy(100.0, 96.0) is True
        
        # Should sell earlier at 5% gain
        purchase_price = 95.0
        assert algo.should_sell(99.75, purchase_price) is True  # 5% gain

    def test_multiple_assets_with_shared_algo(self):
        """Test using same algorithm instance for multiple assets."""
        algo = TradingAlgorithm()
        
        # Asset 1: AAPL
        assert algo.should_buy(150.0, 142.5) is True  # 5% drop
        
        # Asset 2: MSFT
        assert algo.should_buy(300.0, 285.0) is True  # 5% drop
        
        # Config change affects all assets
        algo.update(buy_threshold=2.0)
        
        # Both assets now require 2% drop
        assert algo.should_buy(150.0, 147.0) is True  # 2% drop
        assert algo.should_buy(300.0, 294.0) is True  # 2% drop

    def test_algorithm_consistency(self):
        """Test that algorithm is deterministic with same inputs."""
        algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0, stop_loss=8.0))
        
        # Same inputs should always produce same output
        for _ in range(10):
            assert algo.should_buy(100.0, 95.0) is True
            assert algo.should_buy(100.0, 96.0) is False
            assert algo.should_sell(111.0, 100.0) is True
            assert algo.should_sell(100.0, 100.0) is False

    def test_config_immutability_between_instances(self):
        """Test that config changes in one instance don't affect others."""
        algo1 = TradingAlgorithm()
        algo2 = TradingAlgorithm()
        
        algo1.update(buy_threshold=2.0)
        
        # algo2 should retain original threshold
        assert algo1.config.buy_threshold == 2.0
        assert algo2.config.buy_threshold == 5.0


class TestTypeHandling:
    """Test type handling and parameter validation."""

    def test_config_accepts_numeric_types(self):
        """Test that config accepts various numeric types."""
        config = TradingConfig(
            buy_threshold=5,  # int instead of float
            max_position=100
        )
        assert config.buy_threshold == 5

    def test_algorithm_handles_int_prices(self):
        """Test algorithm with integer prices."""
        algo = TradingAlgorithm()
        # Should work with int prices (Python converts to float in calculations)
        assert algo.should_buy(100, 95) is True

    def test_algorithm_with_mixed_numeric_types(self):
        """Test algorithm with mixed int/float prices."""
        algo = TradingAlgorithm()
        assert algo.should_buy(100.0, 95) is True
        assert algo.should_buy(100, 95.0) is True
