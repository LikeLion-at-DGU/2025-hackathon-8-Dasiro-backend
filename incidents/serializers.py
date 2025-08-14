from rest_framework import serializers
from .models import *

class RecoveryIncidentListSerializer(serializers.ModelSerializer):
    distance_m = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = RecoveryIncident
        fields = [
            'id', 'occurred_at', 'address', 'lat', 'lng',
            'cause', 'method', 'status', 'note', 'image_url',
            'images_count', 'distance_m'
        ]

class RecoveryIncidentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryIncident
        fields = [
            'id', 'occurred_at', 'address', 'lat', 'lng',
            'cause', 'method', 'status', 'note', 'image_url'
        ]