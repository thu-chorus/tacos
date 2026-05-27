from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):  # type: ignore[override]
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "is_staff", False)
                or getattr(request.user, "role", "") in ("Admin", "SuperAdmin")
            )
        )


class IsSelfOrAdmin(BasePermission):
    """允许管理员完整访问，普通用户只能更新自己的成员记录。"""

    def has_permission(self, request, view):  # type: ignore[override]
        if not (request.user and request.user.is_authenticated):
            return False
        if IsAdmin().has_permission(request, view):
            return True
        action = getattr(view, "action", None)
        if action in ("update", "partial_update"):
            return True
        return False

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        if IsAdmin().has_permission(request, view):
            return True
        if request.method in ("PUT", "PATCH"):
            return getattr(getattr(obj, "user", None), "id", None) == getattr(
                request.user, "id", None
            )
        return False


class IsAdminOrSelfReadOnly(BasePermission):
    """MemberViewSet 权限：创建、更新、删除需要管理员。

    列表和详情允许已登录用户读取。
    """

    def has_permission(self, request, view):  # type: ignore[override]
        action = getattr(view, "action", None)
        if action in ("create", "update", "partial_update", "destroy"):
            return IsAdmin().has_permission(request, view)
        # 普通用户可浏览成员列表与详情
        if action in ("list", "retrieve"):
            return bool(request.user and request.user.is_authenticated)
        return IsAdmin().has_permission(request, view)

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        if IsAdmin().has_permission(request, view):
            return True
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return False
