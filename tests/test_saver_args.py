from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auradesktop.core.saver_args import SaverCommand, parse_saver_args


class SaverArgumentTests(unittest.TestCase):
    def test_default_starts_fullscreen_saver(self):
        self.assertEqual(parse_saver_args([]), SaverCommand('screen'))
        self.assertEqual(parse_saver_args(['/s']), SaverCommand('screen'))
        self.assertEqual(parse_saver_args(['-S']), SaverCommand('screen'))

    def test_configuration_forms(self):
        self.assertEqual(parse_saver_args(['/c']), SaverCommand('configure'))
        self.assertEqual(parse_saver_args(['/c:1234']), SaverCommand('configure', 1234))
        self.assertEqual(parse_saver_args(['-c:0x10']), SaverCommand('configure', 16))

    def test_preview_separate_handle(self):
        self.assertEqual(parse_saver_args(['/p', '1234']), SaverCommand('preview', 1234))
        self.assertEqual(parse_saver_args(['-p', '0x20']), SaverCommand('preview', 32))

    def test_preview_inline_handle(self):
        self.assertEqual(parse_saver_args(['/p:1234']), SaverCommand('preview', 1234))
        self.assertEqual(parse_saver_args(['-p:0x20']), SaverCommand('preview', 32))

    def test_invalid_handle_is_not_guessed(self):
        self.assertEqual(parse_saver_args(['/p', 'not-a-handle']), SaverCommand('preview', None))
        self.assertEqual(parse_saver_args(['/p']), SaverCommand('preview', None))


if __name__ == '__main__':
    unittest.main()
