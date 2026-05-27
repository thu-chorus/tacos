# 由 Django 4.2.14 于 2025-10-25 05:15 生成

import apps.sheet_music.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("personnel", "0001_initial"),
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sheet",
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
                    "public_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=16,
                        unique=True,
                    ),
                ),
                ("title", models.CharField(max_length=128)),
                ("lyricist", models.CharField(blank=True, default="", max_length=128)),
                ("composer", models.CharField(blank=True, default="", max_length=128)),
                ("arranger", models.CharField(blank=True, default="", max_length=128)),
                ("introduction", models.TextField(blank=True, default="")),
                (
                    "original_file",
                    models.FileField(upload_to=apps.sheet_music.models.sheet_upload_to),
                ),
                (
                    "copyright_notice",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("is_restricted", models.BooleanField(default=False)),
                ("visible_to_all", models.BooleanField(default=True)),
                ("upload_time", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "visible_events",
                    models.ManyToManyField(
                        blank=True, related_name="sheets", to="events.event"
                    ),
                ),
                (
                    "visible_members",
                    models.ManyToManyField(
                        blank=True, related_name="visible_sheets", to="personnel.member"
                    ),
                ),
            ],
            options={
                "db_table": "sheets",
            },
        ),
        migrations.CreateModel(
            name="SheetDownloadLog",
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
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.CharField(blank=True, default="", max_length=64)),
                (
                    "sheet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="download_logs",
                        to="sheet_music.sheet",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sheet_downloads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "sheet_download_logs",
                "ordering": ["-downloaded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sheet",
            index=models.Index(fields=["title"], name="idx_sheets_title"),
        ),
        migrations.AddIndex(
            model_name="sheet",
            index=models.Index(fields=["composer"], name="idx_sheets_composer"),
        ),
        migrations.AddIndex(
            model_name="sheet",
            index=models.Index(fields=["upload_time"], name="idx_sheets_upload_time"),
        ),
    ]
