from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auradesktop.core.tray_policy import tray_should_be_visible, close_should_hide_to_tray

class TrayPolicyTests(unittest.TestCase):
    def test_tray_visible_when_enabled_and_available(self):
        self.assertTrue(tray_should_be_visible({"minimize_to_tray": True}, True))
    def test_tray_hidden_when_disabled(self):
        self.assertFalse(tray_should_be_visible({"minimize_to_tray": False}, True))
    def test_tray_hidden_when_host_has_no_tray(self):
        self.assertFalse(tray_should_be_visible({"minimize_to_tray": True}, False))
    def test_close_hides_only_when_both_settings_and_tray_available(self):
        settings = {"close_to_tray": True, "minimize_to_tray": True}
        self.assertTrue(close_should_hide_to_tray(settings, True))
        self.assertFalse(close_should_hide_to_tray(settings, False))
    def test_close_does_not_hide_if_close_to_tray_disabled(self):
        self.assertFalse(close_should_hide_to_tray({"close_to_tray": False, "minimize_to_tray": True}, True))
    def test_explicit_exit_always_disables_hide_to_tray(self):
        self.assertFalse(close_should_hide_to_tray({"close_to_tray": True, "minimize_to_tray": True}, True, allow_exit=True))
    def test_missing_settings_use_safe_defaults(self):
        self.assertTrue(close_should_hide_to_tray({}, True))

if __name__ == "__main__":
    unittest.main()
