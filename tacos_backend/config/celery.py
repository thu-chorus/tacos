"""
TaCOS 的 Celery 配置。

该模块初始化用于异步任务处理的 Celery 应用。
"""

import os

from celery import Celery
from celery.schedules import crontab

# 为 Celery 程序设置默认 Django 配置模块。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("tacos")

# 使用字符串配置，避免 worker 向子进程序列化配置对象。
# namespace='CELERY' 表示 Celery 相关配置键使用 CELERY_ 前缀。
app.config_from_object("django.conf:settings", namespace="CELERY")

# 从所有已注册的 Django 应用加载任务模块。
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """用于验证 Celery 是否正常工作的调试任务。"""
    print(f"Request: {self.request!r}")


# 配置周期任务
app.conf.beat_schedule = {
    # 清理过期的乐谱下载任务（每小时）
    "cleanup-expired-download-tasks": {
        "task": "apps.sheet_music.tasks.cleanup_expired_download_tasks",
        "schedule": crontab(minute=0),  # 每小时执行
    },
    # 清理过期的作业导出任务（每小时）
    "cleanup-expired-export-tasks": {
        "task": "apps.events.tasks.cleanup_expired_export_tasks",
        "schedule": crontab(minute=0),  # 每小时执行
    },
    # 清理过期的队员导出任务（每小时）
    "cleanup-expired-member-export-tasks": {
        "task": "apps.personnel.tasks.cleanup_expired_member_export_tasks",
        "schedule": crontab(minute=0),  # 每小时执行
    },
    # 停用超过6个月未登录的在队成员（每天凌晨2:30）
    "deactivate-stale-active-members": {
        "task": "apps.personnel.tasks.deactivate_stale_active_members",
        "schedule": crontab(minute=30, hour=2),  # 每日 02:30 执行
    },
    # 更新本月寿星称号（每月1号凌晨0点）
    "update-monthly-birthday-title": {
        "task": "apps.personnel.tasks.update_monthly_birthday_title",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),  # 每月1日 00:00 执行
    },
}
