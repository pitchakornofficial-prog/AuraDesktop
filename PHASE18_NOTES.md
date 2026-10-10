# Phase 18 — Startup Integration Reliability

## Changes
- Moved Windows per-user startup registration out of the main UI class into `core/startup.py`.
- Centralized Run-key name/path and command construction.
- Quotes executable and source script paths to support spaces in installation paths.
- Ensures the registry handle is closed in all cases and safely tolerates an already-removed startup value.
- Added unit tests using a fake registry module; no real registry writes occur in automated tests.

## Validation
- `python -m compileall -q .`: PASS
- `python -m unittest discover -s tests -v`: PASS (41 tests)
- ZIP integrity: checked after packaging.

## Not tested / not built
- Actual Windows 11 Run registry integration and sign-in startup: NOT TESTED.
- Exact Python 3.15.0 runtime and dependency compatibility: NOT TESTED here.
- Windows GUI behavior, executable, and installer: NOT TESTED / NOT BUILT.
