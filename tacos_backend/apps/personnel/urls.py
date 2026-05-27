from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    AlumniProfileViewSet,
    InstructorViewSet,
    MemberTitleViewSet,
    MemberViewSet,
    TitleViewSet,
)

router = DefaultRouter()
router.register(r"members", MemberViewSet, basename="member")
router.register(r"alumni-profiles", AlumniProfileViewSet, basename="alumni-profile")
router.register(r"instructors", InstructorViewSet, basename="instructor")
router.register(r"titles", TitleViewSet, basename="title")
router.register(r"member-titles", MemberTitleViewSet, basename="member-title")

urlpatterns = router.urls
