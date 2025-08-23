from rest_framework.routers import SimpleRouter
from .views import CitizenReportViewSet

app_name = "reports"

router = SimpleRouter(trailing_slash=False)
router.register("", CitizenReportViewSet, basename="reports")

urlpatterns = router.urls