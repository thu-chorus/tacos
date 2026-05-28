"""
Celery tasks for event-related operations.

Handles asynchronous export generation and cleanup tasks.
"""

import logging
import os
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_assignment_export_task(
    self, task_id: str, assignment_id: int, filter_params: dict
):
    """
    Generate Excel export for assignment submissions.

    Args:
        task_id: The unique task identifier
        assignment_id: The assignment's database ID
        filter_params: Filter parameters (name, user_id, voice_part, only_submitted)

    Returns:
        dict: Task result with status and message
    """
    from apps.personnel.models import Member
    from apps.personnel.sorting import sort_members

    from .models import Assignment, AssignmentExportTask, AssignmentSubmission

    try:
        task = AssignmentExportTask.objects.get(task_id=task_id)
        task.status = "PROCESSING"
        task.save(update_fields=["status", "updated_at"])

        assignment = Assignment.objects.get(id=assignment_id)
        event = assignment.event

        name = filter_params.get("name")
        user_id = filter_params.get("user_id")
        voice_part = filter_params.get("voice_part")
        only_submitted = filter_params.get("only_submitted", False)

        logger.info(f"Generating export for assignment {assignment_id}")

        members_qs = (
            Member.objects.filter(Q(events=event) | Q(managed_events=event))
            .select_related("user")
            .distinct()
        )
        if name:
            members_qs = members_qs.filter(name__icontains=name)
        if user_id:
            members_qs = members_qs.filter(user__user_id__icontains=user_id)
        if voice_part:
            members_qs = members_qs.filter(voice_part=voice_part)

        subs_qs = AssignmentSubmission.objects.filter(
            assignment=assignment, member__in=members_qs
        ).prefetch_related("attachments")
        subs_map: dict[int, AssignmentSubmission] = {
            int(s.member_id): s for s in subs_qs
        }

        if only_submitted:
            members_qs = members_qs.filter(id__in=list(subs_map.keys()))

        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "成绩"
        ws.append(
            [
                "学号",
                "姓名",
                "声部",
                "状态",
                "作业文字",
                "有无附件",
                "分数",
                "评语",
                "提交时间",
                "批改时间",
            ]
        )

        for m in sort_members(members_qs):
            sub = subs_map.get(int(m.id))
            if sub is None:
                status = "未提交"
                text = ""
                has_att = "无"
                score = ""
                comment = ""
                submitted_at = ""
                graded_at = ""
            else:
                status = "已批改" if getattr(sub, "graded_at", None) else "未批改"
                text = getattr(sub, "text", "")
                has_att = (
                    "有" if getattr(sub, "attachments", []).all().exists() else "无"
                )
                score = getattr(sub, "graded_score", "")
                comment = getattr(sub, "graded_comment", "")
                submitted_at_obj = getattr(sub, "submitted_at", None)
                submitted_at = (
                    submitted_at_obj.strftime("%Y-%m-%d %H:%M:%S")
                    if submitted_at_obj
                    else ""
                )
                graded_at_obj = getattr(sub, "graded_at", None)
                graded_at = (
                    graded_at_obj.strftime("%Y-%m-%d %H:%M:%S") if graded_at_obj else ""
                )
            ws.append(
                [
                    getattr(getattr(m, "user", None), "user_id", ""),
                    getattr(m, "name", ""),
                    getattr(m, "voice_part", ""),
                    status,
                    text,
                    has_att,
                    score if score is not None else "",
                    comment,
                    submitted_at,
                    graded_at,
                ]
            )

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"作业成绩_{assignment.title}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        task.result_file.save(
            filename,
            ContentFile(output.read()),
            save=False,
        )

        task.status = "COMPLETED"
        task.save(update_fields=["status", "result_file", "updated_at"])

        logger.info(f"Successfully completed export task {task_id}")
        return {"status": "success", "task_id": task_id}

    except AssignmentExportTask.DoesNotExist:
        logger.error(f"Export task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    except Assignment.DoesNotExist:
        logger.error(f"Assignment {assignment_id} not found for task {task_id}")
        try:
            task = AssignmentExportTask.objects.get(task_id=task_id)
            task.status = "FAILED"
            task.error_message = "作业不存在"
            task.save(update_fields=["status", "error_message", "updated_at"])
        except Exception:
            pass
        return {"status": "error", "message": "Assignment not found"}

    except Exception as e:
        logger.exception(f"Error generating export for task {task_id}: {e}")
        try:
            task = AssignmentExportTask.objects.get(task_id=task_id)
            task.status = "FAILED"
            task.error_message = f"导出失败: {str(e)}"
            task.save(update_fields=["status", "error_message", "updated_at"])
        except Exception as save_error:
            logger.exception(f"Error saving task failure status: {save_error}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_expired_export_tasks():
    """
    Periodic task to clean up expired export tasks.
    Deletes task records and associated files that have expired.

    This should be run hourly via Celery Beat.
    """
    from .models import AssignmentExportTask

    now = timezone.now()
    expired_tasks = AssignmentExportTask.objects.filter(expires_at__lt=now)

    deleted_count = 0
    for task in expired_tasks:
        try:
            if task.result_file:
                try:
                    if os.path.exists(task.result_file.path):
                        os.remove(task.result_file.path)
                        logger.info(
                            f"Deleted file for expired export task {task.task_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not delete file for export task {task.task_id}: {e}"
                    )

            task.delete()
            deleted_count += 1

        except Exception as e:
            logger.exception(f"Error cleaning up export task {task.task_id}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired export tasks")

    return {"deleted_count": deleted_count}
