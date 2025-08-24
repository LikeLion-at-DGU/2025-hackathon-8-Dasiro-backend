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


def make_circle_polygon(lat, lng, radius_m=200, num_points=16):
    coords = []
    R = 6378137.0
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        dx = radius_m * math.cos(angle)
        dy = radius_m * math.sin(angle)
        dlat = (dy / R) * (180 / math.pi)
        dlng = (dx / (R * math.cos(math.pi * lat / 180))) * (180 / math.pi)
        coords.append([lng + dlng, lat + dlat])
    coords.append(coords[0])
    return {"type": "Polygon", "coordinates": [coords]}


def decode_polyline(encoded):
    coords = []
    index, lat, lng = 0, 0, 0
    while index < len(encoded):
        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coords.append([lat / 1e5, lng / 1e5])
    return coords


class KakaoProxyViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="geocode")
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
            return Response({"status": "error", "message": "지오코딩 실패", "code": 502,
                            "data": {"detail": str(e)}}, status=502)

    @action(detail=False, methods=["get"], url_path="reverse-geocode")
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
            return Response({"status": "error", "message": "리버스 지오코딩 실패", "code": 502,
                            "data": {"detail": str(e)}}, status=502)

    @action(detail=False, methods=["post"], url_path="safe-routes")
    def safe_routes(self, request):
        origin = request.data.get("origin")
        destination = request.data.get("destination")
        avoid_incidents = request.data.get("avoid_incidents", True)
        avoid_status = request.data.get("avoid_status", ["UNDER_REPAIR", "TEMP_REPAIRED"])
        avoid_radius_m = int(request.data.get("avoid_radius_m", 200))

        if not origin or not destination:
            return Response({"status": "error", "message": "출발/도착 좌표 누락", "code": 400,
                            "data": {"detail": "origin, destination required"}}, status=400)

        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}
        routes = []

        def extract_path(route_data):
            path = []
            for sec in route_data.get("routes", [])[0].get("sections", []):
                for road in sec.get("roads", []):
                    v = road.get("vertexes", [])
                    for i in range(0, len(v), 2):
                        path.append([v[i + 1], v[i]])
            return path

        def filter_safe_path(path):
            if not avoid_incidents:
                return path
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
            return safe_path or path

        try:
            car_url = f"{settings.KAKAO_API_BASE}/v1/directions"
            car_params = {
                "origin": f"{origin['lng']},{origin['lat']}",
                "destination": f"{destination['lng']},{destination['lat']}"
            }
            car_resp = requests.get(car_url, headers=headers, params=car_params, timeout=settings.KAKAO_TIMEOUT)
            car_resp.raise_for_status()
            car_data = car_resp.json()

            car_path = extract_path(car_data)
            car_path = filter_safe_path(car_path)

            car_summary = car_data.get("routes", [])[0].get("summary", {})
            routes.append({
                "mode": "car",
                "duration_sec": car_summary.get("duration", 0),
                "distance_m": car_summary.get("distance", 0),
                "polyline": car_path
            })
        except Exception as e:
            return Response({"status": "error", "message": "차량 경로 계산 실패", "code": 502,
                            "data": {"detail": str(e)}}, status=502)

        return Response({
            "status": "success",
            "message": "안전 경로 탐색 성공",
            "code": 200,
            "data": {"routes": routes}
        })

class ORSProxyViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["post"], url_path="safe-routes")
    def safe_routes(self, request):
        origin = request.data.get("origin")
        destination = request.data.get("destination")
        avoid_incidents = request.data.get("avoid_incidents", True)
        avoid_status = request.data.get("avoid_status", ["UNDER_REPAIR", "TEMP_REPAIRED"])
        avoid_radius_m = int(request.data.get("avoid_radius_m", 200))

        if not origin or not destination:
            return Response({
                "status": "error",
                "message": "출발/도착 좌표 누락",
                "code": 400,
                "data": {"detail": "origin, destination required"}
            }, status=400)

        url = f"{settings.ORS_BASE}/v2/directions/foot-walking/json"
        headers = {
            "Authorization": settings.ORS_API_KEY,
            "Content-Type": "application/json; charset=utf-8"
        }

        avoid_polygons = None
        if avoid_incidents:
            incidents = RecoveryIncident.objects.filter(status__in=avoid_status)
            polygons = [make_circle_polygon(float(inc.lat), float(inc.lng), avoid_radius_m)
                        for inc in incidents]
            if polygons:
                avoid_polygons = {
                    "type": "MultiPolygon",
                    "coordinates": [p["coordinates"] for p in polygons]
                }

        body = {
            "coordinates": [
                [origin["lng"], origin["lat"]],
                [destination["lng"], destination["lat"]],
            ],
            "elevation": True,
            "geometry": True,
            "geometry_format": "polyline",
            "format": "json"
        }
        if avoid_polygons:
            body["avoid_polygons"] = avoid_polygons

        try:
            r = requests.post(url, headers=headers, json=body, timeout=settings.ORS_TIMEOUT)
            r.raise_for_status()
            data = r.json()

            route = data["routes"][0]
            summary = route["summary"]
            geometry_data = route["geometry"]

            if isinstance(geometry_data, str):
                try:
                    polyline = decode_polyline(geometry_data, precision=1e5)
                except Exception:
                    polyline = decode_polyline(geometry_data, precision=1e6)
            else:
                polyline = [[lat, lng] for lng, lat in geometry_data]

            RouteLog.objects.create(
                origin_lat=origin["lat"],
                origin_lng=origin["lng"],
                dest_lat=destination["lat"],
                dest_lng=destination["lng"],
                mode="walk",
                provider="ors",
                duration_sec=int(summary["duration"]),
                distance_m=int(summary["distance"]),
                raw_response=data
            )

            return Response({
                "status": "success",
                "message": "안전 도보 경로 탐색 성공",
                "code": 200,
                "data": {
                    "mode": "walk",
                    "duration_sec": summary["duration"],
                    "distance_m": summary["distance"],
                    "polyline": polyline
                }
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": "openrouteservice 호출 실패",
                "code": 502,
                "data": {"detail": str(e)}
            }, status=502)

def decode_polyline(encoded, precision=1e5):
    coords = []
    index, lat, lng = 0, 0, 0
    while index < len(encoded):
        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        result, shift = 0, 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coords.append([lat / precision, lng / precision])
    return coords