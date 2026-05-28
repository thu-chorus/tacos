from __future__ import annotations

from typing import Any

from django.contrib.auth.hashers import check_password, make_password

from rest_framework import serializers

from apps.personnel.models import Member, MemberStatus
from apps.personnel.sorting import sort_members
from apps.sheet_music.models import Sheet
from apps.sheet_music.sorting import sort_sheets

from .models import (
    Assignment,
    AssignmentAttachment,
    AssignmentExportTask,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    CheckinType,
    Event,
    EventAnnouncementImage,
    EventCheckinRecord,
    EventCheckinSession,
    EventVisibility,
)


class MemberBriefSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ("id", "name", "user_id", "voice_part", "tier", "status")

    def get_user_id(self, obj: Member) -> str:
        return getattr(getattr(obj, "user", None), "user_id", "")


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    admins = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Member.objects.all(), many=True
    )
    participants = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Member.objects.all(), many=True, required=False
    )
    sheet_ids = serializers.SlugRelatedField(
        source="sheets",
        slug_field="public_id",
        queryset=Sheet.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    admins_detail = serializers.SerializerMethodField(read_only=True)
    participants_detail = serializers.SerializerMethodField(read_only=True)
    announcement_images = serializers.SerializerMethodField(read_only=True)
    sheets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "introduction",
            "announcement",
            "start_date",
            "end_date",
            "visibility",
            "visible_to_alumni",
            "admins",
            "participants",
            "admins_detail",
            "participants_detail",
            "announcement",
            "sheet_ids",
            "sheets",
            "announcement_images",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "admins_detail",
            "participants_detail",
            "announcement_images",
            "sheets",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "结束日期不能早于开始日期"})
        admins = (
            attrs.get("admins")
            if "admins" in attrs
            else (self.instance.admins.all() if self.instance else [])
        )
        admins_list = list(admins)
        if not admins_list:
            raise serializers.ValidationError({"admins": "活动管理员不能为空"})
        visible_to_alumni = attrs.get(
            "visible_to_alumni",
            getattr(self.instance, "visible_to_alumni", False),
        )
        if not visible_to_alumni and any(
            getattr(admin, "status", MemberStatus.ACTIVE) == MemberStatus.ALUMNI
            for admin in admins_list
        ):
            raise serializers.ValidationError(
                {"admins": "校友不能担任校友不可见活动的管理员"}
            )
        return attrs

    def get_announcement_images(self, obj: Event) -> list[dict]:
        from urllib.parse import quote as urlquote

        from apps.common.utils import generate_signed_token

        request = self.context.get("request") if hasattr(self, "context") else None
        results: list[dict] = []
        for img in getattr(obj, "announcement_images", []).all():
            try:
                rel_path = img.image.name
                sub = ""
                try:
                    if (
                        request
                        and hasattr(request, "user")
                        and getattr(request.user, "is_authenticated", False)
                    ):
                        sub = str(
                            getattr(request.user, "user_id", "")
                            or getattr(request.user, "id", "")
                        )
                except Exception:
                    sub = ""
                token = generate_signed_token(
                    rel_path, expires_in_seconds=600, subject=sub
                )
                base = "/api/v1/common/media/"
                url = base + f"?path={urlquote(rel_path)}&token={urlquote(token)}"
                if request and hasattr(request, "build_absolute_uri"):
                    url = request.build_absolute_uri(url)
            except Exception:
                url = ""
            results.append({"id": img.id, "image": url, "created_at": img.created_at})
        return results

    def get_admins_detail(self, obj: Event) -> list[dict]:
        members = sort_members(obj.admins.select_related("user").all())
        return MemberBriefSerializer(members, many=True, context=self.context).data

    def get_participants_detail(self, obj: Event) -> list[dict]:
        members = sort_members(obj.participants.select_related("user").all())
        return MemberBriefSerializer(members, many=True, context=self.context).data

    def get_sheets(self, obj: Event) -> list[dict]:
        try:
            sheets_qs = getattr(obj, "sheets", None)
            if sheets_qs is None:
                return []
            return [
                {
                    "id": getattr(s, "public_id", ""),
                    "title": s.title,
                    "composer": s.composer,
                    "arranger": s.arranger,
                    "is_restricted": s.is_restricted,
                }
                for s in sort_sheets(sheets_qs.all())
            ]
        except Exception:
            return []


class EventBasicSerializer(serializers.ModelSerializer):
    """活动 GET 响应的基础信息，包含当前用户关系。"""

    id = serializers.CharField(source="public_id", read_only=True)
    relation = serializers.SerializerMethodField(read_only=True)
    is_participant = serializers.SerializerMethodField(read_only=True)
    announcement_images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "introduction",
            "announcement",
            "start_date",
            "end_date",
            "visibility",
            "visible_to_alumni",
            "relation",
            "is_participant",
            "announcement_images",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_relation(self, obj: Event) -> str:
        """返回 event_admin、member 或 not_member。"""
        request = (
            getattr(self, "context", {}).get("request")
            if hasattr(self, "context")
            else None
        )
        user = getattr(request, "user", None)
        member = (
            getattr(user, "member", None)
            if user and getattr(user, "is_authenticated", False)
            else None
        )
        if member:
            if obj.admins.filter(pk=getattr(member, "id", None)).exists():
                return "event_admin"
            if obj.participants.filter(pk=getattr(member, "id", None)).exists():
                return "member"
        return "not_member"

    def get_is_participant(self, obj: Event) -> bool:
        """当前用户在参与者列表中时返回 True。"""
        request = (
            getattr(self, "context", {}).get("request")
            if hasattr(self, "context")
            else None
        )
        user = getattr(request, "user", None)
        member = (
            getattr(user, "member", None)
            if user and getattr(user, "is_authenticated", False)
            else None
        )
        if member:
            return obj.participants.filter(pk=getattr(member, "id", None)).exists()
        return False

    def get_announcement_images(self, obj: Event) -> list[dict]:
        from urllib.parse import quote as urlquote

        from apps.common.utils import generate_signed_token

        request = self.context.get("request") if hasattr(self, "context") else None
        results: list[dict] = []
        for img in getattr(obj, "announcement_images", []).all():
            try:
                rel_path = img.image.name
                sub = ""
                try:
                    if (
                        request
                        and hasattr(request, "user")
                        and getattr(request.user, "is_authenticated", False)
                    ):
                        sub = str(
                            getattr(request.user, "user_id", "")
                            or getattr(request.user, "id", "")
                        )
                except Exception:
                    sub = ""
                token = generate_signed_token(
                    rel_path, expires_in_seconds=600, subject=sub
                )
                base = "/api/v1/common/media/"
                url = base + f"?path={urlquote(rel_path)}&token={urlquote(token)}"
                if request and hasattr(request, "build_absolute_uri"):
                    url = request.build_absolute_uri(url)
            except Exception:
                url = ""
            results.append({"id": img.id, "image": url, "created_at": img.created_at})
        return results


class EventCheckinSessionSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=CheckinType.choices)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=False
    )

    class Meta:
        model = EventCheckinSession
        fields = (
            "id",
            "event",
            "name",
            "type",
            "password",
            "location_lat",
            "location_lng",
            "radius_m",
            "is_active",
            "started_at",
            "ended_at",
        )
        read_only_fields = ("id", "is_active", "started_at", "ended_at")

    def create(self, validated_data):  # type: ignore[override]
        raw_password = (self.initial_data or {}).get("password") or ""
        if validated_data.get("type") == CheckinType.PASSWORD:
            if not raw_password:
                raise serializers.ValidationError({"password": "密码签到需要设置密码"})
            validated_data["password_hash"] = make_password(raw_password)
        validated_data.pop("password", None)
        return super().create(validated_data)

    def validate_name(self, value: str) -> str:  # type: ignore[override]
        if not value or not str(value).strip():
            raise serializers.ValidationError("签到名称不能为空")
        return str(value).strip()


class EventCheckinRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField(read_only=True)
    member_user_id = serializers.SerializerMethodField(read_only=True)
    member_public_id = serializers.SerializerMethodField(read_only=True)
    voice_part = serializers.SerializerMethodField(read_only=True)
    tier = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EventCheckinRecord
        fields = (
            "id",
            "session",
            "member",
            "member_public_id",
            "member_name",
            "member_user_id",
            "voice_part",
            "tier",
            "checked_at",
            "lat",
            "lng",
        )
        read_only_fields = (
            "id",
            "checked_at",
            "member_public_id",
            "member_name",
            "member_user_id",
            "voice_part",
            "tier",
        )

    def get_member_name(self, obj):
        return getattr(obj.member, "name", "")

    def get_member_user_id(self, obj):
        return getattr(getattr(obj.member, "user", None), "user_id", "")

    def get_member_public_id(self, obj):
        """返回成员 public_id，用于和活动成员列表匹配。"""
        return getattr(obj.member, "public_id", "")

    def get_voice_part(self, obj):
        return getattr(obj.member, "voice_part", "")

    def get_tier(self, obj):
        return getattr(obj.member, "tier", "")


class AssignmentAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentAttachment
        fields = ("id", "file", "created_at")
        read_only_fields = ("id", "created_at")

    def get_file(self, obj: AssignmentAttachment) -> str:
        from urllib.parse import quote as urlquote

        from django.conf import settings

        from apps.common.utils import generate_signed_token

        try:
            rel_path = obj.file.name  # 相对于 MEDIA_ROOT
        except Exception:
            return ""
        request = (
            getattr(self, "context", {}).get("request")
            if hasattr(self, "context")
            else None
        )
        sub = ""
        try:
            if (
                request
                and hasattr(request, "user")
                and getattr(request.user, "is_authenticated", False)
            ):
                sub = str(
                    getattr(request.user, "user_id", "")
                    or getattr(request.user, "id", "")
                )
        except Exception:
            sub = ""
        token = generate_signed_token(rel_path, expires_in_seconds=600, subject=sub)
        base = "/api/v1/common/media/"
        query = f"?path={urlquote(rel_path)}&token={urlquote(token)}"
        if request and hasattr(request, "build_absolute_uri"):
            return request.build_absolute_uri(base + query)
        return base + query


class AssignmentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    attachments = AssignmentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = (
            "id",
            "event",
            "title",
            "description",
            "deadline",
            "is_closed",
            "created_at",
            "updated_at",
            "attachments",
        )
        read_only_fields = (
            "id",
            "is_closed",
            "created_at",
            "updated_at",
            "attachments",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        deadline = attrs.get("deadline") or getattr(self.instance, "deadline", None)
        if not deadline:
            raise serializers.ValidationError({"deadline": "必须设置作业截止时间"})
        return attrs


class AssignmentSubmissionAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmissionAttachment
        fields = ("id", "file", "created_at")
        read_only_fields = ("id", "created_at")

    def get_file(self, obj: AssignmentSubmissionAttachment) -> str:
        from urllib.parse import quote as urlquote

        from apps.common.utils import generate_signed_token

        try:
            rel_path = obj.file.name
        except Exception:
            return ""
        request = (
            getattr(self, "context", {}).get("request")
            if hasattr(self, "context")
            else None
        )
        sub = ""
        try:
            if (
                request
                and hasattr(request, "user")
                and getattr(request.user, "is_authenticated", False)
            ):
                sub = str(
                    getattr(request.user, "user_id", "")
                    or getattr(request.user, "id", "")
                )
        except Exception:
            sub = ""
        token = generate_signed_token(rel_path, expires_in_seconds=600, subject=sub)
        base = "/api/v1/common/media/"
        query = f"?path={urlquote(rel_path)}&token={urlquote(token)}"
        request = (
            getattr(self, "context", {}).get("request")
            if hasattr(self, "context")
            else None
        )
        if request and hasattr(request, "build_absolute_uri"):
            return request.build_absolute_uri(base + query)
        return base + query


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField(read_only=True)
    member_user_id = serializers.SerializerMethodField(read_only=True)
    voice_part = serializers.SerializerMethodField(read_only=True)
    tier = serializers.SerializerMethodField(read_only=True)
    attachments = AssignmentSubmissionAttachmentSerializer(many=True, read_only=True)
    graded_by_name = serializers.SerializerMethodField(read_only=True)
    graded_by_user_id = serializers.SerializerMethodField(read_only=True)
    graded_by_member_public_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = (
            "id",
            "assignment",
            "member",
            "member_name",
            "member_user_id",
            "voice_part",
            "tier",
            "text",
            "submitted_at",
            "graded_score",
            "graded_comment",
            "graded_by",
            "graded_by_name",
            "graded_by_user_id",
            "graded_by_member_public_id",
            "graded_at",
            "attachments",
        )
        read_only_fields = (
            "id",
            "submitted_at",
            "member_name",
            "member_user_id",
            "voice_part",
            "tier",
            "graded_by",
            "graded_by_name",
            "graded_by_user_id",
            "graded_by_member_public_id",
            "graded_at",
            "attachments",
        )

    def get_member_name(self, obj: AssignmentSubmission) -> str:
        return getattr(obj.member, "name", "")

    def get_member_user_id(self, obj: AssignmentSubmission) -> str:
        return getattr(getattr(obj.member, "user", None), "user_id", "")

    def get_voice_part(self, obj: AssignmentSubmission) -> str:
        return getattr(obj.member, "voice_part", "")

    def get_tier(self, obj: AssignmentSubmission) -> str:
        return getattr(obj.member, "tier", "")

    def get_graded_by_name(self, obj: AssignmentSubmission) -> str:
        user = getattr(obj, "graded_by", None)
        return getattr(user, "name", "") if user else ""

    def get_graded_by_user_id(self, obj: AssignmentSubmission) -> str:
        user = getattr(obj, "graded_by", None)
        return getattr(user, "user_id", "") if user else ""

    def get_graded_by_member_public_id(self, obj: AssignmentSubmission) -> str:
        user = getattr(obj, "graded_by", None)
        if not user:
            return ""
        member = getattr(user, "member", None)
        return getattr(member, "public_id", "") if member else ""


class AssignmentExportTaskSerializer(serializers.ModelSerializer):
    """作业导出任务状态序列化器。"""

    class Meta:
        model = AssignmentExportTask
        fields = (
            "task_id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "expires_at",
        )
        read_only_fields = fields
