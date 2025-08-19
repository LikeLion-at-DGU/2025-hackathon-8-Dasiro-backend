from rest_framework import serializers
from .models import Place

CATEGORY_IMAGES = {
    'FOOD': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/food.png',
    'CAFE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/cafe.png',
    'CONVENIENCE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/convenience.png',
}

class PlaceSerializer(serializers.ModelSerializer):
    final_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ['id', 'name', 'address', 'lat', 'lng', 'category', 'place_url', 'final_image_url']

    def get_final_image_url(self, obj):
        if obj.image_url:
            return obj.image_url
        return CATEGORY_IMAGES.get(obj.category, "")