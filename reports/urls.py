from rest_framework.routers import DefaultRouter
from .views import CitizenReportViewSet

app_name = "reports"

router = DefaultRouter()
router.register("", CitizenReportViewSet, basename="reports")

urlpatterns = router.urls