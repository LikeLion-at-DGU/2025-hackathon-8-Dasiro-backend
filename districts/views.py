import csv
import os
import openai
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from incidents.models import RecoveryIncident
from collections import defaultdict
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import *
from incidents.models import *
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
        
class SafezoneViewSet(viewsets.ViewSet):

    def _latest_metrics(self): # 최신 스냅샷으로 변경 -> 최근 날짜것 불러오기 !
        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        if not latest_date:
            return None, None
        qs = (
            DistrictMetric.objects
            .filter(as_of_date=latest_date)
            .select_related("district")
        )
        return qs, latest_date

    def _is_safe_district(self, metric: DistrictMetric):
        return (metric.total_grade in ("G1", "G2")) or bool(metric.district.is_safezone)

    @action(detail=False, methods=["get"], url_path="gu")
    def gu_summary(self, request):
        metrics, latest_date = self._latest_metrics()
        if latest_date is None:
            return Response({
                "status": "error",
                "message": "안심존 집계 실패",
                "code": 500,
                "data": {"detail": "metrics not prepared"}
            }, status=500)

        safe_gu_info = {}
        for m in metrics:
            if self._is_safe_district(m):
                gu_code = int(str(m.district.id)[:5])
                info = safe_gu_info.setdefault(gu_code, {"grades": set(), "manual": False})
                if m.total_grade in ("G1", "G2"):
                    info["grades"].add(m.total_grade)
                if m.district.is_safezone:
                    info["manual"] = True

        results = []
        for gu_code, info in safe_gu_info.items():
            gu_districts = District.objects.filter(id__startswith=str(gu_code))
            if not gu_districts.exists():
                continue

            avg_lat = sum(float(d.center_lat) for d in gu_districts) / gu_districts.count()
            avg_lng = sum(float(d.center_lng) for d in gu_districts) / gu_districts.count()

            if "G1" in info["grades"]:
                final_grade = "G1"
            elif "G2" in info["grades"] or info["manual"]:
                final_grade = "G2"
            else:
                final_grade = "G2"

            results.append({
                "gu_code": gu_code,
                "sido": gu_districts.first().sido,
                "sigungu": gu_districts.first().sigungu,
                "center_lat": round(avg_lat, 6),
                "center_lng": round(avg_lng, 6),
                "safe_district_count": gu_districts.count(),  # 구 전체 동 개수로 줌
                "final_grade": final_grade,  # G1/G2 구분함 !
            })

        return Response({
            "status": "success",
            "message": "안심존(구) 조회 성공",
            "code": 200,
            "data": {"items": results, "as_of_date": str(latest_date), "count": len(results)}
        })

    @action(detail=False, methods=["get"], url_path="districts")
    def safe_districts(self, request):

        metrics, latest_date = self._latest_metrics()
        if latest_date is None:
            return Response({
                "status": "error",
                "message": "안심존 동 조회 실패",
                "code": 500,
                "data": {"detail": "metrics not prepared"}
            }, status=500)

        safe_items = []
        seen_ids = set()

        for m in metrics:
            if self._is_safe_district(m):
                safe_items.append({
                    "id": m.district.id,
                    "sido": m.district.sido,
                    "sigungu": m.district.sigungu,
                    "dong": m.district.dong,
                    "center_lat": float(m.district.center_lat),
                    "center_lng": float(m.district.center_lng),
                    "total_grade": m.total_grade if m.total_grade in ("G1", "G2") else "G2"
                })
                seen_ids.add(m.district_id)

        manual_safe = District.objects.filter(is_safezone=True).exclude(id__in=seen_ids)
        for d in manual_safe:
            safe_items.append({
                "id": d.id,
                "sido": d.sido,
                "sigungu": d.sigungu,
                "dong": d.dong,
                "center_lat": float(d.center_lat),
                "center_lng": float(d.center_lng),
                "total_grade": "G2",
            })

        return Response({
            "status": "success",
            "message": "안심존(동) 조회 성공",
            "code": 200,
            "data": {"items": safe_items, "as_of_date": str(latest_date), "count": len(safe_items)}
        })
        
class DistrictRiskViewSet(viewsets.ViewSet):

    def _generate_gpt_analysis(self, district, incidents):
        count = incidents.count()
        causes = list(set([i.cause for i in incidents if i.cause]))
        causes_str = ", ".join(causes) if causes else "원인 데이터 없음"

        # DB 기반으로 첫문단 구성
        first_paragraph = f"{district.dong}은 최근 2년간 싱크홀 사고가 {count}건 발생한 지역이에요. 주요 원인은 {causes_str}으로 확인 돼요."

        # GPT는 추가 설명으로 두번째, 세번째 문단을 구성함
        prompt = f"""
        행정동: {district.dong}
        시군구: {district.sigungu}
        최근 2년간 싱크홀 사고 건수: {count}건
        주요 원인: {causes_str}

        위 데이터를 기반으로,
        안내문 형식으로 2번째와 3번째 문단을 작성해줘.
        - 2번째 문단: 해당 지역이 왜 취약한지, 지반·시설·공사 등의 맥락을 객관적으로 설명
        - 3번째 문단: 해당 지역 관리나 점검 필요성, 주의 사항을 설명
        - '주민들은' 같은 직접적 표현 대신 객관적인 설명 위주로 작성
        - 반드시 '~에요, ~돼요, ~해져요' 같은 구어체 설명 문장으로만 작성해
        - '~입니다', '~합니다' 같은 격식체 표현은 절대 쓰지 마
        - 모든 문장은 '~에요'로 끝나도록 해
        - 문단은 2~3줄 단위로 나누어 자연스럽게 이어가고, 말투는 부드럽게
        - 한국어로 작성
        """

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 재난안전 전문가야."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        gpt_text = resp.choices[0].message.content.strip()

        return first_paragraph + "\n\n" + gpt_text

    @action(detail=False, methods=["get", "post"], url_path="risk-info")
    def risk_info_by_dong(self, request):

        dong = request.query_params.get("dong") or request.data.get("dong")

        if not dong:
            return Response({"status": "error", "message": "dong 필요", "code": 400, "data": {}}, status=400)

        district = District.objects.filter(dong__icontains=dong).first()
        if not district:
            return Response({"status": "error", "message": "동 없음", "code": 404, "data": {}}, status=404)

        two_years_ago = timezone.now().date() - timedelta(days=730)
        incidents = RecoveryIncident.objects.filter(
            address__icontains=district.dong,
            occurred_at__gte=two_years_ago
        ).order_by("-occurred_at")

        if not incidents.exists():
            return Response({"status": "error", "message": "사고 데이터 없음", "code": 404, "data": {}}, status=404)

        latest = DistrictMetric.objects.filter(district=district).order_by("-as_of_date").first()
        if not latest:
            return Response({"status": "error", "message": "지표 없음", "code": 404, "data": {}}, status=404)

        # GPT 캐싱 넣었음 !
        if latest.analysis_text:
            gpt_analysis = latest.analysis_text
        else:
            gpt_analysis = self._generate_gpt_analysis(district, incidents)
            latest.analysis_text = gpt_analysis
            latest.save()

        return Response({
            "status": "success",
            "message": "위험도 조회 성공",
            "code": 200,
            "data": {
                "district_id": district.id,
                "sido": district.sido,
                "sigungu": district.sigungu,
                "dong": district.dong,
                "as_of_date": latest.as_of_date,
                "total_grade": latest.total_grade,
                "recent_incidents": incidents.count(),
                "analysis_text": gpt_analysis
            }
        })