"""
test_git_hooks.py — Tests for utils.git_hooks.

Uses a temporary directory to simulate a .git/hooks/ structure.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from devtools.utils.git_hooks import _BEGIN_MARKER, ensure_pre_commit_hook

SAMPLE_CHECK = {
    "id": "test-check",
    "description": "Run tests before commit",
    "command": "python -m pytest",
}


@pytest.fixture
def fake_repo(tmp_path):
    """Create a minimal fake repo with .git/hooks/."""
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    return tmp_path


class TestEnsurePreCommitHook:
    def test_creates_hook_file_when_missing(self, fake_repo):
        hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
        assert not hook_path.exists()

        ensure_pre_commit_hook(str(fake_repo), [SAMPLE_CHECK])

        assert hook_path.exists()
        content = hook_path.read_text()
        assert "test-check" in content
        assert "python -m pytest" in content

    def test_hook_is_executable(self, fake_repo):
        ensure_pre_commit_hook(str(fake_repo), [SAMPLE_CHECK])
        hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
        assert os.access(str(hook_path), os.X_OK)

    def test_idempotent_no_duplication(self, fake_repo):
        ensure_pre_commit_hook(str(fake_repo), [SAMPLE_CHECK])
        ensure_pre_commit_hook(str(fake_repo), [SAMPLE_CHECK])  # run again

        hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        marker = _BEGIN_MARKER.format(id="test-check")
        assert content.count(marker) == 1, "Block should appear exactly once"

    def test_multiple_checks_appended(self, fake_repo):
        check_a = {**SAMPLE_CHECK, "id": "check-a", "command": "echo a"}
        check_b = {**SAMPLE_CHECK, "id": "check-b", "command": "echo b"}

        ensure_pre_commit_hook(str(fake_repo), [check_a, check_b])

        content = (fake_repo / ".git" / "hooks" / "pre-commit").read_text()
        assert "check-a" in content
        assert "check-b" in content

    def test_preserves_existing_content(self, fake_repo):
        hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'existing'\n")

        ensure_pre_commit_hook(str(fake_repo), [SAMPLE_CHECK])

        content = hook_path.read_text()
        assert "existing" in content
        assert "test-check" in content
