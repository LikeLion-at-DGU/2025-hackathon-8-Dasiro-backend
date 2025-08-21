from rest_framework import serializers
from .models import Coupon, CouponCode


class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCode
        fields = ["code", "barcode_type", "status"]


class CouponDetailSerializer(serializers.ModelSerializer):
    code = CouponCodeSerializer(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "place",
            "title",
            "description",
            "starts_at",
            "ends_at",
            "is_active",
            "code",
        ]