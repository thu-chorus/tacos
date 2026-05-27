from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_alter_assignmentsubmission_submitted_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="visible_to_alumni",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["visible_to_alumni"], name="idx_events_alumni"),
        ),
    ]
