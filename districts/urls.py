from rest_framework.routers import SimpleRouter
from .views import *

app_name = "districts"

router = SimpleRouter(trailing_slash=False)

router.register("", DistrictViewSet, basename="districts")
router.register("safezones", SafezoneViewSet, basename="safezones")
router.register("risk", DistrictRiskViewSet, basename="districts-risk")

urlpatterns = router.urls