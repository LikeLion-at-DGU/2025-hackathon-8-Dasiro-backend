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

    ground_stability = models.CharField(max_length=2, choices=RiskGrade.choices)   # 지반 안정성(굴착공사현장)
    groundwater_impact = models.CharField(max_length=2, choices=RiskGrade.choices) # 지하수 영향
    underground_density = models.CharField(max_length=2, choices=RiskGrade.choices) # 지하 구조물 밀집도
    old_building_dist = models.CharField(max_length=2, choices=RiskGrade.choices)  # 노후 건물 분포
    incident_history = models.CharField(max_length=2, choices=RiskGrade.choices, null=True, blank=True)   # 추가함: 싱크홀 사고 이력

    analysis_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("district", "as_of_date")
        indexes = [
            models.Index(fields=["total_grade"]),
        ]

class GuMetric(models.Model):
    sigungu = models.CharField(max_length=50)
    sido = models.CharField(max_length=50)
    as_of_date = models.DateField()
    total_grade = models.CharField(max_length=2, choices=DistrictMetric.RiskGrade.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sigungu", "as_of_date")
        indexes = [
            models.Index(fields=["total_grade"]),
        ]

    def __str__(self):
        return f"{self.sido} {self.sigungu} ({self.as_of_date}): {self.total_grade}"
