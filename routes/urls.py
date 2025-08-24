from rest_framework.routers import SimpleRouter
from .views import KakaoProxyViewSet, ORSProxyViewSet

app_name = "routes"

router = SimpleRouter(trailing_slash=False)
router.register("kakao", KakaoProxyViewSet, basename="kakao-proxy")
router.register("ors", ORSProxyViewSet, basename="ors-proxy")

urlpatterns = router.urls