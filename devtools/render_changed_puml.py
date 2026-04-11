#!/usr/bin/env python3
"""
render_changed_puml.py — Called by the pre-commit hook.

Finds staged .puml files and renders them so the output is always
in sync with the committed source. Exits non-zero if rendering fails.
"""

import logging
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from devtools.utils.plantuml import render_puml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

JAR_PATH = os.path.join(os.path.dirname(__file__), "..", "lib", "plantuml.jar")


def staged_puml_files() -> list[str]:
    """Return list of staged .puml files (paths relative to repo root)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [f for f in result.stdout.splitlines() if f.endswith(".puml")]


def main() -> int:
    files = staged_puml_files()
    if not files:
        log.info("No staged .puml files — nothing to render.")
        return 0

    errors = 0
    for puml in files:
        try:
            render_puml(puml, JAR_PATH)
            # Re-stage the rendered output so it's included in the commit.
            base = os.path.splitext(puml)[0]
            rendered = f"{base}.png"
            if os.path.isfile(rendered):
                subprocess.check_call(["git", "add", rendered])
        except Exception as exc:
            log.error("Failed to render %s: %s", puml, exc)
            errors += 1

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
