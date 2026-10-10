from __future__ import annotations
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auradesktop.core.config import DEFAULTS, SettingsStore

class SettingsStoreTests(unittest.TestCase):
    def test_defaults_are_available(self):
        with tempfile.TemporaryDirectory() as td:
            store = SettingsStore(Path(td) / "settings.json")
            self.assertEqual(store.get("wallpaper_fit"), "Fill")
            self.assertEqual(store.get("monitor_refresh"), 2)

    def test_persistence_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            store = SettingsStore(path)
            store.set("wallpaper_fit", "Stretch")
            store.set("wallpaper_favorites", ["/tmp/a.png"])
            loaded = SettingsStore(path)
            self.assertEqual(loaded.get("wallpaper_fit"), "Stretch")
            self.assertEqual(loaded.get("wallpaper_favorites"), ["/tmp/a.png"])

    def test_invalid_values_are_normalized(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            path.write_text(json.dumps({"wallpaper_fit":"nonsense", "screensaver_timeout":999, "monitor_refresh":0, "unknown_key":1}), encoding="utf-8")
            store = SettingsStore(path)
            self.assertEqual(store.get("wallpaper_fit"), DEFAULTS["wallpaper_fit"])
            self.assertEqual(store.get("screensaver_timeout"), 120)
            self.assertEqual(store.get("monitor_refresh"), 2)
            self.assertIsNone(store.get("unknown_key"))


    def test_malformed_json_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            path.write_text("{not valid json", encoding="utf-8")
            store = SettingsStore(path)
            self.assertEqual(store.get("wallpaper_fit"), "Fill")
            self.assertEqual(store.get("screensaver_mode"), "Clock")

    def test_failed_write_rolls_back_in_memory_state(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            store = SettingsStore(path)
            store.set("wallpaper_fit", "Stretch")
            with patch("auradesktop.core.config.os.replace", side_effect=OSError("simulated disk failure")):
                with self.assertRaises(OSError):
                    store.set("wallpaper_fit", "Center")
            self.assertEqual(store.get("wallpaper_fit"), "Stretch")

    def test_malformed_boolean_and_path_values_use_safe_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            path.write_text(json.dumps({"close_to_tray": "false", "minimize_to_tray": False,
                                        "launch_on_startup": "yes", "wallpaper_path": {"bad": "type"}}), encoding="utf-8")
            store = SettingsStore(path)
            self.assertFalse(store.get("close_to_tray"))
            self.assertFalse(store.get("minimize_to_tray"))
            self.assertFalse(store.get("launch_on_startup"))
            self.assertEqual(store.get("wallpaper_path"), "")

    def test_close_to_tray_requires_tray_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            path.write_text(json.dumps({"minimize_to_tray": False, "close_to_tray": True}), encoding="utf-8")
            store = SettingsStore(path)
            self.assertFalse(store.get("close_to_tray"))


    def test_clock_position_coordinates_persist_and_invalid_values_reset(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            store = SettingsStore(path)
            store.set("clock_x", -1920)
            store.set("clock_y", 180)
            loaded = SettingsStore(path)
            self.assertEqual(loaded.get("clock_x"), -1920)
            self.assertEqual(loaded.get("clock_y"), 180)
            path.write_text(json.dumps({"clock_x": "right", "clock_y": True}), encoding="utf-8")
            malformed = SettingsStore(path)
            self.assertIsNone(malformed.get("clock_x"))
            self.assertIsNone(malformed.get("clock_y"))

    def test_unknown_setting_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store = SettingsStore(Path(td) / "settings.json")
            with self.assertRaises(KeyError):
                store.set("not_a_real_setting", True)

if __name__ == "__main__":
    unittest.main()
