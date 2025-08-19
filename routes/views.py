import math
import requests
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from incidents.models import RecoveryIncident
from .models import RouteLog


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


class KakaoProxyViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=["get"], url_path="kakao/geocode")
    def geocode(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({"status": "error", "message": "주소(query) 필요", "code": 400}, status=400)

        url = f"{settings.KAKAO_LOCAL_BASE}/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}
        params = {"query": query}

        try:
            r = requests.get(url, headers=headers, params=params, timeout=settings.KAKAO_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            items = []
            for d in data.get("documents", []):
                items.append({
                    "address": d.get("address", {}).get("address_name") or query,
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                })
            return Response({"status": "success", "message": "지오코딩 성공", "code": 200,
                            "data": {"items": items, "count": len(items)}})
        except Exception as e:
            return Response({"status": "error", "message": "지오코딩 실패", "code": 502, "data": {"detail": str(e)}}, status=502)

    @action(detail=False, methods=["get"], url_path="kakao/reverse-geocode")
    def reverse_geocode(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        if not lat or not lng:
            return Response({"status": "error", "message": "lat/lng 필요", "code": 400}, status=400)

        url = f"{settings.KAKAO_LOCAL_BASE}/v2/local/geo/coord2address.json"
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}
        params = {"x": lng, "y": lat}

        try:
            r = requests.get(url, headers=headers, params=params, timeout=settings.KAKAO_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            doc = data.get("documents", [{}])[0].get("address", {})
            return Response({
                "status": "success", "message": "리버스 지오코딩 성공", "code": 200,
                "data": {
                    "address": doc.get("address_name"),
                    "district": {
                        "sido": doc.get("region_1depth_name"),
                        "sigungu": doc.get("region_2depth_name"),
                        "dong": doc.get("region_3depth_name"),
                    }
                }
            })
        except Exception as e:
            return Response({"status": "error", "message": "리버스 지오코딩 실패", "code": 502, "data": {"detail": str(e)}}, status=502)

    @action(detail=False, methods=["post"], url_path="kakao/safe-routes")
    def safe_routes(self, request):
        origin = request.data.get("origin")
        destination = request.data.get("destination")
        modes = request.data.get("modes", ["walk", "car"])
        avoid_incidents = request.data.get("avoid_incidents", True)
        avoid_status = request.data.get("avoid_status", ["UNDER_REPAIR", "TEMP_REPAIRED"])
        avoid_radius_m = int(request.data.get("avoid_radius_m", 200))

        if not origin or not destination:
            return Response({"status": "error", "message": "출발/도착 좌표 누락", "code": 400}, status=400)

        routes = []
        for mode in modes:
            url = f"{settings.KAKAO_API_BASE}/v1/directions"
            headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}
            params = {
                "origin": f"{origin['lng']},{origin['lat']}",
                "destination": f"{destination['lng']},{destination['lat']}",
                "vehicle_type": 1 if mode == "walk" else 2,
            }

            try:
                r = requests.get(url, headers=headers, params=params, timeout=settings.KAKAO_TIMEOUT)
                r.raise_for_status()
                data = r.json()

                path = []
                for sec in data.get("routes", [])[0].get("sections", []):
                    for road in sec.get("roads", []):
                        v = road.get("vertexes", [])
                        for i in range(0, len(v), 2):
                            path.append([v[i+1], v[i]])

                if avoid_incidents:
                    incidents = RecoveryIncident.objects.filter(status__in=avoid_status)
                    safe_path = []
                    for lat, lng in path:
                        too_close = False
                        for inc in incidents:
                            dist = haversine(lat, lng, float(inc.lat), float(inc.lng))
                            if dist <= avoid_radius_m:
                                too_close = True
                                break
                        if not too_close:
                            safe_path.append([lat, lng])
                    path = safe_path

                summary = data.get("routes", [])[0].get("summary", {})
                duration = summary.get("duration", 0)
                distance = summary.get("distance", 0)

                RouteLog.objects.create(
                    origin_lat=origin["lat"], origin_lng=origin["lng"],
                    dest_lat=destination["lat"], dest_lng=destination["lng"],
                    mode=mode, provider="kakao",
                    duration_sec=duration, distance_m=distance, raw_response=data
                )

                routes.append({
                    "mode": mode,
                    "duration_sec": duration,
                    "distance_m": distance,
                    "polyline": path
                })
            except Exception as e:
                return Response({"status": "error", "message": "경로 계산 실패", "code": 502, "data": {"detail": str(e)}}, status=502)

        return Response({"status": "success", "message": "안전 경로 탐색 성공", "code": 200, "data": {"routes": routes}})