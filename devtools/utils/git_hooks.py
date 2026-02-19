"""
git_hooks.py — Idempotent git pre-commit hook management.

Git supports exactly one pre-commit file. Multiple behaviours are handled
by appending guarded blocks inside that file. Each block is wrapped in
sentinel comments so we can detect "already installed" and avoid duplication.

Hook blocks delegate to Python scripts rather than embedding logic inline.
"""

import logging
import os
import stat

log = logging.getLogger(__name__)

# Sentinel pattern — unique per check id.
_BEGIN_MARKER = "### BEGIN MANAGED BLOCK: {id} ###"
_END_MARKER = "### END MANAGED BLOCK: {id} ###"

_HOOK_HEADER = """#!/usr/bin/env bash
# Managed by setup.py — do not remove sentinel comments.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_pre_commit_hook(
    repo_root: str,
    checks: list[dict],
) -> None:
    """
    Ensure each check in *checks* is present in .git/hooks/pre-commit.

    Each check dict must have:
      - id:          unique string identifier
      - description: human-readable comment
      - command:     shell command to execute

    Idempotent: blocks whose sentinel already exists are skipped.
    """
    hook_path = os.path.join(repo_root, ".git", "hooks", "pre-commit")

    # Ensure the hook file exists with a shebang.
    if not os.path.isfile(hook_path):
        log.info("Creating pre-commit hook: %s", hook_path)
        os.makedirs(os.path.dirname(hook_path), exist_ok=True)
        _write(hook_path, _HOOK_HEADER)

    content = _read(hook_path)

    for check in checks:
        check_id = check["id"]
        begin = _BEGIN_MARKER.format(id=check_id)

        if begin in content:
            log.info("Hook block '%s' already present — skipped", check_id)
            continue

        block = _make_block(check)
        content += "\n" + block + "\n"
        log.info("Appended hook block '%s'", check_id)

    _write(hook_path, content)
    _make_executable(hook_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_block(check: dict) -> str:
    """Build a guarded shell block for one check."""
    check_id = check["id"]
    description = check.get("description", "")
    command = check["command"]

    return (
        f"{_BEGIN_MARKER.format(id=check_id)}\n"
        f"# {description}\n"
        f"{command}\n"
        f"if [ $? -ne 0 ]; then\n"
        f'  echo "Pre-commit check failed: {check_id}"\n'
        f"  exit 1\n"
        f"fi\n"
        f"{_END_MARKER.format(id=check_id)}"
    )


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def _make_executable(path: str) -> None:
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
