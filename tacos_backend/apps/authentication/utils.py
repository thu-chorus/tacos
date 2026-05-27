from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UserIdBackend(ModelBackend):
    """使用 user_id 而不是用户名进行认证。"""

    def authenticate(self, request, user_id=None, password=None, **kwargs):  # type: ignore[override]
        User = get_user_model()
        if user_id is None:
            return None
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:  # type: ignore[attr-defined]
            return None
        if user.check_password(password):
            return user
        return None
