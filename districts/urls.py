from rest_framework.routers import SimpleRouter
from .views import *

app_name = "districts"

router = SimpleRouter(trailing_slash=False)
router.register("", DistrictViewSet, basename="districts")

urlpatterns = router.urls