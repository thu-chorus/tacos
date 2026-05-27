from django.contrib import admin

from .models import (
    AlumniProfile,
    Instructor,
    Member,
    MemberExportTask,
    MemberTitle,
    Title,
)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_user_id",
        "voice_part",
        "tier",
        "status",
        "department",
        "join_month",
    )
    list_filter = ("voice_part", "tier", "status", "join_month")
    search_fields = ("name", "user__user_id", "department")

    def get_user_id(self, obj):  # pragma: no cover
        return getattr(obj.user, "user_id", "")

    get_user_id.short_description = "user_id"


@admin.register(AlumniProfile)
class AlumniProfileAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "current_city",
        "industry",
        "graduation_month",
        "allow_contact",
        "updated_at",
    )
    list_filter = ("allow_contact", "industry", "current_city")
    search_fields = (
        "member__name",
        "member__user__user_id",
        "current_city",
        "industry",
        "company",
        "job_title",
        "graduation_month",
    )


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("instructor_id", "name", "phone_number", "title", "affiliation")
    search_fields = ("instructor_id", "name", "phone_number")


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ("name", "created_date", "owners_count")
    search_fields = ("name",)

    def owners_count(self, obj):  # pragma: no cover
        return obj.members.count()


@admin.register(MemberTitle)
class MemberTitleAdmin(admin.ModelAdmin):
    list_display = ("member", "title", "awarded_at")
    search_fields = ("member__user__user_id", "member__name", "title__name")


@admin.register(MemberExportTask)
class MemberExportTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_id", "user", "status", "created_at", "expires_at")
    list_filter = ("status", "created_at")
    search_fields = ("task_id", "user__user_id")
    readonly_fields = ("task_id", "created_at", "updated_at")
