from django.db import models
from places.models import Place

class Coupon(models.Model):
    place = models.ForeignKey(Place, on_delete=models.RESTRICT)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    total_qty = models.IntegerField(blank=True, null=True)  # null=무제한
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.place})"


class CouponCode(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    code = models.CharField(max_length=32, unique=True)
    barcode_type = models.CharField(max_length=20)  # 'qr' 등
    issued_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20)  # 'issued','redeemed','expired'

    class Meta:
        indexes = [
            models.Index(fields=["coupon", "status"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.status})"