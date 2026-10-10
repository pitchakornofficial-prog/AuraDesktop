from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auradesktop.core.image_sources import discover_screensaver_images, image_files_from_paths, image_files_in_folder


class ImageSourceTests(unittest.TestCase):
    def test_folder_results_are_sorted_and_only_supported_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ('z.JPG', 'B.png', 'a.webp', 'notes.txt'):
                (root / name).write_bytes(b'x')
            (root / 'folder.jpg').mkdir()
            self.assertEqual([p.name for p in image_files_in_folder(root)], ['a.webp', 'B.png', 'z.JPG'])

    def test_favorite_paths_keep_order_and_ignore_missing_or_non_images(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / 'first.png'; first.write_bytes(b'x')
            second = root / 'second.jpg'; second.write_bytes(b'x')
            text = root / 'notes.txt'; text.write_text('x')
            got = image_files_from_paths([second, first, first, text, root / 'missing.png', None])
            self.assertEqual(got, [second, first])

    def test_newline_source_uses_favorite_list_mode(self):
        with tempfile.TemporaryDirectory() as td:
            image = Path(td) / 'wall.png'; image.write_bytes(b'x')
            self.assertEqual(discover_screensaver_images(f'{image}\n{Path(td) / "gone.jpg"}'), [image])

    def test_folder_source_does_not_treat_newline_as_a_path(self):
        self.assertEqual(discover_screensaver_images(''), [])
        self.assertEqual(discover_screensaver_images(None), [])


if __name__ == '__main__':
    unittest.main()
