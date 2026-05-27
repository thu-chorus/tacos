# 由 Django 4.2.14 于 2025-11-09 06:02 生成

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_assignmentexporttask"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assignmentsubmission",
            name="submitted_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
