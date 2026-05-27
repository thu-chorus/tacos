"""
TaCOS 配置包初始化。
"""

# 确保 Django 启动时导入 Celery 应用，让 shared_task 使用该实例。
# 如果未安装 Celery，Django 仍可运行，但异步任务不可用。
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:
    # 未安装 Celery 时继续启动
    pass
