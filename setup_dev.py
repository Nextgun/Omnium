#!/usr/bin/env python3
"""
setup_dev.py — Developer Environment Setup (idempotent).

Run this once after cloning the repo. Safe to re-run at any time.

Steps:
    1. Ensure conda is installed (Anaconda, Miniconda, or Miniforge)
    2. Create/update the 'omnium-dev' conda environment
    3. Install the omnium package in editable mode
    4. Download PlantUML jar if missing
    5. Install VS Code extensions

Usage:
    python setup_dev.py
"""

import logging
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# setup_dev.py lives at the repo root, so Python automatically adds the
# repo root to sys.path. This means `from devtools.utils import ...` works
# without any sys.path hacking.
# ---------------------------------------------------------------------------
from devtools.utils import (
    ensure_conda,
    ensure_conda_env,
    ensure_plantuml_jar,
    ensure_vscode_extensions,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — centralised so nothing is buried in helper modules.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    # ── Conda ──
    "conda_env_name": "omnium-dev",
    "python_version": "3.11",
    "requirements_file": os.path.join(REPO_ROOT, "requirements.txt"),

    # ── PlantUML ──
    "plantuml_jar_dir": os.path.join(REPO_ROOT, "lib"),
    "plantuml_jar_url": (
        "https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-1.2024.8.jar"
    ),
    "plantuml_jar_name": "plantuml.jar",

    # ── VS Code ──
    "vscode_extensions": [
        "jebbs.plantuml",
        "charliermarsh.ruff",      # Ruff linter extension
        "ms-python.python",
    ],

    # ── Git Pre-Commit Hooks ──
    "git_hook_checks": [
        {
            "id": "plantuml-render",
            "description": "Re-render changed .puml files before commit",
            "command": "python devtools/render_changed_puml.py",
        },
        {
            "id": "ruff-lint",
            "description": "Lint staged Python files with ruff",
            "command": (
                'STAGED=$(git diff --cached --name-only --diff-filter=ACM -- "*.py")\n'
                'if [ -n "$STAGED" ]; then\n'
                '  echo "$STAGED" | xargs ruff check --config ruff.toml\n'
                'fi'
            ),
        },
    ],
}


def _install_editable_package(conda_path: str, env_name: str) -> None:
    """
    Install the omnium package in editable (development) mode.

    This makes `from omnium.models import Price` work from anywhere
    without needing to set PYTHONPATH manually. Uses the pyproject.toml
    at repo root.
    """
    log.info("Installing omnium package in editable mode...")
    pip_cmd = [conda_path, "run", "-n", env_name, "pip", "install", "-e", REPO_ROOT]
    try:
        subprocess.check_call(pip_cmd)
        log.info("omnium package installed in editable mode")
    except subprocess.CalledProcessError:
        log.warning(
            "Editable install failed — you may need to run:\n"
            "    conda activate %s && pip install -e .\n"
            "manually from the repo root.", env_name,
        )


def main() -> int:
    log.info("=" * 60)
    log.info("  Omnium Developer Setup (idempotent)")
    log.info("=" * 60)

    # 1. Conda (Anaconda, Miniconda, or Miniforge)
    conda_path = ensure_conda()

    # 2. Conda environment + deps
    ensure_conda_env(
        conda_path=conda_path,
        env_name=CONFIG["conda_env_name"],
        python_version=CONFIG["python_version"],
        requirements_file=CONFIG["requirements_file"],
    )

    # 3. Editable install of omnium package
    _install_editable_package(conda_path, CONFIG["conda_env_name"])

    # 4. PlantUML jar
    ensure_plantuml_jar(
        dest_dir=CONFIG["plantuml_jar_dir"],
        jar_url=CONFIG["plantuml_jar_url"],
        jar_name=CONFIG["plantuml_jar_name"],
    )

    # 5. Git pre-commit hook — disabled for now (some team members
    #    struggle with git hooks). Revisit post-deadline or move to CI.
    # ensure_pre_commit_hook(
    #     repo_root=REPO_ROOT,
    #     checks=CONFIG["git_hook_checks"],
    # )

    # 6. VS Code extensions
    ensure_vscode_extensions(CONFIG["vscode_extensions"])

    log.info("=" * 60)
    log.info("  Setup complete!")
    log.info("")
    log.info("  Next steps:")
    log.info("    conda activate %s", CONFIG["conda_env_name"])
    log.info("    python -m flask --app src.omnium.api run  # Run the API")
    log.info("    pytest                    # Run tests")
    log.info("    pytest tests/benchmarks   # Run benchmarks")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
