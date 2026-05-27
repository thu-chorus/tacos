# 由 Django 4.2.14 于 2025-10-25 05:15 生成

import apps.common.validators
import apps.personnel.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Member",
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
                ("name", models.CharField(max_length=64)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[("男", "男"), ("女", "女")],
                        default="",
                        max_length=2,
                    ),
                ),
                (
                    "voice_part",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("S1", "S1"),
                            ("S2", "S2"),
                            ("A1", "A1"),
                            ("A2", "A2"),
                            ("T1", "T1"),
                            ("T2", "T2"),
                            ("B1", "B1"),
                            ("B2", "B2"),
                            ("Other", "Other"),
                        ],
                        default="",
                        max_length=8,
                    ),
                ),
                ("wechat_id", models.CharField(blank=True, default="", max_length=64)),
                (
                    "department",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                (
                    "department_other",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                (
                    "class_name",
                    models.CharField(
                        blank=True, db_column="class", default="", max_length=64
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=11,
                        validators=[
                            apps.common.validators.validate_china_mainland_phone
                        ],
                    ),
                ),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("dorm", models.CharField(blank=True, default="", max_length=64)),
                ("birthday", models.DateField(blank=True, null=True)),
                ("hometown", models.CharField(blank=True, default="", max_length=128)),
                ("ethnicity", models.CharField(blank=True, default="", max_length=32)),
                (
                    "political_status",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                (
                    "political_affiliation",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                ("is_specialty", models.BooleanField(default=False)),
                ("is_centralized", models.BooleanField(default=False)),
                ("position", models.CharField(blank=True, default="", max_length=64)),
                (
                    "join_month",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=7,
                        validators=[apps.common.validators.validate_year_month],
                    ),
                ),
                (
                    "graduate_month",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=7,
                        validators=[apps.common.validators.validate_year_month],
                    ),
                ),
                (
                    "tier",
                    models.CharField(
                        choices=[("一队", "一队"), ("二队", "二队")],
                        default="二队",
                        max_length=4,
                    ),
                ),
                ("portfolio", models.TextField(blank=True, default="")),
                (
                    "hidden_fields",
                    models.JSONField(
                        blank=True,
                        default=apps.personnel.models.default_member_hidden_fields,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "members",
            },
        ),
        migrations.CreateModel(
            name="Title",
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
                ("name", models.CharField(max_length=64, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("appearance", models.JSONField(blank=True, default=dict)),
                (
                    "created_date",
                    models.DateField(default=django.utils.timezone.localdate),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "titles",
                "indexes": [models.Index(fields=["name"], name="idx_titles_name")],
            },
        ),
        migrations.CreateModel(
            name="MemberTitle",
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
                    "awarded_at",
                    models.DateField(default=django.utils.timezone.localdate),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="member_titles",
                        to="personnel.member",
                    ),
                ),
                (
                    "title",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="title_members",
                        to="personnel.title",
                    ),
                ),
            ],
            options={
                "db_table": "member_titles",
                "unique_together": {("member", "title")},
            },
        ),
        migrations.AddField(
            model_name="member",
            name="titles",
            field=models.ManyToManyField(
                blank=True,
                related_name="members",
                through="personnel.MemberTitle",
                to="personnel.title",
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="member",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="Instructor",
            fields=[
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
                (
                    "instructor_id",
                    models.CharField(max_length=18, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=64)),
                (
                    "phone_number",
                    models.CharField(
                        max_length=11,
                        validators=[
                            apps.common.validators.validate_china_mainland_phone
                        ],
                    ),
                ),
                (
                    "vehicle_number",
                    models.CharField(blank=True, default="", max_length=16),
                ),
                ("title", models.CharField(blank=True, default="", max_length=64)),
                (
                    "affiliation",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                ("address", models.CharField(blank=True, default="", max_length=128)),
                ("fee", models.CharField(blank=True, default="", max_length=64)),
                ("is_external", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "instructors",
                "indexes": [models.Index(fields=["name"], name="idx_instructors_name")],
            },
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["voice_part"], name="idx_members_voice_part"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["tier"], name="idx_members_tier"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["join_month"], name="idx_members_join_month"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(
                fields=["graduate_month"], name="idx_members_graduate_month"
            ),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["name"], name="idx_members_name"),
        ),
    ]
