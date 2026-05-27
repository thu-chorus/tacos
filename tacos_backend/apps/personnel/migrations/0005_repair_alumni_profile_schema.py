from django.db import migrations

ALUMNI_PROFILE_TABLE = "alumni_profiles"
REMOVED_ALUMNI_COLUMNS = (
    "contact_email",
    "contact_wechat",
    "contact_phone",
    "graduation_year",
    "actual_graduate_month",
)


def get_table_columns(connection, table_name):
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, table_name
            )
        }


def repair_alumni_profile_schema(apps, schema_editor):
    connection = schema_editor.connection
    existing_columns = get_table_columns(connection, ALUMNI_PROFILE_TABLE)
    alumni_profile = apps.get_model("personnel", "AlumniProfile")
    quoted_table = schema_editor.quote_name(ALUMNI_PROFILE_TABLE)

    if "graduation_month" not in existing_columns:
        if "actual_graduate_month" in existing_columns:
            schema_editor.execute(
                f"ALTER TABLE {quoted_table} "
                f"RENAME COLUMN {schema_editor.quote_name('actual_graduate_month')} "
                f"TO {schema_editor.quote_name('graduation_month')}"
            )
        else:
            schema_editor.add_field(
                alumni_profile,
                alumni_profile._meta.get_field("graduation_month"),
            )
        existing_columns = get_table_columns(connection, ALUMNI_PROFILE_TABLE)

    for column in REMOVED_ALUMNI_COLUMNS:
        if column in existing_columns:
            schema_editor.execute(
                f"ALTER TABLE {quoted_table} DROP COLUMN {schema_editor.quote_name(column)}"
            )
            existing_columns.remove(column)


class Migration(migrations.Migration):

    dependencies = [
        ("personnel", "0004_alumniprofile_details"),
    ]

    operations = [
        migrations.RunPython(repair_alumni_profile_schema, migrations.RunPython.noop),
    ]
