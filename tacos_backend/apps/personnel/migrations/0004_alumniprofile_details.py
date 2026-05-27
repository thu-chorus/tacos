from django.db import migrations, models

import apps.common.validators


class Migration(migrations.Migration):

    dependencies = [
        ("personnel", "0003_member_status_alumniprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="alumniprofile",
            name="bio",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="company",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="current_city",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="graduation_month",
            field=models.CharField(
                default="",
                max_length=7,
                validators=[apps.common.validators.validate_year_month],
            ),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="industry",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="job_title",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddIndex(
            model_name="alumniprofile",
            index=models.Index(fields=["current_city"], name="idx_alumni_city"),
        ),
        migrations.AddIndex(
            model_name="alumniprofile",
            index=models.Index(fields=["industry"], name="idx_alumni_industry"),
        ),
    ]
