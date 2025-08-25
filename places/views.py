from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Prefetch
from places.models import Place
from coupons.models import Coupon
from .serializers import CATEGORY_IMAGES
from .utils import haversine
import math

CLIENT_DISTANCE_LIMIT_M = 1000

class PlaceViewSet(viewsets.ViewSet):
    def list(self, request):
        category = request.query_params.get("category")
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

        qs = Place.objects.all()
        if category:
            qs = qs.filter(category=category)

        # 쿠폰 prefetch
        active_coupons_qs = Coupon.objects.filter(is_active=True).only("id", "title", "starts_at", "ends_at", "place_id")
        qs = qs.prefetch_related(Prefetch("coupon_set", queryset=active_coupons_qs))

        items = []
        if user_lat and user_lng:
            user_lat = float(user_lat)
            user_lng = float(user_lng)

        for p in qs:
            dist = None
            if user_lat and user_lng:
                dist = haversine(user_lat, user_lng, float(p.lat), float(p.lng))
                if dist > CLIENT_DISTANCE_LIMIT_M:
                    continue

            coupons = [
                {
                    "id": c.id,
                    "title": c.title,
                    "starts_at": c.starts_at,
                    "ends_at": c.ends_at,
                }
                for c in getattr(p, "coupon_set").all()
            ]

            items.append({
                "name": p.name,
                "address": p.address,
                "lat": float(p.lat),
                "lng": float(p.lng),
                "category": p.category,
                "main_image_url": p.image_url or CATEGORY_IMAGES.get(p.category),
                "kakao_place_id": p.kakao_place_id,
                "kakao_url": p.place_url,
                "distance_m": int(dist) if dist else None,
                "coupons": coupons,
            })

        total_count = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]

        return Response({
            "status": "success",
            "message": "상점 목록 조회 성공",
            "code": 200,
            "data": {
                "items": paginated,
                "count": total_count,
                "page": page,
                "page_size": page_size
            }
        }, status=status.HTTP_200_OK)