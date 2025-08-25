import requests
from django.conf import settings
from places.models import Place
from incidents.models import RecoveryIncident
from places.serializers import CATEGORY_IMAGES

CATEGORY_MAP = {"FOOD": "FD6", "CAFE": "CE7", "CONVENIENCE": "CS2"}
REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}
KAKAO_SEARCH_RADIUS_M = 50

def sync_nearby_places_for_incident(incident_id: int, categories=None) -> int:
    if categories is None:
        categories = ["FOOD", "CAFE", "CONVENIENCE"]

    try:
        incident = RecoveryIncident.objects.only("lat", "lng").get(id=incident_id)
    except RecoveryIncident.DoesNotExist:
        return 0

    kakao_url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_KEY}"}
    upserts = 0

    for cat in categories:
        code = CATEGORY_MAP[cat]
        params = {
            "category_group_code": code,
            "x": float(incident.lng),
            "y": float(incident.lat),
            "radius": KAKAO_SEARCH_RADIUS_M,
            "size": 15,
            "page": 1,
        }

        while True:
            resp = requests.get(kakao_url, headers=headers, params=params, timeout=5)
            if resp.status_code != 200:
                break

            docs = resp.json().get("documents", [])
            if not docs:
                break

            for doc in docs:
                kakao_place_id = doc["id"]
                mapped_cat = REVERSE_CATEGORY_MAP.get(doc["category_group_code"], cat)

                _, _ = Place.objects.update_or_create(
                    kakao_place_id=kakao_place_id,
                    defaults={
                        "name": doc["place_name"],
                        "address": doc["road_address_name"] or doc["address_name"] or "",
                        "lat": float(doc["y"]),
                        "lng": float(doc["x"]),
                        "category": mapped_cat,
                        "place_url": doc["place_url"],
                        "image_url": CATEGORY_IMAGES.get(mapped_cat),
                    }
                )
                upserts += 1

            if resp.json().get("meta", {}).get("is_end", True):
                break
            params["page"] += 1

    return upserts