# SPDX-License-Identifier: MIT

from django.urls import path

from .views import WorkspaceView

urlpatterns = [
    path("workspace", WorkspaceView.as_view(), name="local-workspace"),
]
