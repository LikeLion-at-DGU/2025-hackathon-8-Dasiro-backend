import csv
from django.core.management.base import BaseCommand
from districts.models import District

class Command(BaseCommand):
    help = "서울시 행정동 CSV를 읽어서 District 테이블에 저장합니다."

    def handle(self, *args, **kwargs):
        file_path = "data/서울시행정동.csv"

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                District.objects.update_or_create(
                    sido=row['시도명'],
                    sigungu=row['시군구명'],
                    dong=row['읍면동명'],
                    defaults={
                        'center_lat': float(row['Y']),
                        'center_lng': float(row['X']),
                        'is_safezone': False,
                    }
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f"{count}개의 행정동을 저장했습니다."))