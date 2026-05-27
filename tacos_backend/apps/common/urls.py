from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views
from .views import SystemAnnouncementViewSet, health

router = DefaultRouter()
router.register(
    r"announcements", SystemAnnouncementViewSet, basename="system-announcements"
)

urlpatterns = [
    path("health/", health, name="health"),
    path("media/", views.protected_media, name="protected_media"),
    path("", include(router.urls)),
]
