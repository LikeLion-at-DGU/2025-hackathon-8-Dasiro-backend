from django.contrib import admin
from django.utils.html import format_html
from .models import RecoveryIncident

@admin.register(RecoveryIncident)
class RecoveryIncidentAdmin(admin.ModelAdmin):
    list_display = ('address', 'status', 'occurred_at', 'created_at', 'image_preview', 'district')
    list_filter = ('status', 'occurred_at', 'district')
    search_fields = ('address', 'cause', 'method')

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 60px;"/>', obj.image_url)
        return "-"
    image_preview.short_description = "대표 이미지"