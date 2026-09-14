from django.db import models

from apps.core.models import BaseModel


class Sale(BaseModel):
    student_number = models.CharField(
        max_length=50,
        unique=True,
    )

    student_name = models.CharField(
        max_length=255,
    )

    sold_at = models.DateTimeField()

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "sales"
        ordering = [
            "-sold_at",
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.student_number} - "
            f"{self.student_name}"
        )