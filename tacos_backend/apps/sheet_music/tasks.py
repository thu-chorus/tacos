"""
Celery tasks for sheet music operations.

Handles asynchronous watermark generation and cleanup tasks.
"""

import logging
import os
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_watermarked_pdf_task(
    self, task_id: str, sheet_id: int, user_id: str, user_name: str, watermark_text: str
):
    """
    Generate a watermarked PDF for a sheet download task.

    Args:
        task_id: The unique task identifier
        sheet_id: The sheet's database ID
        user_id: User's ID for the watermark
        user_name: User's name for the watermark
        watermark_text: Full watermark text to apply

    Returns:
        dict: Task result with status and message
    """
    from .constants import WATERMARK_CACHE_VERSION
    from .models import Sheet, SheetDownloadTask
    from .watermark import add_text_watermark_to_pdf

    try:
        task = SheetDownloadTask.objects.get(task_id=task_id)
        task.status = "PROCESSING"
        task.save(update_fields=["status", "updated_at"])

        sheet = Sheet.objects.get(id=sheet_id)

        logger.info(f"Reading PDF file for sheet {sheet_id}")
        with open(sheet.original_file.path, "rb") as f:
            src_bytes = f.read()

        logger.info(f"Applying watermark for task {task_id}")
        watermarked_bytes = add_text_watermark_to_pdf(src_bytes, watermark_text)

        filename = f"{WATERMARK_CACHE_VERSION}_{sheet.title}_{user_id}_{user_name}.pdf"
        task.result_file.save(
            filename,
            ContentFile(watermarked_bytes),
            save=False,
        )

        task.status = "COMPLETED"
        task.save(update_fields=["status", "result_file", "updated_at"])

        logger.info(f"Successfully completed task {task_id}")
        return {"status": "success", "task_id": task_id}

    except SheetDownloadTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    except Sheet.DoesNotExist:
        logger.error(f"Sheet {sheet_id} not found for task {task_id}")
        try:
            task = SheetDownloadTask.objects.get(task_id=task_id)
            task.status = "FAILED"
            task.error_message = "乐谱不存在"
            task.save(update_fields=["status", "error_message", "updated_at"])
        except Exception:
            pass
        return {"status": "error", "message": "Sheet not found"}

    except Exception as e:
        logger.exception(f"Error generating watermarked PDF for task {task_id}: {e}")
        try:
            task = SheetDownloadTask.objects.get(task_id=task_id)
            task.status = "FAILED"
            task.error_message = f"生成水印失败: {str(e)}"
            task.save(update_fields=["status", "error_message", "updated_at"])
        except Exception as save_error:
            logger.exception(f"Error saving task failure status: {save_error}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_expired_download_tasks():
    """
    Periodic task to clean up expired download tasks.
    Deletes task records and associated files that have expired.

    This should be run hourly via Celery Beat.
    """
    from .models import SheetDownloadTask

    now = timezone.now()
    expired_tasks = SheetDownloadTask.objects.filter(expires_at__lt=now)

    deleted_count = 0
    for task in expired_tasks:
        try:
            if task.result_file:
                try:
                    if os.path.exists(task.result_file.path):
                        os.remove(task.result_file.path)
                        logger.info(f"Deleted file for expired task {task.task_id}")
                except Exception as e:
                    logger.warning(
                        f"Could not delete file for task {task.task_id}: {e}"
                    )

            task.delete()
            deleted_count += 1

        except Exception as e:
            logger.exception(f"Error cleaning up task {task.task_id}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired download tasks")

    return {"deleted_count": deleted_count}
