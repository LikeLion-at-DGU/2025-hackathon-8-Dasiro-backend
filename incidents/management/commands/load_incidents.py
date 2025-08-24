import json
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from districts.models import District
from incidents.models import RecoveryIncident
from math import radians, sin, cos, sqrt, atan2


def normalize_address(address: str) -> str:
    """주소에서 '구 + 동'까지만 추출"""
    if not address:
        return ""
    match = re.search(r'([가-힣]+구)\s([가-힣0-9]+동)', address)
    if match:
        dong = match.group(2)
        dong = re.sub(r'제?\d+동', "동", dong)  # 제1동 → 동
        return dong
    return ""


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi/2)**2 + cos(phi1)*cos(phi2)*sin(d_lambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def get_nearest_district(lat, lng, max_distance=500):
    nearest = None
    min_dist = float("inf")
    for d in District.objects.all():
        dist = haversine(lat, lng, d.center_lat, d.center_lng)
        if dist < min_dist and dist <= max_distance:
            min_dist = dist
            nearest = d
    return nearest


def parse_korean_datetime(date_str: str):
    """'YYYY-MM-DD 오전/오후 HH:MM' → datetime"""
    if not date_str:
        return None
    try:
        if "오전" in date_str or "오후" in date_str:
            date_str = (
                date_str.replace("오전", "AM").replace("오후", "PM")
            )
            return datetime.strptime(date_str.strip(), "%Y-%m-%d %p %I:%M")
        else:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except Exception:
        return None

class Command(BaseCommand):
    help = "서울시 복구완료 사고 incidents.json을 읽어서 RecoveryIncident 테이블에 저장합니다."

    def handle(self, *args, **kwargs):
        file_path = "data/incidents.json"
        cutoff = datetime(2023, 1, 1)  # 2023년 1월 1일 이전 데이터 제외

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        skipped = 0

        for item in data:
            address = item.get("사고발생위치")
            lat = float(item.get("위도"))
            lng = float(item.get("경도"))
            occurred_at_str = item.get("사고발생일자")

            occurred_at = parse_korean_datetime(occurred_at_str)
            if not occurred_at or occurred_at < cutoff:
                skipped += 1
                continue

            norm_dong = normalize_address(address)
            district = None
            if norm_dong:
                district = District.objects.filter(dong__contains=norm_dong).first()

            if not district:
                district = get_nearest_district(lat, lng)

            RecoveryIncident.objects.create(
                address=address,
                lat=lat,
                lng=lng,
                status="복구완료",   # 무조건 복구완료
                district=district,
                occurred_at=occurred_at
            )
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count}개의 사고를 저장했습니다. (스킵된 건수: {skipped})"
            )
        )