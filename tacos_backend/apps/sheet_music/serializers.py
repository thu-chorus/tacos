from typing import Any

from rest_framework import serializers

from apps.events.models import Event
from apps.personnel.models import Member
from apps.personnel.sorting import sort_members

from .models import Sheet, SheetDownloadLog, SheetDownloadTask

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class SheetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    original_file_path = serializers.SerializerMethodField(read_only=True)
    visible_event_ids = serializers.SlugRelatedField(
        source="visible_events",
        slug_field="public_id",
        many=True,
        queryset=Event.objects.all(),
        required=False,
        write_only=True,
    )
    visible_member_ids = serializers.SlugRelatedField(
        source="visible_members",
        slug_field="public_id",
        many=True,
        queryset=Member.objects.all(),
        required=False,
        write_only=True,
    )
    visible_events = serializers.SerializerMethodField(read_only=True)
    visible_members = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sheet
        fields = (
            "id",
            "title",
            "lyricist",
            "composer",
            "arranger",
            "introduction",
            "copyright_notice",
            "is_restricted",
            "visible_to_all",
            "visible_to_alumni",
            "visible_event_ids",
            "visible_member_ids",
            "visible_events",
            "visible_members",
            "original_file",
            "original_file_path",
            "upload_time",
            "updated_at",
        )
        read_only_fields = ("upload_time", "updated_at", "original_file_path")
        extra_kwargs = {"original_file": {"required": False}}

    def get_original_file_path(self, obj: Sheet) -> str:
        try:
            return obj.original_file.url  # type: ignore[attr-defined]
        except Exception:
            return ""

    def validate(self, attrs):  # type: ignore[override]
        if self.instance is None and not attrs.get("original_file"):
            raise serializers.ValidationError({"original_file": "文件必填"})
        visible_to_all = attrs.get(
            "visible_to_all", getattr(self.instance, "visible_to_all", True)
        )
        if self.instance is None and "visible_to_all" not in self.initial_data:
            visible_to_all = True
            attrs["visible_to_all"] = True
        visible_to_alumni = attrs.get(
            "visible_to_alumni", getattr(self.instance, "visible_to_alumni", False)
        )
        evs = attrs.get("visible_events", None)
        mbs = attrs.get("visible_members", None)
        if not visible_to_all and not visible_to_alumni:
            has_events = bool(evs) if evs is not None else False
            has_members = bool(mbs) if mbs is not None else False
            if self.instance is not None:
                if evs is None:
                    has_events = self.instance.visible_events.exists()
                if mbs is None:
                    has_members = self.instance.visible_members.exists()
            if not has_events and not has_members:
                raise serializers.ValidationError(
                    "当未选择全员可见时，需指定活动、成员或校友可见"
                )
        return super().validate(attrs)

    def validate_original_file(self, file):  # type: ignore[override]
        if not file:
            return file
        if not str(file.name).lower().endswith(".pdf"):
            raise serializers.ValidationError("仅支持 PDF 文件")
        if hasattr(file, "size") and file.size and file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("文件大小不能超过 20MB")
        return file

    def get_visible_events(self, obj: Sheet):
        try:
            events = getattr(obj, "prefetched_visible_events", None)
            if events is None:
                events = obj.visible_events.order_by(
                    "-start_date", "-created_at", "public_id"
                )
            return [{"id": getattr(e, "public_id", ""), "name": e.name} for e in events]
        except Exception:
            return []

    def get_visible_members(self, obj: Sheet):
        try:
            members = getattr(obj, "prefetched_visible_members", None)
            if members is None:
                members = obj.visible_members.select_related("user").all()
            return [
                {
                    "id": getattr(m, "public_id", ""),
                    "user_id": getattr(m.user, "user_id", ""),
                    "name": m.name,
                }
                for m in sort_members(members)
            ]
        except Exception:
            return []


class SheetDownloadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SheetDownloadLog
        fields = ("id", "sheet", "user", "downloaded_at", "ip_address")
        read_only_fields = ("id", "downloaded_at")


class SheetDownloadTaskSerializer(serializers.ModelSerializer):
    """异步下载任务状态序列化器。"""

    class Meta:
        model = SheetDownloadTask
        fields = (
            "task_id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "expires_at",
        )
        read_only_fields = fields
