# Phase 20 — Windows Build Preflight

- Added `tools/preflight_windows.py`, a read-only preflight intended to run before executable or installer creation.
- It checks exact Python 3.15.0, Windows 11 build number, required source/installer files, PySide6, psutil, PyInstaller, and NSIS (`makensis`).
- The script exits non-zero if any required check fails and never installs or changes Python itself.
- Pure detection helpers have automated tests; running the preflight is not a substitute for target-machine testing.
