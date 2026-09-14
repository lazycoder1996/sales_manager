from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models.sale import Sale


class Payment(BaseModel):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    cash_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    momo_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    paid_at = models.DateTimeField()

    class Meta:
        db_table = "payments"
        ordering = [
            "-paid_at",
            "-created_at",
        ]

    def __str__(self):
        return (
            f"Payment - "
            f"{self.sale.student_number}"
        )