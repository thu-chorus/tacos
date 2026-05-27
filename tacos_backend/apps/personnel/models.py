from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.validators import validate_china_mainland_phone, validate_year_month


def default_member_hidden_fields() -> list[str]:
    """新成员默认隐藏字段。

    新成员的敏感个人信息默认不公开。
    """
    return [
        "birthday",
        "dorm",
        "hometown",
        "ethnicity",
        "political_status",
        "political_affiliation",
        "graduate_month",
    ]


class VoicePart(models.TextChoices):
    S1 = "S1", "S1"
    S2 = "S2", "S2"
    A1 = "A1", "A1"
    A2 = "A2", "A2"
    T1 = "T1", "T1"
    T2 = "T2", "T2"
    B1 = "B1", "B1"
    B2 = "B2", "B2"
    OTHER = "Other", "Other"


class Tier(models.TextChoices):
    FIRST = "一队", "一队"
    SECOND = "二队", "二队"


class MemberStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "在队"
    ALUMNI = "ALUMNI", "校友"
    INACTIVE = "INACTIVE", "停用"


class Member(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, db_index=True, blank=True, default=""
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member"
    )

    name = models.CharField(max_length=64)
    gender = models.CharField(
        max_length=2, choices=(("男", "男"), ("女", "女")), blank=True, default=""
    )
    voice_part = models.CharField(
        max_length=8, choices=VoicePart.choices, blank=True, default=""
    )
    # 微信号（允许空白，序列化层设置默认值）
    wechat_id = models.CharField(max_length=64, blank=True, default="")
    # 院系：自由文本，前端控制选项
    department = models.CharField(max_length=128, blank=True, default="")
    # 当 department 选择“其他”时，填写具体院系名称
    department_other = models.CharField(max_length=128, blank=True, default="")
    class_name = models.CharField(
        max_length=64, db_column="class", blank=True, default=""
    )
    phone_number = models.CharField(
        max_length=11,
        validators=[validate_china_mainland_phone],
        blank=True,
        default="",
    )
    email = models.EmailField(blank=True, default="")
    dorm = models.CharField(max_length=64, blank=True, default="")
    birthday = models.DateField(null=True, blank=True)
    hometown = models.CharField(max_length=128, blank=True, default="")
    ethnicity = models.CharField(max_length=32, blank=True, default="")
    political_status = models.CharField(max_length=32, blank=True, default="")
    political_affiliation = models.CharField(max_length=64, blank=True, default="")
    is_specialty = models.BooleanField(default=False)
    is_centralized = models.BooleanField(default=False)
    position = models.CharField(max_length=64, blank=True, default="")
    # 入队年月（YYYY-MM），为空表示未知
    join_month = models.CharField(
        max_length=7, blank=True, default="", validators=[validate_year_month]
    )
    # 预计毕业时间（YYYY-MM），管理员创建时可暂空，用户首次登录时需补全
    graduate_month = models.CharField(
        max_length=7, blank=True, default="", validators=[validate_year_month]
    )
    status = models.CharField(
        max_length=16,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE,
    )
    tier = models.CharField(max_length=4, choices=Tier.choices, default=Tier.SECOND)
    portfolio = models.TextField(blank=True, default="")
    # 称号：多对多，记录授予时间
    # 通过中间表以便扩展 awarded_at 等信息

    # 用户自定义的隐私字段列表（字段名数组），仅对普通用户生效
    hidden_fields = models.JSONField(default=default_member_hidden_fields, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "members"
        indexes = [
            models.Index(fields=["voice_part"], name="idx_members_voice_part"),
            models.Index(fields=["tier"], name="idx_members_tier"),
            models.Index(fields=["join_month"], name="idx_members_join_month"),
            models.Index(fields=["graduate_month"], name="idx_members_graduate_month"),
            models.Index(fields=["status"], name="idx_members_status"),
            models.Index(fields=["name"], name="idx_members_name"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{getattr(self.user, 'user_id', '')} - {self.name}"

    def save(self, *args, **kwargs):
        if not getattr(self, "public_id", ""):
            from apps.common.utils import ensure_unique_public_id

            self.public_id = ensure_unique_public_id(type(self), prefix="m", length=12)
        return super().save(*args, **kwargs)


class AlumniProfile(models.Model):
    """成员离队后维护的校友专属资料。"""

    member = models.OneToOneField(
        Member, on_delete=models.CASCADE, related_name="alumni_profile"
    )
    current_city = models.CharField(max_length=64, blank=True, default="")
    industry = models.CharField(max_length=64, blank=True, default="")
    company = models.CharField(max_length=128, blank=True, default="")
    job_title = models.CharField(max_length=128, blank=True, default="")
    graduation_month = models.CharField(
        max_length=7, default="", validators=[validate_year_month]
    )
    bio = models.TextField(blank=True, default="")
    contact_note = models.TextField(blank=True, default="")
    allow_contact = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alumni_profiles"
        indexes = [
            models.Index(fields=["allow_contact"], name="idx_alumni_allow_contact"),
            models.Index(fields=["current_city"], name="idx_alumni_city"),
            models.Index(fields=["industry"], name="idx_alumni_industry"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.member.name} alumni profile"


class Instructor(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, db_index=True, blank=True, default=""
    )
    instructor_id = models.CharField(primary_key=True, max_length=18)
    name = models.CharField(max_length=64)
    phone_number = models.CharField(
        max_length=11, validators=[validate_china_mainland_phone]
    )
    vehicle_number = models.CharField(max_length=16, blank=True, default="")
    title = models.CharField(max_length=64, blank=True, default="")
    affiliation = models.CharField(max_length=128, blank=True, default="")
    address = models.CharField(max_length=128, blank=True, default="")
    fee = models.CharField(max_length=64, blank=True, default="")
    # 是否为外请教师
    is_external = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "instructors"
        indexes = [
            models.Index(fields=["name"], name="idx_instructors_name"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.instructor_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not getattr(self, "public_id", ""):
            from apps.common.utils import ensure_unique_public_id

            self.public_id = ensure_unique_public_id(type(self), prefix="i", length=12)
        return super().save(*args, **kwargs)


class Title(models.Model):
    """称号/头衔。"""

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, default="")
    # 外观JSON：例如 { "bg_color": "#409EFF", "text_color": "#ffffff", "icon": "crown", "shape": "pill" }
    appearance = models.JSONField(default=dict, blank=True)
    created_date = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "titles"
        indexes = [
            models.Index(fields=["name"], name="idx_titles_name"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class MemberTitle(models.Model):
    """Member 与 Title 的关联，包括授予时间。"""

    member = models.ForeignKey(
        "Member", on_delete=models.CASCADE, related_name="member_titles"
    )
    title = models.ForeignKey(
        "Title", on_delete=models.CASCADE, related_name="title_members"
    )
    awarded_at = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = "member_titles"
        unique_together = ("member", "title")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.member_id}-{self.title_id}"


# 放在类定义后，避免前向引用问题
Member.add_to_class(
    "titles",
    models.ManyToManyField(
        Title, through=MemberTitle, related_name="members", blank=True
    ),
)


def member_export_task_upload_to(instance: "MemberExportTask", filename: str) -> str:
    """成员导出任务结果的上传路径。"""
    ts = timezone.localtime().strftime("%Y%m%d%H%M%S")
    return f"member_exports/{ts}_{filename}"


class MemberExportTask(models.Model):
    """
    跟踪异步成员导出任务。

    任务过期后会自动清理。
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    task_id = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_export_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    result_file = models.FileField(
        upload_to=member_export_task_upload_to, blank=True, null=True
    )
    error_message = models.TextField(blank=True, default="")
    filter_params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "member_export_tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task_id"], name="idx_member_export_task_id"),
            models.Index(fields=["status"], name="idx_member_export_status"),
            models.Index(fields=["expires_at"], name="idx_member_export_expires"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Member Export Task {self.task_id} - {self.status}"

    def save(self, *args, **kwargs):
        """未设置过期时间时，自动设为创建后 1 小时。"""
        if not self.expires_at:
            from datetime import timedelta

            self.expires_at = timezone.now() + timedelta(hours=1)
        return super().save(*args, **kwargs)
