from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("personnel", "0002_memberexporttask"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="status",
            field=models.CharField(
                choices=[
                    ("ACTIVE", "在队"),
                    ("ALUMNI", "校友"),
                    ("INACTIVE", "停用"),
                ],
                default="ACTIVE",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="AlumniProfile",
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
                ("contact_note", models.TextField(blank=True, default="")),
                ("allow_contact", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "member",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alumni_profile",
                        to="personnel.member",
                    ),
                ),
            ],
            options={
                "db_table": "alumni_profiles",
                "indexes": [
                    models.Index(
                        fields=["allow_contact"], name="idx_alumni_allow_contact"
                    ),
                ],
            },
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["status"], name="idx_members_status"),
        ),
    ]
