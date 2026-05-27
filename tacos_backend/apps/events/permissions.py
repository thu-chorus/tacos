from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrEventAdmin(BasePermission):
    """站点管理员或活动管理员可写，读取需要登录。

    对象权限检查要求视图提供 get_object。
    """

    def has_permission(self, request, view):  # type: ignore[override]
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if request.method in SAFE_METHODS:
            return True
        action = getattr(view, "action", None)
        if action == "create":
            return bool(
                getattr(user, "is_staff", False)
                or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            )
        return True

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        if request.method in SAFE_METHODS:
            return True
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_staff", False) or getattr(user, "role", "") in (
            "Admin",
            "SuperAdmin",
        ):
            return True
        member = getattr(user, "member", None)
        if not member:
            return False
        return bool(obj.admins.filter(pk=getattr(member, "id", None)).exists())
