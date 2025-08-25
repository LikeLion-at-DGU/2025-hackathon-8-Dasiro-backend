from django.core.management.base import BaseCommand
from places.models import Place
from places.serializers import CATEGORY_IMAGES

class Command(BaseCommand):
    help = "이미지 없는 Place에 카테고리 대표 이미지 채우기"

    def handle(self, *args, **options):
        updated = 0
        for p in Place.objects.filter(image_url__isnull=True):
            img = CATEGORY_IMAGES.get(p.category)
            if img:
                p.image_url = img
                p.save(update_fields=["image_url"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Backfilled images: {updated}"))