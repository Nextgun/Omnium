"""
conda.py — Miniconda detection, installation, and environment management.

Every function is idempotent: calling it when the desired state already
exists logs a skip message and returns immediately.
"""

import logging
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_miniconda() -> str:
    """
    Return the path to a working `conda` executable.

    If conda is already on $PATH, return it immediately.
    Otherwise, download and install Miniconda for the current platform
    into ~/miniconda3, then return the new conda path.
    """
    existing = _find_conda()
    if existing:
        log.info("conda already available: %s", existing)
        return existing

    log.info("conda not found — installing Miniconda...")
    install_dir = Path.home() / "miniconda3"
    _install_miniconda(install_dir)

    conda_path = str(install_dir / "bin" / "conda") if _is_unix() else str(install_dir / "Scripts" / "conda.exe")
    if not os.path.isfile(conda_path):
        raise RuntimeError(f"Miniconda install succeeded but conda not found at {conda_path}")

    log.info("Miniconda installed: %s", conda_path)
    return conda_path


def ensure_conda_env(
    conda_path: str,
    env_name: str,
    python_version: str = "3.11",
    requirements_file: str | None = None,
) -> None:
    """
    Ensure a named conda environment exists with the given Python version.

    If *requirements_file* is provided and exists, install/update packages
    via pip inside the environment.
    """
    if _env_exists(conda_path, env_name):
        log.info("conda env '%s' already exists — skipping creation", env_name)
    else:
        log.info("Creating conda env '%s' (python=%s)...", env_name, python_version)
        subprocess.check_call([
            conda_path, "create", "-y", "-n", env_name,
            f"python={python_version}",
        ])

    # Install / sync requirements (always runs — pip is idempotent for
    # already-installed packages at the same version).
    if requirements_file and os.path.isfile(requirements_file):
        log.info("Installing requirements into '%s'...", env_name)
        pip_path = _env_pip(conda_path, env_name)
        subprocess.check_call([pip_path, "install", "-r", requirements_file])
    else:
        log.info("No requirements file to install.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_conda() -> str | None:
    """Return the full path to conda if it's on $PATH, else None."""
    return shutil.which("conda")


def _is_unix() -> bool:
    return platform.system() in ("Linux", "Darwin")


def _miniconda_installer_url() -> str:
    """Return the appropriate Miniconda installer URL for this platform."""
    system = platform.system()
    arch = platform.machine()

    if system == "Linux":
        arch_tag = "x86_64" if arch == "x86_64" else "aarch64"
        return f"https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-{arch_tag}.sh"
    elif system == "Darwin":
        arch_tag = "x86_64" if arch == "x86_64" else "arm64"
        return f"https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-{arch_tag}.sh"
    elif system == "Windows":
        return "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    else:
        raise RuntimeError(f"Unsupported platform: {system}/{arch}")


def _install_miniconda(install_dir: Path) -> None:
    """Download and silently install Miniconda to *install_dir*."""
    url = _miniconda_installer_url()
    system = platform.system()

    with tempfile.TemporaryDirectory() as tmpdir:
        if system == "Windows":
            installer = os.path.join(tmpdir, "miniconda_installer.exe")
            _download(url, installer)
            subprocess.check_call([
                installer, "/InstallationType=JustMe", "/AddToPath=0",
                "/RegisterPython=0", f"/D={install_dir}", "/S",
            ])
        else:
            installer = os.path.join(tmpdir, "miniconda_installer.sh")
            _download(url, installer)
            os.chmod(installer, 0o755)
            subprocess.check_call([
                "bash", installer, "-b", "-p", str(install_dir),
            ])


def _download(url: str, dest: str) -> None:
    """Download a URL to a local file using urllib (no extra deps)."""
    import urllib.request
    log.info("Downloading %s ...", url)
    urllib.request.urlretrieve(url, dest)


def _env_exists(conda_path: str, env_name: str) -> bool:
    """Check whether a named conda environment already exists."""
    result = subprocess.run(
        [conda_path, "env", "list", "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False

    import json
    data = json.loads(result.stdout)
    # data["envs"] is a list of absolute paths; the env name is the last component.
    return any(
        os.path.basename(p) == env_name
        for p in data.get("envs", [])
    )


def _env_pip(conda_path: str, env_name: str) -> str:
    """Return the pip executable inside a conda environment."""
    result = subprocess.run(
        [conda_path, "run", "-n", env_name, "which", "pip"],
        capture_output=True, text=True,
    )
    pip_path = result.stdout.strip()
    if pip_path and os.path.isfile(pip_path):
        return pip_path

    # Fallback: call pip through conda run
    # This returns a synthetic path usable via subprocess
    return f"{conda_path} run -n {env_name} pip"
