"""
test_vscode.py — Tests for utils.vscode.
"""

import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from devtools.utils.vscode import _list_installed, ensure_vscode_extensions


class TestListInstalled:
    def test_parses_extension_list(self):
        result = mock.Mock(returncode=0, stdout="jebbs.plantuml\nms-python.python\n")
        with mock.patch("subprocess.run", return_value=result):
            installed = _list_installed("/usr/bin/code")
        assert "jebbs.plantuml" in installed
        assert "ms-python.python" in installed

    def test_returns_empty_on_failure(self):
        result = mock.Mock(returncode=1, stdout="", stderr="error")
        with mock.patch("subprocess.run", return_value=result):
            assert _list_installed("/usr/bin/code") == set()


class TestEnsureVscodeExtensions:
    def test_skips_when_code_not_found(self):
        with mock.patch("shutil.which", return_value=None):
            # Should not raise
            ensure_vscode_extensions(["jebbs.plantuml"])

    def test_skips_already_installed(self):
        with (
            mock.patch("shutil.which", return_value="/usr/bin/code"),
            mock.patch("devtools.utils.vscode._list_installed", return_value={"jebbs.plantuml"}),
            mock.patch("subprocess.check_call") as mock_call,
        ):
            ensure_vscode_extensions(["jebbs.plantuml"])
            mock_call.assert_not_called()

    def test_installs_missing_extension(self):
        with (
            mock.patch("shutil.which", return_value="/usr/bin/code"),
            mock.patch("devtools.utils.vscode._list_installed", return_value=set()),
            mock.patch("subprocess.check_call") as mock_call,
        ):
            ensure_vscode_extensions(["jebbs.plantuml"])
            mock_call.assert_called_once_with([
                "/usr/bin/code", "--install-extension", "jebbs.plantuml", "--force",
            ])
