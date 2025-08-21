from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import *
from .serializers import *

class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "쿠폰 상세 조회 성공",
            "code": 200,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
