from django.urls import path

from .views import (
    RefreshJWTView,
    change_password,
    first_login_setup,
    login,
    logout,
    me,
    update_profile,
)

urlpatterns = [
    path("login", login, name="login"),
    path("refresh", RefreshJWTView.as_view(), name="token_refresh"),
    path("me", me, name="me"),
    path("logout", logout, name="logout"),
    path("profile", update_profile, name="profile_update"),
    path("password", change_password, name="change_password"),
    path("first-login", first_login_setup, name="first_login_setup"),
]
