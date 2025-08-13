from django.contrib import admin
from .models import CitizenReport, CitizenReportImage, BotMessage

class CitizenReportImageInline(admin.TabularInline):
    model = CitizenReportImage
    extra = 1

class BotMessageInline(admin.TabularInline):
    model = BotMessage
    extra = 1

@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = ('address', 'status', 'risk_score', 'risk_grade', 'created_at')
    list_filter = ('status', 'risk_grade')
    search_fields = ('address', 'text')
    inlines = [CitizenReportImageInline, BotMessageInline]