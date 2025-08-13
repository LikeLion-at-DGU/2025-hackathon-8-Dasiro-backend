from rest_framework import serializers
from .models import *

class RecoveryIncidentListSerializer(serializers.ModelSerializer):
    images_count = serializers.IntegerField()
    distance_m = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = RecoveryIncident
        fields = ['id', 'occurred_at', 'address', 'lat', 'lng', 'cause', 'method', 'status', 'images_count', 'distance_m']

class RecoveryIncidentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryIncidentImage
        fields = ['id', 'image_url', 'created_at']

class RecoveryIncidentDetailSerializer(serializers.ModelSerializer):
    images = RecoveryIncidentImageSerializer(many=True)

    class Meta:
        model = RecoveryIncident
        fields = ['id', 'occurred_at', 'address', 'lat', 'lng', 'cause', 'method', 'status', 'images', 'note']
