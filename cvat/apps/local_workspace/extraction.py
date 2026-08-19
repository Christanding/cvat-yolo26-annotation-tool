# SPDX-License-Identifier: MIT

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

import cv2
import numpy as np

from .workspace import resolve_workspace_file


DEDUPLICATION_THRESHOLDS = {
    "low": 0.005,
    "medium": 0.015,
    "high": 0.030,
}


class ExtractionError(RuntimeError):
    pass


class OutputExistsError(ExtractionError):
    pass


@dataclass(frozen=True)
class VideoMetadata:
    path: str
    duration: int
    fps: float
    frame_count: int
    width: int
    height: int


@dataclass(frozen=True)
class ExtractionStats:
    source_count: int
    exact_duplicates: int
    similar_skipped: int
    kept_count: int
    output_path: str

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


def frame_filename(video_name: str, *, timestamp: int, frame_number: int) -> str:
    return f"{video_name}__t{timestamp:06d}s__f{frame_number:08d}.png"


def output_path_for_video(video_path: PurePosixPath) -> PurePosixPath:
    return video_path.parent / "images" / video_path.stem


def is_path_referenced(output_path: PurePosixPath, server_files: list[str]) -> bool:
    for server_file in server_files:
        referenced_path = PurePosixPath(server_file.rstrip("/"))
        if (
            referenced_path == output_path
            or referenced_path in output_path.parents
            or output_path in referenced_path.parents
        ):
            return True
    return False


def _thumbnail(frame: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)


def similarity_score(previous: np.ndarray, candidate: np.ndarray) -> float:
    difference = cv2.absdiff(_thumbnail(previous), _thumbnail(candidate))
    return float(difference.mean() / 255.0)


def classify_frame(previous: np.ndarray, candidate: np.ndarray, strength: str) -> str:
    if strength not in DEDUPLICATION_THRESHOLDS:
        raise ValueError(f"unsupported deduplication strength: {strength}")
    if previous.shape == candidate.shape and np.array_equal(previous, candidate):
        return "exact"
    if similarity_score(previous, candidate) <= DEDUPLICATION_THRESHOLDS[strength]:
        return "similar"
    return "keep"


def probe_video(root: Path, relative_path: str) -> VideoMetadata:
    video_path = resolve_workspace_file(root, relative_path, allowed_extensions={".mp4", ".mov"})
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise ExtractionError("无法打开视频，请检查文件或编码格式。")
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0 or frame_count <= 0:
            raise ExtractionError("无法读取视频帧率或帧数。")
        return VideoMetadata(
            path=PurePosixPath(relative_path).as_posix(),
            duration=max(0, int((frame_count - 1) / fps)),
            fps=fps,
            frame_count=frame_count,
            width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    finally:
        capture.release()


def extract_video(
    root: Path,
    *,
    relative_path: str,
    start_time: int,
    end_time: int,
    interval: int,
    strength: str,
    overwrite: bool = False,
    progress_callback: Callable[[int], None] | None = None,
) -> ExtractionStats:
    if start_time < 0 or end_time < start_time or interval < 1:
        raise ExtractionError("抽帧时间范围或间隔无效。")
    if strength not in DEDUPLICATION_THRESHOLDS:
        raise ExtractionError("去重强度无效。")

    video_path = resolve_workspace_file(root, relative_path, allowed_extensions={".mp4", ".mov"})
    relative_video_path = PurePosixPath(relative_path)
    relative_output_path = output_path_for_video(relative_video_path)
    resolved_root = root.resolve(strict=True)
    output_path = resolved_root.joinpath(*relative_output_path.parts)
    output_parent = output_path.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    try:
        output_parent.resolve(strict=True).relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise ExtractionError("抽帧输出目录不在工作区内。") from error

    if output_path.exists() and not overwrite:
        raise OutputExistsError("抽帧目录已存在，请选择覆盖或取消。")
    if output_path.exists() and (not output_path.is_dir() or output_path.is_symlink()):
        raise ExtractionError("抽帧输出路径不是可覆盖的文件夹。")

    capture = cv2.VideoCapture(str(video_path))
    staging_path: Path | None = None
    try:
        if not capture.isOpened():
            raise ExtractionError("无法打开视频，请检查文件或编码格式。")
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0 or frame_count <= 0:
            raise ExtractionError("无法读取视频帧率或帧数。")

        timestamps = [
            second
            for second in range(start_time, end_time + 1, interval)
            if round(second * fps) < frame_count
        ]
        if not timestamps:
            raise ExtractionError("所选时间范围内没有可抽取的视频帧。")

        staging_path = Path(tempfile.mkdtemp(prefix=f".{video_path.stem}.extracting-", dir=output_parent))
        source_count = 0
        exact_duplicates = 0
        similar_skipped = 0
        kept_count = 0
        previous_kept: np.ndarray | None = None

        for index, timestamp in enumerate(timestamps, start=1):
            frame_number = round(timestamp * fps)
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            success, frame = capture.read()
            if not success:
                raise ExtractionError(f"无法读取第 {frame_number} 帧。")
            source_count += 1

            classification = "keep" if previous_kept is None else classify_frame(
                previous_kept,
                frame,
                strength,
            )
            if classification == "exact":
                exact_duplicates += 1
            elif classification == "similar":
                similar_skipped += 1
            else:
                destination = staging_path / frame_filename(
                    video_path.stem,
                    timestamp=timestamp,
                    frame_number=frame_number,
                )
                if not cv2.imwrite(str(destination), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
                    raise ExtractionError(f"无法保存第 {frame_number} 帧。")
                previous_kept = frame
                kept_count += 1

            if progress_callback:
                progress_callback(round(index * 100 / len(timestamps)))

        if output_path.exists():
            shutil.rmtree(output_path)
        staging_path.rename(output_path)
        staging_path = None
        return ExtractionStats(
            source_count=source_count,
            exact_duplicates=exact_duplicates,
            similar_skipped=similar_skipped,
            kept_count=kept_count,
            output_path=relative_output_path.as_posix(),
        )
    finally:
        capture.release()
        if staging_path and staging_path.exists():
            shutil.rmtree(staging_path)
