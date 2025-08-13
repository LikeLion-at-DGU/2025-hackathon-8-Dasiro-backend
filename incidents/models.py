from django.db import models

class RecoveryIncident(models.Model):
    class RecoveryStatus(models.TextChoices):
        UNDER_REPAIR = 'UNDER_REPAIR', '복구중'
        TEMP_REPAIRED = 'TEMP_REPAIRED', '임시복구'
        RECOVERED = 'RECOVERED', '복구완료'

    occurred_at = models.DateField()
    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    cause = models.CharField(max_length=255)
    method = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=RecoveryStatus.choices)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.address} ({self.get_status_display()})"


class RecoveryIncidentImage(models.Model):
    incident = models.ForeignKey(RecoveryIncident, on_delete=models.CASCADE, related_name="images")
    image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.incident}"