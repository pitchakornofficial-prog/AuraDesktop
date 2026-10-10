"""Pure checks shared by the Windows release preflight and its unit tests."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable

REQUIRED_PYTHON = (3, 15, 0)
MIN_WINDOWS_11_BUILD = 22000
REQUIRED_SOURCE_FILES = (
    Path("main.py"),
    Path("screensaver_entry.py"),
    Path("requirements.txt"),
    Path("src/auradesktop/app.py"),
    Path("src/auradesktop/screensaver.py"),
    Path("installer/AuraDesktop.nsi"),
    Path("installer/build_windows.ps1"),
)


def python_version_matches(version_info: Iterable[int]) -> bool:
    """Require exactly Python 3.15.0, not merely a compatible minor version."""
    version = tuple(version_info)
    return version[:3] == REQUIRED_PYTHON


def windows_build_is_supported(platform_name: str, build_number: int | str) -> bool:
    """Recognize Windows 11 by the Windows platform and build number."""
    if platform_name != "win32":
        return False
    try:
        return int(build_number) >= MIN_WINDOWS_11_BUILD
    except (TypeError, ValueError):
        return False


def missing_required_files(root: str | Path) -> list[str]:
    """List required project files absent from a checkout or source archive."""
    base = Path(root)
    return [str(relative) for relative in REQUIRED_SOURCE_FILES if not (base / relative).is_file()]
