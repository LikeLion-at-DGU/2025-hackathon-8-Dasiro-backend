from rest_framework import serializers
from .models import Place, PlaceIncidentProximity

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'

class PlaceIncidentProximitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceIncidentProximity
        fields = '__all__'