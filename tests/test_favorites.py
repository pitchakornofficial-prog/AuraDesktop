from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auradesktop.core.favorites import add_favorite_path, remove_favorite_path, favorite_display_name


class WallpaperFavoriteTests(unittest.TestCase):
    def test_add_path_and_report_new_entry(self):
        result, added = add_favorite_path(['/wall/a.png'], '/wall/b.png')
        self.assertTrue(added)
        self.assertEqual(result, ['/wall/a.png', '/wall/b.png'])

    def test_duplicate_add_is_ignored(self):
        result, added = add_favorite_path(['/wall/a.png'], '/wall/a.png')
        self.assertFalse(added)
        self.assertEqual(result, ['/wall/a.png'])

    def test_invalid_and_blank_paths_are_ignored(self):
        result, added = add_favorite_path([None, '', '/wall/a.png', 7], '  ')
        self.assertFalse(added)
        self.assertEqual(result, ['/wall/a.png'])

    def test_remove_only_selected_path(self):
        result = remove_favorite_path(['/wall/a.png', '/wall/b.png'], '/wall/a.png')
        self.assertEqual(result, ['/wall/b.png'])

    def test_display_name_marks_missing_file(self):
        self.assertTrue(favorite_display_name('/surely/missing/a.png').endswith('(missing)'))

    def test_display_name_of_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'image.png'
            path.write_bytes(b'not-an-image-but-a-file')
            self.assertEqual(favorite_display_name(path), 'image.png')


if __name__ == '__main__':
    unittest.main()
