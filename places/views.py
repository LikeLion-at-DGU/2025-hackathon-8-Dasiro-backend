from rest_framework import viewsets, status
from rest_framework.response import Response
from django.conf import settings
import requests

from incidents.models import RecoveryIncident
from .utils import haversine


CATEGORY_MAP = {
    "음식점": "FD6",
    "카페": "CE7",
    "편의점": "CS2"
}


class PlaceViewSet(viewsets.ViewSet):

    def list(self, request):
        category = request.query_params.get("category")  # 음식점, 카페, 편의점
        user_lat = request.query_params.get("lat")
        user_lng = request.query_params.get("lng")

        category_code = CATEGORY_MAP.get(category) if category else "FD6,CE7,CS2"

        kakao_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}

        incidents = RecoveryIncident.objects.filter(status=RecoveryIncident.RecoveryStatus.RECOVERED)

        candidate_places = []

        for incident in incidents:
            params = {
                "query": "맛집",
                "category_group_code": category_code,
                "x": float(incident.lng),
                "y": float(incident.lat),
                "radius": 200
            }
            resp = requests.get(kakao_url, headers=headers, params=params)

            if resp.status_code != 200:
                continue

            docs = resp.json().get("documents", [])
            for doc in docs:
                place = {
                    "name": doc["place_name"],
                    "address": doc["road_address_name"] or doc["address_name"],
                    "lat": float(doc["y"]),
                    "lng": float(doc["x"]),
                    "category": doc["category_group_code"],
                    "place_url": doc["place_url"],
                }
                candidate_places.append(place)

        if user_lat and user_lng:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            filtered = []
            for place in candidate_places:
                dist = haversine(user_lat, user_lng, place["lat"], place["lng"])
                if dist <= 1000:  # 1km 이내만으로 설정
                    filtered.append(place)
            candidate_places = filtered

        return Response({
            "status": "success",
            "count": len(candidate_places),
            "items": candidate_places
        }, status=status.HTTP_200_OK)