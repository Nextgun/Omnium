"""
omnium — Main Entry Point
============================

Boots the entire Omnium system:
    1. Load config from environment
    2. Initialize the Orchestrator (which wires all modules)
    3. Start the system
    4. Handle graceful shutdown on Ctrl+C

Usage:
    python -m omnium                  # Run with defaults
    OMNIUM_SYMBOLS=AAPL,TSLA python -m omnium  # Override symbols
"""

import signal
import sys

from omnium.orchestration import Orchestrator
from omnium.utils import Config, setup_logging


def main() -> None:
    setup_logging(level="INFO")

    config = Config()
    print("\n  Omnium v0.1.0 — Day Trading Platform")
    print(f"  Config: {config}\n")

    orchestrator = Orchestrator(config)

    # Graceful shutdown on Ctrl+C
    def shutdown_handler(signum, frame):
        print("\n\n  Received shutdown signal...")
        orchestrator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start
    orchestrator.start()

    # Keep main thread alive (scheduler + live fetcher run in background)
    print("\n  Omnium is running. Press Ctrl+C to stop.\n")
    try:
        while orchestrator.is_running:
            signal.pause()  # Sleep until a signal arrives
    except AttributeError:
        # signal.pause() not available on Windows
        import time
        while orchestrator.is_running:
            time.sleep(1)


if __name__ == "__main__":
    main()
