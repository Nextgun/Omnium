"""
==========================
test_orchestrator.py - Test suite for trading orchestrator
Tests the main orchestrator functions with sample data
==========================
"""

from trading_logic.orchestrator import run_tick, update_algorithm, get_status


def test_run_tick():
    """Test the run_tick function with different account/asset combinations."""
    print("\n" + "=" * 50)
    print("Testing run_tick()")
    print("=" * 50)
    
    # Test with account 1, asset 1
    result = run_tick(account_id=1, asset_id=1)
    print(f"run_tick(1, 1): {result}")
    
    # Test with account 1, asset 2
    result = run_tick(account_id=1, asset_id=2)
    print(f"run_tick(1, 2): {result}")
    
    # Test with invalid account
    result = run_tick(account_id=999, asset_id=1)
    print(f"run_tick(999, 1): {result}")


def test_update_algorithm():
    """Test the update_algorithm function with different configs."""
    print("\n" + "=" * 50)
    print("Testing update_algorithm()")
    print("=" * 50)
    
    # Test updating buy threshold
    result = update_algorithm(buy_threshold=5.0)
    print(f"Update buy_threshold to 5.0: {result}")
    
    # Test updating multiple parameters
    result = update_algorithm(
        buy_threshold=4.0,
        sell_threshold=3.0,
        max_position=100
    )
    print(f"Update multiple params: {result}")
    
    # Test with no changes
    result = update_algorithm()
    print(f"Update with no params: {result}")


def test_get_status():
    """Test the get_status function."""
    print("\n" + "=" * 50)
    print("Testing get_status()")
    print("=" * 50)
    
    # Test with account 1, asset 1
    result = get_status(account_id=1, asset_id=1)
    print(f"Status for account 1, asset 1:\n{result}\n")
    
    # Test with account 1, asset 2
    result = get_status(account_id=1, asset_id=2)
    print(f"Status for account 1, asset 2:\n{result}\n")
    
    # Test with invalid IDs
    result = get_status(account_id=999, asset_id=999)
    print(f"Status with invalid IDs: {result}")


if __name__ == "__main__":
    print("\n" + "-" * 50)
    print("ORCHESTRATOR TEST SUITE")
    print("-" * 50)
    
    try:
        test_run_tick()
        test_update_algorithm()
        test_get_status()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"\nx Error during testing: {e}")
        import traceback
        traceback.print_exc()
