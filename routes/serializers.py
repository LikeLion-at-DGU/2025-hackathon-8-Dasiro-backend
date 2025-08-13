from rest_framework import serializers
from .models import RouteLog

class RouteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteLog
        fields = '__all__'