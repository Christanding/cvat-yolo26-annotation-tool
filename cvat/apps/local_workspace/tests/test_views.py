# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

from django.test import override_settings
from rest_framework.test import APIRequestFactory, force_authenticate
from rq import Queue

from cvat.apps.local_workspace.views import ExtractionListView, WorkspaceView


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


if __name__ == "__main__":
    unittest.main()
