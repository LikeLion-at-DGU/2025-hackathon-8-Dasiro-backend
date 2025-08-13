from django.db import models

class District(models.Model):
    sido = models.CharField(max_length=50)
    sigungu = models.CharField(max_length=50)
    dong = models.CharField(max_length=50)
    center_lat = models.DecimalField(max_digits=10, decimal_places=7)
    center_lng = models.DecimalField(max_digits=10, decimal_places=7)
    is_safezone = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sido} {self.sigungu} {self.dong}"


class DistrictMetric(models.Model):
    class RiskGrade(models.TextChoices):
        G1 = 'G1', '1등급'
        G2 = 'G2', '2등급'
        G3 = 'G3', '3등급'
        G4 = 'G4', '4등급'
        G5 = 'G5', '5등급'

    district = models.ForeignKey(District, on_delete=models.CASCADE)
    as_of_date = models.DateField()
    total_grade = models.CharField(max_length=2, choices=RiskGrade.choices)
    ground_stability = models.CharField(max_length=2, choices=RiskGrade.choices)
    groundwater_impact = models.CharField(max_length=2, choices=RiskGrade.choices)
    underground_density = models.CharField(max_length=2, choices=RiskGrade.choices)
    old_building_dist = models.CharField(max_length=2, choices=RiskGrade.choices)
    analysis_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("district", "as_of_date")
        indexes = [
            models.Index(fields=["total_grade"]),
        ]

    def __str__(self):
        return f"{self.district} ({self.total_grade})"