import mimetypes
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import quote as urlquote

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.utils.encoding import smart_str

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import SystemAnnouncement
from .permissions import IsAuthenticatedReadAdminWrite
from .serializers import SystemAnnouncementSerializer
from .utils import verify_signed_token
from .viewsets import EnvelopeModelViewSet


def standard_response(
    code: int = 200, message: str = "success", data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if data is None:
        data = {}
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def health(request: HttpRequest) -> JsonResponse:
    """简单健康检查端点。

    返回包含状态信息的标准响应信封。
    """
    body = standard_response(200, "success", {"status": "ok"})
    return JsonResponse(body, status=200)


class SystemAnnouncementViewSet(EnvelopeModelViewSet):
    """系统公告的增删改查。

    - 已登录用户可读取公告列表和详情
    - 仅 Admin、SuperAdmin 或 staff 可写入
    """

    queryset = SystemAnnouncement.objects.all().order_by("-publish_time", "-id")
    serializer_class = SystemAnnouncementSerializer
    permission_classes = [IsAuthenticatedReadAdminWrite]


@api_view(["GET"])
@permission_classes([AllowAny])
def protected_media(request: HttpRequest) -> HttpResponse:
    """通过鉴权和签名令牌校验后返回媒体文件。

    用法：GET /api/v1/common/media/?path=<urlencoded relative path>&token=<signed>
    """
    rel_path = request.GET.get("path") or ""
    token = request.GET.get("token") or ""
    norm_rel = os.path.normpath(rel_path).lstrip(os.sep)
    abs_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, norm_rel))
    media_root_abs = os.path.abspath(str(settings.MEDIA_ROOT))
    if not abs_path.startswith(media_root_abs + os.sep) and abs_path != media_root_abs:
        raise Http404
    if not verify_signed_token(norm_rel, token):
        return JsonResponse(
            {
                "code": 403,
                "message": "无效或过期的下载链接，请刷新原页面重试",
                "data": {},
            },
            status=403,
        )
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        raise Http404
    base_name = os.path.basename(abs_path)
    m = re.match(r"^(\d{14})_(.+)$", base_name)
    download_name = m.group(2) if m else base_name
    guessed, _ = mimetypes.guess_type(download_name)
    content_type = guessed or "application/octet-stream"
    response = FileResponse(open(abs_path, "rb"), content_type=content_type)
    ascii_fallback = re.sub(r"[^A-Za-z0-9._-]+", "_", download_name)
    utf8_encoded = urlquote(download_name)
    response["Content-Disposition"] = (
        f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_encoded}"
    )
    return response
