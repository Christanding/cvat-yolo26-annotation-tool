# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from django.db import transaction

from cvat.apps.engine.models import LabeledShape, ShapeType, Task

from .models import FrameReview


class InvalidFrameError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewSummary:
    total: int
    reviewed: int
    annotated: int
    empty: int
    unreviewed: int


def categories_locked(task: Task) -> bool:
    return FrameReview.objects.filter(task=task).exists() or LabeledShape.objects.filter(
        job__segment__task=task,
    ).exists()


def task_frames(task: Task) -> range:
    return task.require_data().get_valid_frame_indices()


def validate_frame(task: Task, frame: int) -> None:
    if frame not in task_frames(task):
        raise InvalidFrameError("图片序号不属于当前任务。")


def annotated_frames(task: Task) -> set[int]:
    return set(
        LabeledShape.objects.filter(
            job__segment__task=task,
            type=ShapeType.RECTANGLE,
            outside=False,
        ).values_list("frame", flat=True)
    )


def frame_status(task: Task, frame: int) -> str:
    validate_frame(task, frame)
    if frame in annotated_frames(task):
        return "annotated"
    if FrameReview.objects.filter(task=task, frame=frame).exists():
        return "empty"
    return "unreviewed"


@transaction.atomic
def complete_frame(task: Task, frame: int) -> str:
    validate_frame(task, frame)
    FrameReview.objects.get_or_create(task=task, frame=frame)
    return frame_status(task, frame)


@transaction.atomic
def complete_all_frames(task: Task) -> ReviewSummary:
    FrameReview.objects.bulk_create(
        [FrameReview(task=task, frame=frame) for frame in task_frames(task)],
        ignore_conflicts=True,
    )
    return review_summary(task)


def review_summary(task: Task) -> ReviewSummary:
    frames = set(task_frames(task))
    annotated = annotated_frames(task).intersection(frames)
    explicitly_reviewed = set(
        FrameReview.objects.filter(task=task, frame__in=frames).values_list("frame", flat=True)
    )
    reviewed = annotated.union(explicitly_reviewed)
    return ReviewSummary(
        total=len(frames),
        reviewed=len(reviewed),
        annotated=len(annotated),
        empty=len(reviewed.difference(annotated)),
        unreviewed=len(frames.difference(reviewed)),
    )
