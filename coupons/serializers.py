from rest_framework import serializers
from .models import *


class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCode
        fields = ["id", "code", "barcode_type", "status"]


class CouponDetailSerializer(serializers.ModelSerializer):
    codes = CouponCodeSerializer(many=True, source="couponcode_set")

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
            "codes",
        ]