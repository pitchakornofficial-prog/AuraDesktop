# Phase 17 — Reliable Screensaver Image Sources

## Changes
- Extracted slideshow image discovery into a pure, testable helper module.
- Folder sources now list supported image extensions only, skip directories and missing paths, and use stable case-insensitive ordering.
- Wallpaper Favorites sources preserve the user's saved order while skipping missing/non-image files and duplicate references to the same resolved file.
- Screensaver now uses the same discovery logic for its slideshow image list.

## Validation in this development environment
- `python -m compileall -q .`: PASS
- `python -m unittest discover -s tests -v`: PASS (34 tests)
- ZIP integrity: to be checked after packaging.

## Not tested / not built
- Windows 11 screensaver runtime, Control Panel preview/registration, multi-monitor operation, and real image rendering: NOT TESTED.
- Exact Python 3.15.0 runtime and dependency compatibility: NOT TESTED here.
- Windows executable and installer: NOT BUILT.
