from django.db import migrations


def init_system_stats(apps, schema_editor):
    SystemStats = apps.get_model("common", "SystemStats")
    Member = apps.get_model("personnel", "Member")
    total = Member.objects.count()
    # 确保存在 id=1 的统计记录
    obj, created = SystemStats.objects.get_or_create(id=1, defaults={"total_members": total})
    if not created:
        obj.total_members = total
        obj.save(update_fields=["total_members"])


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_systemstats"),
        ("personnel", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(init_system_stats, migrations.RunPython.noop),
    ]

