from rest_framework import serializers
from .models import CitizenReport, CitizenReportImage, BotMessage


class CitizenReportImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenReportImage
        fields = ["id", "image_url", "created_at"]


class BotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotMessage
        fields = ["id", "role", "message", "created_at"]


class CitizenReportSerializer(serializers.ModelSerializer):
    images = CitizenReportImageSerializer(many=True, read_only=True)
    messages = BotMessageSerializer(many=True, read_only=True)

    class Meta:
        model = CitizenReport
        fields = ["id", "text", "lat", "lng", "status", "risk_score", "created_at", "images", "messages"]


class CitizenReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenReport
        fields = ["id", "text", "lat", "lng"]