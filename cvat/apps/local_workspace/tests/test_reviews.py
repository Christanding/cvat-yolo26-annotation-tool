# SPDX-License-Identifier: MIT

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import serializers

from cvat.apps.engine.serializers import LabelSerializer
from cvat.apps.engine.models import Data, Job, Label, LabeledShape, Segment, ShapeType, Task
from cvat.apps.local_workspace.reviews import (
    InvalidFrameError,
    ReviewSummary,
    categories_locked,
    complete_all_frames,
    complete_frame,
    frame_status,
    review_summary,
)


class FrameReviewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        owner = User.objects.create_user(username="local-user")
        data = Data.objects.create(size=3, start_frame=0, stop_frame=2)
        cls.task = Task.objects.create(name="review-task", owner=owner, data=data)
        segment = Segment.objects.create(task=cls.task, start_frame=0, stop_frame=2)
        cls.job = Job.objects.create(segment=segment)
        cls.label = Label.objects.create(task=cls.task, name="defect")

    def test_frame_status_distinguishes_unreviewed_empty_and_annotated(self):
        self.assertEqual(frame_status(self.task, 0), "unreviewed")
        self.assertEqual(complete_frame(self.task, 0), "empty")

        LabeledShape.objects.create(
            job=self.job,
            label=self.label,
            frame=1,
            type=ShapeType.RECTANGLE,
            points=[10, 10, 20, 20],
        )

        self.assertEqual(frame_status(self.task, 1), "annotated")

    def test_summary_counts_annotations_and_confirmed_empty_frames(self):
        complete_frame(self.task, 0)
        LabeledShape.objects.create(
            job=self.job,
            label=self.label,
            frame=1,
            type=ShapeType.RECTANGLE,
            points=[10, 10, 20, 20],
        )

        self.assertEqual(
            review_summary(self.task),
            ReviewSummary(total=3, reviewed=2, annotated=1, empty=1, unreviewed=1),
        )

        self.assertEqual(complete_all_frames(self.task).unreviewed, 0)

    def test_rejects_frame_outside_task(self):
        with self.assertRaises(InvalidFrameError):
            complete_frame(self.task, 3)

    def test_categories_lock_after_first_review(self):
        self.assertFalse(categories_locked(self.task))
        complete_frame(self.task, 0)
        self.assertTrue(categories_locked(self.task))

    def test_locked_category_cannot_be_deleted(self):
        complete_frame(self.task, 0)

        with self.assertRaises(serializers.ValidationError):
            LabelSerializer.update_labels(
                [{"id": self.label.id, "deleted": True, "attributespec_set": []}],
                parent_instance=self.task,
            )
