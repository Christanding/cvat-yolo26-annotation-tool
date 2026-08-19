# SPDX-License-Identifier: MIT

from django.apps import AppConfig


class LocalWorkspaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cvat.apps.local_workspace"
    verbose_name = "Local annotation workspace"
