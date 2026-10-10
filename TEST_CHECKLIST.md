# AuraDesktop manual test checklist

Record every item as PASS, FAIL, or NOT TESTED. Include Windows version, Python version, GPU model/driver, and screenshots/logs for failures.

## Environment and build
- [ ] `python --version` reports exactly `Python 3.15.0`
- [ ] `python -m pip install -r requirements.txt` succeeds without changing Python
- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `installer\build_windows.ps1` builds app and saver without errors
- [ ] NSIS creates a per-user installer; no administrator elevation requested

## UI and settings
- [ ] App opens on Dashboard, English labels, light theme
- [ ] Navigation changes pages without changing settings
- [ ] Settings persist after closing and relaunching
- [ ] Each setting change has confirmation and success/error toast
- [ ] Close button hides to tray; explicit Exit stops the app
- [ ] Startup toggle adds/removes the per-user Windows Run entry

## Wallpaper
- [ ] Select and preview valid image; invalid image shows error
- [ ] Fill, Fit, Stretch, Center apply correctly
- [ ] Wallpaper applies to all monitors and survives relaunch
- [ ] Favorites persist and missing favorite files are handled gracefully

## Desktop clock
- [ ] Enable/disable confirmation works
- [ ] Clock appears on selected monitor at chosen preset/size
- [ ] Clock remains behind normal app windows, not over them
- [ ] Dragging works and shell restart behavior is acceptable
- [ ] Restore after app relaunch works

## Screensaver
- [ ] Clock, Slideshow, Blank modes work
- [ ] Favorites and separate folder sources work
- [ ] Keyboard/mouse exits preview
- [ ] `.scr` registers in Windows Screen Saver Settings and preview works
- [ ] Idle timeout matches selected setting
- [ ] `/s`, `/c`, `/c:<hwnd>`, `/p <hwnd>`, `/p:<hwnd>` are handled as expected

## System monitor
- [ ] CPU, RAM, disk and network rates update about every 2 seconds
- [ ] Battery says Unavailable when hardware has no battery
- [ ] GPU utilization/temperature are real when supported, otherwise Unavailable
- [ ] No fabricated metrics, crashes or unbounded resource use

## Installer and final delivery
- [ ] Install, launch, startup, tray and screensaver work after install
- [ ] Uninstall removes app files and only AuraDesktop's own integration entries
- [ ] Existing Windows screensaver timeout and unrelated settings are preserved
- [ ] Final Source + Installer + manual test report are packaged

## Phase 10 regression checks
- [ ] Toggle System Tray off, save, and confirm the icon is hidden.
- [ ] Confirm close-to-tray is disabled when System Tray is off.
- [ ] Re-enable System Tray, save, and confirm tray icon returns when the OS tray is available.
- [ ] Load a settings file containing invalid boolean/path types and confirm safe defaults are used.

## Phase 11 regression checks
- [ ] Running the saver with `/c` opens AuraDesktop on the Screensaver page.
- [ ] `/s` starts fullscreen saver mode.
- [ ] `/p <HWND>` and `/p:<HWND>` embed into the Windows preview host when supplied a valid HWND.
- [ ] Invalid or missing preview HWND exits safely without a crash.
- [ ] Launching AuraDesktop without arguments still opens Dashboard.
- [ ] `AuraDesktop.exe --page Screensaver` opens the Screensaver page.


## Phase 12 regression checks
- [ ] Drag the desktop clock to a different location, exit and relaunch; verify its position is restored.
- [ ] Drag the clock onto a second monitor; verify the monitor selection/remembered location is consistent after relaunch.
- [ ] Test a monitor arranged to the left of the primary display (negative virtual-desktop coordinates).
- [ ] Load malformed `clock_x` / `clock_y` settings and confirm the clock falls back to the configured position preset.


## Phase 13 regression checks
- [ ] Start the screensaver with one display and confirm it covers the entire display.
- [ ] Start the screensaver with two or more displays and confirm each display is covered.
- [ ] Confirm key press, mouse click, and deliberate mouse movement exit the saver.
- [ ] Confirm small cursor jitter does not immediately exit the saver.
- [ ] Verify `/p HWND` preview still embeds in the Windows preview host and does not spawn extra display windows.

## Phase 14 telemetry regression checks
- [ ] Confirm RX/TX rates start at zero until a second network sample is available.
- [ ] Disconnect/reconnect a network adapter and confirm rates never become negative.
- [ ] Confirm monitor progress bars stay within 0–100 even if a sensor reports malformed values.
- [ ] Confirm unsupported GPU/battery sensors remain explicitly unavailable.


## Phase 15 telemetry regression checks
- [ ] Invalid network counters preserve the last valid baseline.
- [ ] Monotonic time regression never produces negative network speed.
- [ ] GPU N/A / malformed / out-of-range readings display Unavailable.
- [ ] Verify GPU values against the actual driver on Windows 11.


## Phase 16 additions — Wallpaper Favorites
- [ ] Add an existing selected wallpaper to Favorites and verify it appears once.
- [ ] Try adding the same path twice; verify duplicate warning and no duplicate entry.
- [ ] Remove a favorite; verify it disappears from the list but the original image file remains.
- [ ] Move/delete a favorite image outside the app; verify the selector labels it `(missing)`.
- [ ] Select a missing favorite; verify the app reports the missing file instead of applying it.

## Phase 17 — Screensaver slideshow source checks
- [ ] Folder slideshow skips subdirectories and unsupported extensions.
- [ ] Folder slideshow ordering is stable across launches.
- [ ] Favorite slideshow preserves the saved favorite order.
- [ ] Missing/deleted favorite images are skipped without crashing.
- [ ] A folder with no supported images shows the empty-source message.
- [ ] Verify on Windows 11 with Python 3.15.0 and the actual registered `.scr`.

## Phase 18 — Startup integration (manual Windows checks still required)
- [ ] Enable “Launch AuraDesktop when I sign in to Windows”, save, then confirm the per-user Run entry points to the installed executable.
- [ ] Disable startup, save, and confirm the AuraDesktop Run entry is removed.
- [ ] Test an install path containing spaces.
- [ ] Confirm no administrator prompt is shown and startup still works after sign-out/sign-in.
- [ ] If registry access fails, confirm the UI reports failure and does not falsely claim settings were saved.


## Pre-installer gate (run on target Windows 11 machine)
- [ ] Confirm `python --version` reports exactly `Python 3.15.0`.
- [ ] Run `python tools/preflight_windows.py`; resolve every FAIL without changing Python versions automatically.
- [ ] Run unit tests with `python -m unittest discover -s tests -v`.
- [ ] Manually test tray icon availability, close-to-tray, reopening, confirmed Exit, and background clock/timer shutdown.
- [ ] Test startup enable/disable against the real current-user Registry.
- [ ] Test screensaver `/s`, `/c`, and `/p` flows and multi-monitor exit behavior.
- [ ] Test wallpaper application, display fit modes, favorites, missing files, and slideshow.
- [ ] Test app with and without NVIDIA hardware/`nvidia-smi`; verify telemetry degrades gracefully.
- [ ] Only after all above results are recorded, proceed to executable and installer build.

- [ ] Run `python tools/audit_release_sources.py`; static source audit must pass before executable/installer creation.
