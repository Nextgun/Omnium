"""
plantuml.py — PlantUML jar management and rendering helpers.

Idempotent: downloading the jar is skipped if it already exists.
"""

import logging
import os
import shutil
import subprocess
import urllib.request

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_plantuml_jar(
    dest_dir: str,
    jar_url: str,
    jar_name: str = "plantuml.jar",
) -> str:
    """
    Ensure the PlantUML jar exists at *dest_dir*/*jar_name*.

    Downloads from *jar_url* if missing. Returns the full jar path.
    """
    os.makedirs(dest_dir, exist_ok=True)
    jar_path = os.path.join(dest_dir, jar_name)

    if os.path.isfile(jar_path):
        log.info("PlantUML jar already exists: %s — skipped", jar_path)
        return jar_path

    log.info("Downloading PlantUML jar from %s ...", jar_url)
    urllib.request.urlretrieve(jar_url, jar_path)
    log.info("Saved PlantUML jar to %s", jar_path)
    return jar_path


def render_puml(
    puml_file: str,
    jar_path: str,
    output_format: str = "png",
    output_dir: str | None = None,
) -> str:
    """
    Render a single .puml file to the specified format.

    Returns the path of the generated output file.
    Requires java on $PATH.
    """
    if not os.path.isfile(puml_file):
        raise FileNotFoundError(f"PUML file not found: {puml_file}")
    if not os.path.isfile(jar_path):
        raise FileNotFoundError(f"PlantUML jar not found: {jar_path}")

    java = shutil.which("java")
    if not java:
        raise RuntimeError("java not found on $PATH — install a JDK to render PlantUML diagrams")

    cmd = [java, "-jar", jar_path, f"-t{output_format}", puml_file]
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        cmd.extend(["-o", os.path.abspath(output_dir)])

    log.info("Rendering %s → %s", puml_file, output_format)
    subprocess.check_call(cmd)

    # Infer output path (PlantUML writes alongside input unless -o is given).
    base = os.path.splitext(os.path.basename(puml_file))[0]
    if output_dir:
        return os.path.join(output_dir, f"{base}.{output_format}")
    return os.path.join(os.path.dirname(puml_file), f"{base}.{output_format}")
