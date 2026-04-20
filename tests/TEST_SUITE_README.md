# Trading Algorithm Test Suite

## Overview

`test_trading_algorithm.py` contains a comprehensive pytest-based test suite for the Omnium trading algorithm. The suite covers over 60 test cases organized into 8 test classes, ensuring robust validation of the algorithm's behavior.

## Test Coverage

### 1. **TestDefaultConfiguration** (5 tests)
Validates that default configuration values are correct and behave as expected.
- Default config values (5% buy, 10% sell, 8% stop-loss, 100 max position)
- Default behavior in buy/sell logic

### 2. **TestConfigurationUpdates** (8 tests)
Tests the `update()` method for modifying algorithm configuration.
- Single and multiple parameter updates
- Return value validation (True when changed, False when not)
- Sequential updates and persistence
- Edge cases (zero values, negative values, very large values)

### 3. **TestBuySignalLogic** (11 tests)
Comprehensive testing of buy signal determination.
- Threshold matching and boundary conditions
- No signal cases (flat/rising prices)
- Invalid inputs (zero/negative reference prices)
- Custom thresholds
- Small and fractional prices

### 4. **TestSellSignalLogic** (12 tests)
Comprehensive testing of sell signal determination.
- Profit target triggers (positive percentage)
- Stop-loss triggers (negative percentage)
- Threshold boundary conditions
- No signal cases (small gains/losses)
- Invalid inputs (zero/negative purchase prices)
- Both profit and loss evaluation

### 5. **TestEdgeCases** (6 tests)
Tests boundary conditions and unusual inputs.
- Very large prices (millions)
- Very small prices (penny stocks, fractions)
- Floating-point precision
- Negative config values
- Zero max position
- Large max position values

### 6. **TestIntegrationScenarios** (6 tests)
Real-world trading scenarios.
- Complete buy → sell at profit cycle
- Complete buy → sell at stop-loss cycle
- Dynamic reconfiguration during trading
- Multiple assets with shared algorithm instance
- Algorithm consistency (deterministic)
- Config isolation between instances

### 7. **TestTypeHandling** (3 tests)
Type flexibility and numeric handling.
- Config accepts int and float values
- Algorithm works with integer prices
- Mixed numeric types

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

Install pytest (if not already installed):
```bash
pip install pytest
```

Or install from a requirements file:
```bash
pip install -r requirements.txt  # if created with pytest in it
```

## Running the Tests

### Run all tests
```bash
pytest tests/test_trading_algorithm.py -v
```

### Run specific test class
```bash
pytest tests/test_trading_algorithm.py::TestDefaultConfiguration -v
```

### Run specific test
```bash
pytest tests/test_trading_algorithm.py::TestDefaultConfiguration::test_default_config_values -v
```

### Run with coverage report
```bash
pip install pytest-cov
pytest tests/test_trading_algorithm.py --cov=trading_logic --cov-report=html
```

### Run with minimal output
```bash
pytest tests/test_trading_algorithm.py
```

### Run with detailed output on failure
```bash
pytest tests/test_trading_algorithm.py -vv --tb=long
```

## Expected Results

All **60+ tests** should pass. When running `pytest tests/test_trading_algorithm.py -v`, you should see output like:

```
tests/test_trading_algorithm.py::TestDefaultConfiguration::test_default_config_values PASSED
tests/test_trading_algorithm.py::TestDefaultConfiguration::test_algorithm_initializes_with_default_config PASSED
... (many more PASSED) ...

===== X passed in Y.XXs =====
```

## Test Philosophy

### What Gets Tested
✅ Default configuration values and behavior  
✅ Configuration modification and persistence  
✅ Buy signal logic (thresholds, edge cases, invalid inputs)  
✅ Sell signal logic (profit targets, stop-losses, edge cases)  
✅ Edge cases (extreme values, floating-point precision)  
✅ Real-world trading scenarios  
✅ Type handling and flexibility  
✅ Algorithm consistency and determinism  

### What's NOT Tested
❌ Database integration (orchestrator.py uses db.*)  
❌ External price data fetching  
❌ User interface  
❌ Account management  

These are intentionally isolated so tests run fast and independently.

## Code Organization

Each test class is focused on a specific aspect:
- **Clear naming**: Test names describe exactly what they test
- **Single responsibility**: Each test validates one behavior
- **Independent**: Tests don't depend on execution order
- **Comprehensive**: Edge cases and error conditions included

Example test structure:
```python
def test_buy_signal_triggers_at_threshold(self):
    """Test buy signal triggers when price drops exactly to threshold."""
    algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
    ref_price = 100.0
    current_price = 95.0  # exactly 5% drop
    assert algo.should_buy(ref_price, current_price) is True
```

## Continuous Integration

To integrate with CI/CD:

```bash
# Run tests and exit with error code if any fail
pytest tests/test_trading_algorithm.py -v --tb=short

# Generate JUnit XML for CI systems
pytest tests/test_trading_algorithm.py --junit-xml=test-results.xml

# Generate coverage report
pytest tests/test_trading_algorithm.py --cov=trading_logic --cov-report=xml
```

## Extending Tests

To add more tests:

1. Add test method to appropriate class (or create new class)
2. Follow naming convention: `test_<what_is_being_tested>`
3. Include docstring explaining what and why
4. Use clear assertions with meaningful values
5. Run `pytest tests/test_trading_algorithm.py -v` to verify

Example:
```python
def test_my_new_feature(self):
    """Test description of what should happen."""
    algo = TradingAlgorithm(TradingConfig(buy_threshold=5.0))
    result = algo.should_buy(100.0, 95.0)
    assert result is True
```

## Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'trading_logic'`  
**Solution**: Run pytest from the project root directory (`C:\Users\elive\Omnium\`)

**Problem**: `pytest: command not found`  
**Solution**: Install pytest: `pip install pytest`

**Problem**: Some tests fail  
**Solution**: Check the algorithm implementation in `trading_logic/trading_algorithm.py` for changes, or review test logic

## Related Files

- **Implementation**: `trading_logic/trading_algorithm.py` (TradingAlgorithm, TradingConfig)
- **Integration**: `trading_logic/orchestrator.py` (uses TradingAlgorithm with database)
- **Other tests**: `tests/test_auth.py` (existing auth system tests)

---

Created as part of Omnium trading algorithm quality assurance.
