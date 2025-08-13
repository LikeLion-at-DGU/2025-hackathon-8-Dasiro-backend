from rest_framework import serializers
from .models import CitizenReport, CitizenReportImage, BotMessage

class CitizenReportImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenReportImage
        fields = '__all__'

class BotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotMessage
        fields = '__all__'

class CitizenReportSerializer(serializers.ModelSerializer):
    images = CitizenReportImageSerializer(many=True, read_only=True)
    messages = BotMessageSerializer(many=True, read_only=True)

    class Meta:
        model = CitizenReport
        fields = '__all__'