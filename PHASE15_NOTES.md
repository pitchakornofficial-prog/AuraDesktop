# Phase 15 — Telemetry hardening

- Hardened network sampling against malformed counters, negative counters, non-finite timestamps, and monotonic clock regressions. Invalid samples preserve the last valid baseline.
- Extracted NVIDIA-SMI CSV parsing into a pure helper. N/A, malformed, non-finite, or out-of-range values remain explicitly unavailable instead of being displayed as real readings.
- Added isolated regression tests for invalid network samples, clock regressions, valid GPU output, and invalid GPU output.

## Local verification
- Python syntax / compileall: to be run in the packaging environment.
- Unit tests: to be run in the packaging environment.
- Windows 11 hardware/GUI integration: NOT TESTED here.
- Installer: NOT BUILT here.
