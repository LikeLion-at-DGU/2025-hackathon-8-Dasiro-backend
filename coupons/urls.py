from rest_framework.routers import SimpleRouter
from .views import CouponViewSet

app_name = "coupons"

router = SimpleRouter(trailing_slash=False)
router.register("", CouponViewSet, basename="coupon")

urlpatterns = router.urls