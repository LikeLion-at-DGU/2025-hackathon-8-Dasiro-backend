from django.contrib import admin
from .models import Coupon, CouponCode

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('title', 'place', 'starts_at', 'ends_at', 'is_active')
    list_filter = ('is_active', 'starts_at', 'ends_at')
    search_fields = ('title', 'description')

@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'coupon', 'status', 'issued_at', 'redeemed_at')
    list_filter = ('status',)
    search_fields = ('code',)