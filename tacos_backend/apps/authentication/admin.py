from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)
    list_display = ("user_id", "name", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("user_id", "name")

    fieldsets = (
        (None, {"fields": ("user_id", "password")}),
        ("Personal info", {"fields": ("name", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "user_id",
                    "password1",
                    "password2",
                    "name",
                    "role",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    def get_field_queryset(self, db, db_field, request):  # pragma: no cover
        return super().get_field_queryset(db, db_field, request)
