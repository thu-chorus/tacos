# 由 Django 4.2.14 于 2025-10-28 03:52 生成

import apps.sheet_music.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sheet_music", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SheetDownloadTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "task_id",
                    models.CharField(db_index=True, max_length=64, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PROCESSING", "Processing"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "result_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=apps.sheet_music.models.download_task_result_upload_to,
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "sheet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="download_tasks",
                        to="sheet_music.sheet",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sheet_download_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "sheet_download_tasks",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["task_id"], name="idx_download_task_id"),
                    models.Index(fields=["status"], name="idx_download_task_status"),
                    models.Index(
                        fields=["expires_at"], name="idx_download_task_expires"
                    ),
                ],
            },
        ),
    ]
