from django import forms
from django.contrib import admin

from apps.personnel.models import MemberStatus

from .models import (
    Assignment,
    AssignmentAttachment,
    AssignmentExportTask,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    Event,
    EventAnnouncementImage,
    EventCheckinRecord,
    EventCheckinSession,
)


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        admins = cleaned_data.get("admins")
        visible_to_alumni = cleaned_data.get("visible_to_alumni")
        if (
            not visible_to_alumni
            and admins is not None
            and admins.filter(status=MemberStatus.ALUMNI).exists()
        ):
            self.add_error("admins", "校友不能担任校友不可见活动的管理员")
        return cleaned_data


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = (
        "id",
        "name",
        "start_date",
        "end_date",
        "visibility",
        "visible_to_alumni",
    )
    list_filter = ("visibility", "visible_to_alumni", "start_date", "end_date")
    search_fields = ("name",)
    filter_horizontal = ("admins", "participants")


@admin.register(EventCheckinSession)
class EventCheckinSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "type", "is_active", "started_at", "ended_at")
    list_filter = ("type", "is_active")
    search_fields = ("event__name",)


@admin.register(EventCheckinRecord)
class EventCheckinRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "member", "checked_at")
    search_fields = ("session__event__name", "member__name", "member__user__user_id")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "title", "deadline", "is_closed", "created_at")
    list_filter = ("is_closed", "event")
    search_fields = ("title",)


@admin.register(AssignmentAttachment)
class AssignmentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment", "file", "created_at")
    search_fields = ("assignment__title",)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assignment",
        "member",
        "submitted_at",
        "graded_score",
        "graded_at",
    )
    search_fields = ("member__name", "member__user__user_id")
    list_filter = ("assignment",)


@admin.register(AssignmentSubmissionAttachment)
class AssignmentSubmissionAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "file", "created_at")


@admin.register(EventAnnouncementImage)
class EventAnnouncementImageAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "image", "created_at")
    search_fields = ("event__name",)


@admin.register(AssignmentExportTask)
class AssignmentExportTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_id",
        "assignment",
        "user",
        "status",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("task_id", "assignment__title", "user__user_id")
    readonly_fields = ("task_id", "created_at", "updated_at")
