from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from auradesktop.core.preflight import python_version_matches, windows_build_is_supported, missing_required_files

class PreflightTests(unittest.TestCase):
    def test_requires_exact_python_version(self):
        self.assertTrue(python_version_matches((3, 15, 0, 'final', 0)))
        self.assertFalse(python_version_matches((3, 15, 1, 'final', 0)))
        self.assertFalse(python_version_matches((3, 14, 9, 'final', 0)))
    def test_windows_11_build_detection(self):
        self.assertTrue(windows_build_is_supported('win32', '26100'))
        self.assertTrue(windows_build_is_supported('win32', '22000'))
        self.assertFalse(windows_build_is_supported('win32', '19045'))
        self.assertFalse(windows_build_is_supported('linux', '26100'))
        self.assertFalse(windows_build_is_supported('win32', 'unknown'))
    def test_missing_required_files_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertGreater(len(missing_required_files(td)), 0)
    def test_current_source_tree_has_required_files(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(missing_required_files(root), [])

if __name__ == '__main__':
    unittest.main()
