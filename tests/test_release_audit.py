from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auradesktop.core.release_audit import audit_release_sources

class ReleaseAuditTests(unittest.TestCase):
    def test_current_installer_sources_pass_static_audit(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(audit_release_sources(root), [])
    def test_missing_build_script_is_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            issues = audit_release_sources(td)
            self.assertIn("Missing installer/build_windows.ps1", issues)
            self.assertIn("Missing installer/AuraDesktop.nsi", issues)
    def test_insecure_installer_configuration_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "installer").mkdir()
            (root / "installer" / "build_windows.ps1").write_text('"Python 3.15.0"\nNo version changes were made\nAuraDesktopSaver.exe AuraDesktop.scr', encoding="utf-8")
            (root / "installer" / "AuraDesktop.nsi").write_text('AuraDesktop-Setup.exe\nRequestExecutionLevel admin\n', encoding="utf-8")
            issues = audit_release_sources(root)
            self.assertTrue(any("per-user execution level" in issue for issue in issues))
            self.assertTrue(any("Uninstaller must clean up" in issue for issue in issues))

if __name__ == '__main__':
    unittest.main()
