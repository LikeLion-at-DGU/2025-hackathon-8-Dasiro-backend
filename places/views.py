from rest_framework import viewsets, status
from rest_framework.response import Response
from django.conf import settings
import requests

from incidents.models import RecoveryIncident
from coupons.models import Coupon
from places.models import Place
from .utils import haversine
from .serializers import CATEGORY_IMAGES


CATEGORY_MAP = {
    "FOOD": "FD6",
    "CAFE": "CE7",
    "CONVENIENCE": "CS2",
}

class PlaceViewSet(viewsets.ViewSet):
    def list(self, request):
        category = request.query_params.get("category")  # FOOD, CAFE, CONVENIENCE
        user_lat = request.query_params.get("lat")
        user_lng = request.query_params.get("lng")

        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))
        except ValueError:
            return Response({
                "status": "error",
                "message": "page, page_size 값이 올바르지 않습니다.",
                "code": 400,
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if category:
            if category not in CATEGORY_MAP:
                return Response({
                    "status": "error",
                    "message": "잘못된 카테고리",
                    "code": 400,
                    "data": {"detail": "category must be one of FOOD, CAFE, CONVENIENCE"}
                }, status=status.HTTP_400_BAD_REQUEST)
            category_codes = [CATEGORY_MAP[category]]
        else:
            category_codes = ["FD6", "CE7", "CS2"]

        kakao_url = "https://dapi.kakao.com/v2/local/search/category.json"
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}

        # DB 기반 상점 먼저 불러오기
        candidate_places = []
        db_places = Place.objects.all()
        for p in db_places:
            coupons = Coupon.objects.filter(
                place=p, is_active=True
            ).values("id", "title", "starts_at", "ends_at")
            candidate_places.append({
                "name": p.name,
                "address": p.address,
                "lat": float(p.lat),
                "lng": float(p.lng),
                "category": p.category,
                "main_image_url": p.image_url or CATEGORY_IMAGES.get(p.category, None),
                "kakao_place_id": p.kakao_place_id,
                "kakao_url": p.place_url,
                "distance_m": None,
                "coupons": list(coupons),
            })

        # 카카오 API 기반 상점 가져오기 + DB 캐싱
        incidents = RecoveryIncident.objects.filter(
            status=RecoveryIncident.RecoveryStatus.RECOVERED
        )
        for incident in incidents:
            for code in category_codes:
                params = {
                    "category_group_code": code,
                    "x": float(incident.lng),
                    "y": float(incident.lat),
                    "radius": 50,
                }
                resp = requests.get(kakao_url, headers=headers, params=params)
                if resp.status_code != 200:
                    continue

                docs = resp.json().get("documents", [])
                for doc in docs:
                    kakao_place_id = doc["id"]

                    place_obj, created = Place.objects.get_or_create(
                        kakao_place_id=kakao_place_id,
                        defaults={
                            "name": doc["place_name"],
                            "address": doc["road_address_name"] or doc["address_name"],
                            "lat": float(doc["y"]),
                            "lng": float(doc["x"]),
                            "category": category if category else code,
                            "image_url": CATEGORY_IMAGES.get(category, None),
                            "place_url": doc["place_url"],
                        }
                    )

                    coupons = Coupon.objects.filter(
                        place=place_obj, is_active=True
                    ).values("id", "title", "starts_at", "ends_at")

                    candidate_places.append({
                        "name": place_obj.name,
                        "address": place_obj.address,
                        "lat": float(place_obj.lat),
                        "lng": float(place_obj.lng),
                        "category": place_obj.category,
                        "main_image_url": place_obj.image_url or CATEGORY_IMAGES.get(place_obj.category, None),
                        "kakao_place_id": place_obj.kakao_place_id,
                        "kakao_url": place_obj.place_url,
                        "distance_m": None,
                        "coupons": list(coupons),
                    })

        if user_lat and user_lng:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            filtered = []
            for place in candidate_places:
                dist = haversine(user_lat, user_lng, place["lat"], place["lng"])
                if dist <= 200:
                    place["distance_m"] = int(dist)
                    filtered.append(place)
            candidate_places = filtered

        total_count = len(candidate_places)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_places = candidate_places[start:end]

        return Response({
            "status": "success",
            "message": "상점 목록 조회 성공",
            "code": 200,
            "data": {
                "items": paginated_places,
                "count": total_count,
                "page": page,
                "page_size": page_size
            }
        }, status=status.HTTP_200_OK)