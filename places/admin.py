from django.contrib import admin
from .models import Place, PlaceIncidentProximity

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'address')

@admin.register(PlaceIncidentProximity)
class PlaceIncidentProximityAdmin(admin.ModelAdmin):
    list_display = ('place', 'incident', 'distance_m', 'cached_at')
    list_filter = ('distance_m',)