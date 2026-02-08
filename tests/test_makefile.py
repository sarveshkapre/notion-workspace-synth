import subprocess
import sys
from pathlib import Path


def test_makefile_falls_back_to_environment_python_when_venv_is_missing() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    missing_venv = repo_root / ".tmp-makefile-missing-venv"
    python_cmd = sys.executable

    result = subprocess.run(
        [
            "make",
            "-n",
            "lint",
            f"VENV={missing_venv}",
            f"PYTHON={python_cmd}",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"{missing_venv}/bin/python -m ruff check src tests" not in result.stdout
    assert f"{python_cmd} -m ruff check src tests" in result.stdout
