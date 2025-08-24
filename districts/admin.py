from django.contrib import admin
from .models import District, DistrictMetric, GuMetric

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('sido', 'sigungu', 'dong', 'is_safezone')
    list_filter = ('is_safezone', 'sido', 'sigungu')
    search_fields = ('sido', 'sigungu', 'dong')

@admin.register(DistrictMetric)
class DistrictMetricAdmin(admin.ModelAdmin):
    list_display = ('district', 'as_of_date', 'total_grade')
    list_filter = ('total_grade', 'as_of_date', 'district__sigungu')
    search_fields = ('district__sido', 'district__sigungu', 'district__dong')

@admin.register(GuMetric)
class GuMetricAdmin(admin.ModelAdmin):
    list_display = ('sido', 'sigungu', 'as_of_date', 'total_grade')
    list_filter = ('total_grade', 'as_of_date', 'sido', 'sigungu')
    search_fields = ('sido', 'sigungu')