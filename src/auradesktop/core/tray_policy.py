"""Pure policy helpers for tray visibility and close behavior."""
from __future__ import annotations
from typing import Mapping, Any


def tray_should_be_visible(settings: Mapping[str, Any], tray_available: bool) -> bool:
    """Return whether the tray icon should be shown for the saved settings."""
    return bool(settings.get("minimize_to_tray", True)) and bool(tray_available)


def close_should_hide_to_tray(
    settings: Mapping[str, Any], tray_available: bool, *, allow_exit: bool = False
) -> bool:
    """Hide on close only when both settings and an actual tray permit it."""
    return (
        not allow_exit
        and bool(settings.get("close_to_tray", True))
        and bool(settings.get("minimize_to_tray", True))
        and bool(tray_available)
    )
