# SPDX-License-Identifier: MIT

from django.urls import path

from .views import (
    AppendableTaskListView,
    ExtractionDetailView,
    ExtractionListView,
    PackageImportDetailView,
    PackageImportListView,
    TaskFrameStatusView,
    TaskImageAppendView,
    TaskReviewView,
    VideoListView,
    WorkspaceView,
)

urlpatterns = [
    path("workspace", WorkspaceView.as_view(), name="local-workspace"),
    path("videos", VideoListView.as_view(), name="local-videos"),
    path("extractions", ExtractionListView.as_view(), name="local-extractions"),
    path(
        "extractions/<str:job_id>",
        ExtractionDetailView.as_view(),
        name="local-extraction-detail",
    ),
    path("packages", PackageImportListView.as_view(), name="local-packages"),
    path(
        "packages/<str:job_id>",
        PackageImportDetailView.as_view(),
        name="local-package-detail",
    ),
    path("tasks", AppendableTaskListView.as_view(), name="local-appendable-tasks"),
    path(
        "tasks/<int:task_id>/images",
        TaskImageAppendView.as_view(),
        name="local-task-images",
    ),
    path("tasks/<int:task_id>/review", TaskReviewView.as_view(), name="local-task-review"),
    path(
        "tasks/<int:task_id>/frames/<int:frame>/status",
        TaskFrameStatusView.as_view(),
        name="local-task-frame-status",
    ),
]
