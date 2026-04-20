#!/usr/bin/env python3
"""
Quick test runner for the trading algorithm test suite.
Run this script to execute all tests and see results.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --verbose    # Run with verbose output
    python run_tests.py --quick      # Run with minimal output
"""

import subprocess
import sys

def run_tests(verbose=False):
    """Run the trading algorithm test suite."""
    cmd = ["python", "-m", "pytest", "tests/test_trading_algorithm.py"]
    
    if verbose:
        cmd.append("-vv")
        cmd.append("--tb=long")
    else:
        cmd.append("-v")
    
    print("=" * 70)
    print("OMNIUM TRADING ALGORITHM TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        result = subprocess.run(cmd, cwd=".")
        return result.returncode
    except FileNotFoundError:
        print("ERROR: pytest not found.")
        print()
        print("Please install pytest first:")
        print("  pip install pytest")
        return 1

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-vv" in sys.argv
    quick = "--quick" in sys.argv or "-q" in sys.argv
    
    exit_code = run_tests(verbose=verbose)
    
    print()
    print("=" * 70)
    if exit_code == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)
    
    sys.exit(exit_code)
