from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from PIL import Image, UnidentifiedImageError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from apps.common.utils import envelope_error
from apps.common.viewsets import EnvelopeModelViewSet

from .filters import InstructorFilter, MemberFilter
from .importers import build_export_response, build_template_response, parse_bulk_file
from .models import AlumniProfile, Instructor, Member, MemberStatus, MemberTitle, Title
from .permissions import IsAdmin, IsAdminOrSelfReadOnly, IsSelfOrAdmin
from .serializers import (
    AlumniProfileSerializer,
    InstructorSerializer,
    MemberSerializer,
    MemberTitleSerializer,
    TitleSerializer,
)
from .sorting import member_sort_key, sort_instructors, sort_members
from .tasks import update_birthday_title_for_month


class MemberViewSet(EnvelopeModelViewSet):
    queryset = Member.objects.select_related("user").all()
    serializer_class = MemberSerializer
    filterset_class = MemberFilter
    search_fields = ["name"]
    permission_classes = [IsAdminOrSelfReadOnly]
    lookup_field = "public_id"

    def get_permissions(self):  # type: ignore[override]
        """更新成员时使用本人或管理员权限，其余操作使用默认成员权限。"""
        if self.action in ("update", "partial_update", "avatar"):
            return [IsSelfOrAdmin()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):  # type: ignore[override]
        """先对完整成员集排序，再执行分页。

        默认顺序：状态（活跃 -> 校友 -> 非活跃）-> 队别 -> 声部 -> 姓名拼音 -> 学号。
        """
        qs = self.filter_queryset(self.get_queryset())

        items = sort_members(qs)

        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    def get_object(self):  # type: ignore[override]
        return super().get_object()

    @action(
        methods=["get"],
        detail=False,
        url_path="stats",
        permission_classes=[IsAuthenticated],
    )
    def stats(self, request):
        from apps.common.models import SystemStats

        total = SystemStats.get_solo().total_members
        return Response({"total_members": total})

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request, public_id=None):
        """上传或删除成员头像。"""
        member: Member = self.get_object()

        if request.method == "DELETE":
            old_name = getattr(member.avatar, "name", "")
            member.avatar = None
            member.save(update_fields=["avatar", "updated_at"])
            if old_name:
                default_storage.delete(old_name)
            return Response(self.get_serializer(member).data)

        upload = request.FILES.get("avatar") or request.FILES.get("file")
        if not upload:
            return Response(envelope_error(422, "请上传头像文件", {}), status=422)

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        content_type = getattr(upload, "content_type", "") or ""
        if content_type and content_type not in allowed_types:
            return Response(
                envelope_error(422, "仅支持 JPG/PNG/WebP 头像", {}), status=422
            )

        max_size = 2 * 1024 * 1024
        if getattr(upload, "size", 0) > max_size:
            return Response(envelope_error(422, "头像大小不能超过2MB", {}), status=422)

        try:
            image = Image.open(upload)
            image.verify()
        except (UnidentifiedImageError, OSError):
            return Response(envelope_error(422, "头像文件不是有效图片", {}), status=422)
        finally:
            try:
                upload.seek(0)
            except Exception:
                pass

        old_name = getattr(member.avatar, "name", "")
        member.avatar = upload
        member.save(update_fields=["avatar", "updated_at"])
        if old_name and old_name != getattr(member.avatar, "name", ""):
            default_storage.delete(old_name)
        return Response(self.get_serializer(member).data)

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        except ValidationError as e:

            def to_plain(err):
                if isinstance(err, dict):
                    return {k: to_plain(v) for k, v in err.items()}
                if isinstance(err, list):
                    return [str(x) for x in err]
                return str(err)

            details = to_plain(e.detail)
            if isinstance(details, dict):
                parts = []
                for k, v in details.items():
                    if isinstance(v, list):
                        parts.append(f"{k}: {'; '.join(v)}")
                    else:
                        parts.append(f"{k}: {v}")
                message = " | ".join(parts) or "数据验证失败"
            else:
                message = str(details) or "数据验证失败"
            return Response(
                envelope_error(
                    422, message, details if isinstance(details, dict) else {}
                ),
                status=422,
            )

    @action(
        methods=["post"],
        detail=False,
        url_path="bulk-import",
        permission_classes=[IsAdmin],
    )
    def bulk_import(self, request):
        """批量导入队员。支持 CSV/.xlsx。逐行校验，成功的立即创建，失败的返回错误。

        响应结构：
        {
          code, message, data: {
            total, success, failed, rows: [ { index, user_id, status, errors } ]
          }
        }
        """
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                envelope_error(400, "请上传文件，字段名为 file"), status=400
            )

        try:
            # 覆盖导入时保留目标成员非空字段
            rows, fmt = parse_bulk_file(upload.name, upload.read(), annotate_empty=True)
        except ValueError as e:
            return Response(envelope_error(400, str(e)), status=400)
        except Exception:
            return Response(
                envelope_error(
                    400, "无法解析文件，请确认为CSV或.xlsx格式，且编码为UTF-8"
                ),
                status=400,
            )

        # 是否覆盖已存在队员信息（按学号）
        raw_override = request.data.get("override")
        if isinstance(raw_override, bool):
            override = raw_override
        else:
            s = str(raw_override).strip().lower() if raw_override is not None else ""
            override = s in {"1", "true", "yes", "y", "on", "是"}

        results = []
        success = 0
        failed = 0

        # 每行独立提交，避免单行错误影响其他行
        for idx, payload in enumerate(
            rows, start=2
        ):  # 表头在第 1 行，数据从第 2 行开始
            # 跳过全空行
            if not any(v for v in payload.values()):
                continue
            user_id = (payload or {}).get("user_id") or (payload or {}).get(
                "学号 user_id"
            )
            # 当开启 override 时，如果存在相同学号，执行更新而非创建
            if override and user_id:
                try:
                    instance = Member.objects.get(user__user_id=str(user_id))
                except Member.DoesNotExist:
                    instance = None
            else:
                instance = None

            try:
                if instance is not None:
                    # 过滤掉空值字段，避免覆盖已存在的非空属性
                    empty_fields = set(payload.pop("__empty_fields", []) or [])
                    filtered_payload = {}
                    for k, v in payload.items():
                        if k in {"__empty_fields"}:
                            continue
                        if k in empty_fields:
                            # 跳过本次导入中为空的字段
                            continue
                        # 处理键名：如果格式为"中文 英文"，则取英文部分
                        key = k.split(" ")[1] if " " in k else k
                        # 处理值：布尔值转换
                        value = v
                        if isinstance(v, str):
                            v_lower = v.lower()
                            if v_lower in ["1", "true", "yes", "on", "是"]:
                                value = True
                            elif v_lower in ["0", "false", "no", "off", "否"]:
                                value = False
                        filtered_payload[key] = value
                    serializer = self.get_serializer(
                        instance=instance, data=filtered_payload, partial=True
                    )
                else:
                    serializer = self.get_serializer(data=payload)
                serializer.is_valid(raise_exception=True)
                with transaction.atomic():
                    serializer.save()
                results.append(
                    {
                        "index": idx,
                        "user_id": payload.get("user_id", ""),
                        "status": "updated" if instance is not None else "created",
                        "errors": [],
                    }
                )
                success += 1
            except ValidationError as e:

                def to_plain(err):
                    if isinstance(err, dict):
                        return {k: to_plain(v) for k, v in err.items()}
                    if isinstance(err, list):
                        return [str(x) for x in err]
                    return str(err)

                details = to_plain(e.detail)
                if isinstance(details, dict):
                    messages = []
                    for k, v in details.items():
                        if isinstance(v, list):
                            messages.append(f"{k}: {'; '.join(v)}")
                        else:
                            messages.append(f"{k}: {v}")
                else:
                    messages = [str(details)]
                results.append(
                    {
                        "index": idx,
                        "user_id": payload.get("user_id", ""),
                        "status": "error",
                        "errors": messages,
                    }
                )
                failed += 1

        total = success + failed
        try:
            from .signals import rebuild_total_members

            rebuild_total_members()
        except Exception:
            pass

        return Response(
            {
                "total": total,
                "success": success,
                "failed": failed,
                "rows": results,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["get"],
        detail=False,
        url_path="bulk-template",
        permission_classes=[IsAdmin],
    )
    def bulk_template(self, request):
        """下载批量导入模板（.xlsx）。"""
        resp: HttpResponse = build_template_response()
        return resp

    @action(
        methods=["post"], detail=False, url_path="export", permission_classes=[IsAdmin]
    )
    def export(self, request):
        """
        发起异步导出队员信息表格任务。
        返回 task_id 用于轮询任务状态。
        """
        import uuid

        from .models import MemberExportTask
        from .serializers import MemberExportTaskSerializer
        from .tasks import generate_member_export_task

        filter_params = {
            "name__icontains": request.data.get("name__icontains")
            or request.query_params.get("name__icontains"),
            "user_id": request.data.get("user_id")
            or request.query_params.get("user_id"),
            "voice_part": request.data.get("voice_part")
            or request.query_params.get("voice_part"),
            "tier": request.data.get("tier") or request.query_params.get("tier"),
            "status": request.data.get("status") or request.query_params.get("status"),
            "birthday_month": request.data.get("birthday_month")
            or request.query_params.get("birthday_month"),
            # 支持严格匹配参数
            "department": request.data.get("department")
            or request.query_params.get("department"),
            # 兼容旧的模糊匹配参数
            "department__icontains": request.data.get("department__icontains")
            or request.query_params.get("department__icontains"),
        }
        filter_params = {k: v for k, v in filter_params.items() if v is not None}

        task_id = str(uuid.uuid4())
        task = MemberExportTask.objects.create(
            task_id=task_id,
            user=request.user,
            filter_params=filter_params,
            status="PENDING",
        )

        generate_member_export_task.delay(
            task_id=task_id,
            filter_params=filter_params,
        )

        serializer = MemberExportTaskSerializer(task)
        return Response(
            {"task_id": task_id, **serializer.data},
            status=202,
        )

    @action(
        methods=["get"],
        detail=False,
        url_path="export-task/(?P<task_id>[^/.]+)",
        permission_classes=[IsAdmin],
    )
    def export_task(self, request, task_id=None):
        """
        获取导出任务状态或下载结果。
        返回 JSON（处理中）或文件（已完成）。
        """
        import os

        from django.http import FileResponse
        from django.utils.encoding import smart_str

        from .models import MemberExportTask
        from .serializers import MemberExportTaskSerializer

        try:
            task = MemberExportTask.objects.get(task_id=task_id, user=request.user)
        except MemberExportTask.DoesNotExist:
            return Response(
                {"error": "Export task not found"},
                status=404,
            )

        from django.utils import timezone

        if task.expires_at < timezone.now():
            return Response(
                {"error": "Export task expired, please re-initiate export"},
                status=410,
            )

        if task.status == "COMPLETED" and task.result_file:
            try:
                response = FileResponse(
                    task.result_file.open("rb"),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                filename = os.path.basename(task.result_file.name)
                response["Content-Disposition"] = (
                    f'attachment; filename="{smart_str(filename)}"'
                )
                return response
            except Exception as e:
                return Response(
                    {"error": f"Failed to read export file: {e}"},
                    status=500,
                )

        serializer = MemberExportTaskSerializer(task)
        return Response(serializer.data, status=200)


class InstructorViewSet(EnvelopeModelViewSet):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    filterset_class = InstructorFilter
    search_fields = ["name"]
    permission_classes = [IsAdmin]
    lookup_field = "public_id"

    def list(self, request, *args, **kwargs):  # type: ignore[override]
        """默认按教师姓名拼音排序，显式 ordering 参数仍交给 DRF 处理。"""
        if request.query_params.get("ordering"):
            return super().list(request, *args, **kwargs)

        qs = self.filter_queryset(self.get_queryset())
        items = sort_instructors(qs)
        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class AlumniProfileViewSet(EnvelopeModelViewSet):
    queryset = (
        AlumniProfile.objects.select_related("member", "member__user")
        .all()
        .order_by("member__name")
    )
    serializer_class = AlumniProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):  # type: ignore[override]
        if self.action == "me":
            return [IsAuthenticated()]
        if self.action in ("list", "create", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        if IsAdmin().has_permission(self.request, self):
            return qs
        member = getattr(getattr(self.request, "user", None), "member", None)
        if member:
            return qs.filter(member=member)
        return qs.none()

    def list(self, request, *args, **kwargs):  # type: ignore[override]
        qs = self.filter_queryset(self.get_queryset())
        items = sorted(list(qs), key=lambda profile: member_sort_key(profile.member))
        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer: AlumniProfileSerializer) -> None:  # type: ignore[override]
        serializer.save()

    @action(
        methods=["get", "put", "patch"],
        detail=False,
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        member = getattr(request.user, "member", None)
        if not member:
            return Response(
                envelope_error(422, "当前用户没有成员档案", {}),
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if getattr(member, "status", "") != MemberStatus.ALUMNI:
            return Response(
                envelope_error(403, "仅校友成员可以维护校友信息", {}),
                status=status.HTTP_403_FORBIDDEN,
            )

        profile, _ = AlumniProfile.objects.get_or_create(member=member)
        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TitleViewSet(EnvelopeModelViewSet):
    queryset = Title.objects.all().order_by("-created_at")
    serializer_class = TitleSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["post"], url_path="update-birthday-titles")
    def update_birthday_titles(self, request):
        """
        手动触发更新生日称号
        POST /api/v1/personnel/titles/update-birthday-titles/

        Body参数:
        - title_name: 称号名称，默认"本月寿星"
        - month: 目标月份(1-12)，不指定则使用当前月份
        """
        title_name = request.data.get("title_name", "本月寿星")
        month = request.data.get("month")

        if month is None:
            month = timezone.localdate().month

        try:
            month = int(month)
            if not (1 <= month <= 12):
                return Response(
                    envelope_error(400, "月份必须在1-12之间"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                envelope_error(400, "月份必须是有效的数字"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 检查称号是否存在
            if not Title.objects.filter(name__icontains=title_name).exists():
                return Response(
                    envelope_error(404, f'称号 "{title_name}" 不存在'),
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 执行更新
            update_birthday_title_for_month(month, title_name)

            # 返回更新结果
            updated_members = Member.objects.filter(
                birthday__month=month, birthday__isnull=False
            ).count()

            return Response(
                {
                    "code": 200,
                    "message": "生日称号更新成功",
                    "data": {
                        "title_name": title_name,
                        "month": month,
                        "updated_count": updated_members,
                    },
                }
            )

        except Exception as e:
            return Response(
                envelope_error(500, f"更新失败: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MemberTitleViewSet(EnvelopeModelViewSet):
    queryset = (
        MemberTitle.objects.select_related("member", "title")
        .all()
        .order_by("-awarded_at")
    )
    serializer_class = MemberTitleSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        member_id = self.request.query_params.get("member_id")
        title_id = self.request.query_params.get("title_id")
        title_name = self.request.query_params.get("title_name")
        if member_id:
            # 模糊匹配学号
            qs = qs.filter(member__user__user_id__icontains=str(member_id))
        if title_id:
            qs = qs.filter(title_id=title_id)
        if title_name:
            # 模糊匹配称号名
            qs = qs.filter(title__name__icontains=title_name)
        return qs
