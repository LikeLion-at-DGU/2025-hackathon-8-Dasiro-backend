from django.db import models

class CitizenReport(models.Model):
    class RiskGrade(models.TextChoices):
        G1 = 'G1', '1등급'
        G2 = 'G2', '2등급'
        G3 = 'G3', '3등급'
        G4 = 'G4', '4등급'
        G5 = 'G5', '5등급'

    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # 'received','analyzing','done'
    risk_score = models.IntegerField(blank=True, null=True)
    risk_grade = models.CharField(max_length=2, choices=RiskGrade.choices, blank=True, null=True)
    advice_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.address} ({self.status})"


class CitizenReportImage(models.Model):
    report = models.ForeignKey(CitizenReport, on_delete=models.CASCADE, related_name="images")
    image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class BotMessage(models.Model):
    report = models.ForeignKey(CitizenReport, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10)  # 'user','bot'
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)