# SPDX-License-Identifier: MIT

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from cvat.apps.dataset_manager.bindings import CvatImportError
from cvat.apps.local_workspace.yolo_format import (
    _ensure_8_bit_image,
    _load_names,
    _parse_label_file,
    _safe_relative_path,
)


class Yolo26PackageValidationTest(SimpleTestCase):
    def test_loads_continuous_category_mapping(self):
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "data.yaml"
            data_file.write_text("names:\n  0: 组件\n  1: 缺陷\n", encoding="utf-8")

            self.assertEqual(_load_names(data_file), ["组件", "缺陷"])

    def test_rejects_extra_data_yaml_fields(self):
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "data.yaml"
            data_file.write_text("names: [defect]\ntrain: images\n", encoding="utf-8")

            with self.assertRaises(CvatImportError):
                _load_names(data_file)

    def test_parses_valid_box_and_rejects_out_of_bounds_box(self):
        with TemporaryDirectory() as directory:
            label_file = Path(directory) / "sample.txt"
            label_file.write_text("0 0.5 0.5 0.25 0.5\n", encoding="utf-8")
            boxes = _parse_label_file(label_file, width=200, height=100, class_count=1)
            self.assertEqual(boxes[0].get_bbox(), [75.0, 25.0, 50.0, 50.0])

            label_file.write_text("0 0.1 0.5 0.4 0.5\n", encoding="utf-8")
            with self.assertRaises(CvatImportError):
                _parse_label_file(label_file, width=200, height=100, class_count=1)

    def test_rejects_unsafe_archive_path(self):
        with self.assertRaises(ValueError):
            _safe_relative_path("../images/sample.jpg")

    def test_rejects_non_8_bit_image(self):
        image_file = BytesIO()
        Image.new("I;16", (4, 4)).save(image_file, format="PNG")
        with self.assertRaises(CvatImportError):
            _ensure_8_bit_image(image_file.getvalue(), "sample.png", CvatImportError)
