# SPDX-License-Identifier: MIT

from django.urls import path

from .views import ExtractionDetailView, ExtractionListView, VideoListView, WorkspaceView

urlpatterns = [
    path("workspace", WorkspaceView.as_view(), name="local-workspace"),
    path("videos", VideoListView.as_view(), name="local-videos"),
    path("extractions", ExtractionListView.as_view(), name="local-extractions"),
    path(
        "extractions/<str:job_id>",
        ExtractionDetailView.as_view(),
        name="local-extraction-detail",
    ),
]
