# SPDX-License-Identifier: MIT

from django.db import models

from cvat.apps.engine.models import Task


class FrameReview(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="frame_reviews")
    frame = models.PositiveIntegerField()
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=("task", "frame"),
                name="local_workspace_unique_task_frame_review",
            ),
        ]
