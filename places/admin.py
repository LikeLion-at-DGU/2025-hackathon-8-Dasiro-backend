from django.contrib import admin
from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "address", "lat", "lng", "place_url")  # 주소, 카카오 URL 확인 용도 추가
    search_fields = ("name", "address")
    list_filter = ("category",)
