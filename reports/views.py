from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
import boto3
from uuid import uuid4

from .models import CitizenReport, CitizenReportImage, BotMessage
from .serializers import CitizenReportSerializer, CitizenReportCreateSerializer


def upload_to_s3(file):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    key = f"reports/{uuid4()}_{file.name}"
    
    # ACL 제거했음 !
    s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, key)
    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"


class CitizenReportViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = CitizenReportCreateSerializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save(status=CitizenReport.ReportStatus.RECEIVED)
            return Response({"status": "success", "message": "제보 접수 완료", "code": 200, "data": CitizenReportSerializer(report).data})
        return Response({"status": "error", "message": "유효하지 않은 입력", "code": 400, "data": serializer.errors}, status=400)

    def retrieve(self, request, pk=None):
        try:
            report = CitizenReport.objects.get(pk=pk)
        except CitizenReport.DoesNotExist:
            return Response({"status": "error", "message": "제보를 찾을 수 없습니다."}, status=404)

        return Response({"status": "success", "message": "조회 성공", "code": 200, "data": CitizenReportSerializer(report).data})

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        try:
            report = CitizenReport.objects.get(pk=pk)
        except CitizenReport.DoesNotExist:
            return Response({"status": "error", "message": "제보 없음"}, status=404)

        msgs = BotMessage.objects.filter(report=report).order_by("created_at")
        return Response({"status": "success", "message": "메시지 조회 성공", "code": 200, "data": [{"role": m.role, "message": m.message, "created_at": m.created_at} for m in msgs]})

    @action(detail=True, methods=["post"], url_path="images")
    def upload_images(self, request, pk=None):
        try:
            report = CitizenReport.objects.get(pk=pk)
        except CitizenReport.DoesNotExist:
            return Response({"status": "error", "message": "제보 없음"}, status=404)

        files = request.FILES.getlist("files")
        if not files:
            return Response({"status": "error", "message": "파일이 필요합니다."}, status=400)

        if report.images.count() + len(files) > 3:
            return Response({"status": "error", "message": "이미지는 최대 3장까지 업로드 가능합니다."}, status=400)

        uploaded_urls = []
        for f in files:
            url = upload_to_s3(f)
            img = CitizenReportImage.objects.create(report=report, image_url=url)
            uploaded_urls.append(img.image_url)

        return Response({"status": "success", "message": "이미지 업로드 성공", "code": 200, "data": {"image_urls": uploaded_urls}})

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        try:
            report = CitizenReport.objects.get(pk=pk)
        except CitizenReport.DoesNotExist:
            return Response({"status": "error", "message": "제보 없음"}, status=404)

        image_urls = request.data.get("image_urls")
        if not image_urls:
            return Response({"status": "error", "message": "분석할 이미지가 필요합니다."}, status=400)

        # TODO: AI 서버 프록시 호출 → risk_score 수신
        fake_score = 82
        report.risk_score = fake_score
        report.status = CitizenReport.ReportStatus.DONE
        report.save()

        BotMessage.objects.create(report=report, role="bot", message=f"위험도 분석 결과: {fake_score}")

        response_data = {"risk_score": fake_score}

        #  50점 이상이면 자동 전송
        if fake_score >= 50:
            message = f"""
            [싱크홀 탐지 기반 서비스 '다시로' 제보 알림]

            시민 제보가 접수되었으며, AI 분석 결과 위험 점수가 {fake_score}점으로 확인되었습니다.
            아래 내용을 확인 바랍니다.

            📌 제보 내용
            {report.text if report.text else '내용 없음'}

            📍 위치 정보
            위도: {report.lat}
            경도: {report.lng}

            🖼 첨부 이미지
            {'\n'.join(image_urls) if image_urls else '첨부 이미지 없음'}

            감사합니다.
            - 다시로 드림
            """

            send_mail(
                subject=f"[싱크홀 제보] Report #{report.id}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["jinhwanpark@seoul.go.kr"],
            )

            response_data["sent_to"] = "jinhwanpark@seoul.go.kr"
            response_data["sent_at"] = report.updated_at.isoformat() if hasattr(report, "updated_at") else None

        return Response({
            "status": "success",
            "message": "위험도 분석 완료",
            "code": 200,
            "data": response_data
        })


    @action(detail=True, methods=["post"], url_path="send-city")
    def send_city(self, request, pk=None):
        try:
            report = CitizenReport.objects.get(pk=pk)
        except CitizenReport.DoesNotExist:
            return Response({"status": "error", "message": "제보 없음"}, status=404)

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

        try:
            send_mail(
                subject=f"[싱크홀 제보] Report #{report.id}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["jinhwanpark@seoul.go.kr"],
            )
            return Response({
                "status": "success",
                "message": "시청 전송 완료",
                "code": 200,
                "data": {"sent_to": "jinhwanpark@seoul.go.kr"}
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": "시청 전송 실패",
                "code": 500,
                "data": {"detail": str(e)}
            }, status=500)
