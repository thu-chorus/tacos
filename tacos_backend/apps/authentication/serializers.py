from django.contrib.auth import authenticate

from rest_framework import serializers

from .models import User
from .policies import (
    get_login_block_reason,
    user_is_first_login,
    user_needs_profile_setup,
)


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):  # type: ignore[override]
        user_id = attrs.get("user_id")
        password = attrs.get("password")
        if user_id and password:
            # 首先检查用户是否存在
            try:
                user_obj = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"user_id": "学号/工号或密码错误，请重新输入"},
                    code="user_not_found",
                )

            block_reason = get_login_block_reason(user_obj)
            if block_reason is not None:
                raise serializers.ValidationError(
                    {"user_id": block_reason.message},
                    code=block_reason.code,
                )

            # 验证密码
            user = authenticate(
                request=self.context.get("request"), user_id=user_id, password=password
            )
            if not user:
                raise serializers.ValidationError(
                    {"password": "学号/工号或密码错误，请重新输入"},
                    code="invalid_password",
                )
        else:
            raise serializers.ValidationError("学号/工号和密码都是必填项")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    is_first_login = serializers.SerializerMethodField(read_only=True)
    needs_profile_setup = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "role",
            "name",
            "is_first_login",
            "needs_profile_setup",
        )

    def get_is_first_login(self, obj: User) -> bool:
        return user_is_first_login(obj)

    def get_needs_profile_setup(self, obj: User) -> bool:
        return user_needs_profile_setup(obj)


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)
        extra_kwargs = {"name": {"required": True, "allow_blank": False}}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):  # type: ignore[override]
        request = self.context.get("request")
        user = getattr(request, "user", None)
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "原密码不正确"})
        if len(new_password or "") < 8:
            raise serializers.ValidationError({"new_password": "密码长度不能少于8位"})
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "两次输入的密码不一致"}
            )

        return attrs


class FirstLoginSerializer(serializers.Serializer):
    # 用户基本信息
    name = serializers.CharField(required=True, allow_blank=False)

    # 成员信息
    gender = serializers.CharField(required=True, allow_blank=False)
    wechat_id = serializers.CharField(required=True, allow_blank=False)
    voice_part = serializers.CharField(required=True, allow_blank=False)
    tier = serializers.CharField(required=True, allow_blank=False)
    department = serializers.CharField(required=True, allow_blank=False)
    department_other = serializers.CharField(required=False, allow_blank=True)
    class_name = serializers.CharField(required=True, allow_blank=False)
    phone_number = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False)
    dorm = serializers.CharField(required=True, allow_blank=False)
    birthday = serializers.DateField(required=True)
    hometown = serializers.CharField(required=True, allow_blank=False)
    ethnicity = serializers.CharField(required=True, allow_blank=False)
    political_status = serializers.CharField(required=True, allow_blank=False)
    political_affiliation = serializers.CharField(required=True, allow_blank=False)
    is_specialty = serializers.BooleanField(required=False, default=False)
    is_centralized = serializers.BooleanField(required=False, default=False)
    position = serializers.CharField(required=False, allow_blank=True)
    join_month = serializers.CharField(required=True, allow_blank=False)
    graduate_month = serializers.CharField(required=True, allow_blank=False)
    portfolio = serializers.CharField(required=False, allow_blank=True)

    # 密码修改 - 移除旧密码验证
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_gender(self, value):
        if value not in ("男", "女"):
            raise serializers.ValidationError("性别必须是男或女")
        return value

    def validate_voice_part(self, value):
        valid_parts = ["S1", "S2", "A1", "A2", "T1", "T2", "B1", "B2", "Other"]
        if value not in valid_parts:
            raise serializers.ValidationError("声部选择无效")
        return value

    def validate_tier(self, value):
        if value not in ("一队", "二队"):
            raise serializers.ValidationError("梯队必须是一队或二队")
        return value

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("手机号必须是11位数字")
        return value

    def validate_join_month(self, value):
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", value):
            raise serializers.ValidationError("入队年月格式必须为YYYY-MM")
        return value

    def validate_graduate_month(self, value):
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", value):
            raise serializers.ValidationError("预计毕业时间格式必须为YYYY-MM")
        return value

    def validate(self, attrs):  # type: ignore[override]
        request = self.context.get("request")
        user = getattr(request, "user", None)
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")
        department = attrs.get("department")
        department_other = attrs.get("department_other")

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        if len(new_password or "") < 8:
            raise serializers.ValidationError({"new_password": "密码长度不能少于8位"})
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "两次输入的密码不一致"}
            )

        # 验证院系和院系其他的关系
        if department == "其他" and not department_other:
            raise serializers.ValidationError(
                {"department_other": '当选择"其他"时，必须填写具体院系'}
            )

        return attrs
