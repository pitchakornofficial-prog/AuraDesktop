# AuraDesktop

A Windows 11 desktop customization hub with an English, light-theme UI.

## Current build scope
- Dashboard, Wallpaper selection/preview/favorites, desktop clock experiment, screensaver preferences/preview, system metrics, Settings, and System Tray.
- Persistent settings stored under `%APPDATA%\AuraDesktop\settings.json`.
- Wallpaper application and startup integration are Windows-specific. GPU telemetry is best-effort via `nvidia-smi`; unsupported metrics are shown as unavailable.
- Desktop clock uses experimental Windows WorkerW parenting. Shell behavior is not guaranteed on all Windows 11 configurations.
- The screensaver executable supports fullscreen Clock/Slideshow/Blank modes and basic `/s`, `/c`, `/p` command handling; full Control Panel preview behavior must be verified on Windows.

## Strict environment requirement
Python **3.15.0 exactly** is required by the project build script. The script stops if another version is active and never changes Python versions.

## Run from source
```powershell
python --version  # must report Python 3.15.0
python -m pip install -r requirements.txt
python main.py
```

## Build Windows artifacts
On Windows 11 with Python 3.15.0 installed and available as `python`:
```powershell
.\installer\build_windows.ps1
```
Then compile `installer\AuraDesktop.nsi` with NSIS while keeping the project folder structure intact. The resulting installer is per-user and does not request administrator rights. Startup is controlled by the in-app Settings toggle, not forced by installation.

## Important limitations before final testing
- This development environment is not Windows, so Windows shell integration, actual `.scr` registration, multi-monitor behavior, and packaged binaries have not been verified here.
- Confirm the screensaver idle timeout from Windows Screen Saver Settings; the current installer registers the saver path but the OS timeout UI is still the authoritative setting.
- The WorkerW desktop clock is experimental; if it overlays applications or disappears after Explorer restarts, mark that test FAIL rather than assuming success.
- Review the generated installer script before distribution.

## Manual test checklist
See `TEST_CHECKLIST.md`. Report PASS / FAIL / NOT TESTED honestly.


Phase 8 adds settings validation, isolated settings tests, and more robust screensaver argument handling. See `BUILD_STATUS.md` and `TEST_CHECKLIST.md`.


## Phase 9 hardening notes
- Settings write failures now restore the complete in-memory snapshot, including values adjusted during normalization.
- Choosing a wallpaper favorite now asks for confirmation and clarifies that Windows wallpaper changes only after Apply.
- The desktop-clock action refuses non-Windows environments before persisting an enabled clock state.
- Added tests for malformed JSON recovery and settings write-failure rollback.

## Phase 10 development update
- System Tray visibility now follows the saved `minimize_to_tray` setting, and close-to-tray is disabled when the tray option is off.
- Settings normalization rejects malformed boolean/path values instead of interpreting arbitrary strings as enabled options.
- Added regression tests for malformed settings and the tray/close dependency.
- This remains a development build. Windows GUI, WorkerW behavior, Screen Saver Control Panel integration, and packaged installer require final testing on Windows 11 with Python 3.15.0 exactly.

## Phase 11 development update
- Screen-saver configuration requests now launch the app on its Screensaver page via `/c` when the sibling app executable is present, or via the source entry point during development.
- The saver command parser accepts common `/s`, `/c`, `/c:<HWND>`, `/p <HWND>`, and `/p:<HWND>` forms; malformed preview handles are rejected rather than guessed.
- The main app still opens Dashboard by default and supports an explicit `--page Screensaver` argument for Windows integration.


## Phase 12 development update
- Desktop Clock drag position now persists across application restarts using optional virtual-desktop coordinates (`clock_x`, `clock_y`).
- Dragging the clock updates the remembered monitor index when the release point falls on a detected display.
- Clock coordinates are normalized defensively; malformed values reset to the position-preset behavior.
- The clock still uses experimental WorkerW parenting. Persisted placement does not guarantee desktop-layer behavior on every Windows 11 shell configuration; verify during final Windows testing.


### Phase 13 note
Fullscreen screensaver mode now attempts to open a separate fullscreen surface on each detected display and exits on key, click, or deliberate mouse movement. This is an implementation target, not a verified Windows result; test it on Windows 11 before relying on it.


## Phase 16 development update
- Wallpaper Favorites can now be removed from the list without deleting the underlying image file.
- The Favorites list marks paths whose image files are no longer present, so missing files are not presented as usable favorites.
- Adding favorites now validates that the selected image path points to a file and de-duplicates entries safely.
- Added six pure unit tests for favorite add/remove behavior and missing-file labels.
- Phase 16 remains a source development build; Windows GUI behavior and the installer are still not verified.

## Phase 18 — Startup Integration Reliability
- Extracted per-user Windows startup registration into `core/startup.py` so command construction and registry behavior can be tested independently from the GUI.
- Startup commands quote both the executable and source entry script, including paths containing spaces.
- Uses the current user's `Run` registry key; no administrator elevation is requested.
- Disabling startup tolerates an already-absent registry value and the registry handle is closed on success or failure.
- Windows runtime behavior still requires manual verification on the target Windows 11 system.


## Phase 19 — System Tray and Shutdown Lifecycle
- Tray visibility and close-to-tray policy are isolated and unit-tested.
- Confirmed exit stops app timers, closes the optional desktop clock, and hides the tray icon.
- Qt GUI and actual Windows tray integration remain NOT TESTED in this environment.

## Phase 20 — Windows Build Preflight
- Run `python tools/preflight_windows.py` on the target build machine before building.
- Requires exactly Python 3.15.0, Windows 11, PySide6, psutil, PyInstaller, and NSIS for Setup.exe.
- The preflight is read-only and never changes Python. A PASS does not certify the app's Windows runtime behavior.


## Phase 21 — Pre-installer source audit
- Run `python tools/audit_release_sources.py` to statically inspect the build/NSIS scripts before creating any binaries.
- The audit checks the Python 3.15.0 guard, screensaver packaging, per-user installation, expected output name, and uninstall registry cleanup.
- A static PASS is not a Windows build/runtime PASS. The next step after target-machine preflight and manual test sign-off is executable/installer creation.
