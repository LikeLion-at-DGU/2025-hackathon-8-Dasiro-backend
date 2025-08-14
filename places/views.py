from django.db.models import F
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from math import radians, sin, cos, acos

from incidents.models import RecoveryIncident
from .models import Place, PlaceIncidentProximity

CATEGORY_IMAGES = {
    'FOOD': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/food.png',
    'CAFE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/cafe.png',
    'CONVENIENCE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/convenience.png',
    'OTHER': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/other.png',
}

def api_response(status_str, message, code, data):
    return Response(
        {
            "status": status_str,
            "message": message,
            "code": code,
            "data": data
        },
        status=code
    )

def apply_default_images(qs):
    for place in qs:
        if not place.main_image_url:
            place.main_image_url = CATEGORY_IMAGES.get(place.category)
    return qs

def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371000  # meters
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    return R * acos(
        cos(lat1) * cos(lat2) * cos(lng2 - lng1) + sin(lat1) * sin(lat2)
    )

class PlaceViewSet(viewsets.ViewSet):
    def list(self, request):
        category = request.GET.get('category')
        if category and category not in CATEGORY_IMAGES.keys():
            return api_response(
                "error",
                "잘못된 카테고리",
                400,
                {"detail": f"category must be one of {','.join(CATEGORY_IMAGES.keys())}"}
            )

        # 1️⃣ 복구완료 사고 목록
        recovered_incidents = RecoveryIncident.objects.filter(status='RECOVERED')

        # 2️⃣ 복구완료 사고 주변 200m 이내 상점만
        places_in_radius = set()
        for incident in recovered_incidents:
            nearby_places = Place.objects.all()
            if category:
                nearby_places = nearby_places.filter(category=category)

            for p in nearby_places:
                dist = calculate_distance(float(incident.lat), float(incident.lng), float(p.lat), float(p.lng))
                if dist <= 200:
                    places_in_radius.add(p.id)

        qs = Place.objects.filter(id__in=places_in_radius)
        qs = apply_default_images(qs)

        items = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "address": p.address,
                "lat": p.lat,
                "lng": p.lng,
                "main_image_url": p.main_image_url,
                "kakao_place_id": p.kakao_place_id,
                "kakao_url": p.kakao_url,
                "distance_m": None
            }
            for p in qs
        ]

        return api_response(
            "success",
            "상점 목록 조회 성공",
            200,
            {
                "items": items,
                "count": len(items)
            }
        )
        
    @action(detail=False, methods=['get'], url_path="near")
    def near(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lng = float(request.GET.get('lng'))
        except (TypeError, ValueError):
            return api_response("error", "lat/lng 파라미터가 필요합니다.", 400, {})

        radius = float(request.GET.get('radius', 1000))
        category = request.GET.get('category')

        qs = Place.objects.filter(
            id__in=PlaceIncidentProximity.objects.filter(
                incident__status='RECOVERED'
            ).values_list('place_id', flat=True)
        )

        if category and category in CATEGORY_IMAGES.keys():
            qs = qs.filter(category=category)

        qs = apply_default_images(qs)

        count = 0
        for p in qs:
            dist = calculate_distance(lat, lng, float(p.lat), float(p.lng))
            if dist <= radius:
                count += 1

        return api_response(
            "success",
            "반경 내 상점 개수 조회 성공",
            200,
            {"count": count}
        )

    @action(detail=False, methods=['get'], url_path="near-incidents")
    def near_incidents(self, request):
        try:
            incident_id = int(request.GET.get('incident_id'))
        except (TypeError, ValueError):
            return api_response("error", "incident_id 파라미터가 필요합니다.", 400, {})

        radius = float(request.GET.get('radius', 200))
        category = request.GET.get('category')

        try:
            incident = RecoveryIncident.objects.get(id=incident_id)
        except RecoveryIncident.DoesNotExist:
            return api_response("error", "해당 incident가 존재하지 않습니다.", 404, {})

        qs = Place.objects.all()
        if category and category in CATEGORY_IMAGES.keys():
            qs = qs.filter(category=category)

        qs = apply_default_images(qs)

        count = 0
        for p in qs:
            dist = calculate_distance(float(incident.lat), float(incident.lng), float(p.lat), float(p.lng))
            if dist <= radius:
                count += 1

        return api_response(
            "success",
            "사고 주변 상점 개수 조회 성공",
            200,
            {"count": count}
        )