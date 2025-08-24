from rest_framework import serializers
from .models import Place

CATEGORY_IMAGES = {
    'FOOD': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/Property+1%3D%EC%9D%8C%EC%8B%9D%EC%A0%90.png',
    'CAFE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/Property+1%3D%EC%B9%B4%ED%8E%98.png',
    'CONVENIENCE': 'https://dasirobucket.s3.ap-northeast-2.amazonaws.com/Property+1%3D%ED%8E%B8%EC%9D%98%EC%A0%90.png',
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