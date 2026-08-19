# SPDX-License-Identifier: MIT

from __future__ import annotations

import math
import stat
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath

import yaml
from datumaro.components.annotation import AnnotationType, Bbox
from datumaro.components.dataset import Dataset
from datumaro.components.dataset_base import DatasetItem
from datumaro.components.media import Image
from PIL import Image as PILImage

from cvat.apps.dataset_manager.bindings import (
    CvatExportError,
    CvatImportError,
    GetCVATDataExtractor,
    import_dm_annotations,
)
from cvat.apps.dataset_manager.formats.registry import exporter, importer
from cvat.apps.dataset_manager.util import make_zip_archive


FORMAT_NAME = "YOLO26 Detect 标注包"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".png"}
SUPPORTED_8_BIT_MODES = {"L", "LA", "P", "RGB", "RGBA", "CMYK", "YCbCr"}


def _safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("压缩包内包含无效路径。")
    return path


def _extract_package(source, destination: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        extracted_paths: set[PurePosixPath] = set()
        for member in archive.infolist():
            try:
                relative_path = _safe_relative_path(member.filename)
            except ValueError as error:
                raise CvatImportError("压缩包内包含无效路径。") from error
            if relative_path in extracted_paths:
                raise CvatImportError(f"压缩包内存在重复路径：{relative_path.as_posix()}")
            extracted_paths.add(relative_path)
            mode = member.external_attr >> 16
            if member.flag_bits & 0x1 or stat.S_ISLNK(mode):
                raise CvatImportError("压缩包不能包含加密文件或符号链接。")
            target = destination.joinpath(*relative_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if member.is_dir():
                target.mkdir(exist_ok=True)
                continue
            with archive.open(member) as source_file, target.open("wb") as target_file:
                while chunk := source_file.read(1024 * 1024):
                    target_file.write(chunk)


def _package_root(directory: Path) -> Path:
    candidates = [
        path.parent
        for path in directory.rglob("data.yaml")
        if (path.parent / "images").is_dir() and (path.parent / "labels").is_dir()
    ]
    if len(candidates) != 1:
        raise CvatImportError("压缩包必须且只能包含一组 images、labels 和 data.yaml。")
    return candidates[0]


def _load_names(data_file: Path) -> list[str]:
    try:
        content = yaml.safe_load(data_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise CvatImportError("data.yaml 无法读取。") from error
    if not isinstance(content, dict) or set(content) != {"names"}:
        raise CvatImportError("data.yaml 只能包含 names 类别映射。")

    raw_names = content["names"]
    if isinstance(raw_names, list):
        names = raw_names
    elif isinstance(raw_names, dict):
        try:
            indexed_names = {int(index): name for index, name in raw_names.items()}
        except (TypeError, ValueError) as error:
            raise CvatImportError("data.yaml 的类别编号必须是从 0 开始的整数。") from error
        if len(indexed_names) != len(raw_names):
            raise CvatImportError("data.yaml 的类别编号不能重复。")
        if sorted(indexed_names) != list(range(len(indexed_names))):
            raise CvatImportError("data.yaml 的类别编号必须连续且从 0 开始。")
        names = [indexed_names[index] for index in range(len(indexed_names))]
    else:
        raise CvatImportError("data.yaml 的 names 必须是列表或编号映射。")

    if not names or any(not isinstance(name, str) or not name.strip() for name in names):
        raise CvatImportError("类别名称不能为空。")
    normalized = [name.strip() for name in names]
    if len(set(normalized)) != len(normalized):
        raise CvatImportError("类别名称不能重复。")
    return normalized


def _task_names(instance_data) -> list[str]:
    labels = instance_data.meta[instance_data.META_FIELD]["labels"]
    return [label["name"] for _, label in labels]


def _parse_label_file(label_file: Path, width: int, height: int, class_count: int) -> list[Bbox]:
    boxes: list[Bbox] = []
    try:
        lines = label_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise CvatImportError(f"无法读取标签文件：{label_file.name}") from error

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行必须包含 5 个字段。")
        try:
            class_id = int(fields[0])
            center_x, center_y, box_width, box_height = map(float, fields[1:])
        except ValueError as error:
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行包含无效数字。") from error
        values = (center_x, center_y, box_width, box_height)
        if class_id not in range(class_count):
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行的类别编号不存在。")
        if not all(math.isfinite(value) for value in values):
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行包含非有限坐标。")
        if box_width <= 0 or box_height <= 0:
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行的框宽高必须大于 0。")
        left = center_x - box_width / 2
        top = center_y - box_height / 2
        right = center_x + box_width / 2
        bottom = center_y + box_height / 2
        if min(left, top) < 0 or max(right, bottom) > 1:
            raise CvatImportError(f"{label_file.name} 第 {line_number} 行的归一化坐标超出图片范围。")
        boxes.append(Bbox(
            x=left * width,
            y=top * height,
            w=box_width * width,
            h=box_height * height,
            label=class_id,
        ))
    return boxes


def _format_number(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".")


def _task_instance(instance_data, error_type):
    from cvat.apps.engine.models import Task

    instance = instance_data.db_instance
    if not isinstance(instance, Task):
        raise error_type("该格式仅支持任务级导入导出。")
    return instance


def _ensure_8_bit_image(source: bytes | Path, image_name: str, error_type) -> None:
    try:
        with PILImage.open(BytesIO(source) if isinstance(source, bytes) else source) as image:
            if image.mode not in SUPPORTED_8_BIT_MODES:
                raise error_type(f"仅支持 8 位 JPG、PNG 图片：{image_name}")
    except error_type:
        raise
    except (OSError, ValueError) as error:
        raise error_type(f"无法读取图片：{image_name}") from error


def _inspect_package(root: Path) -> tuple[list[str], list[tuple[Path, Path, PurePosixPath]]]:
    names = _load_names(root / "data.yaml")
    images_directory = root / "images"
    labels_directory = root / "labels"
    image_files = sorted(
        path for path in images_directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )
    if not image_files:
        raise CvatImportError("images 文件夹中没有 JPG 或 PNG 图片。")

    image_stems: set[PurePosixPath] = set()
    package_files = []
    for image_file in image_files:
        relative_image = PurePosixPath(image_file.relative_to(images_directory).as_posix())
        item_id = relative_image.with_suffix("")
        if item_id in image_stems:
            raise CvatImportError(f"存在同名图片：{item_id.as_posix()}")
        image_stems.add(item_id)
        label_file = labels_directory.joinpath(*item_id.parts).with_suffix(".txt")
        if not label_file.is_file():
            raise CvatImportError(f"缺少标签文件：labels/{item_id.as_posix()}.txt")
        _ensure_8_bit_image(image_file, relative_image.as_posix(), CvatImportError)
        package_files.append((image_file, label_file, relative_image))

    label_stems = {
        PurePosixPath(path.relative_to(labels_directory).as_posix()).with_suffix("")
        for path in labels_directory.rglob("*.txt")
    }
    if label_stems != image_stems:
        extras = sorted(path.as_posix() for path in label_stems.difference(image_stems))
        raise CvatImportError(f"存在没有对应图片的标签文件：{extras[0]}")

    return names, package_files


@exporter(name=FORMAT_NAME, ext="ZIP", version="1.0", display_name="{NAME}")
def export_yolo26_package(dst_file, temp_dir: str, instance_data, **_kwargs):
    from .reviews import review_summary

    task = _task_instance(instance_data, CvatExportError)
    summary = review_summary(task)
    if summary.unreviewed:
        raise CvatExportError(f"仍有 {summary.unreviewed} 张图片未检查，完成后才能导出。")

    destination = Path(temp_dir)
    images_directory = destination / "images"
    labels_directory = destination / "labels"
    images_directory.mkdir(parents=True, exist_ok=True)
    labels_directory.mkdir(parents=True, exist_ok=True)

    with GetCVATDataExtractor(instance_data, include_images=True) as extractor:
        categories = extractor.categories()[AnnotationType.label]
        names = [item.name for item in categories.items]
        (destination / "data.yaml").write_text(
            yaml.safe_dump({"names": dict(enumerate(names))}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        for item in extractor:
            try:
                item_path = _safe_relative_path(item.id)
            except ValueError as error:
                raise CvatExportError(f"图片路径无效：{item.id}") from error
            extension = item.media.ext.lower()
            if extension not in SUPPORTED_IMAGE_EXTENSIONS:
                raise CvatExportError(f"不支持导出图片格式：{extension}")
            height, width = item.media.size
            if width <= 0 or height <= 0:
                raise CvatExportError(f"无法读取图片尺寸：{item.id}")
            image_bytes = item.media.bytes
            if image_bytes is None:
                raise CvatExportError(f"无法读取原始图片：{item.id}")
            _ensure_8_bit_image(image_bytes, item.id, CvatExportError)

            image_path = images_directory.joinpath(*item_path.parts).with_suffix(extension)
            label_path = labels_directory.joinpath(*item_path.parts).with_suffix(".txt")
            image_path.parent.mkdir(parents=True, exist_ok=True)
            label_path.parent.mkdir(parents=True, exist_ok=True)
            item.media.save(str(image_path))

            lines = []
            for annotation in item.annotations:
                if annotation.type != AnnotationType.bbox:
                    raise CvatExportError(f"图片 {item.id} 包含非矩形框标注，无法导出。")
                x, y, box_width, box_height = annotation.get_bbox()
                values = (x, y, box_width, box_height)
                if (
                    annotation.label not in range(len(names))
                    or not all(math.isfinite(value) for value in values)
                    or box_width <= 0
                    or box_height <= 0
                    or x < 0
                    or y < 0
                    or x + box_width > width
                    or y + box_height > height
                    or annotation.attributes.get("rotation", 0) != 0
                ):
                    raise CvatExportError(f"图片 {item.id} 包含无效矩形框。")
                center_x = (x + box_width / 2) / width
                center_y = (y + box_height / 2) / height
                normalized_width = box_width / width
                normalized_height = box_height / height
                if min(center_x, center_y, normalized_width, normalized_height) < 0 or max(
                    center_x, center_y, normalized_width, normalized_height,
                ) > 1:
                    raise CvatExportError(f"图片 {item.id} 的矩形框超出图片范围。")
                lines.append(" ".join([
                    str(annotation.label),
                    _format_number(center_x),
                    _format_number(center_y),
                    _format_number(normalized_width),
                    _format_number(normalized_height),
                ]))
            label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    make_zip_archive(temp_dir, dst_file)


@importer(name=FORMAT_NAME, ext="ZIP", version="1.0", display_name="{NAME}")
def import_yolo26_package(src_file, temp_dir: str, instance_data, **_kwargs):
    from .reviews import complete_all_frames

    task = _task_instance(instance_data, CvatImportError)
    source = getattr(src_file, "name", src_file)
    _extract_package(source, Path(temp_dir))
    root = _package_root(Path(temp_dir))
    names, package_files = _inspect_package(root)
    if names != _task_names(instance_data):
        raise CvatImportError("导入包的类别及顺序必须与当前任务完全一致。")

    items = []
    for image_file, label_file, relative_image in package_files:
        item_id = relative_image.with_suffix("")
        media = Image.from_file(path=str(image_file))
        height, width = media.size
        items.append(DatasetItem(
            id=item_id.as_posix(),
            media=media,
            annotations=_parse_label_file(label_file, width, height, len(names)),
        ))

    dataset = Dataset.from_iterable(items, categories=names)
    import_dm_annotations(dataset, instance_data)
    complete_all_frames(task)
