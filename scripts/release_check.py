#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import tomllib


def _read_version(root: Path) -> str:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    return str(pyproject["project"]["version"])


def _read_package_version(root: Path) -> str:
    init_py = (root / "src" / "notion_synth" / "__init__.py").read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_py)
    if not match:
        raise ValueError("Could not find __version__ in src/notion_synth/__init__.py")
    return match.group(1)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    try:
        version = _read_version(root)
    except Exception as exc:
        errors.append(f"Failed to read pyproject version: {exc}")
        version = "unknown"

    try:
        pkg_version = _read_package_version(root)
        if version != "unknown" and pkg_version != version:
            errors.append(
                f"Version mismatch: pyproject.toml has {version} but src/notion_synth/__init__.py has {pkg_version}"
            )
    except Exception as exc:
        errors.append(str(exc))

    release_doc = (root / "docs" / "RELEASE.md").read_text()
    if version != "unknown" and f"## v{version} checklist" not in release_doc:
        errors.append(f"docs/RELEASE.md missing checklist header for v{version}")
    if "Update `CHANGELOG.md`" not in release_doc:
        errors.append("docs/RELEASE.md should reference updating CHANGELOG.md (repo root)")

    changelog = (root / "CHANGELOG.md").read_text()
    if version != "unknown" and f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md missing section header '## [{version}]'")

    if version != "unknown":
        try:
            out = subprocess.check_output(
                ["git", "tag", "--list", f"v{version}"],
                cwd=root,
                text=True,
            ).strip()
            if out:
                errors.append(f"git tag v{version} already exists")
        except Exception as exc:
            errors.append(f"Failed to check git tag existence for v{version}: {exc}")

    if errors:
        for err in errors:
            print(f"release-check: {err}", file=sys.stderr)
        return 1

    print(f"release-check: ok (v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

