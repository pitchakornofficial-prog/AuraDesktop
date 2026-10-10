from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_NAME = "AuraDesktop"
DEFAULTS: dict[str, Any] = {
    "wallpaper_path": "", "wallpaper_fit": "Fill", "wallpaper_favorites": [],
    "clock_enabled": False, "clock_position": "Top Right", "clock_size": "Medium", "clock_monitor": 0, "clock_x": None, "clock_y": None,
    "screensaver_mode": "Clock", "screensaver_source": "Wallpaper Favorites", "screensaver_folder": "", "screensaver_timeout": 10,
    "launch_on_startup": False, "minimize_to_tray": True, "close_to_tray": True,
    "monitor_refresh": 2, "theme": "Light",
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


class SettingsStore:
    """Small atomic JSON settings store; path injection supports isolated tests."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else config_dir() / "settings.json"
        self.data = dict(DEFAULTS)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                # Ignore unknown keys so older/newer builds remain forward-compatible.
                self.data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except (OSError, ValueError, TypeError):
            pass
        self._normalize()

    def _normalize(self) -> None:
        if self.data.get("wallpaper_fit") not in {"Fill", "Fit", "Stretch", "Center"}:
            self.data["wallpaper_fit"] = DEFAULTS["wallpaper_fit"]
        if self.data.get("clock_position") not in {"Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"}:
            self.data["clock_position"] = DEFAULTS["clock_position"]
        if self.data.get("clock_size") not in {"Small", "Medium", "Large"}:
            self.data["clock_size"] = DEFAULTS["clock_size"]
        if self.data.get("screensaver_mode") not in {"Clock", "Slideshow", "Blank"}:
            self.data["screensaver_mode"] = DEFAULTS["screensaver_mode"]
        if self.data.get("screensaver_source") not in {"Wallpaper Favorites", "Separate folder"}:
            self.data["screensaver_source"] = DEFAULTS["screensaver_source"]
        try:
            self.data["screensaver_timeout"] = max(1, min(120, int(self.data["screensaver_timeout"])))
        except (ValueError, TypeError):
            self.data["screensaver_timeout"] = DEFAULTS["screensaver_timeout"]
        try:
            self.data["monitor_refresh"] = max(2, min(30, int(self.data["monitor_refresh"])))
        except (ValueError, TypeError):
            self.data["monitor_refresh"] = DEFAULTS["monitor_refresh"]
        try:
            self.data["clock_monitor"] = max(0, int(self.data["clock_monitor"]))
        except (ValueError, TypeError):
            self.data["clock_monitor"] = 0
        # Absolute virtual-desktop coordinates are optional and are saved only
        # after a user drags the clock away from its position preset.
        for key in ("clock_x", "clock_y"):
            value = self.data.get(key)
            self.data[key] = value if isinstance(value, int) and not isinstance(value, bool) else None
        favs = self.data.get("wallpaper_favorites")
        self.data["wallpaper_favorites"] = [str(p) for p in favs if isinstance(p, (str, Path))] if isinstance(favs, list) else []
        for key in ("clock_enabled", "launch_on_startup", "minimize_to_tray", "close_to_tray"):
            value = self.data.get(key, DEFAULTS[key])
            # Do not treat malformed strings such as "false" as truthy booleans.
            self.data[key] = value if isinstance(value, bool) else DEFAULTS[key]
        for key in ("wallpaper_path", "screensaver_folder"):
            value = self.data.get(key, "")
            self.data[key] = value if isinstance(value, str) else ""
        if self.data["close_to_tray"] and not self.data["minimize_to_tray"]:
            self.data["close_to_tray"] = False

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULTS:
            raise KeyError(f"Unknown AuraDesktop setting: {key}")
        previous = dict(self.data)
        self.data[key] = value
        self._normalize()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            # Restore the complete in-memory state, not only the changed key:
            # normalization can also adjust dependent or malformed values.
            self.data = previous
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise
