from rest_framework.routers import SimpleRouter
from .views import KakaoProxyViewSet

app_name = "routes"

router = SimpleRouter(trailing_slash=False)
router.register("", KakaoProxyViewSet, basename="proxy")

urlpatterns = router.urls