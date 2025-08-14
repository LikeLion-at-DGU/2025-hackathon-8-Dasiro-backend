from django.contrib import admin
from django.utils.html import format_html
from .models import Place, PlaceIncidentProximity

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'created_at', 'main_image_preview')
    list_filter = ('category',)
    search_fields = ('name', 'address')

    def main_image_preview(self, obj):
        if obj.main_image_url:
            return format_html('<img src="{}" style="max-height: 60px;"/>', obj.main_image_url)
        return "-"
    main_image_preview.short_description = "대표 이미지"

@admin.register(PlaceIncidentProximity)
class PlaceIncidentProximityAdmin(admin.ModelAdmin):
    list_display = ('place', 'incident', 'distance_m', 'cached_at')
    list_filter = ('distance_m',)