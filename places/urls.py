from rest_framework.routers import SimpleRouter
from .views import PlaceViewSet

app_name = "places"

router = SimpleRouter(trailing_slash=False)
router.register("", PlaceViewSet, basename="places")

urlpatterns = router.urls