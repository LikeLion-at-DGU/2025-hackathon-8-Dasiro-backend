from django.db import models

class RecoveryIncident(models.Model):
    class RecoveryStatus(models.TextChoices):
        UNDER_REPAIR = 'UNDER_REPAIR', '복구중'
        TEMP_REPAIRED = 'TEMP_REPAIRED', '임시복구'
        RECOVERED = 'RECOVERED', '복구완료'

    occurred_at = models.DateField()
    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=20, decimal_places=15)
    lng = models.DecimalField(max_digits=20, decimal_places=15)
    cause = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=RecoveryStatus.choices)
    note = models.TextField(blank=True, null=True)

    # 이미지 테이블 제거, 사고/현장 대표 이미지 1장만 (복구중·임시복구 상태에서만 사용)
    image_url = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.address} ({self.get_status_display()})"