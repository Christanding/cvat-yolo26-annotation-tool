# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from django.test import override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from cvat.apps.local_workspace.views import WorkspaceView


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


if __name__ == "__main__":
    unittest.main()
