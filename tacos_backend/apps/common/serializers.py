from rest_framework import serializers

from .models import SystemAnnouncement


class SystemAnnouncementSerializer(serializers.ModelSerializer):
    """带基础校验的系统公告序列化器。"""

    class Meta:
        model = SystemAnnouncement
        fields = ["id", "title", "publish_time", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_content(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("公告文字不能为空")
        if len(value) > 5000:
            raise serializers.ValidationError("公告文字过长（最多5000字符）")
        return value.strip()

    def validate_title(self, value: str) -> str:
        if value is None:
            return ""
        v = str(value).strip()
        if len(v) > 200:
            raise serializers.ValidationError("公告标题过长（最多200字符）")
        return v
