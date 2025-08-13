from rest_framework import serializers
from .models import RecoveryIncident, RecoveryIncidentImage

class RecoveryIncidentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryIncidentImage
        fields = '__all__'

class RecoveryIncidentSerializer(serializers.ModelSerializer):
    images = RecoveryIncidentImageSerializer(many=True, read_only=True)

    class Meta:
        model = RecoveryIncident
        fields = '__all__'