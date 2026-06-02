"""Tests for MP4 versioning before export overwrite."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.video_archive import archive_existing_video, next_archived_video_path, video_archive_dir_for


class VideoArchiveTest(unittest.TestCase):
    def test_archives_with_incrementing_version(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "clouds_coast.mp4"
            out.write_bytes(b"v1")
            first = archive_existing_video(out)
            self.assertIsNotNone(first)
            assert first is not None
            self.assertEqual(first, video_archive_dir_for(out) / "001-clouds_coast.mp4")
            self.assertFalse(out.exists())
            self.assertTrue(first.exists())

            out.write_bytes(b"v2")
            second = archive_existing_video(out)
            self.assertEqual(second, video_archive_dir_for(out) / "002-clouds_coast.mp4")

    def test_next_path_when_nothing_to_archive(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "new.mp4"
            self.assertEqual(next_archived_video_path(out).name, "001-new.mp4")


if __name__ == "__main__":
    unittest.main()
