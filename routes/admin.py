from django.contrib import admin
from .models import RouteLog

@admin.register(RouteLog)
class RouteLogAdmin(admin.ModelAdmin):
    list_display = ('mode', 'duration_sec', 'distance_m', 'created_at')
    list_filter = ('mode', 'provider')