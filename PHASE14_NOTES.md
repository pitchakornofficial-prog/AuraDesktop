# Phase 14 notes — telemetry reliability

Changes:
- Added pure, unit-testable helpers for network rate calculation, rate formatting, and bounded percentage values.
- Network adapter counter resets no longer create negative RX/TX rates.
- Invalid telemetry formatting is represented as `Unavailable` instead of leaking malformed values into the UI.
- Monitor progress bars clamp percentages to the 0–100 range.

Validation performed in the current development environment:
- Python compileall: PASS
- Unit tests: see reported run result
- ZIP integrity: see reported archive check

Not tested here:
- Windows 11 GUI/runtime behavior
- Real hardware telemetry and multiple displays
- PyInstaller/NSIS Windows installer build

The application build must use Python 3.15.0 exactly; no Python version is changed by these files.
