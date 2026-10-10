# AuraDesktop Source Build — Phase 8

This is a development source package, not a verified release. Phase 8 hardens settings persistence, adds isolated automated tests, improves handling of invalid wallpaper selections and missing telemetry dependencies, and supports common Windows screensaver command-line forms.

## Checks performed in this environment
- Python source syntax parsed / `compileall` completed.
- Isolated `SettingsStore` unit tests run against temporary files; user settings are not modified by tests.
- ZIP archive integrity checked after packaging.

## Not tested / not built here
- GUI runtime (PySide6 availability must be confirmed in the target environment).
- Windows 11 / Python 3.15.0 exact-version build.
- Desktop WorkerW parenting, wallpaper changes, tray behavior, Startup registry integration, `.scr` registration and Control Panel preview, multi-monitor behavior, GPU telemetry.
- Packaged EXE and installer are NOT BUILT in this environment.

## Release discipline
Do not mark Windows integration items PASS until tested on the target machine. Python must be exactly 3.15.0; build scripts must stop on mismatch and must not change the user's Python installation.


## Phase 9 update
- Added atomic settings rollback coverage and malformed-settings recovery test.
- Added confirmation before selecting a wallpaper favorite.
- Prevented unsupported non-Windows runs from persisting a requested desktop-clock state.
- Local verification is limited to syntax, unit tests, and archive integrity. Windows runtime integration and installer creation remain NOT TESTED / NOT BUILT.
- Final Phase 9 local test run: `python -m compileall -q .` PASS; `python -m unittest discover -s tests -v` PASS (6 tests).

## Phase 10 update
- System Tray visibility now follows the saved tray setting; close-to-tray is only active when tray support is enabled.
- Malformed boolean and path settings are normalized to safe defaults.
- Added two settings regression tests.
- This package is a development source archive. Windows GUI integration and the final installer remain NOT TESTED / NOT BUILT.

## Phase 11 update
- Added a pure screen-saver command-line parser for `/s`, `/c`, `/c:<HWND>`, `/p <HWND>`, and `/p:<HWND>` forms, with safe handling of missing/invalid handles.
- Screen-saver `/c` now launches AuraDesktop directly on the Screensaver page (source-run or packaged layout), instead of silently returning without opening configuration.
- Main application accepts `--page` / `--page=...` while keeping Dashboard as the default page.
- Added isolated tests for supported screen-saver argument forms. Windows Control Panel invocation and preview embedding remain NOT TESTED on this non-Windows environment.


## Phase 12 development update
- Added persistent absolute position for the draggable desktop clock, including negative virtual-desktop coordinates for left-side monitors.
- Added SettingsStore regression coverage for saved and malformed clock coordinates.
- Local checks are syntax/compile, unit tests, and ZIP integrity only; Windows shell behavior and installer build remain NOT TESTED / NOT BUILT.


## Phase 13 development update
- Screen-saver mode now creates a fullscreen surface for each detected display, keeping references alive for the event loop; this is intended to cover multi-monitor setups.
- Added exit-on-deliberate-mouse-movement behavior in addition to key and click exit, with a small movement threshold to reduce cursor-jitter exits.
- These changes are source-level only in this environment. Multi-monitor fullscreen behavior, cursor event behavior, Windows screensaver registration, and `.scr` launch remain NOT TESTED on Windows 11.

## Phase 14 — telemetry reliability
- Added unit-tested helpers for RX/TX rate calculation, binary rate formatting, and percentage clamping.
- Network counter resets are handled without negative rates.
- Current environment validation: compileall PASS; 20 unit tests PASS.
- Windows 11 GUI, hardware telemetry, and installer build remain NOT TESTED / NOT BUILT.


## Phase 15 — telemetry input validation
- Network telemetry now rejects malformed/negative counters and non-finite timestamps without corrupting the previous baseline; non-positive elapsed intervals return zero rates.
- NVIDIA-SMI parsing is isolated and rejects malformed, unavailable, non-finite, and out-of-range sensor values.
- Added regression tests for network sample corruption and GPU parsing.
- Windows hardware telemetry and Installer remain NOT TESTED / NOT BUILT.


## Phase 16
- Added removable Wallpaper Favorites; removal affects only the saved list, not the image file.
- Missing favorite files are labeled `(missing)` in the selector.
- Added pure helper tests for add, duplicate detection, invalid paths, removal, and display labels.
- Local validation: Compileall PASS; Unit Tests PASS (30 tests); ZIP integrity PASS after packaging.
- Windows GUI, Python 3.15.0 target environment, and installer build remain NOT TESTED / NOT BUILT.

## Phase 17 — screensaver image-source reliability
- Slideshow source discovery moved into a pure helper, with supported-extension filtering, missing-file filtering, duplicate-path removal, and deterministic folder ordering.
- Favorites retain user-defined order; folder slideshows use stable alphabetical ordering.
- Local validation: compileall PASS; 34 unit tests PASS.
- Windows 11 screensaver rendering/Control Panel integration, Python 3.15.0 exact runtime, and Installer remain NOT TESTED / NOT BUILT.

## Phase 18 validation update
- Startup command construction and per-user registry behavior are isolated in `src/auradesktop/core/startup.py`.
- Automated tests cover frozen/source commands, paths with spaces, enable/disable behavior, missing registry values, and non-Windows guard behavior.
- Current local validation: compileall PASS; 41 unit tests PASS. Windows registry behavior has been tested with a mock only, not against the real Windows registry.
- Python 3.15.0 target runtime: NOT TESTED. Windows executable/installer: NOT BUILT.


## Phase 19 — tray and shutdown lifecycle
- Added unit-tested policy for tray visibility and close-to-tray behavior.
- Confirmed shutdown now stops the monitoring, clock-preview, and toast timers; closes the optional desktop clock; and hides the tray icon.
- Local validation: compileall PASS; unit tests PASS (48 tests). Windows GUI behavior remains NOT TESTED.

## Phase 20 — pre-installer preflight tooling
- Added `tools/preflight_windows.py` to check exact Python 3.15.0, Windows 11 build, required source files, PySide6, psutil, PyInstaller, and NSIS.
- Preflight fails closed and does not install dependencies or modify the Python installation.
- Unit tests cover version/build detection and required-file checks. Actual target preflight, Windows GUI, executable build, and installer remain NOT TESTED / NOT BUILT.


## Phase 21 — pre-installer source audit
- Added `tools/audit_release_sources.py` to statically check installer/build-script safety and expected packaging outputs.
- Added tests for valid installer configuration and missing/insecure source configuration.
- This phase intentionally stops before running PyInstaller or NSIS. The target Windows 11 machine must pass preflight and manual integration checks before installer creation.
