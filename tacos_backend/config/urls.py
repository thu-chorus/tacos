from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/common/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.personnel.urls")),
    path("api/v1/", include("apps.sheet_music.urls")),
    path("api/v1/", include("apps.events.urls")),
]

# 即使在开发环境也不直接托管媒体文件，避免绕过鉴权
