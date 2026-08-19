# SPDX-License-Identifier: MIT

from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from rq import get_current_job

from cvat.apps.dataset_manager.bindings import CvatImportError
from cvat.apps.dataset_manager.task import import_task_annotations
from cvat.apps.engine.models import Data, Task
from cvat.apps.engine.serializers import DataSerializer, TaskWriteSerializer
from cvat.apps.engine.task import initialize_task

from .extraction import ExtractionError, extract_video
from .workspace import WorkspacePathError
from .yolo_format import FORMAT_NAME, _extract_package, _inspect_package, _package_root


def _update_job(progress: int, status: str) -> None:
    job = get_current_job()
    if job:
        job.meta.update(progress=progress, status=status)
        job.save_meta()


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


def import_package_job(*, archive_path: str, task_name: str, user_id: int):
    archive = Path(archive_path)
    db_data: Data | None = None
    db_task: Task | None = None
    try:
        _update_job(5, "正在检查标注包")
        with TemporaryDirectory(prefix="package-import-", dir=settings.TMP_FILES_ROOT) as directory:
            extraction_directory = Path(directory)
            _extract_package(archive, extraction_directory)
            package_root = _package_root(extraction_directory)
            names, package_files = _inspect_package(package_root)
            image_root = package_root / "images"
            server_files = [
                image_file.relative_to(image_root).as_posix()
                for image_file, _label_file, _relative_image in package_files
            ]

            _update_job(20, "正在创建任务")
            data_serializer = DataSerializer(data={
                "server_files": server_files,
                "image_quality": 70,
                "use_zip_chunks": True,
                "use_cache": True,
                "copy_data": True,
                "sorting_method": "lexicographical",
            })
            data_serializer.is_valid(raise_exception=True)
            db_data = data_serializer.save()

            task_serializer = TaskWriteSerializer(data={
                "name": task_name,
                "labels": [{"name": name, "type": "rectangle"} for name in names],
            })
            task_serializer.is_valid(raise_exception=True)
            user = get_user_model().objects.get(pk=user_id)
            db_task = task_serializer.save(owner=user, data_id=db_data.id)

            data = dict(data_serializer.data)
            for field in ("use_zip_chunks", "use_cache", "copy_data"):
                data[field] = data_serializer.validated_data[field]
            data["server_files_path"] = str(image_root)
            data["stop_frame"] = None

            _update_job(35, "正在复制图片")
            initialize_task(db_task=db_task, data=data)
            _update_job(75, "正在导入标注")
            import_task_annotations(archive, db_task.id, FORMAT_NAME, False)
            _update_job(100, "导入完成")
            return {"task_id": db_task.id}
    except Exception as error:
        if db_task:
            db_task.delete()
        elif db_data:
            db_data.delete()
        job = get_current_job()
        if job:
            message = str(error) if isinstance(error, CvatImportError) else "导入失败，请检查压缩包结构和内容。"
            job.meta["error"] = message
            job.save_meta()
        raise
    finally:
        archive.unlink(missing_ok=True)
