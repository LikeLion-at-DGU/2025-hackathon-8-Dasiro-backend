from django.contrib import admin
from .models import CitizenReport, CitizenReportImage, BotMessage
from django.core.mail import send_mail
from django.conf import settings


@admin.register(CitizenReportImage)
class CitizenReportImageAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "image_url", "created_at")


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "role", "message", "created_at")


@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "status", "risk_score")

    actions = ["send_to_city"]

    def send_to_city(self, request, queryset):
        for report in queryset:
            image_urls = [img.image_url for img in report.images.all()]
            message = f"""
            [싱크홀 탐지 기반 서비스 '다시로' 제보 알림]

            안녕하세요. 다시로 시스템을 통해 시민으로부터 싱크홀 관련 제보가 접수되었습니다.
            아래 내용을 확인해 주시기 바랍니다.

            ──────────────────────────────
            📌 제보 내용
            {report.text if report.text else '내용 없음'}

            📍 위치 정보
            위도: {report.lat}
            경도: {report.lng}

            🖼 첨부 이미지
            {'\n'.join(image_urls) if image_urls else '첨부 이미지 없음'}
            ──────────────────────────────

            본 제보는 시민 참여 기반으로 수집된 것으로, 현장 확인 및 후속 조치가 필요할 수 있습니다.

            감사합니다.
            - 싱크홀 탐지 기반 서비스 다시로 드림
            """

            send_mail(
                subject=f"[싱크홀 제보] Report #{report.id}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["forestbin0420@dgu.ac.kr"],
            )
        self.message_user(request, f"{queryset.count()}건 전송 완료")

    send_to_city.short_description = "선택한 제보를 시청으로 전송"