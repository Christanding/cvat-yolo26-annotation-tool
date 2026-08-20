# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from PIL import Image as PILImage
from rest_framework.test import APIRequestFactory, force_authenticate
from rq import Queue

from cvat.apps.engine.models import (
    Data,
    DataChoice,
    DimensionType,
    Image,
    Job,
    MediaType,
    Segment,
    SegmentType,
    ServerFile,
    StorageChoice,
    StorageMethodChoice,
    Task,
    TaskMode,
)
from cvat.apps.local_workspace.models import FrameReview
from cvat.apps.local_workspace.views import (
    AppendableTaskListView,
    ExtractionListView,
    TaskImageAppendView,
    WorkspaceView,
)


class WorkspaceViewTest(unittest.TestCase):
    def test_authenticated_user_can_list_workspace_images(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "thermal.png").touch()
            request = APIRequestFactory().get("/api/local/workspace")
            force_authenticate(
                request,
                user=SimpleNamespace(is_authenticated=True),
            )

            with override_settings(LOCAL_WORKSPACE_ROOT=root):
                response = WorkspaceView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, [{"path": "thermal.png", "kind": "image"}])

    def test_anonymous_user_cannot_list_workspace(self):
        request = APIRequestFactory().get("/api/local/workspace")

        response = WorkspaceView.as_view()(request)

        self.assertEqual(response.status_code, 401)


class ExtractionListViewTest(unittest.TestCase):
    @patch("cvat.apps.local_workspace.views.django_rq.get_queue")
    def test_authenticated_user_can_enqueue_extraction(self, get_queue):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "clip.mp4").touch()
            queued_job = MagicMock(id="job-1")
            queue = create_autospec(Queue, instance=True)
            queue.enqueue_call.return_value = queued_job
            get_queue.return_value = queue
            request = APIRequestFactory().post(
                "/api/local/extractions",
                {
                    "path": "clip.mp4",
                    "start_time": 0,
                    "end_time": 10,
                    "interval": 1,
                    "strength": "medium",
                },
                format="json",
            )
            force_authenticate(
                request,
                user=SimpleNamespace(id=7, is_authenticated=True),
            )

            with override_settings(LOCAL_WORKSPACE_ROOT=root):
                response = ExtractionListView.as_view()(request)

            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.data, {"id": "job-1", "status": "queued"})
            job_parameters = queue.enqueue_call.call_args.kwargs["kwargs"]
            self.assertEqual(job_parameters["relative_path"], "clip.mp4")
            self.assertNotIn("path", job_parameters)

    def test_existing_output_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "clip.mp4").touch()
            (root / "images" / "clip").mkdir(parents=True)
            request = APIRequestFactory().post(
                "/api/local/extractions",
                {
                    "path": "clip.mp4",
                    "start_time": 0,
                    "end_time": 10,
                    "interval": 1,
                    "strength": "medium",
                },
                format="json",
            )
            force_authenticate(
                request,
                user=SimpleNamespace(id=7, is_authenticated=True),
            )

            with override_settings(LOCAL_WORKSPACE_ROOT=root):
                response = ExtractionListView.as_view()(request)

            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.data["code"], "output_exists")


class TaskImageAppendViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="local-user")
        self.data = Data.objects.create(
            size=1,
            start_frame=0,
            stop_frame=0,
            chunk_size=36,
            image_quality=70,
            storage=StorageChoice.SHARE,
            storage_method=StorageMethodChoice.CACHE,
            original_chunk_type=DataChoice.IMAGESET,
            compressed_chunk_type=DataChoice.IMAGESET,
        )
        self.task = Task.objects.create(
            name="现有任务",
            owner=self.user,
            data=self.data,
            dimension=DimensionType.DIM_2D,
            mode=TaskMode.ANNOTATION,
            media_type=MediaType.IMAGE,
            segment_size=1,
            overlap=0,
        )
        self.segment = Segment.objects.create(
            task=self.task,
            start_frame=0,
            stop_frame=0,
            type=SegmentType.RANGE,
        )
        Job.objects.create(segment=self.segment)
        Image.objects.create(
            data=self.data,
            path="original.png",
            frame=0,
            width=16,
            height=12,
        )
        ServerFile.objects.create(data=self.data, file="original.png")
        FrameReview.objects.create(task=self.task, frame=0)

    @patch("cvat.apps.local_workspace.task_images.TaskFrameProvider.invalidate_chunks")
    def test_owner_can_append_extracted_images_to_existing_task(self, invalidate_chunks):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output = root / "images" / "clip"
            output.mkdir(parents=True)
            PILImage.new("RGB", (20, 10)).save(output / "clip__t000000s__f00000000.png")
            PILImage.new("RGB", (30, 15)).save(output / "clip__t000005s__f00000125.png")

            request = APIRequestFactory().post(
                f"/api/local/tasks/{self.task.id}/images",
                {"path": "images/clip"},
                format="json",
            )
            force_authenticate(request, user=self.user)
            with override_settings(LOCAL_WORKSPACE_ROOT=root):
                response = TaskImageAppendView.as_view()(request, task_id=self.task.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["added_count"], 2)
        self.assertEqual(response.data["total_count"], 3)
        self.data.refresh_from_db()
        self.segment.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual((self.data.size, self.data.stop_frame), (3, 2))
        self.assertEqual(self.segment.stop_frame, 2)
        self.assertEqual(self.task.segment_size, 3)
        self.assertEqual(
            list(self.data.images.order_by("frame").values_list("frame", "path")),
            [
                (0, "original.png"),
                (1, "images/clip/clip__t000000s__f00000000.png"),
                (2, "images/clip/clip__t000005s__f00000125.png"),
            ],
        )
        self.assertEqual(FrameReview.objects.filter(task=self.task).count(), 1)
        self.assertEqual(invalidate_chunks.call_count, 2)

    def test_appendable_task_list_only_returns_workspace_image_tasks(self):
        request = APIRequestFactory().get("/api/local/tasks")
        force_authenticate(request, user=self.user)

        response = AppendableTaskListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{"id": self.task.id, "name": "现有任务", "size": 1}])

    def test_extraction_output_used_by_task_cannot_be_overwritten(self):
        ServerFile.objects.create(data=self.data, file="images/clip/frame.png")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "clip.mp4").touch()
            (root / "images" / "clip").mkdir(parents=True)
            request = APIRequestFactory().post(
                "/api/local/extractions",
                {
                    "path": "clip.mp4",
                    "start_time": 0,
                    "end_time": 10,
                    "interval": 1,
                    "strength": "medium",
                },
                format="json",
            )
            force_authenticate(request, user=self.user)
            with override_settings(LOCAL_WORKSPACE_ROOT=root):
                response = ExtractionListView.as_view()(request)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "output_in_use")


if __name__ == "__main__":
    unittest.main()
