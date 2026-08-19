# SPDX-License-Identifier: MIT

import unittest
from pathlib import PurePosixPath

import numpy as np

from cvat.apps.local_workspace.extraction import (
    classify_frame,
    frame_filename,
    is_path_referenced,
    output_path_for_video,
)


class ExtractionTest(unittest.TestCase):
    def test_frame_name_contains_video_time_and_frame_number(self):
        self.assertEqual(
            frame_filename("thermal", timestamp=12, frame_number=360),
            "thermal__t000012s__f00000360.png",
        )

    def test_output_directory_is_next_to_video(self):
        self.assertEqual(
            output_path_for_video(PurePosixPath("site/clip.MP4")),
            PurePosixPath("site/images/clip"),
        )

    def test_similarity_strength_controls_frame_classification(self):
        previous = np.zeros((64, 64, 3), dtype=np.uint8)
        candidate = np.full((64, 64, 3), 2, dtype=np.uint8)

        self.assertEqual(classify_frame(previous, previous.copy(), "low"), "exact")
        self.assertEqual(classify_frame(previous, candidate, "low"), "keep")
        self.assertEqual(classify_frame(previous, candidate, "medium"), "similar")

    def test_detects_task_reference_to_output_or_its_contents(self):
        output = PurePosixPath("site/images/clip")

        self.assertTrue(is_path_referenced(output, ["site/images/clip/"]))
        self.assertTrue(is_path_referenced(output, ["site/images/clip/frame.png"]))
        self.assertTrue(is_path_referenced(output, ["site/"]))
        self.assertFalse(is_path_referenced(output, ["site/images/other/"]))


if __name__ == "__main__":
    unittest.main()
