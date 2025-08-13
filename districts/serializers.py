from rest_framework import serializers
from .models import District, DistrictMetric

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class DistrictMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistrictMetric
        fields = '__all__'