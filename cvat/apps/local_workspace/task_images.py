# SPDX-License-Identifier: MIT

from dataclasses import asdict, dataclass
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from cvat.apps.engine.media_io.frame_provider import TaskFrameProvider
from cvat.apps.engine.models import (
    Data,
    DimensionType,
    FrameQuality,
    Image,
    JobType,
    MediaType,
    Segment,
    SegmentType,
    ServerFile,
    StorageChoice,
    StorageMethodChoice,
    Task,
    TaskMode,
    ValidationLayout,
)

from .workspace import WorkspacePathError, resolve_workspace_file, scan_workspace
from .yolo_format import SUPPORTED_8_BIT_MODES


class TaskImageAppendError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AppendableTask:
    id: int
    name: str
    size: int

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(frozen=True)
class TaskImageAppendResult:
    task_id: int
    added_count: int
    total_count: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def _appendable_segment(task: Task) -> Segment | None:
    data = task.require_data()
    if (
        task.project_id is not None
        or task.media_type != MediaType.IMAGE
        or task.mode != TaskMode.ANNOTATION
        or task.dimension != DimensionType.DIM_2D
        or task.consensus_replicas
        or data.storage != StorageChoice.SHARE
        or data.storage_method != StorageMethodChoice.CACHE
        or ValidationLayout.objects.filter(task_data=data).exists()
    ):
        return None

    segments = list(task.segment_set.all())
    if len(segments) != 1:
        return None

    segment = segments[0]
    if (
        segment.type != SegmentType.RANGE
        or segment.start_frame != 0
        or segment.job_set.exclude(type=JobType.ANNOTATION).exists()
        or segment.job_set.filter(type=JobType.ANNOTATION).count() != 1
    ):
        return None
    return segment


def list_appendable_tasks(user) -> list[AppendableTask]:
    tasks = (
        Task.objects.filter(owner=user, data__isnull=False)
        .select_related("data")
        .prefetch_related("segment_set__job_set")
        .order_by("-updated_date", "-id")
    )
    return [
        AppendableTask(id=task.id, name=task.name, size=task.require_data().size)
        for task in tasks
        if _appendable_segment(task)
    ]


def _read_image_size(root: Path, relative_path: str) -> tuple[int, int]:
    image_path = resolve_workspace_file(root, relative_path, allowed_extensions={".jpg", ".png"})
    try:
        with PILImage.open(image_path) as image:
            image.load()
            if image.mode not in SUPPORTED_8_BIT_MODES:
                raise TaskImageAppendError(
                    "unsupported_image",
                    f"仅支持 8 位 JPG、PNG 图片：{relative_path}",
                )
            return image.size
    except (OSError, UnidentifiedImageError) as error:
        raise TaskImageAppendError(
            "invalid_image", f"无法读取图片：{relative_path}"
        ) from error


def append_workspace_images(
    task: Task, root: Path, relative_directory: str
) -> TaskImageAppendResult:
    entries = scan_workspace(root, relative_path=relative_directory, recursive=True)
    image_paths = [entry.path for entry in entries if entry.kind == "image"]
    if not image_paths:
        raise TaskImageAppendError("no_images", "所选抽帧目录中没有可添加的图片。")

    dimensions = {path: _read_image_size(root, path) for path in image_paths}

    with transaction.atomic():
        locked_task = (
            Task.objects.select_for_update()
            .prefetch_related("segment_set__job_set")
            .get(pk=task.pk, owner_id=task.owner_id)
        )
        segment = _appendable_segment(locked_task)
        if not segment:
            raise TaskImageAppendError(
                "task_not_appendable",
                "该任务不是可追加图片的本地工作区图片任务。",
            )

        data = Data.objects.select_for_update().get(pk=locked_task.data_id)
        existing_paths = set(data.images.values_list("path", flat=True))
        new_paths = [path for path in image_paths if path not in existing_paths]
        if not new_paths:
            raise TaskImageAppendError("no_new_images", "这些图片已经在所选任务中。")

        frame_step = data.get_frame_step()
        first_frame = data.stop_frame + frame_step if data.size else data.start_frame
        Image.objects.bulk_create(
            [
                Image(
                    data=data,
                    path=path,
                    frame=first_frame + index * frame_step,
                    width=dimensions[path][0],
                    height=dimensions[path][1],
                )
                for index, path in enumerate(new_paths)
            ]
        )
        ServerFile.objects.bulk_create(
            [ServerFile(data=data, file=path) for path in new_paths],
            ignore_conflicts=True,
        )

        data.size += len(new_paths)
        data.stop_frame = data.start_frame + (data.size - 1) * frame_step
        data.save(update_fields=["size", "stop_frame"])
        locked_task.data = data

        segment.stop_frame = data.stop_frame
        segment.chunks_updated_date = timezone.now()
        segment.save(update_fields=["stop_frame", "chunks_updated_date"])

        locked_task.segment_size = data.size
        locked_task.updated_date = timezone.now()
        locked_task.save(update_fields=["segment_size", "updated_date"])

        frame_provider = TaskFrameProvider(locked_task)
        for quality in FrameQuality:
            frame_provider.invalidate_chunks(quality=quality)

    return TaskImageAppendResult(
        task_id=locked_task.id,
        added_count=len(new_paths),
        total_count=data.size,
    )
