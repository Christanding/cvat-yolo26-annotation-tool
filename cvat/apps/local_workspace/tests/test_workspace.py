# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path

from cvat.apps.local_workspace.workspace import WorkspacePathError, scan_workspace


class ScanWorkspaceTest(unittest.TestCase):
    def test_recursively_lists_supported_images(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "frame.JPG").touch()
            (root / "notes.txt").touch()
            nested = root / "nested"
            nested.mkdir()
            (nested / "thermal.png").touch()

            entries = scan_workspace(root, recursive=True)

            self.assertEqual(
                [entry.path for entry in entries],
                ["frame.JPG", "nested/thermal.png"],
            )

    def test_lists_directories_videos_and_archives_with_their_kind(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "folder").mkdir()
            (root / "clip.MOV").touch()
            (root / "dataset.zip").touch()

            entries = scan_workspace(root)

            self.assertEqual(
                [(entry.path, entry.kind) for entry in entries],
                [
                    ("folder", "directory"),
                    ("clip.MOV", "video"),
                    ("dataset.zip", "archive"),
                ],
            )

    def test_rejects_paths_outside_the_workspace(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            workspace = temporary_root / "workspace"
            workspace.mkdir()
            (temporary_root / "outside").mkdir()

            with self.assertRaises(WorkspacePathError):
                scan_workspace(workspace, relative_path="../outside")

    def test_excludes_internal_state_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state_directory = root / ".CVAT-LOCAL"
            state_directory.mkdir()
            (state_directory / "cached.png").touch()
            (root / "visible.png").touch()

            entries = scan_workspace(root, recursive=True)

            self.assertEqual([entry.path for entry in entries], ["visible.png"])

    def test_excludes_symbolic_links_to_files_outside_the_workspace(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            workspace = temporary_root / "workspace"
            workspace.mkdir()
            outside_image = temporary_root / "outside.png"
            outside_image.touch()
            (workspace / "linked.png").symlink_to(outside_image)

            entries = scan_workspace(workspace, recursive=True)

            self.assertEqual(entries, [])

    def test_reports_a_missing_workspace_as_a_path_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_workspace = Path(temporary_directory) / "missing"

            with self.assertRaises(WorkspacePathError):
                scan_workspace(missing_workspace)


if __name__ == "__main__":
    unittest.main()
