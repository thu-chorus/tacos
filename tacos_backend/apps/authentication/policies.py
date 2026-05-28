from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from apps.personnel.models import MemberStatus


@dataclass(frozen=True)
class LoginBlockReason:
    code: str
    message: str


def get_login_block_reason(user) -> Optional[LoginBlockReason]:
    """返回账号登录拦截原因。

    `User.is_active` 是平台级账号开关；`Member.status` 是成员生命周期状态。
    """
    if not user.is_active:
        return LoginBlockReason(
            code="user_inactive",
            message="用户账号已被禁用，请联系管理员",
        )

    member = getattr(user, "member", None)
    if member is not None and getattr(member, "status", None) == MemberStatus.INACTIVE:
        return LoginBlockReason(
            code="member_inactive",
            message="账号已停用，请联系管理员协助处理",
        )

    return None


def user_needs_profile_setup(user) -> bool:
    """所有账号都必须关联成员档案。"""
    return getattr(user, "member", None) is None


def user_is_first_login(user) -> bool:
    """按默认初始密码判断是否仍处于首次登录状态。"""
    default_password = getattr(settings, "DEFAULT_INITIAL_PASSWORD", "ChangeMe123!")
    return bool(default_password and user.check_password(default_password))
