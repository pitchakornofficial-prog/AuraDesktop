# Phase 19 — System Tray and Shutdown Lifecycle

- Extracted tray visibility and close-to-tray decisions into pure, unit-tested policy helpers.
- Closing the window only hides it when close-to-tray and tray visibility are enabled and the host reports a tray available.
- Explicit exit and confirmed window-close stop monitor, clock-preview, and toast timers; close the optional desktop clock; and hide the tray icon before quitting.
- Added regression tests for unavailable tray, disabled settings, safe defaults, and explicit exit.
- This is source-level validation. Qt GUI behavior and Windows 11 tray integration remain NOT TESTED on the target OS.
