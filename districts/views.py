import openai
from django.db.models import Count, F, Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from incidents.models import *
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import *
from incidents.models import *
from django.db.models import Max


class DistrictViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="gu/metrics")
    def gu_metrics(self, request):
        latest_date = GuMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        qs = GuMetric.objects.filter(as_of_date=latest_date)

        data = [
            {
                "sigungu": m.sigungu,
                "sido": m.sido,
                "final_grade": m.total_grade,
                "as_of_date": m.as_of_date,
            }
            for m in qs
        ]

        return Response({
            "status": "success",
            "message": "구 집계 조회 성공",
            "code": 200,
            "data": {"items": data, "as_of_date": latest_date, "count": len(data)}
        })

    @action(detail=False, methods=["get"], url_path="search")
    def search_districts(self, request):
        q = request.GET.get("q", "").strip()
        sido = request.GET.get("sido")
        sigungu = request.GET.get("sigungu")
        try:
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            limit = 20
        limit = min(limit, 50)

        if not q:
            return Response({
                "status": "error",
                "message": "검색어가 필요합니다",
                "code": 400,
                "data": {"detail": "q required (min length 1)"}
            }, status=400)

        qs = District.objects.all()
        qs = qs.filter(dong__icontains=q)
        if sido:
            qs = qs.filter(sido=sido)
        if sigungu:
            qs = qs.filter(sigungu=sigungu)
        qs = qs[:limit]

        data = []
        for d in qs:
            latest_metric = DistrictMetric.objects.filter(district=d).order_by("-as_of_date").first()
            if latest_metric:
                data.append({
                    "id": d.id,
                    "sido": d.sido,
                    "sigungu": d.sigungu,
                    "dong": d.dong,
                    "center_lat": float(d.center_lat),
                    "center_lng": float(d.center_lng),
                    "is_safezone": d.is_safezone,
                    "total_grade": latest_metric.total_grade,
                    "ground_stability": latest_metric.ground_stability,
                    "groundwater_impact": latest_metric.groundwater_impact,
                    "underground_density": latest_metric.underground_density,
                    "old_building_dist": latest_metric.old_building_dist,
                    "incident_history": latest_metric.incident_history,
                })
            else:
                data.append({
                    "id": d.id,
                    "sido": d.sido,
                    "sigungu": d.sigungu,
                    "dong": d.dong,
                    "center_lat": float(d.center_lat),
                    "center_lng": float(d.center_lng),
                    "is_safezone": d.is_safezone,
                    "total_grade": None,
                    "ground_stability": None,
                    "groundwater_impact": None,
                    "underground_density": None,
                    "old_building_dist": None,
                    "incident_history": None,
                })

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
        if grade not in ["G1", "G2", "G3", "G4", "G5"]:
            return Response({
                "status": "error",
                "message": "잘못된 등급",
                "code": 400,
                "data": {"detail": "grade must be one of G1..G5"}
            }, status=400)

        latest_date = GuMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        qs = GuMetric.objects.filter(as_of_date=latest_date, total_grade=grade)

        data = [
            {
                "sigungu": m.sigungu,
                "sido": m.sido,
                "total_grade": m.total_grade,
                "as_of_date": m.as_of_date,
            }
            for m in qs
        ]

        return Response({
            "status": "success",
            "message": "구 등급 필터 조회 성공",
            "code": 200,
            "data": {"items": data, "as_of_date": latest_date, "count": len(data)}
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

        latest_date = DistrictMetric.objects.aggregate(latest=Max("as_of_date"))["latest"]
        qs = DistrictMetric.objects.filter(as_of_date=latest_date, total_grade=grade).select_related("district")

        data = [
            {
                "id": m.district.id,
                "sido": m.district.sido,
                "sigungu": m.district.sigungu,
                "dong": m.district.dong,
                "center_lat": float(m.district.center_lat),
                "center_lng": float(m.district.center_lng),
                "total_grade": m.total_grade,
            }
            for m in qs
        ]

        return Response({
            "status": "success",
            "message": f"{grade} 등급 동 조회 성공",
            "code": 200,
            "data": {"items": data, "as_of_date": latest_date, "count": len(data)}
        })

    @action(detail=False, methods=["get"], url_path="gu/recovery-status")
    def gu_recovery_status(self, request):

        incidents = (
            RecoveryIncident.objects
            .values("status", "district_id")
            .annotate(count=Count("id"))
        )

        gu_data = {}
        for row in incidents:
            district_id = row.get("district_id")
            if not district_id:
                continue

            try:
                gu_code = int(str(district_id)[:5])
            except (ValueError, TypeError):
                continue

            status_name = row["status"]
            count = row["count"]

            if gu_code not in gu_data:
                gu_data[gu_code] = {"RECOVERING": 0, "TEMP_REPAIRED": 0, "RECOVERED": 0}

            if status_name in gu_data[gu_code]:
                gu_data[gu_code][status_name] = count

        results = []
        for gu_code, counts in gu_data.items():
            gu_districts = District.objects.filter(id__startswith=str(gu_code))
            if not gu_districts.exists():
                continue

            avg_lat = sum(float(d.center_lat) for d in gu_districts) / gu_districts.count()
            avg_lng = sum(float(d.center_lng) for d in gu_districts) / gu_districts.count()
            first = gu_districts.first()

            results.append({
                "gu_code": gu_code,
                "sido": first.sido,
                "sigungu": first.sigungu,
                "center_lat": round(avg_lat, 6),
                "center_lng": round(avg_lng, 6),
                "recovery_counts": counts,
            })

        return Response({
            "status": "success",
            "message": "구별 복구 현황 조회 성공",
            "code": 200,
            "data": {"items": results, "count": len(results)}
        })

class SafezoneViewSet(viewsets.ViewSet):

    def _latest_metrics(self):
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
        return metric.total_grade == "G1"

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
                info = safe_gu_info.setdefault(gu_code, {"grades": set()})
                info["grades"].add(m.total_grade)

        results = []
        for gu_code, info in safe_gu_info.items():
            gu_districts = District.objects.filter(id__startswith=str(gu_code))
            if not gu_districts.exists():
                continue

            avg_lat = sum(float(d.center_lat) for d in gu_districts) / gu_districts.count()
            avg_lng = sum(float(d.center_lng) for d in gu_districts) / gu_districts.count()

            results.append({
                "gu_code": gu_code,
                "sido": gu_districts.first().sido,
                "sigungu": gu_districts.first().sigungu,
                "center_lat": round(avg_lat, 6),
                "center_lng": round(avg_lng, 6),
                "safe_district_count": gu_districts.count(),  # 구 전체 동 개수
                "final_grade": "G1",  # 무조건 G1
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
                    "total_grade": "G1"
                })
                seen_ids.add(m.district_id)

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

        # DB 기반으로 첫문단 구성함
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

        incidents = RecoveryIncident.objects.filter(
            district=district
        ).order_by("-occurred_at")

        latest = DistrictMetric.objects.filter(district=district).order_by("-as_of_date").first()
        if not latest:
            return Response({"status": "error", "message": "지표 없음", "code": 404, "data": {}}, status=404)

        if not incidents.exists():
            first_paragraph = f"{district.dong}은 2년 이내에 싱크홀 사고가 발생하지 않은 지역이에요. 현재까지는 특별히 위험 징후가 확인되지 않았어요."

            prompt = f"""
            행정동: {district.dong}
            시군구: {district.sigungu}
            싱크홀 사고 건수: 0건

            위 데이터를 기반으로,
            안내문 형식으로 2번째와 3번째 문단을 작성해줘.
            - 2번째 문단: 사고가 없는 지역의 특성을 설명하고, 지반·시설·공사 측면에서 안정적일 수 있음을 언급
            - 3번째 문단: 앞으로도 주의 깊은 관리가 필요하지만 현재는 비교적 안전하다는 내용을 설명
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
            gpt_analysis = first_paragraph + "\n\n" + gpt_text

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
                    "recent_incidents": 0,
                    "analysis_text": gpt_analysis
                }
            })

        # 사고가 있는 경우 (집계 반영)
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
                "recent_incidents": incidents.count(),   # 전체 건수
                "analysis_text": gpt_analysis
            }
        })