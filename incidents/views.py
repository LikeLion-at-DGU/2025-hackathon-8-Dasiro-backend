from django.db.models import Count
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RecoveryIncident
from .serializers import *


def api_response(status: str, message: str, code: int, data: dict):
    return Response({
        "status": status,
        "message": message,
        "code": code,
        "data": data
    }, status=code)


class RecoveryIncidentViewSet(viewsets.ViewSet):

    def _apply_status_filter(self, queryset, status_filter):
        if status_filter:
            status_values = status_filter.split(",")
            valid_status = dict(RecoveryIncident.RecoveryStatus.choices).keys()
            if not all(s in valid_status for s in status_values):
                return None, api_response(
                    "error",
                    "유효하지 않은 status 값",
                    400,
                    {"detail": f"status must be CSV of {list(valid_status)}"}
                )
            queryset = queryset.filter(status__in=status_values)
        return queryset, None

    def _apply_distance_filter(self, queryset, lat, lng, radius):
        queryset = queryset.annotate(
            distance_m=6371000 * ACos(
                Cos(Radians(lat)) *
                Cos(Radians("lat")) *
                Cos(Radians("lng") - Radians(lng)) +
                Sin(Radians(lat)) * Sin(Radians("lat"))
            )
        ).filter(distance_m__lte=radius)
        return queryset

    def list(self, request):
        status_filter = request.GET.get("status")
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius")

        queryset = RecoveryIncident.objects.annotate(images_count=Count("images"))

        queryset, error_response = self._apply_status_filter(queryset, status_filter)
        if error_response:
            return error_response

        if lat and lng and radius:
            try:
                lat = float(lat)
                lng = float(lng)
                radius = float(radius)
            except ValueError:
                return api_response("error", "lat/lng/radius 값이 유효하지 않습니다", 400, {})

            queryset = self._apply_distance_filter(queryset, lat, lng, radius)
        else:
            queryset = queryset.annotate(distance_m=None)

        serializer = RecoveryIncidentListSerializer(queryset, many=True)
        return api_response("success", "사고 목록 조회 성공", 200, {
            "items": serializer.data,
            "count": queryset.count()
        })

    def retrieve(self, request, pk=None):
        incident = get_object_or_404(RecoveryIncident.objects.prefetch_related("images"), id=pk)
        serializer = RecoveryIncidentDetailSerializer(incident)
        return api_response("success", "사고 상세 조회 성공", 200, serializer.data)

    @action(detail=True, methods=["get"])
    def images(self, request, pk=None):
        incident = get_object_or_404(RecoveryIncident, id=pk)
        images = incident.images.all()
        serializer = RecoveryIncidentImageSerializer(images, many=True)
        return api_response("success", "사고 이미지 조회 성공", 200, {
            "items": serializer.data,
            "count": images.count()
        })

    @action(detail=False, methods=["get"])
    def near(self, request):
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius")
        status_filter = request.GET.get("status")

        if not (lat and lng and radius):
            return api_response("error", "lat,lng,radius required", 400, {"detail": "lat,lng required"})

        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return api_response("error", "lat/lng/radius 값이 유효하지 않습니다", 400, {})

        queryset = RecoveryIncident.objects.annotate(images_count=Count("images"))
        queryset = self._apply_distance_filter(queryset, lat, lng, radius)

        queryset, error_response = self._apply_status_filter(queryset, status_filter)
        if error_response:
            return error_response

        serializer = RecoveryIncidentListSerializer(queryset, many=True)
        return api_response("success", "주변 사고 조회 성공", 200, {
            "items": serializer.data,
            "count": queryset.count()
        })