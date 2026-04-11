#!/usr/bin/env python3
"""
watcher.py — Driver script: watches .puml files and re-renders on change.

Usage:
    python src/watcher.py [--watch-dir .] [--jar lib/plantuml.jar] [--format png]

This is a *driver script* (executed directly), not library code.
It imports from utils but is not itself importable by other modules.
"""

import argparse
import logging
import os
import sys
import time

# Driver script — allowed to adjust path once.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from devtools.utils.plantuml import render_puml

log = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch .puml files and render on change")
    parser.add_argument("--watch-dir", default=".", help="Directory to watch (default: cwd)")
    parser.add_argument("--jar", default="lib/plantuml.jar", help="Path to plantuml.jar")
    parser.add_argument("--format", default="png", help="Output format (default: png)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        log.error(
            "watchdog is not installed. Run:\n"
            "  pip install -r src/requirements.txt\n"
            "or activate the conda environment first."
        )
        return 1

    class PumlHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            if event.src_path.endswith(".puml"):
                log.info("Change detected: %s", event.src_path)
                try:
                    render_puml(event.src_path, args.jar, output_format=args.format)
                except Exception as exc:
                    log.error("Render failed for %s: %s", event.src_path, exc)

    observer = Observer()
    observer.schedule(PumlHandler(), args.watch_dir, recursive=True)
    observer.start()
    log.info("Watching %s for .puml changes (Ctrl+C to stop)...", os.path.abspath(args.watch_dir))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
