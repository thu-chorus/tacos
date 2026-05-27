from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sheet_music", "0002_sheetdownloadtask"),
    ]

    operations = [
        migrations.AddField(
            model_name="sheet",
            name="visible_to_alumni",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="sheet",
            index=models.Index(fields=["visible_to_alumni"], name="idx_sheets_alumni"),
        ),
    ]
