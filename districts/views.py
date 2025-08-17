import csv
import os
from collections import defaultdict
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import District, DistrictMetric
from django.db.models import Max


# 등급 임시 매핑용
grade_map = {
    11110515: "G4", # 청운효자동
    11110530: "G2", # 사직동
    # ...
}


class DistrictViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="gu/metrics")
    def gu_metrics(self, request):
        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        qs = DistrictMetric.objects.filter(as_of_date=latest_date).select_related("district")

        data = [
            {
                "gu_code": int(str(d.district.id)[:5]),  # 동코드 앞 5자리 → 구코드로 변환 시킴
                "sido": d.district.sido,
                "sigungu": d.district.sigungu,
                "center_lat": float(d.district.center_lat),
                "center_lng": float(d.district.center_lng),
                "total_grade": d.total_grade,
            }
            for d in qs
        ]

        return Response({
            "status": "success",
            "message": "구 집계 조회 성공",
            "code": 200,
            "data": {"items": data, "as_of_date": latest_date, "count": len(data)}
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
                "center_lng": float(d.center_lng),
            }
            for d in qs
        ]

        return Response({
            "status": "success",
            "message": "동 검색 성공",
            "code": 200,
            "data": {"items": data, "count": len(data)}
        })

    @action(detail=True, methods=["get"], url_path="metrics")
    def district_metrics(self, request, pk=None):
        latest = DistrictMetric.objects.filter(district_id=pk).order_by("-as_of_date").first()
        if not latest:
            return Response({
                "status": "error",
                "message": "지표를 찾을 수 없습니다",
                "code": 404,
                "data": {"detail": f"district_id={pk}"}
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
                "analysis_text": latest.analysis_text,
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
                "data": {"detail": "lat,lng required"}
            }, status=400)

        from math import radians, cos, sin, acos

        def distance(lat1, lng1, lat2, lng2):
            R = 6371000
            lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
            return R * acos(cos(lat1) * cos(lat2) * cos(lng2 - lng1) + sin(lat1) * sin(lat2))

        districts = District.objects.all()
        nearest = min(districts, key=lambda d: distance(lat, lng, float(d.center_lat), float(d.center_lng)))

        latest_metric = DistrictMetric.objects.filter(district=nearest).order_by("-as_of_date").first()
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
                    "dong": nearest.dong,
                },
                "total_grade": latest_metric.total_grade,
                "danger": danger,
                "as_of_date": latest_metric.as_of_date,
            }
        })

    @action(detail=False, methods=["get"], url_path="gu/metrics/by-grade")
    def gu_metrics_by_grade(self, request):
        grade = request.GET.get("grade")
        match_rule = request.GET.get("match_rule", "any")

        if grade not in ["G1", "G2", "G3", "G4", "G5"]:
            return Response({
                "status": "error",
                "message": "잘못된 등급",
                "code": 400,
                "data": {"detail": "grade must be one of G1..G5"}
            }, status=400)

        csv_path = os.path.join(settings.BASE_DIR, "data", "서울시행정동.csv")
        gu_data = defaultdict(list)

        with open(csv_path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                dong_code = int(row[0])
                sido = row[1]
                sigungu = row[2]
                dong = row[3]
                lng = float(row[4])
                lat = float(row[5])

                dong_grade = grade_map.get(dong_code)
                if dong_grade:
                    gu_code = int(str(dong_code)[:5])
                    gu_data[(gu_code, sido, sigungu)].append((lat, lng, dong_grade))

        results = []
        for (gu_code, sido, sigungu), records in gu_data.items():
            avg_lat = sum(r[0] for r in records) / len(records)
            avg_lng = sum(r[1] for r in records) / len(records)
            grade_nums = [int(r[2][1]) for r in records]  # G1 → 1, G5 → 5로 숫자 매칭함
            avg_grade = sum(grade_nums) / len(grade_nums)
            final_grade = f"G{round(avg_grade)}"

            results.append({
                "gu_code": gu_code,
                "sido": sido,
                "sigungu": sigungu,
                "center_lat": round(avg_lat, 6),
                "center_lng": round(avg_lng, 6),
                "matching_district_count": len(records),
                "final_grade": final_grade,
            })

        return Response({
            "status": "success",
            "message": "구 등급 필터 조회 성공",
            "code": 200,
            "data": {"items": results, "as_of_date": "2025-08-01", "count": len(results)}
        })

    @action(detail=False, methods=["get"], url_path="by-grade")
    def districts_by_grade(self, request):
        grade = request.GET.get("grade")
        if grade not in ["G1", "G2", "G3", "G4", "G5"]:
            return Response({
                "status": "error",
                "message": "잘못된 등급",
                "code": 400,
                "data": {"detail": "grade must be one of G1..G5"}
            }, status=400)

        csv_path = os.path.join(settings.BASE_DIR, "data", "서울시행정동.csv")
        data = []

        with open(csv_path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                dong_code = int(row[0])
                sido = row[1]
                sigungu = row[2]
                dong = row[3]
                lng = float(row[4])
                lat = float(row[5])

                if grade_map.get(dong_code) == grade:
                    data.append({
                        "id": dong_code,
                        "sido": sido,
                        "sigungu": sigungu,
                        "dong": dong,
                        "center_lat": lat,
                        "center_lng": lng,
                    })

        return Response({
            "status": "success",
            "message": "동 등급 필터 조회 성공",
            "code": 200,
            "data": {"items": data, "as_of_date": "2025-08-01", "count": len(data)}
        })