"""Static checks for the source package before any Windows build is attempted."""
from __future__ import annotations
from pathlib import Path


def audit_release_sources(root: str | Path) -> list[str]:
    """Return blocking source-package issues; an empty list means static checks pass."""
    base = Path(root)
    issues: list[str] = []
    build_path = base / "installer" / "build_windows.ps1"
    nsi_path = base / "installer" / "AuraDesktop.nsi"
    if not build_path.is_file():
        issues.append("Missing installer/build_windows.ps1")
    if not nsi_path.is_file():
        issues.append("Missing installer/AuraDesktop.nsi")
    if issues:
        return issues

    build = build_path.read_text(encoding="utf-8", errors="replace")
    nsi = nsi_path.read_text(encoding="utf-8", errors="replace")
    if '"Python 3.15.0"' not in build or "No version changes were made" not in build:
        issues.append("Build script must enforce exact Python 3.15.0 without changing Python")
    if "AuraDesktopSaver.exe" not in build or "AuraDesktop.scr" not in build:
        issues.append("Build script must package the screensaver executable as .scr")
    if "RequestExecutionLevel user" not in nsi:
        issues.append("Installer must use per-user execution level")
    if "AuraDesktop-Setup.exe" not in nsi:
        issues.append("Installer output filename is not configured")
    if "DeleteRegValue HKCU" not in nsi:
        issues.append("Uninstaller must clean up the per-user registry values it owns")
    return issues
