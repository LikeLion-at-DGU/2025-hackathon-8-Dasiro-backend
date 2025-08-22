from django.db import models

class Place(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    lat = models.FloatField()
    lng = models.FloatField()
    category = models.CharField(max_length=50)  # FOOD / CAFE / CONVENIENCE
    place_url = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    kakao_place_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category})"