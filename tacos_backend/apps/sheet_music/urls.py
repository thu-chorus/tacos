from rest_framework.routers import DefaultRouter

from .views import SheetViewSet

router = DefaultRouter()
router.register(r"sheets", SheetViewSet, basename="sheet")

urlpatterns = router.urls
