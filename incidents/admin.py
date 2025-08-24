from django.contrib import admin
from django.utils.html import format_html
from .models import RecoveryIncident


@admin.register(RecoveryIncident)
class RecoveryIncidentAdmin(admin.ModelAdmin):
    list_display = ('address', 'status', 'occurred_at', 'created_at', 'image_preview', 'district')
    list_filter = ('status', 'occurred_at', 'district')
    search_fields = ('address', 'cause', 'method')
    actions = ['mark_as_recovered']

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 60px;"/>', obj.image_url)
        return "-"
    image_preview.short_description = "대표 이미지"

    def mark_as_recovered(self, request, queryset):
        updated = queryset.update(status=RecoveryIncident.RecoveryStatus.RECOVERED)
        self.message_user(request, f"{updated}건이 복구완료로 변경되었습니다.")
    mark_as_recovered.short_description = "선택된 사고들을 복구완료로 변경"
