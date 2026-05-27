from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="仅用于平台级账号禁用；成员在队、校友、停用请维护成员状态。",
                verbose_name="账号启用",
            ),
        ),
    ]
