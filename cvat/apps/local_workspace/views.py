# SPDX-License-Identifier: MIT

from pathlib import Path, PurePosixPath
from uuid import uuid4

import django_rq
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from rest_framework.views import APIView

from cvat.apps.engine.models import ServerFile, Task

from .extraction import (
    ExtractionError,
    is_path_referenced,
    output_path_for_video,
    probe_video,
)
from .jobs import extract_video_job, import_package_job
from .reviews import (
    InvalidFrameError,
    complete_all_frames,
    complete_frame,
    frame_status,
    review_summary,
)
from .workspace import WorkspacePathError, resolve_workspace_file, scan_workspace


class WorkspaceQuerySerializer(serializers.Serializer):
    path = serializers.CharField(required=False, allow_blank=True, default="")
    recursive = serializers.BooleanField(required=False, default=False)


class WorkspaceEntrySerializer(serializers.Serializer):
    path = serializers.CharField()
    kind = serializers.ChoiceField(choices=["directory", "image", "video", "archive"])


class ExtractionRequestSerializer(serializers.Serializer):
    path = serializers.CharField()
    start_time = serializers.IntegerField(min_value=0)
    end_time = serializers.IntegerField(min_value=0)
    interval = serializers.IntegerField(min_value=1)
    strength = serializers.ChoiceField(choices=["low", "medium", "high"], default="medium")
    overwrite = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs["end_time"] < attrs["start_time"]:
            raise serializers.ValidationError({"end_time": "结束时间不能早于开始时间。"})
        return attrs


class VideoMetadataSerializer(serializers.Serializer):
    path = serializers.CharField()
    duration = serializers.IntegerField()
    fps = serializers.FloatField()
    frame_count = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class ExtractionQueuedSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()


class ExtractionResultSerializer(serializers.Serializer):
    source_count = serializers.IntegerField()
    exact_duplicates = serializers.IntegerField()
    similar_skipped = serializers.IntegerField()
    kept_count = serializers.IntegerField()
    output_path = serializers.CharField()


class ExtractionStatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    result = ExtractionResultSerializer(required=False)
    error = serializers.CharField(required=False)


class PackageImportRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256, trim_whitespace=True)
    file = serializers.FileField()

    def validate_file(self, value):
        if Path(value.name).suffix.lower() != ".zip":
            raise serializers.ValidationError("请选择 ZIP 标注包。")
        return value


class PackageImportResultSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()


class PackageImportStatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    message = serializers.CharField(required=False)
    result = PackageImportResultSerializer(required=False)
    error = serializers.CharField(required=False)


class FrameStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["unreviewed", "annotated", "empty"])


class ReviewSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    reviewed = serializers.IntegerField()
    annotated = serializers.IntegerField()
    empty = serializers.IntegerField()
    unreviewed = serializers.IntegerField()


def owned_task(request, task_id: int) -> Task:
    return get_object_or_404(
        Task.objects.select_related("data"),
        pk=task_id,
        owner=request.user,
    )


class WorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List local workspace entries",
        parameters=[WorkspaceQuerySerializer],
        responses=WorkspaceEntrySerializer(many=True),
        tags=["local workspace"],
    )
    def get(self, request):
        query = WorkspaceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        try:
            entries = scan_workspace(
                settings.LOCAL_WORKSPACE_ROOT,
                relative_path=query.validated_data["path"],
                recursive=query.validated_data["recursive"],
            )
        except WorkspacePathError as error:
            raise ValidationError({"path": "所选路径不存在，或不在工作区内。"}) from error

        return Response(WorkspaceEntrySerializer(entries, many=True).data)


class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List videos in the local workspace",
        responses=VideoMetadataSerializer(many=True),
        tags=["local workspace"],
    )
    def get(self, request):
        try:
            videos = [
                probe_video(Path(settings.LOCAL_WORKSPACE_ROOT), entry.path)
                for entry in scan_workspace(
                    Path(settings.LOCAL_WORKSPACE_ROOT),
                    recursive=True,
                )
                if entry.kind == "video"
            ]
        except (ExtractionError, WorkspacePathError) as error:
            raise ValidationError({"path": str(error)}) from error
        return Response(VideoMetadataSerializer(videos, many=True).data)


class ExtractionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Start extracting frames from a workspace video",
        request=ExtractionRequestSerializer,
        responses=ExtractionQueuedSerializer,
        tags=["local workspace"],
    )
    def post(self, request):
        serializer = ExtractionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parameters = dict(serializer.validated_data)
        relative_path = parameters.pop("path")
        root = Path(settings.LOCAL_WORKSPACE_ROOT)
        try:
            resolve_workspace_file(root, relative_path, allowed_extensions={".mp4", ".mov"})
        except WorkspacePathError as error:
            raise ValidationError({"path": "所选视频不存在，或不在工作区内。"}) from error

        relative_output = output_path_for_video(PurePosixPath(relative_path))
        output = root.resolve(strict=True).joinpath(*relative_output.parts)
        if output.exists() and not parameters["overwrite"]:
            return Response(
                {"code": "output_exists", "message": "抽帧目录已存在，请选择覆盖或取消。"},
                status=HTTP_409_CONFLICT,
            )
        if output.exists() and is_path_referenced(
            relative_output,
            list(ServerFile.objects.values_list("file", flat=True)),
        ):
            return Response(
                {"code": "output_in_use", "message": "抽帧目录已被标注任务使用，不能覆盖。"},
                status=HTTP_409_CONFLICT,
            )

        queue = django_rq.get_queue(settings.CVAT_QUEUES.LOCAL_MEDIA.value)
        job = queue.enqueue_call(
            func=extract_video_job,
            kwargs={"relative_path": relative_path, **parameters},
            result_ttl=24 * 60 * 60,
            failure_ttl=24 * 60 * 60,
            meta={"user_id": request.user.id, "progress": 0},
        )
        return Response({"id": job.id, "status": "queued"}, status=HTTP_202_ACCEPTED)


class ExtractionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get frame extraction status",
        responses=ExtractionStatusSerializer,
        tags=["local workspace"],
    )
    def get(self, request, job_id: str):
        queue = django_rq.get_queue(settings.CVAT_QUEUES.LOCAL_MEDIA.value)
        job = queue.fetch_job(job_id)
        if not job or job.meta.get("user_id") != request.user.id:
            return Response(status=HTTP_404_NOT_FOUND)

        job_status = job.get_status(refresh=True)
        status_value = job_status.value if hasattr(job_status, "value") else str(job_status)
        response = {
            "id": job.id,
            "status": status_value,
            "progress": job.meta.get("progress", 0),
        }
        if status_value == "finished":
            response["result"] = job.return_value()
        elif status_value == "failed":
            response["error"] = job.meta.get("error", "抽帧失败，请检查视频文件和参数。")
        return Response(response)


class PackageImportListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        summary="Create a task from a YOLO26 package",
        request=PackageImportRequestSerializer,
        responses=ExtractionQueuedSerializer,
        tags=["local annotation"],
    )
    def post(self, request):
        serializer = PackageImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        archive = Path(settings.TMP_FILES_ROOT) / f"local-package-{uuid4().hex}.zip"
        try:
            with archive.open("wb") as destination:
                for chunk in upload.chunks():
                    destination.write(chunk)
            queue = django_rq.get_queue(settings.CVAT_QUEUES.IMPORT_DATA.value)
            job = queue.enqueue_call(
                func=import_package_job,
                kwargs={
                    "archive_path": str(archive),
                    "task_name": serializer.validated_data["name"],
                    "user_id": request.user.id,
                },
                result_ttl=24 * 60 * 60,
                failure_ttl=24 * 60 * 60,
                meta={"user_id": request.user.id, "progress": 0},
            )
        except Exception:
            archive.unlink(missing_ok=True)
            raise
        return Response({"id": job.id, "status": "queued"}, status=HTTP_202_ACCEPTED)


class PackageImportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get package import status",
        responses=PackageImportStatusSerializer,
        tags=["local annotation"],
    )
    def get(self, request, job_id: str):
        queue = django_rq.get_queue(settings.CVAT_QUEUES.IMPORT_DATA.value)
        job = queue.fetch_job(job_id)
        if not job or job.meta.get("user_id") != request.user.id:
            return Response(status=HTTP_404_NOT_FOUND)

        job_status = job.get_status(refresh=True)
        status_value = job_status.value if hasattr(job_status, "value") else str(job_status)
        response = {
            "id": job.id,
            "status": status_value,
            "progress": job.meta.get("progress", 0),
        }
        if message := job.meta.get("status"):
            response["message"] = message
        if status_value == "finished":
            response["result"] = job.return_value()
        elif status_value == "failed":
            response["error"] = job.meta.get("error", "导入失败，请检查标注包。")
        return Response(response)


class TaskFrameStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get the review status of a task frame",
        responses=FrameStatusSerializer,
        tags=["local annotation"],
    )
    def get(self, request, task_id: int, frame: int):
        task = owned_task(request, task_id)
        try:
            status_value = frame_status(task, frame)
        except InvalidFrameError as error:
            raise ValidationError({"frame": str(error)}) from error
        return Response({"status": status_value})

    @extend_schema(
        summary="Mark a task frame as reviewed",
        request=None,
        responses=FrameStatusSerializer,
        tags=["local annotation"],
    )
    def post(self, request, task_id: int, frame: int):
        task = owned_task(request, task_id)
        try:
            status_value = complete_frame(task, frame)
        except InvalidFrameError as error:
            raise ValidationError({"frame": str(error)}) from error
        return Response({"status": status_value})


class TaskReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get task review statistics",
        responses=ReviewSummarySerializer,
        tags=["local annotation"],
    )
    def get(self, request, task_id: int):
        summary = review_summary(owned_task(request, task_id))
        return Response(ReviewSummarySerializer(summary).data)

    @extend_schema(
        summary="Mark every frame in a task as reviewed",
        request=None,
        responses=ReviewSummarySerializer,
        tags=["local annotation"],
    )
    def post(self, request, task_id: int):
        summary = complete_all_frames(owned_task(request, task_id))
        return Response(ReviewSummarySerializer(summary).data)
