from django.db import models

class CitizenReport(models.Model):
    class ReportStatus(models.TextChoices):
        RECEIVED = "received", "접수됨"
        ANALYZING = "analyzing", "분석중"
        DONE = "done", "분석완료"

    text = models.TextField()  # 제보 텍스트
    lat = models.DecimalField(max_digits=20, decimal_places=10)  # 위도
    lng = models.DecimalField(max_digits=20, decimal_places=10)  # 경도
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.RECEIVED)
    risk_score = models.IntegerField(blank=True, null=True)  # 0~100

    def __str__(self):
        return f"Report #{self.id} ({self.status})"


class CitizenReportImage(models.Model):
    report = models.ForeignKey(CitizenReport, on_delete=models.CASCADE, related_name="images")
    image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class BotMessage(models.Model):
    report = models.ForeignKey(CitizenReport, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10)  # 'user','bot'
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)