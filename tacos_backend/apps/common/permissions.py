from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(BasePermission):
    """允许已登录用户读取，仅 staff/admin 可写。"""

    def has_permission(self, request, view):  # type: ignore[override]
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_staff)


class PublicReadAdminWrite(BasePermission):
    """允许所有人读取，仅 staff/admin 可写。

    - 安全方法（GET/HEAD/OPTIONS）：任意请求均可访问。
    - 写入方法：需要 is_staff 或角色为 Admin/SuperAdmin。

    注意：该权限类允许匿名访问，应谨慎使用。
    大多数端点应使用 IsAuthenticatedReadAdminWrite。
    """

    def has_permission(self, request, view):  # type: ignore[override]
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        is_staff = getattr(user, "is_staff", False)
        role = getattr(user, "role", "")
        return bool(is_staff or role in ("Admin", "SuperAdmin"))


class IsAuthenticatedReadAdminWrite(BasePermission):
    """读取需要登录，写入需要管理员权限。

    - 安全方法（GET/HEAD/OPTIONS）：需要已登录用户。
    - 写入方法：需要 is_staff 或角色为 Admin/SuperAdmin。
    """

    def has_permission(self, request, view):  # type: ignore[override]
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        is_staff = getattr(user, "is_staff", False)
        role = getattr(user, "role", "")
        return bool(is_staff or role in ("Admin", "SuperAdmin"))
