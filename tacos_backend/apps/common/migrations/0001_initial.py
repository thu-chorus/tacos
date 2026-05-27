# 由 Django 4.2.14 于 2025-10-25 05:15 生成

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemAnnouncement",
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
                ("title", models.CharField(blank=True, default="", max_length=200)),
                ("publish_time", models.DateTimeField(db_index=True)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "system_announcements",
                "ordering": ["-publish_time", "-id"],
                "indexes": [
                    models.Index(fields=["publish_time"], name="idx_ann_publish_time")
                ],
            },
        ),
    ]
