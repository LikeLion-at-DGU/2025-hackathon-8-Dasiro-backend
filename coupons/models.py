import random
import string
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from places.models import Place


def generate_coupon_code():
    return ''.join(random.choices(string.digits, k=14))


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
    coupon = models.OneToOneField(Coupon, on_delete=models.CASCADE, related_name="code")  
    code = models.CharField(max_length=32, unique=True, default=generate_coupon_code)
    barcode_type = models.CharField(max_length=20, default="ean13")  # 기본값 바코드 타입
    issued_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="issued")  # 'issued','redeemed','expired'

    def __str__(self):
        return f"{self.code} ({self.status})"


@receiver(post_save, sender=Coupon)
def create_coupon_code(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "code"):
        CouponCode.objects.create(coupon=instance)
