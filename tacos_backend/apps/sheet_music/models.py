from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.validators import validate_pdf_file_extension


def sheet_upload_to(instance: "Sheet", filename: str) -> str:
    ts = timezone.localtime().strftime("%Y%m%d%H%M%S")
    return f"sheets/{ts}_{filename}"


class Sheet(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, db_index=True, blank=True, default=""
    )
    title = models.CharField(max_length=128)
    lyricist = models.CharField(max_length=128, blank=True, default="")
    composer = models.CharField(max_length=128, blank=True, default="")
    arranger = models.CharField(max_length=128, blank=True, default="")
    introduction = models.TextField(blank=True, default="")
    original_file = models.FileField(upload_to=sheet_upload_to)

    copyright_notice = models.CharField(max_length=255, blank=True, default="")
    is_restricted = models.BooleanField(default=False)

    visible_to_all = models.BooleanField(default=True)
    visible_to_alumni = models.BooleanField(default=False)
    visible_events = models.ManyToManyField(
        "events.Event", related_name="sheets", blank=True
    )
    visible_members = models.ManyToManyField(
        "personnel.Member", related_name="visible_sheets", blank=True
    )

    upload_time = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sheets"
        indexes = [
            models.Index(fields=["title"], name="idx_sheets_title"),
            models.Index(fields=["composer"], name="idx_sheets_composer"),
            models.Index(fields=["upload_time"], name="idx_sheets_upload_time"),
            models.Index(fields=["visible_to_alumni"], name="idx_sheets_alumni"),
        ]

    def clean(self) -> None:
        if self.original_file and hasattr(self.original_file, "name"):
            validate_pdf_file_extension(self.original_file.name)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title}"

    def save(self, *args, **kwargs):
        if not getattr(self, "public_id", ""):
            from apps.common.utils import ensure_unique_public_id

            self.public_id = ensure_unique_public_id(type(self), prefix="s", length=12)
        return super().save(*args, **kwargs)


class SheetDownloadLog(models.Model):
    sheet = models.ForeignKey(
        Sheet, on_delete=models.CASCADE, related_name="download_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sheet_downloads",
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "sheet_download_logs"
        ordering = ["-downloaded_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.sheet_id} by {getattr(self.user, 'user_id', '')} at {self.downloaded_at}"


def download_task_result_upload_to(instance: "SheetDownloadTask", filename: str) -> str:
    """水印 PDF 结果的上传路径。"""
    ts = timezone.localtime().strftime("%Y%m%d%H%M%S")
    return f"sheet_download_tasks/{ts}_{filename}"


class SheetDownloadTask(models.Model):
    """
    跟踪异步乐谱下载和预览任务。

    任务会生成水印文件，并在过期后自动清理。
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    task_id = models.CharField(max_length=64, unique=True, db_index=True)
    sheet = models.ForeignKey(
        Sheet, on_delete=models.CASCADE, related_name="download_tasks"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sheet_download_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    result_file = models.FileField(
        upload_to=download_task_result_upload_to, blank=True, null=True
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "sheet_download_tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task_id"], name="idx_download_task_id"),
            models.Index(fields=["status"], name="idx_download_task_status"),
            models.Index(fields=["expires_at"], name="idx_download_task_expires"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Task {self.task_id} - {self.status}"

    def save(self, *args, **kwargs):
        """未设置过期时间时，自动设为创建后 1 小时。"""
        if not self.expires_at:
            from datetime import timedelta

            self.expires_at = timezone.now() + timedelta(hours=1)
        return super().save(*args, **kwargs)
