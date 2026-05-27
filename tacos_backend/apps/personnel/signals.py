from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Member


def rebuild_total_members() -> None:
    """重新计算并保存成员总数。

    保持逻辑简单，确保重复调用时也能得到正确结果。
    """
    try:
        from apps.common.models import SystemStats

        total = Member.objects.count()
        stats = SystemStats.get_solo()
        if stats.total_members != total:
            stats.total_members = total
            stats.save(update_fields=["total_members", "updated_at"])
    except Exception:
        pass


@receiver(post_save, sender=Member)
def on_member_saved(sender, instance: Member, created: bool, **kwargs):  # noqa: ARG001
    rebuild_total_members()


@receiver(post_delete, sender=Member)
def on_member_deleted(sender, instance: Member, **kwargs):  # noqa: ARG001
    rebuild_total_members()
