"""Run before building AuraDesktop executables or the installer on Windows."""
from __future__ import annotations
import importlib.util
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from auradesktop.core.preflight import (  # noqa: E402
    missing_required_files, python_version_matches, windows_build_is_supported,
)


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python version exactly 3.15.0", python_version_matches(sys.version_info), platform.python_version()))
    build = platform.version().split(".")[-1]
    checks.append(("Windows 11", windows_build_is_supported(sys.platform, build), f"platform={sys.platform}, version={platform.version()}"))
    missing = missing_required_files(ROOT)
    checks.append(("Required source and installer files", not missing, ", ".join(missing) if missing else "all present"))
    for module in ("PySide6", "psutil", "PyInstaller"):
        found = importlib.util.find_spec(module) is not None
        checks.append((f"Python module: {module}", found, "available" if found else "not installed"))
    nsis = shutil.which("makensis")
    checks.append(("NSIS compiler", nsis is not None, nsis or "not found (required for Setup.exe)"))

    print("AuraDesktop Windows preflight")
    print("=============================")
    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {label}: {detail}")
    failed = [label for label, passed, _ in checks if not passed]
    if failed:
        print("\nPreflight blocked. Resolve the FAIL items before building. No Python version was changed.")
        return 1
    print("\nPreflight passed. This does not replace GUI, screensaver, tray, or installer testing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
