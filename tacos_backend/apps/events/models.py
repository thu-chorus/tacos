from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class EventVisibility(models.TextChoices):
    ALL = "ALL", "面向全体"
    FIRST = "FIRST", "面向一队"
    SECOND = "SECOND", "面向二队"
    PARTIAL = "PARTIAL", "面向部分"


class Event(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, db_index=True, blank=True, default=""
    )
    name = models.CharField(max_length=128)
    introduction = models.TextField()
    announcement = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    visibility = models.CharField(
        max_length=16, choices=EventVisibility.choices, default=EventVisibility.PARTIAL
    )
    visible_to_alumni = models.BooleanField(default=False)

    admins = models.ManyToManyField(
        "personnel.Member", related_name="managed_events", blank=False
    )
    participants = models.ManyToManyField(
        "personnel.Member", related_name="events", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"
        indexes = [
            models.Index(fields=["start_date"], name="idx_events_start_date"),
            models.Index(fields=["end_date"], name="idx_events_end_date"),
            models.Index(fields=["visibility"], name="idx_events_visibility"),
            models.Index(fields=["visible_to_alumni"], name="idx_events_alumni"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.name

    def save(self, *args, **kwargs):
        if not getattr(self, "public_id", ""):
            from apps.common.utils import ensure_unique_public_id

            self.public_id = ensure_unique_public_id(type(self), prefix="e", length=12)
        return super().save(*args, **kwargs)


def event_announcement_upload_to(instance, filename):  # pragma: no cover
    from django.utils import timezone

    ts = timezone.localtime().strftime("%Y%m%d%H%M%S")
    return f"events/announcements/{instance.event_id}/{ts}_{filename}"


class EventAnnouncementImage(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="announcement_images"
    )
    image = models.ImageField(upload_to=event_announcement_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_announcement_images"
        ordering = ["id"]


class CheckinType(models.TextChoices):
    NONE = "NONE", "无条件签到"
    PASSWORD = "PASSWORD", "密码签到"
    LOCATION = "LOCATION", "地点签到"


class EventCheckinSession(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="checkin_sessions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_checkin_sessions",
    )
    name = models.CharField(max_length=128, default="")
    type = models.CharField(
        max_length=16, choices=CheckinType.choices, default=CheckinType.NONE
    )
    password_hash = models.CharField(max_length=128, blank=True, default="")
    location_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    location_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    radius_m = models.IntegerField(default=500)
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event_checkin_sessions"
        ordering = ["-started_at"]
        indexes = [
            models.Index(
                fields=["event", "is_active"], name="idx_checkin_event_active"
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Session {self.id} for Event {self.event_id}"


class EventCheckinRecord(models.Model):
    session = models.ForeignKey(
        EventCheckinSession, on_delete=models.CASCADE, related_name="records"
    )
    member = models.ForeignKey(
        "personnel.Member", on_delete=models.CASCADE, related_name="checkin_records"
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "event_checkin_records"
        unique_together = ("session", "member")
        ordering = ["-checked_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Record {self.member_id} @ {self.checked_at}"


class Assignment(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, db_index=True, blank=True, default=""
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="assignments"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_assignments",
    )
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    deadline = models.DateTimeField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_assignments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["event", "deadline"], name="idx_assignment_event_deadline"
            ),
            models.Index(fields=["is_closed"], name="idx_assignment_closed"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Assignment {self.id} for Event {self.event_id}"

    def save(self, *args, **kwargs):
        if not getattr(self, "public_id", ""):
            from apps.common.utils import ensure_unique_public_id

            self.public_id = ensure_unique_public_id(type(self), prefix="a", length=12)
        return super().save(*args, **kwargs)

    @property
    def is_past_deadline(self) -> bool:
        return timezone.now() >= self.deadline


def assignment_attachment_upload_to(instance, filename):  # pragma: no cover
    return f"assignments/{instance.assignment_id}/{timezone.localtime().strftime('%Y%m%d%H%M%S')}_{filename}"


class AssignmentAttachment(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=assignment_attachment_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignment_attachments"
        ordering = ["id"]


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    member = models.ForeignKey(
        "personnel.Member",
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    text = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(default=timezone.now)
    graded_score = models.CharField(max_length=32, blank=True, default="")
    graded_comment = models.TextField(blank=True, default="")
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_assignment_submissions",
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assignment_submissions"
        unique_together = ("assignment", "member")
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(
                fields=["assignment", "member"], name="idx_subm_assign_member"
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Submission {self.member_id} @ {self.submitted_at}"


def assignment_submission_upload_to(instance, filename):  # pragma: no cover
    return f"submissions/{instance.submission_id}/{timezone.localtime().strftime('%Y%m%d%H%M%S')}_{filename}"


class AssignmentSubmissionAttachment(models.Model):
    submission = models.ForeignKey(
        AssignmentSubmission, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=assignment_submission_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignment_submission_attachments"
        ordering = ["id"]


def export_task_result_upload_to(
    instance: "AssignmentExportTask", filename: str
) -> str:
    """作业导出任务结果的上传路径。"""
    ts = timezone.localtime().strftime("%Y%m%d%H%M%S")
    return f"assignment_exports/{ts}_{filename}"


class AssignmentExportTask(models.Model):
    """
    跟踪异步作业导出任务。

    任务过期后会自动清理。
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    task_id = models.CharField(max_length=64, unique=True, db_index=True)
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="export_tasks"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_export_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    result_file = models.FileField(
        upload_to=export_task_result_upload_to, blank=True, null=True
    )
    error_message = models.TextField(blank=True, default="")
    filter_params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "assignment_export_tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task_id"], name="idx_export_task_id"),
            models.Index(fields=["status"], name="idx_export_task_status"),
            models.Index(fields=["expires_at"], name="idx_export_task_expires"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Export Task {self.task_id} - {self.status}"

    def save(self, *args, **kwargs):
        """未设置过期时间时，自动设为创建后 1 小时。"""
        if not self.expires_at:
            from datetime import timedelta

            self.expires_at = timezone.now() + timedelta(hours=1)
        return super().save(*args, **kwargs)
