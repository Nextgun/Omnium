"""
test_conda.py — Tests for utils.conda.

These tests mock subprocess and filesystem calls so they run anywhere
without actually installing Miniconda.
"""

import json
import os
import sys
from unittest import mock

# Allow imports from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from devtools.utils.conda import _env_exists, _find_conda, ensure_conda_env, ensure_miniconda


class TestFindConda:
    def test_returns_path_when_conda_on_path(self):
        with mock.patch("shutil.which", return_value="/usr/local/bin/conda"):
            assert _find_conda() == "/usr/local/bin/conda"

    def test_returns_none_when_missing(self):
        with mock.patch("shutil.which", return_value=None):
            assert _find_conda() is None


class TestEnvExists:
    def test_true_when_env_listed(self):
        env_json = json.dumps({"envs": ["/home/user/miniconda3/envs/plantuml-env"]})
        result = mock.Mock(returncode=0, stdout=env_json)
        with mock.patch("subprocess.run", return_value=result):
            assert _env_exists("/usr/bin/conda", "plantuml-env") is True

    def test_false_when_env_missing(self):
        env_json = json.dumps({"envs": ["/home/user/miniconda3/envs/other"]})
        result = mock.Mock(returncode=0, stdout=env_json)
        with mock.patch("subprocess.run", return_value=result):
            assert _env_exists("/usr/bin/conda", "plantuml-env") is False

    def test_false_on_command_failure(self):
        result = mock.Mock(returncode=1, stdout="")
        with mock.patch("subprocess.run", return_value=result):
            assert _env_exists("/usr/bin/conda", "plantuml-env") is False


class TestEnsureMiniconda:
    def test_returns_existing_conda(self):
        with mock.patch("devtools.utils.conda._find_conda", return_value="/usr/bin/conda"):
            assert ensure_miniconda() == "/usr/bin/conda"

    def test_installs_when_missing(self):
        with (
            mock.patch("devtools.utils.conda._find_conda", return_value=None),
            mock.patch("devtools.utils.conda._install_miniconda"),
            mock.patch("os.path.isfile", return_value=True),
            mock.patch("devtools.utils.conda._is_unix", return_value=True),
        ):
            result = ensure_miniconda()
            assert "conda" in result


class TestEnsureCondaEnv:
    def test_skips_creation_when_env_exists(self):
        with (
            mock.patch("devtools.utils.conda._env_exists", return_value=True),
            mock.patch("subprocess.check_call") as mock_call,
        ):
            ensure_conda_env("/usr/bin/conda", "myenv")
            # check_call should NOT be called for creation
            mock_call.assert_not_called()

    def test_creates_env_when_missing(self):
        with (
            mock.patch("devtools.utils.conda._env_exists", return_value=False),
            mock.patch("subprocess.check_call") as mock_call,
        ):
            ensure_conda_env("/usr/bin/conda", "myenv", python_version="3.11")
            mock_call.assert_called_once_with([
                "/usr/bin/conda", "create", "-y", "-n", "myenv", "python=3.11",
            ])

    def test_installs_requirements_when_file_exists(self):
        with (
            mock.patch("devtools.utils.conda._env_exists", return_value=True),
            mock.patch("os.path.isfile", return_value=True),
            mock.patch("devtools.utils.conda._env_pip", return_value="/envs/myenv/bin/pip"),
            mock.patch("subprocess.check_call") as mock_call,
        ):
            ensure_conda_env("/usr/bin/conda", "myenv", requirements_file="reqs.txt")
            mock_call.assert_called_once_with(["/envs/myenv/bin/pip", "install", "-r", "reqs.txt"])
