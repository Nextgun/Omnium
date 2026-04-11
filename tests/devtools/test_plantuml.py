"""
test_plantuml.py — Tests for utils.plantuml.
"""

import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from devtools.utils.plantuml import ensure_plantuml_jar, render_puml


class TestEnsurePlantUmlJar:
    def test_skips_download_when_jar_exists(self, tmp_path):
        jar = tmp_path / "plantuml.jar"
        jar.write_text("fake jar")

        with mock.patch("urllib.request.urlretrieve") as mock_dl:
            result = ensure_plantuml_jar(str(tmp_path), "http://example.com/plantuml.jar")
            mock_dl.assert_not_called()

        assert result == str(jar)

    def test_downloads_when_missing(self, tmp_path):
        dest = tmp_path / "lib"

        with mock.patch("urllib.request.urlretrieve") as mock_dl:
            result = ensure_plantuml_jar(str(dest), "http://example.com/plantuml.jar")
            mock_dl.assert_called_once()

        assert result.endswith("plantuml.jar")

    def test_creates_directory(self, tmp_path):
        dest = tmp_path / "nested" / "lib"
        assert not dest.exists()

        with mock.patch("urllib.request.urlretrieve"):
            ensure_plantuml_jar(str(dest), "http://example.com/plantuml.jar")

        assert dest.exists()


class TestRenderPuml:
    def test_raises_if_puml_missing(self):
        with pytest.raises(FileNotFoundError, match="PUML file not found"):
            render_puml("/nonexistent.puml", "/some/plantuml.jar")

    def test_raises_if_jar_missing(self, tmp_path):
        puml = tmp_path / "test.puml"
        puml.write_text("@startuml\n@enduml")

        with pytest.raises(FileNotFoundError, match="PlantUML jar not found"):
            render_puml(str(puml), "/nonexistent/plantuml.jar")

    def test_raises_if_java_missing(self, tmp_path):
        puml = tmp_path / "test.puml"
        puml.write_text("@startuml\n@enduml")
        jar = tmp_path / "plantuml.jar"
        jar.write_text("fake")

        with mock.patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="java not found"):
                render_puml(str(puml), str(jar))
