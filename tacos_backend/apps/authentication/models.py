from __future__ import annotations

from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SuperAdmin", "SuperAdmin"
    ADMIN = "Admin", "Admin"
    MEMBER = "Member", "Member"


class UserManager(BaseUserManager):
    """使用 user_id 作为唯一标识的自定义用户管理器。"""

    use_in_migrations = True

    def create_user(self, user_id: str, password: Optional[str] = None, **extra_fields):  # type: ignore[override]
        if not user_id:
            raise ValueError("The user_id must be set")
        user_id = str(user_id).strip()
        user = self.model(user_id=user_id, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id: str, password: str, **extra_fields):  # type: ignore[override]
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(user_id=user_id, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """使用学号或工号作为 user_id 的角色用户。"""

    user_id = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=64, blank=True, default="")
    role = models.CharField(
        max_length=16, choices=UserRole.choices, default=UserRole.MEMBER
    )

    # 平台级账号开关；成员在队、校友、停用状态由 Member.status 表示。
    is_active = models.BooleanField(
        "账号启用",
        default=True,
        help_text="仅用于平台级账号禁用；成员在队、校友、停用请维护成员状态。",
    )
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}"
