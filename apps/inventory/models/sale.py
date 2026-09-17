from django.db import models

from apps.core.models import BaseModel


class Sale(BaseModel):
    student = models.ForeignKey(
        "inventory.Student",
        on_delete=models.PROTECT,
        related_name="sales",
    )

    # Kept temporarily for existing/historical sales.
    student_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    # Kept temporarily for existing/historical sales.
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
        if self.student:
            return (
                f"{self.student.admission_number or ''} - "
                f"{self.student.firstname} "
                f"{self.student.surname}"
            )

        return (
            f"{self.student_number} - "
            f"{self.student_name}"
        )