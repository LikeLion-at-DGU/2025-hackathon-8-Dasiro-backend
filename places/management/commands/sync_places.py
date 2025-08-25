from django.core.management.base import BaseCommand
from places.services import sync_nearby_places_for_incident
from incidents.models import RecoveryIncident

class Command(BaseCommand):
    help = "복구완료된 싱크홀 기준으로 카카오 상점 동기화"

    def handle(self, *args, **options):
        ids = list(RecoveryIncident.objects.filter(
            status=RecoveryIncident.RecoveryStatus.RECOVERED
        ).values_list("id", flat=True))
        total = 0
        for i in ids:
            total += sync_nearby_places_for_incident(i)
        self.stdout.write(self.style.SUCCESS(f"동기화 완료: {total} 개 상점 upsert"))