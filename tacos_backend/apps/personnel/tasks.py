"""
Celery tasks for personnel-related operations.

Handles asynchronous member export generation and cleanup tasks.
"""

import logging
import os
from calendar import monthrange

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db.models import Q
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


def _months_before(value, months: int):
    """返回 value 往前 months 个自然月的同一时刻。"""
    month = value.month - months
    year = value.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


@shared_task
def deactivate_stale_active_members(months: int = 6):
    """将超过指定月数未登录的在队成员设为停用。

    仅处理 `ACTIVE` 成员；校友和已停用成员不会被修改。没有登录记录的
    成员按账号创建时间判断，避免新建账号被立即停用。
    """
    from .models import Member, MemberStatus

    months = int(months)
    if months < 1:
        raise ValueError("months must be positive")

    now = timezone.now()
    cutoff = _months_before(now, months)
    stale_members = Member.objects.filter(status=MemberStatus.ACTIVE).filter(
        Q(user__last_login__lte=cutoff)
        | Q(user__last_login__isnull=True, user__date_joined__lte=cutoff)
    )

    updated_count = stale_members.update(
        status=MemberStatus.INACTIVE,
        updated_at=now,
    )
    logger.info(
        "已将 %s 名超过 %s 个月未登录的在队成员设为停用，截止时间：%s",
        updated_count,
        months,
        cutoff.isoformat(),
    )
    return {
        "status": "success",
        "months": months,
        "cutoff": cutoff.isoformat(),
        "updated_count": updated_count,
    }


@shared_task
def update_monthly_birthday_title():
    """
    更新本月寿星称号的定时任务
    在每月第一天自动执行，清空现有的"本月寿星"称号授予，
    并重新授予给当月生日的队员。

    这个任务会在 Celery Beat 中配置为每月1号0点执行。
    """
    current_month = timezone.localdate().month
    logger.info(f"开始执行本月寿星称号更新任务，目标月份: {current_month}月")

    try:
        # 调用管理命令
        call_command(
            "update_birthday_titles",
            title_name="本月寿星",
            month=current_month,
            verbosity=1,
        )
        logger.info("本月寿星称号更新任务执行成功")
        return {"status": "success", "month": current_month}
    except Exception as e:
        logger.error(f"本月寿星称号更新任务执行失败: {e}")
        raise


@shared_task
def update_birthday_title_for_month(month, title_name="本月寿星"):
    """
    为指定月份更新生日称号

    可以手动调用此任务为任意月份更新称号。

    Args:
        month (int): 目标月份 (1-12)
        title_name (str): 称号名称，默认为"本月寿星"

    Returns:
        dict: 包含执行状态和月份信息
    """
    if not (1 <= month <= 12):
        raise ValueError("月份必须在1-12之间")

    logger.info(f"开始为 {month}月 更新 {title_name} 称号")

    try:
        call_command(
            "update_birthday_titles", title_name=title_name, month=month, verbosity=1
        )
        logger.info(f"{month}月 {title_name} 称号更新成功")
        return {"status": "success", "month": month, "title_name": title_name}
    except Exception as e:
        logger.error(f"{month}月 {title_name} 称号更新失败: {e}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_member_export_task(self, task_id: str, filter_params: dict):
    """
    Generate Excel export for members.

    Args:
        task_id: The unique task identifier
        filter_params: Filter parameters (name__icontains, user_id, voice_part, etc.)

    Returns:
        dict: Task result with status and message
    """
    from .importers import build_export_workbook
    from .models import Member, MemberExportTask
    from .sorting import sort_members

    try:
        task = MemberExportTask.objects.get(task_id=task_id)
        task.status = "PROCESSING"
        task.save(update_fields=["status", "updated_at"])

        logger.info(f"Generating member export for task {task_id}")

        qs = Member.objects.all()

        if filter_params.get("name__icontains"):
            qs = qs.filter(name__icontains=filter_params["name__icontains"])
        if filter_params.get("user_id"):
            qs = qs.filter(user__user_id__icontains=filter_params["user_id"])
        if filter_params.get("voice_part"):
            qs = qs.filter(voice_part=filter_params["voice_part"])
        if filter_params.get("tier"):
            qs = qs.filter(tier=filter_params["tier"])
        if filter_params.get("status"):
            qs = qs.filter(status=filter_params["status"])
        if filter_params.get("birthday_month"):
            qs = qs.filter(birthday__month=int(filter_params["birthday_month"]))
        if filter_params.get("department__icontains"):
            qs = qs.filter(department__icontains=filter_params["department__icontains"])

        wb = build_export_workbook(sort_members(qs.select_related("user")))

        from io import BytesIO

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"members_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        task.result_file.save(
            filename,
            ContentFile(output.read()),
            save=False,
        )

        task.status = "COMPLETED"
        task.save(update_fields=["status", "result_file", "updated_at"])

        logger.info(f"Successfully completed member export task {task_id}")
        return {"status": "success", "task_id": task_id}

    except MemberExportTask.DoesNotExist:
        logger.error(f"Member export task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    except Exception as e:
        logger.exception(f"Error generating member export for task {task_id}: {e}")
        try:
            task = MemberExportTask.objects.get(task_id=task_id)
            task.status = "FAILED"
            task.error_message = f"导出失败: {str(e)}"
            task.save(update_fields=["status", "error_message", "updated_at"])
        except Exception as save_error:
            logger.exception(f"Error saving task failure status: {save_error}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_expired_member_export_tasks():
    """
    Periodic task to clean up expired member export tasks.
    Deletes task records and associated files that have expired.

    This should be run hourly via Celery Beat.
    """
    from .models import MemberExportTask

    now = timezone.now()
    expired_tasks = MemberExportTask.objects.filter(expires_at__lt=now)

    deleted_count = 0
    for task in expired_tasks:
        try:
            if task.result_file:
                try:
                    if os.path.exists(task.result_file.path):
                        os.remove(task.result_file.path)
                        logger.info(
                            f"Deleted file for expired member export task {task.task_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not delete file for member export task {task.task_id}: {e}"
                    )

            task.delete()
            deleted_count += 1

        except Exception as e:
            logger.exception(
                f"Error cleaning up member export task {task.task_id}: {e}"
            )

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired member export tasks")

    return {"deleted_count": deleted_count}
