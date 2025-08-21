from django.contrib import admin
from .models import Coupon, CouponCode

class CouponCodeInline(admin.TabularInline):
    model = CouponCode
    extra = 0
    readonly_fields = ("issued_at", "redeemed_at")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("title", "place", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("title", "description")
    inlines = [CouponCodeInline]

@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "coupon", "status", "issued_at", "redeemed_at")
    list_filter = ("status", "coupon__is_active")
    search_fields = ("code", "coupon__title")
    readonly_fields = ("issued_at",)
