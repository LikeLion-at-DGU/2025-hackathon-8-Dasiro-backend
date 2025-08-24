from rest_framework import serializers
from .models import RecoveryIncident


class RecoveryIncidentListSerializer(serializers.ModelSerializer):
    distance_m = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = RecoveryIncident
        fields = [
            "id",
            "occurred_at",
            "address",
            "lat",
            "lng",
            "cause",
            "method",
            "status",
            "note",
            "image_url",
            "distance_m",
        ]


class RecoveryIncidentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryIncident
        fields = [
            "id",
            "occurred_at",
            "address",
            "lat",
            "lng",
            "cause",
            "method",
            "status",
            "note",
            "image_url",
        ]

class RecoveryIncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryIncident
        fields = [
            "address",
            "lat",
            "lng",
            "cause",
            "method",
            "note",
            "image_url",
            "status",
            "district",
        ]