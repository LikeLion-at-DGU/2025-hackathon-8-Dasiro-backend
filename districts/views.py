from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from .models import *
from django.db.models import Max, Count

class DistrictViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="gu/metrics")
    def gu_metrics(self, request):

        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        qs = DistrictMetric.objects.filter(as_of_date=latest_date) \
            .select_related("district")

        data = [
            {
                "gu_code": d.district.id,
                "sido": d.district.sido,
                "sigungu": d.district.sigungu,
                "center_lat": float(d.district.center_lat),
                "center_lng": float(d.district.center_lng),
                "total_grade": d.total_grade
            }
            for d in qs
        ]
        return Response({
            "status": "success",
            "message": "구 집계 조회 성공",
            "code": 200,
            "data": {
                "items": data,
                "as_of_date": latest_date,
                "count": len(data)
            }
        })

    @action(detail=False, methods=["get"], url_path="search")
    def search_districts(self, request):
        q = request.GET.get("q", "")
        qs = District.objects.filter(dong__icontains=q)[:20]
        data = [
            {
                "id": d.id,
                "sido": d.sido,
                "sigungu": d.sigungu,
                "dong": d.dong,
                "center_lat": float(d.center_lat),
                "center_lng": float(d.center_lng)
            }
            for d in qs
        ]
        return Response({
            "status": "success",
            "message": "동 검색 성공",
            "code": 200,
            "data": {
                "items": data,
                "count": len(data)
            }
        })

    @action(detail=True, methods=["get"], url_path="metrics")
    def district_metrics(self, request, pk=None):
        latest = DistrictMetric.objects.filter(district_id=pk) \
                                        .order_by("-as_of_date") \
                                        .first()
        if not latest:
            return Response({
                "status": "error",
                "message": "지표를 찾을 수 없습니다",
                "code": 404,
                "data": { "detail": f"district_id={pk}" }
            }, status=404)

        return Response({
            "status": "success",
            "message": "동 지표 조회 성공",
            "code": 200,
            "data": {
                "district_id": latest.district_id,
                "as_of_date": latest.as_of_date,
                "total_grade": latest.total_grade,
                "ground_stability": latest.ground_stability,
                "groundwater_impact": latest.groundwater_impact,
                "underground_density": latest.underground_density,
                "old_building_dist": latest.old_building_dist,
                "analysis_text": latest.analysis_text
            }
        })

    @action(detail=False, methods=["get"], url_path="risk/by-coord")
    def risk_by_coord(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lng = float(request.GET.get("lng"))
        except (TypeError, ValueError):
            return Response({
                "status": "error",
                "message": "필수 파라미터 누락",
                "code": 400,
                "data": { "detail": "lat,lng required" }
            }, status=400)

        from math import radians, sin, cos, acos
        def distance(lat1, lng1, lat2, lng2):
            R = 6371000
            lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
            return R * acos(
                cos(lat1) * cos(lat2) * cos(lng2 - lng1) + sin(lat1) * sin(lat2)
            )

        districts = District.objects.all()
        nearest = min(districts, key=lambda d: distance(lat, lng, float(d.center_lat), float(d.center_lng)))

        latest_metric = DistrictMetric.objects.filter(district=nearest) \
                                                .order_by("-as_of_date") \
                                                .first()

        danger = latest_metric.total_grade in ["G4", "G5"]

        return Response({
            "status": "success",
            "message": "좌표 위험 요약 조회 성공",
            "code": 200,
            "data": {
                "district": {
                    "id": nearest.id,
                    "sido": nearest.sido,
                    "sigungu": nearest.sigungu,
                    "dong": nearest.dong
                },
                "total_grade": latest_metric.total_grade,
                "danger": danger,
                "as_of_date": latest_metric.as_of_date
            }
        })

    @action(detail=False, methods=["post"], url_path="gu/metrics/by-grade")
    def gu_metrics_by_grade(self, request):
        grade = request.data.get("grade")
        match_rule = request.data.get("match_rule", "any")
        if grade not in ["G1","G2","G3","G4","G5"]:
            return Response({
                "status": "error",
                "message": "잘못된 등급",
                "code": 400,
                "data": { "detail": "grade must be one of G1..G5" }
            }, status=400)

        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]

        grouped = DistrictMetric.objects.filter(as_of_date=latest_date) \
                                        .values("district__sigungu") \
                                        .annotate(matching_count=Count("id"))

        data = [
            {
                "gu_code": g["district__sigungu"], #임시
                "sido": "서울특별시",
                "sigungu": g["district__sigungu"],
                "center_lat": 0,
                "center_lng": 0,
                "matching_district_count": g["matching_count"]
            }
            for g in grouped
        ]
        return Response({
            "status": "success",
            "message": "구 등급 필터 조회 성공",
            "code": 200,
            "data": {
                "items": data,
                "as_of_date": latest_date,
                "count": len(data)
            }
        })

    @action(detail=False, methods=["post"], url_path="by-grade")
    def districts_by_grade(self, request):
        grade = request.data.get("grade")
        if grade not in ["G1","G2","G3","G4","G5"]:
            return Response({
                "status": "error",
                "message": "잘못된 등급",
                "code": 400,
                "data": { "detail": "grade must be one of G1..G5" }
            }, status=400)

        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]

        qs = DistrictMetric.objects.filter(as_of_date=latest_date, total_grade=grade) \
                                    .select_related("district")

        data = [
            {
                "id": d.district.id,
                "sido": d.district.sido,
                "sigungu": d.district.sigungu,
                "dong": d.district.dong,
                "center_lat": float(d.district.center_lat),
                "center_lng": float(d.district.center_lng)
            }
            for d in qs
        ]

        return Response({
            "status": "success",
            "message": "동 등급 필터 조회 성공",
            "code": 200,
            "data": {
                "items": data,
                "as_of_date": latest_date,
                "count": len(data)
            }
        })