from django.db import models


class SystemAnnouncement(models.Model):
    """仪表盘可见的全局系统公告。

    业务仅要求发布时间和公告正文，created_at/updated_at 用于审计。
    """

    title = models.CharField(max_length=200, blank=True, default="")
    publish_time = models.DateTimeField(db_index=True)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_announcements"
        ordering = ["-publish_time", "-id"]
        indexes = [
            models.Index(fields=["publish_time"], name="idx_ann_publish_time"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        title = (self.title or "").strip()
        head = title if title else str(self.content)
        return f"[{self.publish_time}] {head[:32]}"


class SystemStats(models.Model):
    """近似单例的系统统计存储。

    保存频繁计算成本较高的轻量计数，目前包含 total_members。
    """

    total_members = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_stats"

    def __str__(self) -> str:  # pragma: no cover
        return f"SystemStats(total_members={self.total_members})"

    @classmethod
    def get_solo(cls) -> "SystemStats":
        obj, _created = cls.objects.get_or_create(id=1, defaults={"total_members": 0})
        return obj
