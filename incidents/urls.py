from rest_framework.routers import SimpleRouter
from .views import RecoveryIncidentViewSet

app_name = "incidents"

router = SimpleRouter(trailing_slash=False)
router.register("", RecoveryIncidentViewSet, basename="incidents")

urlpatterns = router.urls