from django.contrib import admin
from .models import District, DistrictMetric

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('sido', 'sigungu', 'dong', 'is_safezone')
    list_filter = ('is_safezone', 'sido', 'sigungu')
    search_fields = ('sido', 'sigungu', 'dong')

@admin.register(DistrictMetric)
class DistrictMetricAdmin(admin.ModelAdmin):
    list_display = ('district', 'as_of_date', 'total_grade')
    list_filter = ('total_grade', 'as_of_date')