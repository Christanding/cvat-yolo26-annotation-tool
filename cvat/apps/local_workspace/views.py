# SPDX-License-Identifier: MIT

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .workspace import WorkspacePathError, scan_workspace


class WorkspaceQuerySerializer(serializers.Serializer):
    path = serializers.CharField(required=False, allow_blank=True, default="")
    recursive = serializers.BooleanField(required=False, default=False)


class WorkspaceEntrySerializer(serializers.Serializer):
    path = serializers.CharField()
    kind = serializers.ChoiceField(choices=["directory", "image", "video", "archive"])


class WorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List local workspace entries",
        parameters=[WorkspaceQuerySerializer],
        responses=WorkspaceEntrySerializer(many=True),
        tags=["local workspace"],
    )
    def get(self, request):
        query = WorkspaceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        try:
            entries = scan_workspace(
                settings.LOCAL_WORKSPACE_ROOT,
                relative_path=query.validated_data["path"],
                recursive=query.validated_data["recursive"],
            )
        except WorkspacePathError as error:
            raise ValidationError({"path": "所选路径不存在，或不在工作区内。"}) from error

        return Response(WorkspaceEntrySerializer(entries, many=True).data)
