from typing import Any, Optional
from urllib.parse import quote as urlquote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import serializers

from apps.authentication.models import UserRole
from apps.common.utils import generate_signed_token
from apps.common.validators import YEAR_MONTH_REGEX

from .models import (
    AlumniProfile,
    Instructor,
    Member,
    MemberExportTask,
    MemberStatus,
    MemberTitle,
    Tier,
    Title,
    VoicePart,
)


class AlumniProfileSerializer(serializers.ModelSerializer):
    graduation_month = serializers.CharField(required=True, allow_blank=False)

    member_id = serializers.SlugRelatedField(
        source="member",
        slug_field="public_id",
        queryset=Member.objects.all(),
        write_only=True,
        required=False,
    )
    member_public_id = serializers.SerializerMethodField(read_only=True)
    member_user_id = serializers.SerializerMethodField(read_only=True)
    member_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AlumniProfile
        fields = (
            "id",
            "member_id",
            "member_public_id",
            "member_user_id",
            "member_name",
            "current_city",
            "industry",
            "company",
            "job_title",
            "graduation_month",
            "bio",
            "contact_note",
            "allow_contact",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "member_public_id",
            "member_user_id",
            "member_name",
            "created_at",
            "updated_at",
        )

    def get_member_public_id(self, obj: AlumniProfile) -> str:
        return getattr(obj.member, "public_id", "")

    def get_member_user_id(self, obj: AlumniProfile) -> str:
        return getattr(getattr(obj.member, "user", None), "user_id", "")

    def get_member_name(self, obj: AlumniProfile) -> str:
        return getattr(obj.member, "name", "")

    def validate_graduation_month(self, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("毕业时间为必填项")
        if not YEAR_MONTH_REGEX.match(value):
            raise serializers.ValidationError("毕业时间格式必须为YYYY-MM")
        return value

    def to_internal_value(self, data: Any) -> Any:  # type: ignore[override]
        if hasattr(data, "keys"):
            unknown_fields = sorted(set(data.keys()) - set(self.fields.keys()))
            if unknown_fields:
                raise serializers.ValidationError(
                    {field: "Unknown field." for field in unknown_fields}
                )
        return super().to_internal_value(data)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        member = attrs.get("member", getattr(self.instance, "member", None))
        if self.instance is None and member is None:
            raise serializers.ValidationError({"member_id": "member_id is required"})
        if member and getattr(member, "status", "") != MemberStatus.ALUMNI:
            raise serializers.ValidationError(
                {"member_id": "仅校友成员可以维护校友信息"}
            )

        graduation_month = attrs.get(
            "graduation_month", getattr(self.instance, "graduation_month", "")
        )
        if not str(graduation_month or "").strip():
            raise serializers.ValidationError({"graduation_month": "毕业时间为必填项"})
        return super().validate(attrs)


class MemberSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)
    titles = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.SerializerMethodField(read_only=True)
    password_hash = serializers.SerializerMethodField(read_only=True)
    alumni_profile = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.BooleanField(write_only=True, required=False, default=False)
    role = serializers.ChoiceField(
        write_only=True, required=False, choices=UserRole.choices
    )
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=False
    )
    class_name = serializers.CharField(required=False, allow_blank=True)
    birthday = serializers.DateField(required=False, allow_null=True)
    join_month = serializers.CharField(required=False, allow_blank=True)
    graduate_month = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    voice_part = serializers.CharField(required=False, allow_blank=True)
    wechat_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=MemberStatus.choices, required=False)

    department = serializers.CharField(required=False, allow_blank=True)
    department_other = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Member
        fields = (
            "id",
            "user_id",
            "avatar",
            "name",
            "gender",
            "voice_part",
            "department",
            "department_other",
            "class_name",
            "wechat_id",
            "phone_number",
            "email",
            "dorm",
            "birthday",
            "hometown",
            "ethnicity",
            "political_status",
            "political_affiliation",
            "is_specialty",
            "is_centralized",
            "position",
            "join_month",
            "graduate_month",
            "status",
            "tier",
            "portfolio",
            "titles",
            "alumni_profile",
            "hidden_fields",
            "password_hash",
            "created_at",
            "updated_at",
            "is_admin",
            "role",
            "password",
        )
        read_only_fields = ("id", "avatar", "created_at", "updated_at", "user_id")

    def get_user_id(self, obj: Member) -> str:
        return getattr(obj.user, "user_id", "")

    def get_avatar(self, obj: Member) -> str:
        avatar = getattr(obj, "avatar", None)
        if not avatar or not getattr(avatar, "name", ""):
            return ""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        subject = ""
        if user and getattr(user, "is_authenticated", False):
            subject = str(getattr(user, "user_id", "") or getattr(user, "id", ""))
        rel_path = avatar.name
        token = generate_signed_token(
            rel_path, expires_in_seconds=3600, subject=subject
        )
        url = f"/api/v1/common/media/?path={urlquote(rel_path)}&token={urlquote(token)}"
        if request and hasattr(request, "build_absolute_uri"):
            return request.build_absolute_uri(url)
        return url

    def validate_voice_part(self, value: str) -> str:
        if not value:
            return "Other"
        if value not in VoicePart.values:
            raise serializers.ValidationError("Invalid voice_part")
        return value

    def validate_gender(self, value: str) -> str:
        if not value:
            return ""
        if value not in ("男", "女"):
            raise serializers.ValidationError("Invalid gender")
        return value

    def validate_tier(self, value: str) -> str:
        # 导入器负责默认值；此处也接受空值并兜底为二队
        if not value:
            return "二队"
        if value not in Tier.values:
            raise serializers.ValidationError("Invalid tier")
        return value

    def validate_graduate_month(self, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            return ""
        if not YEAR_MONTH_REGEX.match(value):
            raise serializers.ValidationError("预计毕业时间格式必须为YYYY-MM")
        return value

    def to_internal_value(self, data: Any) -> Any:  # type: ignore[override]
        mutable = dict(data)
        for key in ("birthday",):
            if mutable.get(key) == "":
                mutable[key] = None
        if "class" in mutable and not mutable.get("class_name"):
            mutable["class_name"] = mutable["class"]
        if "hidden_fields" in mutable and mutable["hidden_fields"] is None:
            mutable["hidden_fields"] = []
        dept = mutable.get("department", "")
        if dept is None:
            mutable["department"] = ""
        dept_other = mutable.get("department_other", "")
        if dept_other is None:
            mutable["department_other"] = ""
        return super().to_internal_value(mutable)

    def create(self, validated_data: dict[str, Any]) -> Member:
        user_id = (self.initial_data or {}).get("user_id")
        if not user_id:
            raise serializers.ValidationError({"user_id": "user_id is required"})

        initial_role = (self.initial_data or {}).get("role")
        is_admin_flag = (self.initial_data or {}).get("is_admin")
        is_admin = False
        if isinstance(is_admin_flag, bool):
            is_admin = is_admin_flag
        elif isinstance(is_admin_flag, str):
            is_admin = is_admin_flag.lower() in {"1", "true", "yes", "on", "是"}
        if isinstance(initial_role, str):
            is_admin = is_admin or (initial_role in ("Admin", "SuperAdmin"))

        raw_password = (self.initial_data or {}).get("password")
        if not raw_password:
            raw_password = getattr(settings, "DEFAULT_INITIAL_PASSWORD", "ChangeMe123!")

        validated_data.pop("is_admin", None)
        validated_data.pop("role", None)
        validated_data.pop("password", None)

        dept = validated_data.get("department", "") or ""
        dept_other = validated_data.get("department_other", "") or ""
        if dept == "其他":
            if not dept_other.strip():
                raise serializers.ValidationError(
                    {"department_other": "当选择“其他”时，必须填写具体院系"}
                )
        else:
            # 院系不是“其他”或为空时清空补充院系
            validated_data["department_other"] = ""

        User = get_user_model()
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            extra_fields: dict[str, Any] = {
                "name": validated_data.get("name", ""),
                "role": "Admin" if is_admin else "Member",
                "is_staff": bool(is_admin),
            }
            user = User.objects.create_user(
                user_id=user_id, password=raw_password, **extra_fields
            )
        else:
            if hasattr(user, "member"):
                raise serializers.ValidationError({"user_id": "该用户的队员档案已存在"})

        join_month_value = validated_data.get("join_month", "")
        if not join_month_value:
            validated_data["join_month"] = timezone.localdate().strftime("%Y-%m")

        validated_data["user"] = user
        member = super().create(validated_data)
        if member.status == MemberStatus.ALUMNI:
            AlumniProfile.objects.get_or_create(member=member)
        return member

    def validate_wechat_id(self, value: str) -> str:
        if not value or not value.strip():
            return "请及时填写正确微信号"
        if len(value) > 64:
            raise serializers.ValidationError("wechat_id too long")
        return value.strip()

    def validate_hidden_fields(self, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "hidden_fields must be a list of field names"
            )
        allowed_sensitive = {
            "gender",
            "phone_number",
            "email",
            "dorm",
            "birthday",
            "hometown",
            "ethnicity",
            "political_status",
            "political_affiliation",
            "is_specialty",
            "is_centralized",
            "graduate_month",
        }
        mandatory_visible = {
            "name",
            "user_id",
            "class_name",
            "wechat_id",
            "join_month",
            "position",
            "voice_part",
            "department",
            "department_other",
            "tier",
            "portfolio",
            "class_name",
            "titles",
        }
        for field in value:
            if not isinstance(field, str):
                raise serializers.ValidationError("hidden_fields must contain strings")
            if field in mandatory_visible:
                raise serializers.ValidationError(f"field {field} cannot be hidden")
            if field not in allowed_sensitive:
                raise serializers.ValidationError(f"field {field} is not hideable")
        return value

    def to_representation(self, instance: Member) -> dict[str, Any]:  # type: ignore[override]
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
        ):
            return data

        if user and getattr(getattr(instance, "user", None), "id", None) == getattr(
            user, "id", None
        ):
            return data

        hidden = set(getattr(instance, "hidden_fields", []) or [])
        for key in list(data.keys()):
            if key in {
                "id",
                "user_id",
                "name",
                "class_name",
                "wechat_id",
                "join_month",
                "position",
                "created_at",
                "updated_at",
            }:
                continue
            if key in hidden:
                data[key] = None
        data.pop("hidden_fields", None)
        return data

    def get_password_hash(self, obj: Member) -> Optional[str]:  # type: ignore[override]
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "role", "") == "SuperAdmin":
            related_user = getattr(obj, "user", None)
            return getattr(related_user, "password", None)
        return None

    def update(self, instance: Member, validated_data: dict[str, Any]) -> Member:  # type: ignore[override]
        raw_password = (self.initial_data or {}).get("password")
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        actor_role = getattr(actor, "role", "")
        actor_is_admin = bool(
            getattr(actor, "is_staff", False) or actor_role in ("Admin", "SuperAdmin")
        )
        if not actor_is_admin:
            admin_only_fields = {
                "status": "仅管理员可修改成员状态",
                "tier": "仅管理员可修改成员梯队",
            }
            for field, message in admin_only_fields.items():
                new_value = validated_data.get(field)
                if field in validated_data and new_value != getattr(instance, field):
                    raise serializers.ValidationError({field: message})
        if (
            not actor_is_admin
            and "graduate_month" in (self.initial_data or {})
            and not str((self.initial_data or {}).get("graduate_month") or "").strip()
        ):
            raise serializers.ValidationError(
                {"graduate_month": "预计毕业时间为必填项"}
            )
        if raw_password and actor_role == "SuperAdmin":
            related_user = getattr(instance, "user", None)
            if related_user:
                related_user.set_password(raw_password)
                related_user.save(update_fields=["password"])
        validated_data.pop("is_admin", None)
        validated_data.pop("role", None)
        validated_data.pop("password", None)
        dept = (
            validated_data.get("department", getattr(instance, "department", "")) or ""
        )
        dept_other = validated_data.get("department_other", "") or ""
        if dept == "其他":
            if not dept_other.strip():
                raise serializers.ValidationError(
                    {"department_other": "当选择“其他”时，必须填写具体院系"}
                )
        else:
            validated_data["department_other"] = ""

        member = super().update(instance, validated_data)
        if member.status == MemberStatus.ALUMNI:
            AlumniProfile.objects.get_or_create(member=member)
        return member

    def get_alumni_profile(self, obj: Member) -> Optional[dict[str, Any]]:
        try:
            profile = obj.alumni_profile
        except AlumniProfile.DoesNotExist:
            return None

        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_admin = user and (
            getattr(user, "is_staff", False)
            or getattr(user, "role", "") in ("Admin", "SuperAdmin")
        )
        is_self = user and getattr(getattr(obj, "user", None), "id", None) == getattr(
            user, "id", None
        )
        if not (is_admin or is_self or profile.allow_contact):
            return None
        data = AlumniProfileSerializer(profile, context=self.context).data
        if not (is_admin or is_self):
            data.pop("allow_contact", None)
        return data

    def get_titles(self, obj: Member) -> list[dict[str, Any]]:
        # 称号始终可见，不受 hidden_fields 影响，因此单独组装
        items = []
        member_titles = getattr(obj, "prefetched_member_titles", None)
        if member_titles is None:
            member_titles = obj.member_titles.select_related("title").order_by(
                "-awarded_at"
            )
        for mt in member_titles:
            t = mt.title
            items.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "appearance": t.appearance,
                    "awarded_at": str(mt.awarded_at),
                }
            )
        return items


class TitleSerializer(serializers.ModelSerializer):
    owners_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Title
        fields = (
            "id",
            "name",
            "description",
            "appearance",
            "created_date",
            "owners_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owners_count", "created_at", "updated_at")

    def get_owners_count(self, obj: Title) -> int:
        return obj.members.count()


class MemberTitleSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    title_id = serializers.PrimaryKeyRelatedField(
        queryset=Title.objects.all(), write_only=True, source="title"
    )
    # 接受学号(user_id)、成员主键ID(pk) 或 public_id
    member_id = serializers.CharField(write_only=True)
    member_user_id = serializers.SerializerMethodField(read_only=True)
    member_name = serializers.SerializerMethodField(read_only=True)
    member_public_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MemberTitle
        fields = (
            "id",
            "title",
            "title_id",
            "member_id",
            "member_user_id",
            "member_name",
            "member_public_id",
            "awarded_at",
        )
        read_only_fields = ("id", "member_user_id", "member_name", "member_public_id")

    def get_member_user_id(self, obj: MemberTitle) -> str:
        return getattr(getattr(obj.member, "user", None), "user_id", "")

    def get_member_name(self, obj: MemberTitle) -> str:
        return getattr(obj.member, "name", "")

    def get_member_public_id(self, obj: MemberTitle) -> str:
        return getattr(obj.member, "public_id", "")

    def create(self, validated_data: dict[str, Any]) -> MemberTitle:  # type: ignore[override]
        # 将传入的 member_id（学号 user_id / 成员PK / public_id）解析为 Member 实例
        raw_member_id = (self.initial_data or {}).get("member_id")
        member = None
        if raw_member_id:
            # 1) public_id 精确匹配
            try:
                member = Member.objects.get(public_id=str(raw_member_id))
            except Member.DoesNotExist:
                member = None

            # 2) 学号(user_id) 匹配
            if member is None:
                try:
                    member = Member.objects.get(user__user_id=str(raw_member_id))
                except Member.DoesNotExist:
                    member = None

            # 3) 数字则按主键ID匹配
            if member is None and str(raw_member_id).isdigit():
                try:
                    member = Member.objects.get(pk=int(raw_member_id))
                except Member.DoesNotExist:
                    member = None
        if member is None:
            raise serializers.ValidationError(
                {"member_id": "成员不存在（请使用 public_id、学号或成员ID）"}
            )

        # 检查是否已存在该称号
        title = validated_data.get("title")
        if title and MemberTitle.objects.filter(member=member, title=title).exists():
            member_name = getattr(member, "name", "")
            member_user_id = getattr(getattr(member, "user", None), "user_id", "")
            title_name = getattr(title, "name", "")
            raise serializers.ValidationError(
                {
                    "member_id": f"队员 {member_name}（{member_user_id}）已拥有称号「{title_name}」"
                }
            )

        # 清理掉 write-only 的 member_id，写入真正的 member 外键
        validated_data.pop("member_id", None)
        validated_data["member"] = member
        return super().create(validated_data)


class InstructorSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)

    class Meta:
        model = Instructor
        fields = (
            "id",
            "instructor_id",
            "name",
            "phone_number",
            "vehicle_number",
            "title",
            "affiliation",
            "address",
            "fee",
            "is_external",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_instructor_id(self, value: str) -> str:
        # 允许 10 位工号或 18 位身份证（末位允许 X/x）
        is_ten_digit_emp_id = len(value) == 10 and value.isdigit()
        is_eighteen_id_card = (
            len(value) == 18
            and value[:17].isdigit()
            and (value[17].isdigit() or value[17] in "Xx")
        )
        if not (is_ten_digit_emp_id or is_eighteen_id_card):
            raise serializers.ValidationError(
                "instructor_id must be 10 digits or 18 digits ending with 0-9/X"
            )
        return value


class MemberExportTaskSerializer(serializers.ModelSerializer):
    """成员导出任务状态序列化器。"""

    class Meta:
        model = MemberExportTask
        fields = (
            "task_id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "expires_at",
        )
        read_only_fields = fields
