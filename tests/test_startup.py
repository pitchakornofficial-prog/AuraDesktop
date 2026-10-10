from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auradesktop.core.startup import build_startup_command, set_windows_startup, RUN_KEY, VALUE_NAME


class FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_SET_VALUE = 2
    REG_SZ = 1
    def __init__(self):
        self.values = {}
        self.closed = False
    def OpenKey(self, root, path, reserved, access):
        assert root is self.HKEY_CURRENT_USER
        assert path == RUN_KEY
        assert access == self.KEY_SET_VALUE
        return object()
    def SetValueEx(self, key, name, reserved, kind, value):
        self.values[name] = (kind, value)
    def DeleteValue(self, key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]
    def CloseKey(self, key):
        self.closed = True


class StartupTests(unittest.TestCase):
    def test_frozen_command_quotes_executable(self):
        with tempfile.TemporaryDirectory(prefix="Aura Desktop ") as td:
            exe = Path(td) / "AuraDesktop.exe"
            command = build_startup_command(exe, frozen=True)
            self.assertTrue(command.startswith('"'))
            self.assertTrue(command.endswith('"'))
            self.assertIn("AuraDesktop.exe", command)

    def test_source_command_quotes_executable_and_entry(self):
        with tempfile.TemporaryDirectory(prefix="Aura Desktop ") as td:
            exe = Path(td) / "python.exe"
            script = Path(td) / "my project" / "main.py"
            command = build_startup_command(exe, frozen=False, entry_script=script)
            self.assertEqual(command, f'"{exe.resolve()}" "{script.resolve()}"')

    def test_source_command_requires_entry_script(self):
        with self.assertRaises(ValueError):
            build_startup_command("python.exe", frozen=False)

    def test_enable_writes_per_user_run_value_and_closes_key(self):
        fake = FakeWinreg()
        with tempfile.TemporaryDirectory() as td:
            set_windows_startup(True, executable=Path(td) / "AuraDesktop.exe", frozen=True, winreg_module=fake)
        kind, command = fake.values[VALUE_NAME]
        self.assertEqual(kind, fake.REG_SZ)
        self.assertIn("AuraDesktop.exe", command)
        self.assertTrue(fake.closed)

    def test_disable_deletes_existing_value(self):
        fake = FakeWinreg()
        fake.values[VALUE_NAME] = (fake.REG_SZ, '"old.exe"')
        set_windows_startup(False, winreg_module=fake)
        self.assertNotIn(VALUE_NAME, fake.values)
        self.assertTrue(fake.closed)

    def test_disable_missing_value_is_safe(self):
        fake = FakeWinreg()
        set_windows_startup(False, winreg_module=fake)
        self.assertEqual(fake.values, {})

    @patch("auradesktop.core.startup.os.name", "posix")
    def test_non_windows_enable_is_rejected_without_registry(self):
        with self.assertRaisesRegex(RuntimeError, "only on Windows"):
            set_windows_startup(True)

if __name__ == "__main__":
    unittest.main()
