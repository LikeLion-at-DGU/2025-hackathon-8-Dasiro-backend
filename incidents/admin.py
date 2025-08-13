from django.contrib import admin
from .models import RecoveryIncident, RecoveryIncidentImage

class RecoveryIncidentImageInline(admin.TabularInline):
    model = RecoveryIncidentImage
    extra = 1

@admin.register(RecoveryIncident)
class RecoveryIncidentAdmin(admin.ModelAdmin):
    list_display = ('address', 'status', 'occurred_at', 'created_at')
    list_filter = ('status', 'occurred_at')
    search_fields = ('address', 'cause', 'method')
    inlines = [RecoveryIncidentImageInline]