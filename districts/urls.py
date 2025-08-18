from rest_framework.routers import SimpleRouter
from .views import DistrictViewSet, SafezoneViewSet

app_name = "districts"

router = SimpleRouter(trailing_slash=False)

router.register("", DistrictViewSet, basename="districts")
router.register("safezones", SafezoneViewSet, basename="safezones")

urlpatterns = router.urls