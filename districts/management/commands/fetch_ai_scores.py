from django.core.management.base import BaseCommand
from districts.models import District, DistrictMetric, GuMetric
import requests
from datetime import date

class Command(BaseCommand):
    help = "Fetch AI dong_scores and district_scores, save to DB"

    def handle(self, *args, **options):
        today = date.today()

        # 동별 저장
        ai_url = "http://52.78.104.121:8001/dong_scores"
        resp = requests.get(ai_url)
        resp.raise_for_status()
        data = resp.json()

        dong_created, dong_updated = 0, 0
        safezone_set, safezone_unset = 0, 0

        for item in data:
            dong = item["dong"].strip()
            gu = item["gu"].strip()

            district = District.objects.filter(dong=dong, sigungu=gu).first()
            if not district:
                continue

            metric, is_new = DistrictMetric.objects.update_or_create(
                district=district,
                as_of_date=today,
                defaults={
                    "total_grade": f"G{item['final_grade_simple']}",
                    "ground_stability": f"G{item['construction_grade']}",
                    "groundwater_impact": f"G{item['groundwater']}",
                    "underground_density": f"G{item['subway_grade']}",
                    "old_building_dist": f"G{item['old']}",
                    "incident_history": f"G{item['incident_grade']}",
                }
            )

            # Safezone 처리 (G1만 True, 나머지는 False)
            if metric.total_grade == "G1":
                if not district.is_safezone:
                    district.is_safezone = True
                    district.save(update_fields=["is_safezone"])
                    safezone_set += 1
            else:
                if district.is_safezone:
                    district.is_safezone = False
                    district.save(update_fields=["is_safezone"])
                    safezone_unset += 1

            if is_new: 
                dong_created += 1
            else: 
                dong_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"[동별] AI 위험도 저장 완료: 신규 {dong_created}건, 업데이트 {dong_updated}건, "
            f"Safezone 설정 {safezone_set}건, 해제 {safezone_unset}건"
        ))

        # 구별 저장
        sigungus = District.objects.values_list("sigungu", "sido").distinct()
        gu_created, gu_updated = 0, 0

        for sigungu, sido in sigungus:
            gu_url = f"http://52.78.104.121:8001/district_scores/{sigungu}"
            try:
                gu_resp = requests.get(gu_url, timeout=5)
                gu_resp.raise_for_status()
                gu_data = gu_resp.json()
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"[구별] {sigungu} 조회 실패: {e}"
                ))
                continue

            metric, is_new = GuMetric.objects.update_or_create(
                sigungu=sigungu,
                as_of_date=today,
                defaults={
                    "sido": sido,
                    "total_grade": f"G{gu_data['final_grade_simple']}",
                }
            )
            if is_new:
                gu_created += 1
            else:
                gu_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"[구별] AI 위험도 저장 완료: 신규 {gu_created}건, 업데이트 {gu_updated}건"
        ))