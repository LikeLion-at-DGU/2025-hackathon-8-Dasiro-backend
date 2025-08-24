from django.shortcuts import get_object_or_404
from django.db.models import Value, FloatField, F
from django.db.models.functions import ACos, Cos, Sin, Radians
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import RecoveryIncident
from .serializers import (
    RecoveryIncidentListSerializer,
    RecoveryIncidentDetailSerializer,
    RecoveryIncidentCreateSerializer,
)
from districts.models import District
import re
from math import radians, sin, cos, sqrt, atan2


def normalize_address(address: str) -> str:
    if not address:
        return ""

    match = re.search(r'([가-힣]+구)\s([가-힣0-9]+동)', address)
    if match:
        dong = match.group(2)
        dong = re.sub(r'제?\d+동', "동", dong)
        return dong

    return ""


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi/2)**2 + cos(phi1)*cos(phi2)*sin(d_lambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def get_nearest_district(lat, lng, max_distance=500):
    nearest = None
    min_dist = float("inf")
    for d in District.objects.all():
        dist = haversine(lat, lng, d.center_lat, d.center_lng)
        if dist < min_dist and dist <= max_distance:
            min_dist = dist
            nearest = d
    return nearest

class RecoveryIncidentViewSet(viewsets.ModelViewSet):
    queryset = RecoveryIncident.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return RecoveryIncidentListSerializer
        elif self.action == "retrieve":
            return RecoveryIncidentDetailSerializer
        return RecoveryIncidentCreateSerializer 

    def _api_response(self, status_str, message, code, data):
        return Response(
            {
                "status": status_str,
                "message": message,
                "code": code,
                "data": data,
            },
            status=code,
        )

    def _apply_status_filter(self, queryset, status_filter):
        if status_filter:
            status_values = status_filter.split(",")
            valid_status = dict(RecoveryIncident.RecoveryStatus.choices).keys()
            if not all(s in valid_status for s in status_values):
                return None, self._api_response(
                    "error",
                    "유효하지 않은 status 값",
                    status.HTTP_400_BAD_REQUEST,
                    {"detail": f"status must be CSV of {list(valid_status)}"},
                )
            queryset = queryset.filter(status__in=status_values)
        return queryset, None

    def _apply_distance_filter(self, queryset, lat, lng, radius):
        if lat and lng and radius:
            try:
                lat = float(lat)
                lng = float(lng)
                radius = float(radius)
            except ValueError:
                return None, self._api_response(
                    "error", "lat/lng/radius 값이 유효하지 않습니다", 400, {}
                )

            queryset = queryset.annotate(
                distance_m=6371000
                * ACos(
                    Cos(Radians(lat))
                    * Cos(Radians(F("lat")))
                    * Cos(Radians(F("lng")) - Radians(lng))
                    + Sin(Radians(lat)) * Sin(Radians(F("lat")))
                )
            ).filter(distance_m__lte=radius)
        else:
            queryset = queryset.annotate(
                distance_m=Value(0.0, output_field=FloatField())
            )
        return queryset, None

    def perform_create(self, serializer):
        status_value = serializer.validated_data.get("status", "복구완료")
        instance = serializer.save(status=status_value)

        norm_dong = normalize_address(instance.address)
        district = None
        if norm_dong:
            district = District.objects.filter(dong__contains=norm_dong).first()

        if not district and instance.lat and instance.lng:
            district = get_nearest_district(instance.lat, instance.lng)

        instance.district = district
        instance.save()

    def list(self, request):
        status_filter = request.GET.get("status")
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius")

        queryset = RecoveryIncident.objects.all()

        queryset, error = self._apply_status_filter(queryset, status_filter)
        if error:
            return error

        queryset, error = self._apply_distance_filter(queryset, lat, lng, radius)
        if error:
            return error

        serializer = RecoveryIncidentListSerializer(queryset, many=True)
        return self._api_response(
            "success",
            "사고 목록 조회 성공",
            200,
            {"items": serializer.data, "count": queryset.count()},
        )

    def retrieve(self, request, pk=None):
        incident = get_object_or_404(RecoveryIncident, id=pk)
        serializer = RecoveryIncidentDetailSerializer(incident)
        return self._api_response("success", "사고 상세 조회 성공", 200, serializer.data)

    @action(detail=False, methods=["get"], url_path="near")
    def near(self, request):
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius")
        status_filter = request.GET.get("status")

        if not (lat and lng and radius):
            return self._api_response(
                "error",
                "lat,lng,radius required",
                400,
                {"detail": "lat,lng required"},
            )

        queryset = RecoveryIncident.objects.all()

        queryset, error = self._apply_distance_filter(queryset, lat, lng, radius)
        if error:
            return error

        queryset, error = self._apply_status_filter(queryset, status_filter)
        if error:
            return error

        serializer = RecoveryIncidentListSerializer(queryset, many=True)
        return self._api_response(
            "success",
            "주변 사고 조회 성공",
            200,
            {"items": serializer.data, "count": queryset.count()},
        )