# 由 Django 4.2.14 于 2025-10-25 05:15 生成

import apps.events.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("personnel", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Assignment",
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
                ("description", models.TextField(blank=True, default="")),
                ("deadline", models.DateTimeField()),
                ("is_closed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "event_assignments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentSubmission",
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
                ("text", models.TextField(blank=True, default="")),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "graded_score",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                ("graded_comment", models.TextField(blank=True, default="")),
                ("graded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="events.assignment",
                    ),
                ),
                (
                    "graded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="graded_assignment_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_submissions",
                        to="personnel.member",
                    ),
                ),
            ],
            options={
                "db_table": "assignment_submissions",
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.CreateModel(
            name="Event",
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
                ("name", models.CharField(max_length=128)),
                ("introduction", models.TextField()),
                ("announcement", models.TextField(blank=True, default="")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("ALL", "面向全体"),
                            ("FIRST", "面向一队"),
                            ("SECOND", "面向二队"),
                            ("PARTIAL", "面向部分"),
                        ],
                        default="PARTIAL",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "admins",
                    models.ManyToManyField(
                        related_name="managed_events", to="personnel.member"
                    ),
                ),
                (
                    "participants",
                    models.ManyToManyField(
                        blank=True, related_name="events", to="personnel.member"
                    ),
                ),
            ],
            options={
                "db_table": "events",
            },
        ),
        migrations.CreateModel(
            name="EventCheckinSession",
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
                ("name", models.CharField(default="", max_length=128)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("NONE", "无条件签到"),
                            ("PASSWORD", "密码签到"),
                            ("LOCATION", "地点签到"),
                        ],
                        default="NONE",
                        max_length=16,
                    ),
                ),
                (
                    "password_hash",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                (
                    "location_lat",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                (
                    "location_lng",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                ("radius_m", models.IntegerField(default=500)),
                ("is_active", models.BooleanField(default=False)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_checkin_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkin_sessions",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "db_table": "event_checkin_sessions",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="EventCheckinRecord",
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
                ("checked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "lat",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                (
                    "lng",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkin_records",
                        to="personnel.member",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="records",
                        to="events.eventcheckinsession",
                    ),
                ),
            ],
            options={
                "db_table": "event_checkin_records",
                "ordering": ["-checked_at"],
            },
        ),
        migrations.CreateModel(
            name="EventAnnouncementImage",
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
                    "image",
                    models.ImageField(
                        upload_to=apps.events.models.event_announcement_upload_to
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcement_images",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "db_table": "event_announcement_images",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentSubmissionAttachment",
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
                    "file",
                    models.FileField(
                        upload_to=apps.events.models.assignment_submission_upload_to
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="events.assignmentsubmission",
                    ),
                ),
            ],
            options={
                "db_table": "assignment_submission_attachments",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentAttachment",
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
                    "file",
                    models.FileField(
                        upload_to=apps.events.models.assignment_attachment_upload_to
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="events.assignment",
                    ),
                ),
            ],
            options={
                "db_table": "assignment_attachments",
                "ordering": ["id"],
            },
        ),
        migrations.AddField(
            model_name="assignment",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="events.event",
            ),
        ),
        migrations.AddIndex(
            model_name="eventcheckinsession",
            index=models.Index(
                fields=["event", "is_active"], name="idx_checkin_event_active"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="eventcheckinrecord",
            unique_together={("session", "member")},
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["start_date"], name="idx_events_start_date"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["end_date"], name="idx_events_end_date"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["visibility"], name="idx_events_visibility"),
        ),
        migrations.AddIndex(
            model_name="assignmentsubmission",
            index=models.Index(
                fields=["assignment", "member"], name="idx_subm_assign_member"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="assignmentsubmission",
            unique_together={("assignment", "member")},
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(
                fields=["event", "deadline"], name="idx_assignment_event_deadline"
            ),
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["is_closed"], name="idx_assignment_closed"),
        ),
    ]
