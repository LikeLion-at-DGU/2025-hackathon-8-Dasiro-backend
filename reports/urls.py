from rest_framework.routers import SimpleRouter
from django.urls import path
from .views import CitizenReportViewSet, S3PresignedURLView

app_name = "reports"

router = SimpleRouter(trailing_slash=False)
router.register("", CitizenReportViewSet, basename="reports")

urlpatterns = [
    path("s3/presigned-url/", S3PresignedURLView.as_view(), name="s3_presigned_url"),
]

urlpatterns += router.urls