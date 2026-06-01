import os
import uuid
from datetime import timedelta
from typing import Optional
from urllib.parse import quote, urlencode

from django.core import signing
from django.db.models import Prefetch, Q, prefetch_related_objects
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
)
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.views.decorators.clickjacking import xframe_options_exempt

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsAuthenticatedReadAdminWrite
from apps.common.viewsets import EnvelopeModelViewSet
from apps.events.models import Event
from apps.personnel.models import Member, MemberStatus

from .constants import (
    SHEET_STREAM_TOKEN_MAX_AGE_SECONDS,
    SHEET_STREAM_TOKEN_SALT,
    WATERMARK_CACHE_VERSION,
)
from .models import Sheet, SheetDownloadLog, SheetDownloadTask
from .serializers import SheetDownloadTaskSerializer, SheetSerializer
from .sorting import sort_sheets
from .tasks import generate_watermarked_pdf_task


class SheetViewSet(EnvelopeModelViewSet):
    queryset = Sheet.objects.all().order_by("-upload_time")
    serializer_class = SheetSerializer
    lookup_field = "public_id"
    active_task_reuse_window = timedelta(minutes=5)
    permission_classes = [IsAuthenticatedReadAdminWrite]
    filterset_fields = {
        "title": ["exact", "icontains"],
        "composer": ["exact", "icontains"],
        "visible_to_alumni": ["exact"],
    }
    search_fields = ["title", "composer", "arranger"]

    def _prefetch_list_relations(self, items) -> None:
        prefetch_related_objects(
            items,
            Prefetch(
                "visible_events",
                queryset=Event.objects.order_by(
                    "-start_date", "-created_at", "public_id"
                ),
                to_attr="prefetched_visible_events",
            ),
            Prefetch(
                "visible_members",
                queryset=Member.objects.select_related("user"),
                to_attr="prefetched_visible_members",
            ),
        )

    def list(self, request, *args, **kwargs):  # type: ignore[override]
        """默认按曲名拼音排序，显式 ordering 参数仍交给 DRF 处理。"""
        if request.query_params.get("ordering"):
            qs = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(qs)
            if page is not None:
                self._prefetch_list_relations(page)
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            items = list(qs)
            self._prefetch_list_relations(items)
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)

        qs = self.filter_queryset(self.get_queryset())
        items = sort_sheets(qs)
        page = self.paginate_queryset(items)
        if page is not None:
            self._prefetch_list_relations(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        self._prefetch_list_relations(items)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if (
            user
            and getattr(user, "is_authenticated", False)
            and (
                getattr(user, "is_staff", False)
                or getattr(user, "role", "") in ("Admin", "SuperAdmin")
            )
        ):
            base_qs = qs
        else:
            member = getattr(user, "member", None) if user else None
            if member:
                member_status = getattr(member, "status", MemberStatus.ACTIVE)
                if member_status == MemberStatus.ALUMNI:
                    base_qs = qs.filter(
                        Q(visible_to_alumni=True)
                        | Q(visible_members=member)
                        | Q(visible_events__visible_to_alumni=True)
                        | Q(visible_events__participants=member)
                        | Q(visible_events__admins=member)
                    ).distinct()
                elif member_status == MemberStatus.INACTIVE:
                    base_qs = qs.none()
                else:
                    base_qs = qs.filter(
                        Q(visible_to_all=True)
                        | Q(visible_members=member)
                        | Q(visible_events__participants=member)
                        | Q(visible_events__admins=member)
                    ).distinct()
            else:
                base_qs = qs.filter(visible_to_all=True)

        event_id = self.request.query_params.get("event") if request else None
        if event_id:
            try:
                base_qs = base_qs.filter(visible_events__id=int(event_id)).distinct()
            except Exception:
                base_qs = base_qs.none()
        return base_qs.order_by("-upload_time")

    def _is_preview_request(self, request) -> bool:
        preview = request.query_params.get("preview")
        if preview is None:
            try:
                preview = request.data.get("preview")
            except Exception:
                preview = None
        return str(preview).lower() in {"1", "true", "yes", "on"}

    def _task_result_exists(self, task: SheetDownloadTask) -> bool:
        if not task.result_file or not task.result_file.name:
            return False
        try:
            return task.result_file.storage.exists(task.result_file.name)
        except Exception:
            return False

    def _task_uses_current_watermark_version(self, task: SheetDownloadTask) -> bool:
        return bool(
            task.result_file
            and task.result_file.name
            and WATERMARK_CACHE_VERSION in task.result_file.name
        )

    def _find_reusable_download_task(
        self, sheet: Sheet, user
    ) -> Optional[SheetDownloadTask]:
        now = timezone.now()
        base_qs = SheetDownloadTask.objects.filter(
            sheet=sheet,
            user=user,
            expires_at__gt=now,
        )

        source_updated_at = getattr(sheet, "updated_at", None) or getattr(
            sheet, "upload_time", None
        )
        if source_updated_at:
            base_qs = base_qs.filter(created_at__gte=source_updated_at)

        active_task = (
            base_qs.filter(
                status__in=["PENDING", "PROCESSING"],
                created_at__gte=now - self.active_task_reuse_window,
            )
            .order_by("-created_at")
            .first()
        )
        if active_task:
            return active_task

        completed_tasks = base_qs.filter(
            status="COMPLETED",
            result_file__isnull=False,
        ).order_by("-created_at")[:5]
        for task in completed_tasks:
            if self._task_uses_current_watermark_version(
                task
            ) and self._task_result_exists(task):
                return task

        return None

    def _task_stream_token(self, task: SheetDownloadTask) -> str:
        return signing.dumps(
            {"task_id": task.task_id, "user_pk": task.user_id},
            salt=SHEET_STREAM_TOKEN_SALT,
        )

    def _task_stream_url(self, task: SheetDownloadTask) -> str:
        query = urlencode(
            {
                "token": self._task_stream_token(task),
                "preview": "true",
            }
        )
        return f"/api/v1/sheets/task/{task.task_id}/stream/?{query}"

    def _task_data(self, task: SheetDownloadTask) -> dict:
        data = dict(SheetDownloadTaskSerializer(task).data)
        data["stream_url"] = self._task_stream_url(task)
        return data

    def _task_response(self, download_task: SheetDownloadTask, message: str):
        return JsonResponse(
            {
                "code": 202,
                "message": message,
                "data": self._task_data(download_task),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _watermark_text_for_user(self, user) -> str:
        user_id = getattr(user, "user_id", "")
        user_name = getattr(user, "name", "")
        return f"清华合唱-{user_name}-{user_id}"

    def _content_disposition(self, disposition: str, filename: str) -> str:
        encoded_filename = quote(smart_str(filename))
        return f"{disposition}; filename*=UTF-8''{encoded_filename}"

    def _mark_completed_task_file_missing(self, task: SheetDownloadTask) -> None:
        task.status = "FAILED"
        task.error_message = "生成文件不存在，请重新发起下载"
        task.save(update_fields=["status", "error_message", "updated_at"])

    def _parse_range_header(self, range_header: str, file_size: int):
        if not range_header or not range_header.startswith("bytes="):
            return None
        range_spec = range_header.removeprefix("bytes=").split(",", 1)[0].strip()
        if "-" not in range_spec:
            return None

        start_text, end_text = range_spec.split("-", 1)
        try:
            if start_text == "":
                suffix_length = int(end_text)
                if suffix_length <= 0:
                    return None
                start = max(file_size - suffix_length, 0)
                end = file_size - 1
            else:
                start = int(start_text)
                end = int(end_text) if end_text else file_size - 1
        except ValueError:
            return None

        if start < 0 or end < start or start >= file_size:
            return "invalid"
        return start, min(end, file_size - 1)

    def _iter_file_range(self, path: str, start: int, length: int, chunk_size=8192):
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    def _pdf_file_response(self, request, task: SheetDownloadTask, disposition: str):
        path = task.result_file.path
        file_size = os.path.getsize(path)
        filename = os.path.basename(task.result_file.name)
        range_result = self._parse_range_header(
            request.META.get("HTTP_RANGE", ""),
            file_size,
        )

        if range_result == "invalid":
            response = HttpResponse(
                status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
            )
            response["Content-Range"] = f"bytes */{file_size}"
            return response

        if range_result:
            start, end = range_result
            length = end - start + 1
            response = StreamingHttpResponse(
                self._iter_file_range(path, start, length),
                status=status.HTTP_206_PARTIAL_CONTENT,
                content_type="application/pdf",
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Length"] = str(length)
        else:
            response = FileResponse(open(path, "rb"), content_type="application/pdf")
            response["Content-Length"] = str(file_size)

        response["Accept-Ranges"] = "bytes"
        response["Content-Disposition"] = self._content_disposition(
            disposition,
            filename,
        )
        return response

    @action(
        detail=True,
        methods=["post"],
        url_path="download",
        permission_classes=[IsAuthenticated],
    )
    def download(self, request, public_id=None):  # type: ignore[override]
        """
        Initiate an async download task for watermarked PDF generation.

        Returns:
            202 Accepted with task_id and status
        """
        try:
            sheet = self.get_object()
        except Exception as e:  # pragma: no cover
            raise Http404 from e

        is_preview = self._is_preview_request(request)
        if not is_preview:
            SheetDownloadLog.objects.create(
                sheet=sheet,
                user=request.user,
                ip_address=request.META.get("REMOTE_ADDR", ""),
            )

        reusable_task = self._find_reusable_download_task(sheet, request.user)
        if reusable_task:
            return self._task_response(reusable_task, "任务已存在")

        task_id = str(uuid.uuid4())

        download_task = SheetDownloadTask.objects.create(
            task_id=task_id,
            sheet=sheet,
            user=request.user,
            status="PENDING",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        # 构造水印文本：清华合唱-姓名-学号
        user_id = getattr(request.user, "user_id", "")
        user_name = getattr(request.user, "name", "")
        wm_text = self._watermark_text_for_user(request.user)

        generate_watermarked_pdf_task.delay(
            task_id=task_id,
            sheet_id=sheet.id,
            user_id=user_id,
            user_name=user_name,
            watermark_text=wm_text,
        )

        return self._task_response(download_task, "任务已创建")

    @action(
        detail=False,
        methods=["get"],
        url_path="task/(?P<task_id>[^/.]+)",
        permission_classes=[IsAuthenticated],
    )
    def download_task(self, request, task_id=None):  # type: ignore[override]
        """
        Poll task status or retrieve the completed watermarked PDF.

        Query params:
            preview (bool): If true, set Content-Disposition to inline
            status_only (bool): If true, always return JSON task status

        Returns:
            - JSON with task status for status_only/pending/processing/failed
            - PDF response if completed and status_only is false
        """
        try:
            task = SheetDownloadTask.objects.get(task_id=task_id)
        except SheetDownloadTask.DoesNotExist:
            return JsonResponse(
                {
                    "code": 404,
                    "message": "任务不存在或已过期",
                    "data": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if task.user != request.user:
            return JsonResponse(
                {
                    "code": 403,
                    "message": "无权访问此任务",
                    "data": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if timezone.now() > task.expires_at:
            return JsonResponse(
                {
                    "code": 410,
                    "message": "任务已过期，请重新发起下载",
                    "data": {},
                },
                status=status.HTTP_410_GONE,
            )

        if task.status == "COMPLETED" and not self._task_result_exists(task):
            self._mark_completed_task_file_missing(task)

        if request.query_params.get("status_only", "false").lower() == "true":
            return JsonResponse(
                {
                    "code": 200,
                    "message": "任务状态",
                    "data": self._task_data(task),
                },
                status=status.HTTP_200_OK,
            )

        if task.status in ["PENDING", "PROCESSING"]:
            return JsonResponse(
                {
                    "code": 200,
                    "message": "任务处理中",
                    "data": self._task_data(task),
                },
                status=status.HTTP_200_OK,
            )

        if task.status == "FAILED":
            return JsonResponse(
                {
                    "code": 500,
                    "message": task.error_message or "任务处理失败",
                    "data": self._task_data(task),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if task.status == "COMPLETED" and task.result_file:
            is_preview = request.query_params.get("preview", "false").lower() == "true"
            disposition = "inline" if is_preview else "attachment"
            return self._pdf_file_response(request, task, disposition)

        return JsonResponse(
            {
                "code": 500,
                "message": "任务状态异常",
                "data": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @method_decorator(xframe_options_exempt)
    @action(
        detail=False,
        methods=["get"],
        url_path="task/(?P<task_id>[^/.]+)/stream",
        permission_classes=[AllowAny],
    )
    def download_task_stream(self, request, task_id=None):  # type: ignore[override]
        """
        Stream a completed task result using a short-lived signed URL.

        This is used by the browser PDF viewer, which cannot attach the normal
        Authorization header to an iframe request.
        """
        token = request.query_params.get("token", "")
        try:
            token_data = signing.loads(
                token,
                salt=SHEET_STREAM_TOKEN_SALT,
                max_age=SHEET_STREAM_TOKEN_MAX_AGE_SECONDS,
            )
        except signing.SignatureExpired:
            return JsonResponse(
                {
                    "code": 410,
                    "message": "预览链接已过期，请刷新页面",
                    "data": {},
                },
                status=status.HTTP_410_GONE,
            )
        except signing.BadSignature:
            return JsonResponse(
                {
                    "code": 403,
                    "message": "预览链接无效",
                    "data": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if token_data.get("task_id") != task_id:
            return JsonResponse(
                {
                    "code": 403,
                    "message": "预览链接无效",
                    "data": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            task = SheetDownloadTask.objects.get(task_id=task_id)
        except SheetDownloadTask.DoesNotExist:
            return JsonResponse(
                {
                    "code": 404,
                    "message": "任务不存在或已过期",
                    "data": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if str(task.user_id) != str(token_data.get("user_pk")):
            return JsonResponse(
                {
                    "code": 403,
                    "message": "预览链接无效",
                    "data": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if timezone.now() > task.expires_at:
            return JsonResponse(
                {
                    "code": 410,
                    "message": "任务已过期，请重新发起下载",
                    "data": {},
                },
                status=status.HTTP_410_GONE,
            )

        if task.status != "COMPLETED":
            return JsonResponse(
                {
                    "code": 409,
                    "message": "任务尚未完成",
                    "data": self._task_data(task),
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not self._task_result_exists(task):
            self._mark_completed_task_file_missing(task)
            return JsonResponse(
                {
                    "code": 500,
                    "message": task.error_message,
                    "data": self._task_data(task),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        is_preview = request.query_params.get("preview", "true").lower() == "true"
        disposition = "inline" if is_preview else "attachment"
        return self._pdf_file_response(request, task, disposition)
