"""
vscode.py — Idempotent VS Code extension installation.

Uses the `code` CLI. If VS Code isn't installed, logs a warning and
continues (non-fatal — teammates without VS Code shouldn't be blocked).
"""

import logging
import shutil
import subprocess

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_vscode_extensions(extensions: list[str]) -> None:
    """
    Install each extension if not already present.

    Silently skips if the `code` CLI is not available.
    """
    code = shutil.which("code")
    if not code:
        log.warning("VS Code CLI ('code') not found — skipping extension install")
        return

    installed = _list_installed(code)

    for ext in extensions:
        # Extension IDs are case-insensitive.
        if ext.lower() in installed:
            log.info("VS Code extension '%s' already installed — skipped", ext)
        else:
            log.info("Installing VS Code extension '%s'...", ext)
            subprocess.check_call([code, "--install-extension", ext, "--force"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _list_installed(code_path: str) -> set[str]:
    """Return a lowercase set of currently installed extension IDs."""
    result = subprocess.run(
        [code_path, "--list-extensions"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.warning("Could not list VS Code extensions: %s", result.stderr)
        return set()

    return {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}
