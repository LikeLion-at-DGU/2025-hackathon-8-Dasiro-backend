from django.db import models
from incidents.models import RecoveryIncident

class Place(models.Model):
    class PlaceCategory(models.TextChoices):
        FOOD = 'FOOD', '음식점'
        CAFE = 'CAFE', '카페'
        CONVENIENCE = 'CONVENIENCE', '편의점'
        OTHER = 'OTHER', '기타'

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=PlaceCategory.choices)
    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    main_image_url = models.TextField(blank=True, null=True)
    kakao_place_id = models.CharField(max_length=64, blank=True, null=True)
    kakao_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["lat", "lng"], name="idx_place_lat_lng"),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name


class PlaceIncidentProximity(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    incident = models.ForeignKey(RecoveryIncident, on_delete=models.CASCADE)
    distance_m = models.IntegerField()
    cached_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("place", "incident")
        indexes = [
            models.Index(fields=["incident"]),
            models.Index(fields=["distance_m"]),
        ]

    def __str__(self):
        return f"{self.place} - {self.incident} ({self.distance_m}m)"