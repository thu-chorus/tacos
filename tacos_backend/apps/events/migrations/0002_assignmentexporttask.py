# 由 Django 4.2.14 于 2025-10-28 06:13 生成

import apps.events.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignmentExportTask",
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
                        upload_to=apps.events.models.export_task_result_upload_to,
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="")),
                ("filter_params", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="export_tasks",
                        to="events.assignment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_export_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "assignment_export_tasks",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["task_id"], name="idx_export_task_id"),
                    models.Index(fields=["status"], name="idx_export_task_status"),
                    models.Index(fields=["expires_at"], name="idx_export_task_expires"),
                ],
            },
        ),
    ]
