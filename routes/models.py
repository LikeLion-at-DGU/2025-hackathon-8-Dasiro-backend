from django.db import models

class RouteLog(models.Model):
    origin_lat = models.DecimalField(max_digits=10, decimal_places=7)
    origin_lng = models.DecimalField(max_digits=10, decimal_places=7)
    dest_lat = models.DecimalField(max_digits=10, decimal_places=7)
    dest_lng = models.DecimalField(max_digits=10, decimal_places=7)
    mode = models.CharField(max_length=10)  # 'walk','car'
    provider = models.CharField(max_length=10)  # 'kakao'
    duration_sec = models.IntegerField()
    distance_m = models.IntegerField()
    raw_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.mode} {self.duration_sec}s {self.distance_m}m"