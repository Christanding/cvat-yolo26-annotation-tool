# SPDX-License-Identifier: MIT

from pathlib import Path

from django.conf import settings
from rq import get_current_job

from .extraction import ExtractionError, extract_video
from .workspace import WorkspacePathError


def extract_video_job(**parameters):
    job = get_current_job()

    def update_progress(progress: int) -> None:
        if job:
            job.meta["progress"] = progress
            job.save_meta()

    try:
        result = extract_video(
            Path(settings.LOCAL_WORKSPACE_ROOT),
            **parameters,
            progress_callback=update_progress,
        )
        return result.as_dict()
    except (ExtractionError, WorkspacePathError) as error:
        if job:
            job.meta["error"] = str(error)
            job.save_meta()
        raise
